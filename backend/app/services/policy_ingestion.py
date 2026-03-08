import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.db.models import (
    Campaign,
    CampaignRule,
    CampaignRuleType,
    CampaignStatus,
    PolicyClause,
    PolicyClauseType,
    PolicyDocument,
    PolicyDocumentType,
    PolicyDocumentStatus,
    RebateProgram,
    UploadedFile,
    User,
)
from app.schemas.policy import PolicyReviewUpdateRequest, PolicyUploadRequest
from app.services.audit_logger import log_audit
from app.services.model_run_logger import log_model_run

logger = logging.getLogger("app")


@dataclass
class ExtractedClause:
    clause_type: PolicyClauseType
    raw_text: str
    structured_json: dict
    confidence: float


class LLMClause(BaseModel):
    clause_type: PolicyClauseType
    raw_text: str = Field(min_length=1)
    structured_json: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class LLMClauseResponse(BaseModel):
    clauses: list[LLMClause] = Field(default_factory=list)


def _extract_dates(text: str) -> list[str]:
    return re.findall(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b", text)


def _extract_gift_skus(text: str) -> list[str]:
    return sorted(set(re.findall(r"\bRPG-BAG-[A-Z]{2}\b", text.upper())))


def _extract_generic_skus(text: str) -> list[str]:
    rows = re.findall(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b", text.upper())
    return sorted(set(rows))


def _extract_percentages(text: str) -> list[float]:
    return [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)]


def _extract_currency_amounts(text: str) -> list[float]:
    return [float(value) for value in re.findall(r"(?:rm|myr)\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)]


def _extract_tier_rates(text: str) -> dict[str, float]:
    tier_rates: dict[str, float] = {}
    for tier in ("strategic", "core", "growth"):
        match = re.search(rf"{tier}\D{{0,25}}(\d+(?:\.\d+)?)\s*%", text, flags=re.IGNORECASE)
        if match:
            tier_rates[tier] = float(match.group(1))
    return tier_rates


def _extract_channel(text: str) -> str | None:
    lower = text.lower()
    mapping = {
        "direct": "direct",
        "lsp": "direct",
        "distributor": "distributor",
        "wm": "distributor",
        "project": "project",
        "em": "project",
    }
    for key, value in mapping.items():
        if key in lower:
            return value
    return None


def validate_clause_schema(data: dict) -> list[ExtractedClause]:
    validated = LLMClauseResponse.model_validate(data)
    return [
        ExtractedClause(
            clause_type=item.clause_type,
            raw_text=item.raw_text,
            structured_json=item.structured_json,
            confidence=item.confidence,
        )
        for item in validated.clauses
    ]


def _extract_text_from_foundry_response(data: dict) -> str | None:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    if isinstance(data.get("output"), list):
        text_parts: list[str] = []
        for block in data["output"]:
            if not isinstance(block, dict):
                continue
            content = block.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        text_parts.append(item["text"])
        if text_parts:
            return "".join(text_parts)
    if isinstance(data.get("choices"), list) and data["choices"]:
        message = data["choices"][0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
    return None


def _is_azure_openai_endpoint(endpoint_url: str) -> bool:
    host = urlparse(endpoint_url).netloc.lower()
    return "openai.azure.com" in host


@retry(wait=wait_exponential(multiplier=0.5, min=1, max=4), stop=stop_after_attempt(2), reraise=True)
def _call_foundry_clause_extraction(
    text: str,
    doc_type: PolicyDocumentType,
    request_id: str,
) -> list[ExtractedClause] | None:
    settings = get_settings()
    if not settings.foundry_endpoint_url or not settings.foundry_api_key:
        return None

    headers = {
        "Content-Type": "application/json",
        "x-request-id": request_id,
    }
    if _is_azure_openai_endpoint(settings.foundry_endpoint_url):
        headers["api-key"] = settings.foundry_api_key
    else:
        headers["Authorization"] = f"Bearer {settings.foundry_api_key}"

    schema_hint = {
        "clauses": [
            {
                "clause_type": "eligibility|exclusion|entitlement|pricing|rebate|incentive|payment_terms|returns|exchange|other",
                "raw_text": "exact snippet",
                "structured_json": {"key": "value"},
                "confidence": 0.9,
            }
        ]
    }
    system_prompt = (
        "Extract policy clauses. Return STRICT JSON only. "
        f"Schema: {json.dumps(schema_hint, ensure_ascii=True)}. "
        "Do not include markdown. Do not invent unsupported numbers."
    )
    user_payload = {"doc_type": doc_type.value, "text": text[:12000]}

    if "/responses" in settings.foundry_endpoint_url:
        body = {
            "model": settings.foundry_model_name,
            "instructions": system_prompt,
            "input": json.dumps(user_payload, ensure_ascii=True),
            "temperature": 0,
        }
    else:
        body = {
            "model": settings.foundry_model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
            ],
            "temperature": 0,
        }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(settings.foundry_endpoint_url, json=body, headers=headers)
        response.raise_for_status()
        text_response = _extract_text_from_foundry_response(response.json())
        if not text_response:
            return None
        parsed = json.loads(text_response)
        return validate_clause_schema(parsed)


def _extract_clauses_deterministic(text: str) -> list[ExtractedClause]:
    clauses: list[ExtractedClause] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_text = " ".join(lines)
    full_text_lower = full_text.lower()

    if "dc pump" in full_text_lower and "water heater" in full_text_lower:
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.eligibility,
                raw_text="DC pump water heater campaign eligibility",
                structured_json={"product_category": "water_heater", "model_type": "dc_pump"},
                confidence=0.95,
            )
        )

    if "flusso" in full_text_lower:
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.exclusion,
                raw_text="FLUSSO series exclusion",
                structured_json={"series_excluded": ["FLUSSO"]},
                confidence=0.95,
            )
        )

    if "not applicable" in full_text_lower:
        exclusions = []
        lower = full_text_lower
        if "corporate account" in lower:
            exclusions.append("corporate_account")
        if "project sales" in lower:
            exclusions.append("project_sales")
        if "special price purchase" in lower:
            exclusions.append("special_price_purchase")
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.exclusion,
                raw_text="Not applicable terms",
                structured_json={"not_applicable_for": exclusions or ["unspecified"]},
                confidence=0.9,
            )
        )

    gift_skus = _extract_gift_skus(full_text)
    if "free gift" in full_text_lower or gift_skus:
        gift_costs = _extract_currency_amounts(full_text)
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.entitlement,
                raw_text="Free gift entitlement",
                structured_json={
                    "gift_skus": gift_skus,
                    "quantity_per_quote": 1,
                    **({"gift_cost_amount": gift_costs[0]} if gift_costs else {}),
                },
                confidence=0.95,
            )
        )

    date_candidates = _extract_dates(full_text)
    if "effective" in full_text_lower or date_candidates:
        structured = {"dates": date_candidates}
        if len(date_candidates) >= 2:
            structured["effective_start"] = date_candidates[0]
            structured["effective_end"] = date_candidates[1]
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.pricing,
                raw_text="Effective date window",
                structured_json=structured,
                confidence=0.85,
            )
        )

    for line in lines:
        lower = line.lower()
        if "rebate" in lower:
            percentages = _extract_percentages(line)
            tier_rates = _extract_tier_rates(line)
            structured_json = {"rule": "rebate", "text": line}
            if tier_rates:
                structured_json["tier_rates"] = tier_rates
            elif percentages:
                structured_json["default_rebate_percent"] = percentages[0]
            channel = _extract_channel(line)
            if channel:
                structured_json["channel"] = channel
            if "retroactive" in lower:
                structured_json["retroactive_incentive"] = True
                if percentages:
                    structured_json["retroactive_rate_percent"] = percentages[0]
            clauses.append(
                ExtractedClause(
                    clause_type=PolicyClauseType.rebate,
                    raw_text=line,
                    structured_json=structured_json,
                    confidence=0.8,
                )
            )
        if "incentive" in lower or "mdf" in lower or "manager discretion" in lower:
            percentages = _extract_percentages(line)
            structured_json = {"rule": "incentive", "text": line}
            if "display incentive" in lower and percentages:
                structured_json["display_incentive_percent"] = percentages[0]
            if "mdf" in lower and percentages:
                structured_json["mdf_percent"] = percentages[0]
            if "manager discretion" in lower:
                structured_json["manager_discretion_warning"] = line
                if percentages:
                    structured_json["manager_discretion_percent"] = percentages[0]
            if "retroactive" in lower:
                structured_json["retroactive_incentive"] = True
                if percentages:
                    structured_json["retroactive_rate_percent"] = percentages[0]
            channel = _extract_channel(line)
            if channel:
                structured_json["channel"] = channel
            clauses.append(
                ExtractedClause(
                    clause_type=PolicyClauseType.incentive,
                    raw_text=line,
                    structured_json=structured_json,
                    confidence=0.8,
                )
            )
        if "discount" in lower and ("campaign" in lower or "promo" in lower or "promotion" in lower):
            percentages = _extract_percentages(line)
            amounts = _extract_currency_amounts(line)
            structured_json = {"campaign_rule_type": "discount", "applies_to": "quote"}
            if percentages:
                structured_json["discount_percent"] = percentages[0]
            if amounts:
                structured_json["discount_amount"] = amounts[0]
            clauses.append(
                ExtractedClause(
                    clause_type=PolicyClauseType.entitlement,
                    raw_text=line,
                    structured_json=structured_json,
                    confidence=0.85,
                )
            )
        if "bundle" in lower:
            bundle_skus = [sku for sku in _extract_generic_skus(line) if not sku.startswith("RPG-BAG-")]
            percentages = _extract_percentages(line)
            amounts = _extract_currency_amounts(line)
            structured_json = {
                "campaign_rule_type": "bundle",
                "bundle_skus": bundle_skus,
            }
            if percentages:
                structured_json["bundle_discount_percent"] = percentages[0]
            if amounts:
                structured_json["bundle_cost_amount"] = amounts[0]
            clauses.append(
                ExtractedClause(
                    clause_type=PolicyClauseType.entitlement,
                    raw_text=line,
                    structured_json=structured_json,
                    confidence=0.82,
                )
            )

    if not clauses:
        clauses.append(
            ExtractedClause(
                clause_type=PolicyClauseType.other,
                raw_text=text.strip()[:2000],
                structured_json={"rule": "unclassified"},
                confidence=0.6,
            )
        )
    return clauses


def extract_clauses_from_text(
    text: str,
    doc_type: PolicyDocumentType,
    request_id: str,
) -> list[ExtractedClause]:
    try:
        from_foundry = _call_foundry_clause_extraction(
            text=text,
            doc_type=doc_type,
            request_id=request_id,
        )
        if from_foundry:
            return from_foundry
    except (httpx.HTTPError, ValueError, ValidationError) as exc:
        logger.exception(
            {
                "event": "policy_clause_extraction_fallback",
                "request_id": request_id,
                "error": str(exc),
            }
        )
    return _extract_clauses_deterministic(text)


def _build_campaign_rule_payloads(clauses: list[ExtractedClause]) -> list[dict]:
    eligibility: dict = {}
    exclusion: dict = {}
    free_gift_entitlement: dict = {}
    discount_entitlement: dict = {}
    bundle_entitlement: dict = {}

    for clause in clauses:
        if clause.clause_type == PolicyClauseType.eligibility:
            eligibility.update(clause.structured_json)
        elif clause.clause_type == PolicyClauseType.exclusion:
            if "series_excluded" in clause.structured_json:
                existing = exclusion.get("series_excluded", [])
                exclusion["series_excluded"] = sorted(
                    set(existing + clause.structured_json["series_excluded"])
                )
            if "not_applicable_for" in clause.structured_json:
                existing = exclusion.get("not_applicable_for", [])
                exclusion["not_applicable_for"] = sorted(
                    set(existing + clause.structured_json["not_applicable_for"])
                )
            if "channel_excluded" in clause.structured_json:
                existing = exclusion.get("channel_excluded", [])
                exclusion["channel_excluded"] = sorted(
                    set(existing + clause.structured_json["channel_excluded"])
                )
        elif clause.clause_type == PolicyClauseType.entitlement:
            structured = clause.structured_json
            rule_type = structured.get("campaign_rule_type")
            if structured.get("gift_skus"):
                free_gift_entitlement["gift_skus"] = sorted(set(structured["gift_skus"]))
                if "quantity_per_quote" in structured:
                    free_gift_entitlement["quantity_per_quote"] = structured["quantity_per_quote"]
                if "gift_cost_amount" in structured:
                    free_gift_entitlement["gift_cost_amount"] = structured["gift_cost_amount"]
            if rule_type == "discount" or "discount_percent" in structured or "discount_amount" in structured:
                if "discount_percent" in structured:
                    discount_entitlement["discount_percent"] = structured["discount_percent"]
                if "discount_amount" in structured:
                    discount_entitlement["discount_amount"] = structured["discount_amount"]
                if "applies_to" in structured:
                    discount_entitlement["applies_to"] = structured["applies_to"]
            if rule_type == "bundle" or "bundle_skus" in structured or "bundle_cost_amount" in structured:
                if structured.get("bundle_skus"):
                    existing = bundle_entitlement.get("bundle_skus", [])
                    bundle_entitlement["bundle_skus"] = sorted(set(existing + structured["bundle_skus"]))
                if "bundle_cost_amount" in structured:
                    bundle_entitlement["bundle_cost_amount"] = structured["bundle_cost_amount"]
                if "bundle_discount_percent" in structured:
                    bundle_entitlement["bundle_discount_percent"] = structured["bundle_discount_percent"]
                if "bundle_discount_amount" in structured:
                    bundle_entitlement["bundle_discount_amount"] = structured["bundle_discount_amount"]

    payloads: list[dict] = []
    if free_gift_entitlement:
        payloads.append(
            {
                "rule_type": CampaignRuleType.free_gift,
                "eligibility_json": dict(eligibility),
                "exclusion_json": dict(exclusion),
                "entitlement_json": free_gift_entitlement,
            }
        )
    if discount_entitlement:
        payloads.append(
            {
                "rule_type": CampaignRuleType.discount,
                "eligibility_json": dict(eligibility),
                "exclusion_json": dict(exclusion),
                "entitlement_json": discount_entitlement,
            }
        )
    if bundle_entitlement:
        payloads.append(
            {
                "rule_type": CampaignRuleType.bundle,
                "eligibility_json": dict(eligibility),
                "exclusion_json": dict(exclusion),
                "entitlement_json": bundle_entitlement,
            }
        )
    return payloads


def _build_rebate_program_payload(
    clauses: list[ExtractedClause],
    document: PolicyDocument,
) -> dict | None:
    tier_rates: dict[str, float] = {}
    channel: str | None = None
    mdf_percent = 0.0
    display_incentive_percent = 0.0
    manager_discretion_warning: str | None = None
    retroactive_incentive = False
    retroactive_rate_percent = 0.0
    manager_discretion_percent = 0.0
    source_clause_types: set[str] = set()
    source_notes: list[str] = []

    for clause in clauses:
        if clause.clause_type not in {PolicyClauseType.rebate, PolicyClauseType.incentive}:
            continue
        source_clause_types.add(clause.clause_type.value)
        source_notes.append(clause.raw_text)
        structured = clause.structured_json or {}
        raw_text = clause.raw_text
        line_tier_rates = structured.get("tier_rates") or _extract_tier_rates(raw_text)
        for tier, rate in line_tier_rates.items():
            tier_rates[str(tier).lower()] = float(rate)

        if not tier_rates:
            default_rebate = structured.get("default_rebate_percent")
            if default_rebate is None:
                percentages = _extract_percentages(raw_text)
                if percentages and clause.clause_type == PolicyClauseType.rebate:
                    default_rebate = percentages[0]
            if default_rebate is not None:
                tier_rates["default"] = float(default_rebate)

        if channel is None:
            channel = structured.get("channel") or _extract_channel(raw_text)

        if structured.get("mdf_percent") is not None:
            mdf_percent = float(structured["mdf_percent"])
        elif "mdf" in raw_text.lower():
            percentages = _extract_percentages(raw_text)
            if percentages:
                mdf_percent = float(percentages[0])

        if structured.get("display_incentive_percent") is not None:
            display_incentive_percent = float(structured["display_incentive_percent"])
        elif "display incentive" in raw_text.lower():
            percentages = _extract_percentages(raw_text)
            if percentages:
                display_incentive_percent = float(percentages[0])

        if structured.get("manager_discretion_warning") or "manager discretion" in raw_text.lower():
            manager_discretion_warning = str(
                structured.get("manager_discretion_warning") or raw_text
            ).strip()
            if structured.get("manager_discretion_percent") is not None:
                manager_discretion_percent = float(structured["manager_discretion_percent"])
            else:
                percentages = _extract_percentages(raw_text)
                if percentages:
                    manager_discretion_percent = float(percentages[0])

        if structured.get("retroactive_incentive") or "retroactive" in raw_text.lower():
            retroactive_incentive = True
            if structured.get("retroactive_rate_percent") is not None:
                retroactive_rate_percent = float(structured["retroactive_rate_percent"])
            else:
                percentages = _extract_percentages(raw_text)
                if percentages:
                    retroactive_rate_percent = float(percentages[0])

    if not (
        tier_rates
        or display_incentive_percent > 0
        or mdf_percent > 0
        or manager_discretion_warning
        or retroactive_incentive
    ):
        return None

    return {
        "name": document.title,
        "channel": channel,
        "tier_rates_json": tier_rates,
        "mdf_percent": mdf_percent,
        "display_incentive_percent": display_incentive_percent,
        "manager_discretion_warning": manager_discretion_warning,
        "retroactive_incentive": retroactive_incentive,
        "program_meta_json": {
            "retroactive_rate_percent": retroactive_rate_percent,
            "manager_discretion_percent": manager_discretion_percent,
            "source_clause_types": sorted(source_clause_types),
            "source_notes": source_notes[:10],
        },
    }


def _create_campaign_from_policy(
    db: Session,
    document: PolicyDocument,
    clauses: list[ExtractedClause],
    actor_user_id: str,
) -> Campaign | None:
    payloads = _build_campaign_rule_payloads(clauses)
    if not payloads:
        return None

    status = CampaignStatus.active if document.status == PolicyDocumentStatus.active else CampaignStatus.inactive
    campaign = Campaign(
        name=document.title,
        effective_start=document.effective_start,
        effective_end=document.effective_end,
        status=status,
        source_document_id=document.id,
    )
    db.add(campaign)
    db.flush()

    for payload in payloads:
        db.add(
            CampaignRule(
                campaign_id=campaign.id,
                rule_type=payload["rule_type"],
                eligibility_json=payload["eligibility_json"],
                exclusion_json=payload["exclusion_json"],
                entitlement_json=payload["entitlement_json"],
            )
        )
    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="campaign_created",
        entity_type="campaign",
        entity_id=str(campaign.id),
        new_json={
            "source_document_id": str(document.id),
            "rule_types": [payload["rule_type"].value for payload in payloads],
        },
    )
    return campaign


def _sync_campaign_from_policy(
    db: Session,
    document: PolicyDocument,
    clauses: list[ExtractedClause],
    actor_user_id: str,
) -> Campaign | None:
    existing = db.scalar(
        select(Campaign)
        .where(Campaign.source_document_id == document.id)
        .options(selectinload(Campaign.rules))
    )
    payloads = _build_campaign_rule_payloads(clauses)

    if not payloads:
        if existing:
            existing.status = CampaignStatus.inactive
        return existing

    desired_status = (
        CampaignStatus.active
        if document.status == PolicyDocumentStatus.active
        else CampaignStatus.inactive
    )
    if not existing:
        return _create_campaign_from_policy(
            db=db,
            document=document,
            clauses=clauses,
            actor_user_id=actor_user_id,
        )

    existing.name = document.title
    existing.effective_start = document.effective_start
    existing.effective_end = document.effective_end
    existing.status = desired_status

    desired_by_type = {payload["rule_type"]: payload for payload in payloads}
    existing_by_type = {rule.rule_type: rule for rule in existing.rules}

    for rule_type, payload in desired_by_type.items():
        rule = existing_by_type.get(rule_type)
        if rule is None:
            db.add(
                CampaignRule(
                    campaign_id=existing.id,
                    rule_type=rule_type,
                    eligibility_json=payload["eligibility_json"],
                    exclusion_json=payload["exclusion_json"],
                    entitlement_json=payload["entitlement_json"],
                )
            )
            continue
        rule.eligibility_json = payload["eligibility_json"]
        rule.exclusion_json = payload["exclusion_json"]
        rule.entitlement_json = payload["entitlement_json"]

    for rule_type, rule in existing_by_type.items():
        if rule_type not in desired_by_type:
            db.delete(rule)

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="campaign_synced_from_policy",
        entity_type="campaign",
        entity_id=str(existing.id),
        new_json={
            "source_document_id": str(document.id),
            "status": existing.status.value,
            "rule_types": [payload["rule_type"].value for payload in payloads],
        },
    )
    return existing


def _create_rebate_program_from_policy(
    db: Session,
    document: PolicyDocument,
    clauses: list[ExtractedClause],
    actor_user_id: str,
) -> RebateProgram | None:
    payload = _build_rebate_program_payload(clauses=clauses, document=document)
    if not payload:
        return None

    program = RebateProgram(
        name=payload["name"],
        channel=payload["channel"],
        tier_rates_json=payload["tier_rates_json"],
        mdf_percent=payload["mdf_percent"],
        display_incentive_percent=payload["display_incentive_percent"],
        manager_discretion_warning=payload["manager_discretion_warning"],
        retroactive_incentive=payload["retroactive_incentive"],
        program_meta_json=payload["program_meta_json"],
        effective_start=document.effective_start,
        effective_end=document.effective_end,
        source_document_id=document.id,
    )
    db.add(program)
    db.flush()

    if document.source_uploaded_file_id:
        uploaded_file = db.get(UploadedFile, document.source_uploaded_file_id)
        if uploaded_file:
            uploaded_file.linked_rebate_program_id = program.id

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="rebate_program_created",
        entity_type="rebate_program",
        entity_id=str(program.id),
        new_json={
            "source_document_id": str(document.id),
            "channel": program.channel,
        },
    )
    return program


def _sync_rebate_program_from_policy(
    db: Session,
    document: PolicyDocument,
    clauses: list[ExtractedClause],
    actor_user_id: str,
) -> RebateProgram | None:
    existing = db.scalar(select(RebateProgram).where(RebateProgram.source_document_id == document.id))
    payload = _build_rebate_program_payload(clauses=clauses, document=document)

    if not payload:
        if existing:
            existing.effective_end = document.reviewed_at or datetime.now(timezone.utc)
            meta = dict(existing.program_meta_json or {})
            meta["archived_with_policy"] = True
            existing.program_meta_json = meta
        return existing

    if not existing:
        return _create_rebate_program_from_policy(
            db=db,
            document=document,
            clauses=clauses,
            actor_user_id=actor_user_id,
        )

    existing.name = payload["name"]
    existing.channel = payload["channel"]
    existing.tier_rates_json = payload["tier_rates_json"]
    existing.mdf_percent = payload["mdf_percent"]
    existing.display_incentive_percent = payload["display_incentive_percent"]
    existing.manager_discretion_warning = payload["manager_discretion_warning"]
    existing.retroactive_incentive = payload["retroactive_incentive"]
    existing.program_meta_json = payload["program_meta_json"]
    existing.effective_start = document.effective_start
    existing.effective_end = document.effective_end

    if document.source_uploaded_file_id:
        uploaded_file = db.get(UploadedFile, document.source_uploaded_file_id)
        if uploaded_file:
            uploaded_file.linked_rebate_program_id = existing.id

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="rebate_program_synced_from_policy",
        entity_type="rebate_program",
        entity_id=str(existing.id),
        new_json={
            "source_document_id": str(document.id),
            "channel": existing.channel,
            "retroactive_incentive": existing.retroactive_incentive,
        },
    )
    return existing


def _replace_policy_clauses(
    db: Session,
    document: PolicyDocument,
    clauses: list[ExtractedClause],
) -> None:
    for existing in list(document.clauses):
        db.delete(existing)
    db.flush()

    for clause in clauses:
        db.add(
            PolicyClause(
                policy_document_id=document.id,
                clause_type=clause.clause_type,
                structured_json=clause.structured_json,
                raw_text=clause.raw_text,
                confidence=clause.confidence,
            )
        )
    db.flush()


def ingest_policy_document(
    db: Session,
    payload: PolicyUploadRequest,
    uploaded_by: User,
    request_id: str = "policy-ingestion",
) -> PolicyDocument:
    digest = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
    source_uploaded_file_id = None
    if payload.source_uploaded_file_id:
        try:
            source_uploaded_file_id = uuid.UUID(payload.source_uploaded_file_id)
        except ValueError as exc:
            raise ValueError("Invalid source_uploaded_file_id") from exc

    document = PolicyDocument(
        title=payload.title,
        doc_type=payload.doc_type,
        source_uri=payload.source_uri,
        file_hash=digest,
        uploaded_by_user_id=uploaded_by.id,
        source_uploaded_file_id=source_uploaded_file_id,
        effective_start=payload.effective_start,
        effective_end=payload.effective_end,
        auto_create_campaign=payload.auto_create_campaign,
        status=PolicyDocumentStatus.draft,
    )
    db.add(document)
    db.flush()

    if source_uploaded_file_id:
        uploaded_file = db.get(UploadedFile, source_uploaded_file_id)
        if uploaded_file is None:
            raise ValueError("Source uploaded file not found")
        uploaded_file.linked_policy_id = document.id

    extracted = extract_clauses_from_text(
        text=payload.text,
        doc_type=payload.doc_type,
        request_id=request_id,
    )
    _replace_policy_clauses(db=db, document=document, clauses=extracted)

    avg_confidence = round(
        sum(float(clause.confidence) for clause in extracted) / len(extracted),
        4,
    ) if extracted else 0.0
    settings = get_settings()
    log_model_run(
        db=db,
        run_type="policy_extraction",
        model_name=settings.foundry_model_name,
        model_version=settings.foundry_model_name,
        request_id=request_id,
        status="completed",
        meta_json={"clause_count": len(extracted), "average_confidence": avg_confidence},
    )

    log_audit(
        db=db,
        actor_user_id=str(uploaded_by.id),
        action="policy_uploaded",
        entity_type="policy_document",
        entity_id=str(document.id),
        new_json={
            "title": payload.title,
            "doc_type": payload.doc_type.value,
            "file_hash": digest,
            "status": document.status.value,
            "requested_status": payload.status.value,
        },
    )
    log_audit(
        db=db,
        actor_user_id=str(uploaded_by.id),
        action="policy_clause_extracted",
        entity_type="policy_document",
        entity_id=str(document.id),
        new_json={
            "clause_count": len(extracted),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.commit()
    db.refresh(document)
    return document


def review_policy_document(
    db: Session,
    policy_id: str,
    payload: PolicyReviewUpdateRequest,
    reviewed_by: User,
) -> PolicyDocument:
    document = require_policy_document(db=db, policy_id=policy_id)
    document = db.scalar(
        select(PolicyDocument)
        .where(PolicyDocument.id == document.id)
        .options(selectinload(PolicyDocument.clauses))
    )
    if document is None:
        raise ValueError("Policy document not found")

    if payload.title is not None:
        document.title = payload.title
    if payload.source_uri is not None:
        document.source_uri = payload.source_uri
    if payload.effective_start is not None:
        document.effective_start = payload.effective_start
    if payload.effective_end is not None:
        document.effective_end = payload.effective_end
    if payload.auto_create_campaign is not None:
        document.auto_create_campaign = payload.auto_create_campaign
    if payload.review_notes is not None:
        document.review_notes = payload.review_notes.strip() or None

    reviewed_clauses: list[ExtractedClause] | None = None
    if payload.clauses is not None:
        reviewed_clauses = [
            ExtractedClause(
                clause_type=clause.clause_type,
                raw_text=clause.raw_text,
                structured_json=clause.structured_json,
                confidence=clause.confidence,
            )
            for clause in payload.clauses
        ]
        _replace_policy_clauses(db=db, document=document, clauses=reviewed_clauses)
    else:
        reviewed_clauses = [
            ExtractedClause(
                clause_type=clause.clause_type,
                raw_text=clause.raw_text,
                structured_json=clause.structured_json,
                confidence=float(clause.confidence),
            )
            for clause in document.clauses
        ]

    if not reviewed_clauses:
        raise ValueError("At least one policy clause is required before saving review changes")

    document.reviewed_by_user_id = reviewed_by.id
    document.reviewed_at = datetime.now(timezone.utc)

    if payload.action.value == "activate":
        document.status = PolicyDocumentStatus.active
        if document.auto_create_campaign and document.doc_type == PolicyDocumentType.memo:
            _sync_campaign_from_policy(
                db=db,
                document=document,
                clauses=reviewed_clauses,
                actor_user_id=str(reviewed_by.id),
            )
        if document.doc_type in {PolicyDocumentType.trading_terms, PolicyDocumentType.finance}:
            _sync_rebate_program_from_policy(
                db=db,
                document=document,
                clauses=reviewed_clauses,
                actor_user_id=str(reviewed_by.id),
            )
    elif payload.action.value == "archive":
        document.status = PolicyDocumentStatus.archived
        existing_campaign = db.scalar(select(Campaign).where(Campaign.source_document_id == document.id))
        if existing_campaign:
            existing_campaign.status = CampaignStatus.inactive
        existing_rebate_program = db.scalar(select(RebateProgram).where(RebateProgram.source_document_id == document.id))
        if existing_rebate_program:
            existing_rebate_program.effective_end = document.reviewed_at or datetime.now(timezone.utc)
            meta = dict(existing_rebate_program.program_meta_json or {})
            meta["archived_with_policy"] = True
            existing_rebate_program.program_meta_json = meta
    else:
        document.status = PolicyDocumentStatus.draft

    log_audit(
        db=db,
        actor_user_id=str(reviewed_by.id),
        action="policy_review_updated",
        entity_type="policy_document",
        entity_id=str(document.id),
        new_json={
            "status": document.status.value,
            "clause_count": len(reviewed_clauses),
            "auto_create_campaign": document.auto_create_campaign,
        },
        reason=document.review_notes,
    )
    db.commit()
    db.refresh(document)
    return document


def create_campaign(
    db: Session,
    name: str,
    source_document_id: str,
    status: CampaignStatus,
    effective_start: datetime | None,
    effective_end: datetime | None,
    actor_user_id: str,
) -> Campaign:
    try:
        source_id = uuid.UUID(source_document_id)
    except ValueError as exc:
        raise ValueError("Invalid source_document_id") from exc

    document = db.get(PolicyDocument, source_id)
    if not document:
        raise ValueError("Source policy document not found")

    campaign = Campaign(
        name=name,
        source_document_id=source_id,
        status=status,
        effective_start=effective_start,
        effective_end=effective_end,
    )
    db.add(campaign)
    db.flush()

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="campaign_created",
        entity_type="campaign",
        entity_id=str(campaign.id),
        new_json={"name": name, "source_document_id": source_document_id},
    )
    db.commit()
    db.refresh(campaign)
    return campaign


def add_campaign_rule(
    db: Session,
    campaign_id: str,
    rule_type: CampaignRuleType,
    eligibility_json: dict,
    exclusion_json: dict,
    entitlement_json: dict,
    actor_user_id: str,
) -> CampaignRule:
    try:
        parsed = uuid.UUID(campaign_id)
    except ValueError as exc:
        raise ValueError("Invalid campaign id") from exc

    campaign = db.get(Campaign, parsed)
    if not campaign:
        raise ValueError("Campaign not found")

    rule = CampaignRule(
        campaign_id=campaign.id,
        rule_type=rule_type,
        eligibility_json=eligibility_json,
        exclusion_json=exclusion_json,
        entitlement_json=entitlement_json,
    )
    db.add(rule)
    db.flush()
    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="campaign_rule_created",
        entity_type="campaign_rule",
        entity_id=str(rule.id),
        new_json={"campaign_id": campaign_id, "rule_type": rule_type.value},
    )
    db.commit()
    db.refresh(rule)
    return rule


def require_policy_document(db: Session, policy_id: str) -> PolicyDocument:
    try:
        parsed = uuid.UUID(policy_id)
    except ValueError as exc:
        raise ValueError("Invalid policy id") from exc
    document = db.get(PolicyDocument, parsed)
    if not document:
        raise ValueError("Policy document not found")
    return document

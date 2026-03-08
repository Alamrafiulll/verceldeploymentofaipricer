from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Quote
from app.services.audit_logger import log_audit
from app.services.campaign_engine import evaluate_campaigns
from app.services.contract_engine import evaluate_contract_pricing
from app.services.market_comparison_engine import analyze_product_market_position
from app.services.pricebook_enforcement import evaluate_pricebook_compliance


def evaluate_quote_policies(
    db: Session,
    quote: Quote,
    actor_user_id: str | None = None,
    price_override: float | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    violations: list[dict] = []
    pricebook_summary = evaluate_pricebook_compliance(
        db=db,
        quote=quote,
        price_override=price_override,
    )
    if pricebook_summary["status"] == "channel_unmapped":
        violations.append(
            {
                "severity": "medium",
                "code": "pricebook_channel_unmapped",
                "message": pricebook_summary["message"],
                "source_document_id": None,
                "clause_id": None,
            }
        )
    elif pricebook_summary["status"] == "no_active_pricebook":
        violations.append(
            {
                "severity": "high",
                "code": "pricebook_missing",
                "message": pricebook_summary["message"],
                "source_document_id": pricebook_summary["source_document_id"],
                "clause_id": None,
            }
        )
    elif pricebook_summary["status"] == "product_missing":
        violations.append(
            {
                "severity": "medium",
                "code": "pricebook_item_missing",
                "message": pricebook_summary["message"],
                "source_document_id": pricebook_summary["source_document_id"],
                "clause_id": None,
            }
        )
    elif pricebook_summary["status"] == "below_reference_price":
        violations.append(
            {
                "severity": "high",
                "code": "below_pricebook_list",
                "message": pricebook_summary["message"],
                "source_document_id": pricebook_summary["source_document_id"],
                "clause_id": None,
            }
        )

    campaign_result = evaluate_campaigns(
        db=db,
        quote=quote,
        price_override=price_override,
        as_of=now,
    )
    violations.extend(campaign_result["violations"])
    entitlements = campaign_result["entitlements"]
    market_analysis = analyze_product_market_position(db=db, product_id=str(quote.items[0].product_id))
    contract_summary = evaluate_contract_pricing(
        db=db,
        quote=quote,
        price_override=price_override,
        as_of=now,
    )
    if contract_summary["status"] == "conflicting_contract_bounds":
        violations.append(
            {
                "severity": "high",
                "code": "conflicting_contract_bounds",
                "message": contract_summary["message"],
                "source_document_id": contract_summary["source_document_ids"][0]
                if contract_summary["source_document_ids"]
                else None,
                "clause_id": None,
            }
        )
    elif contract_summary["status"] == "below_contract_floor":
        violations.append(
            {
                "severity": "high",
                "code": "below_contract_floor",
                "message": contract_summary["message"],
                "source_document_id": contract_summary["source_document_ids"][0]
                if contract_summary["source_document_ids"]
                else None,
                "clause_id": None,
            }
        )
    elif contract_summary["status"] == "above_contract_ceiling":
        violations.append(
            {
                "severity": "medium",
                "code": "above_contract_ceiling",
                "message": contract_summary["message"],
                "source_document_id": contract_summary["source_document_ids"][0]
                if contract_summary["source_document_ids"]
                else None,
                "clause_id": None,
            }
        )
    elif contract_summary["status"] == "exceeds_contract_discount_cap":
        violations.append(
            {
                "severity": "high",
                "code": "exceeds_contract_discount_cap",
                "message": contract_summary["message"],
                "source_document_id": contract_summary["source_document_ids"][0]
                if contract_summary["source_document_ids"]
                else None,
                "clause_id": None,
            }
        )

    if actor_user_id:
        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="policy_checked",
            entity_type="quote",
            entity_id=str(quote.id),
            new_json={
                "violation_count": len(violations),
                "entitlement_count": len(entitlements),
                "eligible_campaign_count": campaign_result["campaign_summary"]["eligible_campaign_count"],
                "contract_status": contract_summary["status"],
                "value_positioning_label": market_analysis.value_positioning_label if market_analysis else None,
            },
        )

    return {
        "quote_id": str(quote.id),
        "checked_at": now,
        "pricebook_compliance_summary": pricebook_summary,
        "contract_pricing_summary": contract_summary,
        "campaign_summary": campaign_result["campaign_summary"],
        "campaign_evaluations": campaign_result["campaign_evaluations"],
        "market_comparison_summary": (
            {
                "market_comparison_summary": market_analysis.market_comparison_summary,
                "value_positioning_label": market_analysis.value_positioning_label,
                "recommended_strategy": market_analysis.recommended_strategy,
                "value_score": market_analysis.value_score,
                "competitor_count": market_analysis.competitor_count,
            }
            if market_analysis
            else None
        ),
        "recommended_action": (
            market_analysis.recommended_strategy.replace("_", " ").title()
            if market_analysis
            else "Proceed With Standard Governance Review"
        ),
        "violations": violations,
        "entitlements": entitlements,
    }

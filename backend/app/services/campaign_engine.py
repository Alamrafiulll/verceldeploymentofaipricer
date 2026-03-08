from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Campaign, CampaignRule, CampaignRuleType, Product, Quote
from app.services.pricebook_enforcement import is_effective


def _as_float(value: float | None) -> float | None:
    return float(value) if value is not None else None


def _product_text(quote: Quote) -> str:
    item = quote.items[0]
    product = item.product
    return f"{product.name} {product.sku}".lower()


def _matches_common_eligibility(rule: CampaignRule, quote: Quote, price_to_check: float) -> bool:
    item = quote.items[0]
    product = item.product
    eligibility = rule.eligibility_json or {}
    product_text = _product_text(quote)

    if eligibility.get("product_category"):
        if product.category.lower() != str(eligibility["product_category"]).lower():
            return False
    if eligibility.get("model_type") == "dc_pump":
        if "dc" not in product_text or "pump" not in product_text:
            return False
    if eligibility.get("min_quantity") is not None:
        if item.quantity < int(eligibility["min_quantity"]):
            return False
    if eligibility.get("min_price") is not None:
        if price_to_check < float(eligibility["min_price"]):
            return False
    if eligibility.get("quote_channel_in"):
        allowed_channels = {str(value).lower() for value in eligibility["quote_channel_in"]}
        if quote.channel.lower() not in allowed_channels:
            return False
    if eligibility.get("customer_tiers"):
        allowed_tiers = {str(value).lower() for value in eligibility["customer_tiers"]}
        if quote.customer.tier.value.lower() not in allowed_tiers:
            return False
    if eligibility.get("sku_in"):
        allowed_skus = {str(value).upper() for value in eligibility["sku_in"]}
        if product.sku.upper() not in allowed_skus:
            return False
    return True


def _build_exclusion_violation(campaign: Campaign, reason: str) -> dict:
    return {
        "severity": "medium",
        "code": "campaign_excluded",
        "message": f"Campaign {campaign.name} excludes this quote context. {reason}",
        "source_document_id": str(campaign.source_document_id),
        "clause_id": None,
    }


def _check_exclusions(rule: CampaignRule, quote: Quote, price_to_check: float) -> str | None:
    item = quote.items[0]
    product = item.product
    exclusion = rule.exclusion_json or {}
    product_text = _product_text(quote)

    for series in exclusion.get("series_excluded") or []:
        if str(series).lower() in product_text:
            return f"Excluded series: {series}."

    for sku in exclusion.get("sku_excluded") or []:
        if str(sku).upper() == product.sku.upper():
            return f"Excluded SKU: {sku}."

    for channel in exclusion.get("channel_excluded") or []:
        if str(channel).lower() == quote.channel.lower():
            return f"Excluded channel: {channel}."

    for tier in exclusion.get("customer_tiers_excluded") or []:
        if str(tier).lower() == quote.customer.tier.value.lower():
            return f"Excluded customer tier: {tier}."

    not_applicable_for = exclusion.get("not_applicable_for") or []
    channel_text = quote.channel.lower()
    if "project_sales" in not_applicable_for and "project" in channel_text:
        return "Not applicable for project sales."
    if "corporate_account" in not_applicable_for and "corporate" in channel_text:
        return "Not applicable for corporate accounts."
    if "special_price_purchase" in not_applicable_for and "special" in channel_text:
        return "Not applicable for special price purchase."
    if "distributor_channel" in not_applicable_for and "distributor" in channel_text:
        return "Not applicable for distributor channel."

    if exclusion.get("max_discount_percent") is not None:
        discount_percent = 0.0
        if float(product.list_price) > 0:
            discount_percent = ((float(product.list_price) - price_to_check) / float(product.list_price)) * 100
        if discount_percent > float(exclusion["max_discount_percent"]):
            return "Quote discount is above the campaign allowance."

    return None


def _load_costable_products(db: Session, sku_codes: set[str]) -> dict[str, Product]:
    if not sku_codes:
        return {}
    rows = list(db.scalars(select(Product).where(Product.sku.in_(sorted(sku_codes)))).all())
    return {row.sku.upper(): row for row in rows}


def _resolve_free_gift_cost(
    db: Session,
    entitlement: dict,
) -> tuple[float, list[str]]:
    gift_skus = [str(code).upper() for code in entitlement.get("gift_skus", [])]
    quantity_per_quote = int(entitlement.get("quantity_per_quote", 1))
    explicit_cost = _as_float(entitlement.get("gift_cost_amount"))
    if explicit_cost is not None:
        return round(explicit_cost, 2), gift_skus

    costable_products = _load_costable_products(db, set(gift_skus))
    total_cost = 0.0
    resolved_skus: list[str] = []
    for sku in gift_skus:
        product = costable_products.get(sku)
        if not product:
            continue
        total_cost += float(product.unit_cost) * quantity_per_quote
        resolved_skus.append(sku)
    return round(total_cost, 2), resolved_skus


def _resolve_bundle_cost(
    db: Session,
    entitlement: dict,
) -> tuple[float, list[str]]:
    bundle_skus = [str(code).upper() for code in entitlement.get("bundle_skus", [])]
    explicit_cost = _as_float(entitlement.get("bundle_cost_amount"))
    if explicit_cost is not None:
        return round(explicit_cost, 2), bundle_skus

    costable_products = _load_costable_products(db, set(bundle_skus))
    total_cost = 0.0
    resolved_skus: list[str] = []
    for sku in bundle_skus:
        product = costable_products.get(sku)
        if not product:
            continue
        total_cost += float(product.unit_cost)
        resolved_skus.append(sku)
    return round(total_cost, 2), resolved_skus


def _resolve_promotion_allocation(entitlement: dict, quote_quantity: int) -> float:
    explicit_amount = _as_float(
        entitlement.get("promotion_allocation_amount")
        or entitlement.get("promotion_cost_amount")
        or entitlement.get("campaign_cost_amount")
    )
    if explicit_amount is not None:
        return round(explicit_amount, 2)

    per_unit_amount = _as_float(entitlement.get("promotion_allocation_per_unit"))
    if per_unit_amount is not None:
        return round(per_unit_amount * quote_quantity, 2)

    return 0.0


def evaluate_campaigns(
    db: Session,
    quote: Quote,
    price_override: float | None = None,
    as_of: datetime | None = None,
) -> dict:
    now = as_of or datetime.now(timezone.utc)
    item = quote.items[0]
    product = item.product
    price_to_check = (
        _as_float(price_override)
        or _as_float(item.final_price)
        or _as_float(item.requested_price)
        or _as_float(item.recommended_price)
        or float(product.list_price)
    )

    campaigns = list(
        db.scalars(select(Campaign).options(selectinload(Campaign.rules)).order_by(Campaign.effective_start.desc())).all()
    )

    entitlements: list[dict] = []
    violations: list[dict] = []
    evaluations: list[dict] = []
    total_campaign_cost = 0.0
    total_gift_cost = 0.0
    total_bundle_cost = 0.0
    total_promotion_allocation = 0.0

    for campaign in campaigns:
        if campaign.status.value != "active":
            continue
        if not is_effective(now, campaign.effective_start, campaign.effective_end):
            continue

        for rule in campaign.rules:
            eligible = _matches_common_eligibility(rule=rule, quote=quote, price_to_check=price_to_check)
            exclusion_reason = (
                _check_exclusions(rule=rule, quote=quote, price_to_check=price_to_check)
                if eligible
                else None
            )
            if exclusion_reason:
                violations.append(_build_exclusion_violation(campaign=campaign, reason=exclusion_reason))
                evaluations.append(
                    {
                        "campaign_id": str(campaign.id),
                        "campaign_name": campaign.name,
                        "rule_type": rule.rule_type.value,
                        "eligibility_status": "excluded",
                        "business_impact": exclusion_reason,
                        "estimated_campaign_cost": 0.0,
                        "source_document_id": str(campaign.source_document_id),
                    }
                )
                continue

            if not eligible:
                evaluations.append(
                    {
                        "campaign_id": str(campaign.id),
                        "campaign_name": campaign.name,
                        "rule_type": rule.rule_type.value,
                        "eligibility_status": "not_eligible",
                        "business_impact": "Quote does not meet the campaign eligibility conditions.",
                        "estimated_campaign_cost": 0.0,
                        "source_document_id": str(campaign.source_document_id),
                    }
                )
                continue

            estimated_cost = 0.0
            summary = ""
            next_action = "Use the campaign benefit in the quote if the customer accepts the offer."
            entitlement = rule.entitlement_json or {}
            promotion_allocation_amount = _resolve_promotion_allocation(entitlement=entitlement, quote_quantity=item.quantity)
            entitlement_record = {
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "rule_type": rule.rule_type.value,
                "source_document_id": str(campaign.source_document_id),
                "eligibility_status": "eligible",
                "estimated_campaign_cost": 0.0,
                "summary": None,
                "next_action": next_action,
                "sku_codes": [],
                "quantity": int(entitlement.get("quantity_per_quote", 1)),
                "discount_percent": None,
                "discount_amount": None,
                "bundle_skus": [],
                "promotion_allocation_amount": promotion_allocation_amount,
            }

            if rule.rule_type == CampaignRuleType.free_gift:
                estimated_cost, resolved_skus = _resolve_free_gift_cost(db=db, entitlement=entitlement)
                total_gift_cost += estimated_cost
                gift_skus = [str(code) for code in entitlement.get("gift_skus", [])]
                entitlement_record["sku_codes"] = gift_skus
                entitlement_record["quantity"] = int(entitlement.get("quantity_per_quote", 1))
                summary = (
                    f"Eligible for free gift campaign with {len(gift_skus)} gift option(s). "
                    f"Estimated gift cost impact: RM {estimated_cost:.2f}."
                )
                if gift_skus and not resolved_skus and estimated_cost == 0:
                    summary = (
                        f"Eligible for free gift campaign with {len(gift_skus)} gift option(s). "
                        "Gift cost is not yet mapped in master data."
                    )
            elif rule.rule_type == CampaignRuleType.discount:
                discount_percent = _as_float(entitlement.get("discount_percent"))
                discount_amount = _as_float(entitlement.get("discount_amount"))
                if discount_percent is not None:
                    discount_value = round(price_to_check * item.quantity * discount_percent / 100, 2)
                    summary = (
                        f"Eligible for campaign discount of {discount_percent:.2f}% "
                        f"with customer value of RM {discount_value:.2f} at the evaluated price."
                    )
                elif discount_amount is not None:
                    summary = (
                        f"Eligible for fixed campaign discount of RM {discount_amount:.2f} "
                        "for this quote."
                    )
                else:
                    summary = "Eligible for a campaign discount based on the reviewed campaign memo."
                entitlement_record["discount_percent"] = discount_percent
                entitlement_record["discount_amount"] = discount_amount
                next_action = "Confirm the campaign discount is reflected in the negotiated quote price."
                entitlement_record["next_action"] = next_action
                if promotion_allocation_amount > 0:
                    summary += f" Promotion allocation cost impact: RM {promotion_allocation_amount:.2f}."
            elif rule.rule_type == CampaignRuleType.bundle:
                estimated_cost, resolved_bundle_skus = _resolve_bundle_cost(db=db, entitlement=entitlement)
                total_bundle_cost += estimated_cost
                bundle_skus = [str(code) for code in entitlement.get("bundle_skus", [])]
                bundle_discount_percent = _as_float(entitlement.get("bundle_discount_percent"))
                bundle_discount_amount = _as_float(entitlement.get("bundle_discount_amount"))
                entitlement_record["bundle_skus"] = bundle_skus
                entitlement_record["sku_codes"] = bundle_skus
                entitlement_record["discount_percent"] = bundle_discount_percent
                entitlement_record["discount_amount"] = bundle_discount_amount
                summary = (
                    f"Eligible for bundle offer covering {len(bundle_skus)} bundled item(s). "
                    f"Estimated bundle cost impact: RM {estimated_cost:.2f}."
                )
                if bundle_discount_percent is not None:
                    summary += f" Bundle discount guidance: {bundle_discount_percent:.2f}%."
                elif bundle_discount_amount is not None:
                    summary += f" Bundle discount guidance: RM {bundle_discount_amount:.2f}."
                if bundle_skus and not resolved_bundle_skus and estimated_cost == 0:
                    summary = (
                        f"Eligible for bundle offer covering {len(bundle_skus)} bundled item(s). "
                        "Bundle item cost is not yet mapped in master data."
                    )
                next_action = "Use the bundle offer only if the customer accepts the packaged value position."
                entitlement_record["next_action"] = next_action
                if promotion_allocation_amount > 0:
                    summary += f" Promotion allocation cost impact: RM {promotion_allocation_amount:.2f}."

            entitlement_record["summary"] = summary
            entitlement_record["estimated_campaign_cost"] = round(estimated_cost + promotion_allocation_amount, 2)
            entitlements.append(entitlement_record)
            total_promotion_allocation += promotion_allocation_amount
            total_campaign_cost += estimated_cost + promotion_allocation_amount
            evaluations.append(
                {
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "rule_type": rule.rule_type.value,
                    "eligibility_status": "eligible",
                    "business_impact": summary,
                    "estimated_campaign_cost": round(estimated_cost + promotion_allocation_amount, 2),
                    "promotion_allocation_amount": round(promotion_allocation_amount, 2),
                    "source_document_id": str(campaign.source_document_id),
                }
            )

    eligible_count = sum(1 for row in evaluations if row["eligibility_status"] == "eligible")
    excluded_count = sum(1 for row in evaluations if row["eligibility_status"] == "excluded")
    not_eligible_count = sum(1 for row in evaluations if row["eligibility_status"] == "not_eligible")
    summary = {
        "eligible_campaign_count": eligible_count,
        "excluded_campaign_count": excluded_count,
        "not_eligible_campaign_count": not_eligible_count,
        "estimated_campaign_cost": round(total_campaign_cost, 2),
        "gift_cost_amount": round(total_gift_cost, 2),
        "bundle_cost_amount": round(total_bundle_cost, 2),
        "promotion_allocation_amount": round(total_promotion_allocation, 2),
        "recommended_action": (
            "Apply the eligible campaign benefits and review exclusions before asking for approval."
            if eligible_count
            else "No eligible campaign benefit is available for this quote."
        ),
        "business_impact": (
            f"Active campaign cost impact on true margin is RM {total_campaign_cost:.2f}."
            if total_campaign_cost > 0
            else "No additional campaign cost is reducing true margin at the current quote setup."
        ),
    }

    return {
        "entitlements": entitlements,
        "violations": violations,
        "campaign_evaluations": evaluations,
        "campaign_cost_amount": round(total_campaign_cost, 2),
        "gift_cost_amount": round(total_gift_cost, 2),
        "bundle_cost_amount": round(total_bundle_cost, 2),
        "promotion_allocation_amount": round(total_promotion_allocation, 2),
        "campaign_summary": summary,
    }

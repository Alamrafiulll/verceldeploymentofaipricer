def _round_amount(value: float) -> float:
    return round(float(value), 2)


def _append_reason(
    reasons: list[dict],
    *,
    code: str,
    label: str,
    amount: float,
    message: str,
    severity: str = "medium",
    included_in_leakage_amount: bool = True,
) -> None:
    rounded_amount = _round_amount(amount)
    if rounded_amount <= 0 and included_in_leakage_amount:
        return
    reasons.append(
        {
            "code": code,
            "label": label,
            "amount": rounded_amount,
            "message": message,
            "severity": severity,
            "included_in_leakage_amount": included_in_leakage_amount,
        }
    )


def build_leakage_summary(
    *,
    proposed_price: float,
    list_price: float,
    quantity: int,
    pricebook_summary: dict | None,
    contract_summary: dict | None,
    rebate_summary: dict | None,
    gift_cost_amount: float,
    bundle_cost_amount: float,
    promotion_allocation_amount: float,
    freight_amount: float,
    fees_amount: float,
    mdf_amount: float,
    net_margin_amount: float,
    policy_violations: list[dict] | None = None,
) -> dict:
    flags: list[dict] = []
    reasons: list[dict] = []

    list_revenue_total = float(list_price) * quantity
    discounted_revenue_total = float(proposed_price) * quantity
    price_discount_amount = max(0.0, list_revenue_total - discounted_revenue_total)

    base_rebate_amount = float(rebate_summary.get("standard_rebate_amount") or 0) if rebate_summary else 0.0
    retroactive_rebate_amount = float(rebate_summary.get("retroactive_rebate_amount") or 0) if rebate_summary else 0.0
    manager_discretion_amount = float(rebate_summary.get("manager_discretion_amount") or 0) if rebate_summary else 0.0
    display_incentive_amount = float(rebate_summary.get("display_incentive_amount") or 0) if rebate_summary else 0.0
    base_mdf_amount = float(rebate_summary.get("standard_mdf_amount") or 0) if rebate_summary else 0.0

    leakage_amount = (
        price_discount_amount
        + base_rebate_amount
        + retroactive_rebate_amount
        + manager_discretion_amount
        + display_incentive_amount
        + base_mdf_amount
        + float(gift_cost_amount)
        + float(bundle_cost_amount)
        + float(promotion_allocation_amount)
        + float(freight_amount)
        + float(fees_amount)
    )

    _append_reason(
        reasons,
        code="price_discount_from_list",
        label="Discounted Revenue Gap",
        amount=price_discount_amount,
        message="Quoted revenue is below list revenue, reducing margin before other cost drivers.",
        severity="medium",
    )
    _append_reason(
        reasons,
        code="rebate_cost",
        label="Rebate Cost",
        amount=base_rebate_amount,
        message="Approved rebate programs reduce true margin on this quote.",
    )
    _append_reason(
        reasons,
        code="retroactive_rebate_cost",
        label="Retroactive Incentive",
        amount=retroactive_rebate_amount,
        message="Retroactive incentive logic increases the true margin cost on this quote.",
    )
    _append_reason(
        reasons,
        code="manager_discretion_cost",
        label="Manager Discretion Cost",
        amount=manager_discretion_amount,
        message="Manager discretion rebate cost applies to this quote.",
        severity="high" if manager_discretion_amount > 0 else "medium",
    )
    _append_reason(
        reasons,
        code="mdf_allocation_cost",
        label="MDF Allocation",
        amount=base_mdf_amount,
        message="Market development funding allocation reduces true margin.",
    )
    _append_reason(
        reasons,
        code="display_incentive_cost",
        label="Display Incentive",
        amount=display_incentive_amount,
        message="Display incentive support reduces true margin.",
    )
    _append_reason(
        reasons,
        code="free_gift_cost",
        label="Free Gift Cost",
        amount=float(gift_cost_amount),
        message="Free gift entitlement cost reduces true margin.",
    )
    _append_reason(
        reasons,
        code="bundle_cost",
        label="Bundle Cost",
        amount=float(bundle_cost_amount),
        message="Bundle support cost reduces true margin.",
    )
    _append_reason(
        reasons,
        code="promotion_allocation_cost",
        label="Promotion Allocation",
        amount=float(promotion_allocation_amount),
        message="Promotion allocation cost reduces true margin.",
    )
    _append_reason(
        reasons,
        code="freight_cost",
        label="Freight Cost",
        amount=float(freight_amount),
        message="Freight cost reduces true margin.",
    )
    _append_reason(
        reasons,
        code="fees_cost",
        label="Fees Cost",
        amount=float(fees_amount),
        message="Fees reduce true margin.",
    )

    if contract_summary:
        floor_price = contract_summary.get("floor_price")
        ceiling_price = contract_summary.get("ceiling_price")
        discount_cap_percent = contract_summary.get("discount_cap_percent")

        if floor_price is not None and proposed_price < float(floor_price):
            gap_amount = (float(floor_price) - float(proposed_price)) * quantity
            flags.append(
                {
                    "code": "violates_contract_floor",
                    "severity": "high",
                    "message": "Proposed price is below contract floor.",
                }
            )
            _append_reason(
                reasons,
                code="contract_floor_gap",
                label="Contract Floor Gap",
                amount=gap_amount,
                message="Quoted price is below the customer contract floor.",
                severity="high",
                included_in_leakage_amount=False,
            )
        if ceiling_price is not None and proposed_price > float(ceiling_price):
            flags.append(
                {
                    "code": "violates_contract_ceiling",
                    "severity": "high",
                    "message": "Proposed price is above contract ceiling.",
                }
            )
        if discount_cap_percent is not None and list_price > 0:
            discount_percent = ((list_price - proposed_price) / list_price) * 100
            if discount_percent > float(discount_cap_percent):
                flags.append(
                    {
                        "code": "exceeds_contract_discount_cap",
                        "severity": "medium",
                        "message": "Proposed discount exceeds contract discount cap.",
                    }
                )

    if pricebook_summary and pricebook_summary.get("status") == "below_reference_price":
        reference_price = float(pricebook_summary.get("reference_price") or 0)
        if reference_price > proposed_price:
            gap_amount = (reference_price - proposed_price) * quantity
            _append_reason(
                reasons,
                code="pricebook_reference_gap",
                label="Pricebook Gap",
                amount=gap_amount,
                message="Quoted price is below the active pricebook reference price.",
                severity="high",
                included_in_leakage_amount=False,
            )

    if net_margin_amount < 0:
        flags.append(
            {
                "code": "negative_margin_after_rebates",
                "severity": "high",
                "message": "Net margin is negative after rebates and fees.",
            }
        )

    if rebate_summary:
        if rebate_summary.get("manager_discretion_warning"):
            flags.append(
                {
                    "code": "manager_discretion_rebate_warning",
                    "severity": "medium",
                    "message": rebate_summary["manager_discretion_warning"],
                }
            )
        if float(rebate_summary.get("retroactive_rebate_amount") or 0) > 0:
            flags.append(
                {
                    "code": "retroactive_incentive_applied",
                    "severity": "medium",
                    "message": "Retroactive rebate logic increases true margin cost for this quote.",
                }
            )

    if policy_violations:
        for violation in policy_violations:
            flags.append(
                {
                    "code": f"policy_{violation['code']}",
                    "severity": violation.get("severity", "medium"),
                    "message": violation.get("message", "Policy violation detected."),
                }
            )

    return {
        "flags": flags,
        "leakage_amount": _round_amount(leakage_amount),
        "leakage_reasons": reasons,
        "price_discount_amount": _round_amount(price_discount_amount),
    }


def evaluate_leakage_flags(
    proposed_price: float,
    list_price: float,
    contract_bounds: dict | None,
    net_margin_amount: float,
    rebate_summary: dict | None = None,
    policy_violations: list[dict] | None = None,
) -> list[dict]:
    summary = build_leakage_summary(
        proposed_price=proposed_price,
        list_price=list_price,
        quantity=1,
        pricebook_summary=None,
        contract_summary=contract_bounds,
        rebate_summary=rebate_summary,
        gift_cost_amount=0.0,
        bundle_cost_amount=0.0,
        promotion_allocation_amount=0.0,
        freight_amount=0.0,
        fees_amount=0.0,
        mdf_amount=float(rebate_summary.get("mdf_amount") or 0) if rebate_summary else 0.0,
        net_margin_amount=net_margin_amount,
        policy_violations=policy_violations,
    )
    return summary["flags"]

"""Three-level explanation generator for AI recommendations.

Produces:
 1. Quick Summary     – 1-2 sentences for busy users
 2. Business Explanation – paragraph for managers
 3. Detailed Trace    – full technical details for auditors/admins
"""
from dataclasses import dataclass


@dataclass
class ThreeLevelExplanation:
    quick_summary: str
    business_explanation: str
    detailed_trace: str


def generate_three_level_explanation(
    product_name: str,
    recommended_price: float,
    list_price: float,
    unit_cost: float,
    margin_percent: float,
    confidence: float,
    channel: str = "direct",
    win_probability: float | None = None,
    risk_level: str = "low",
    discount_percent: float = 0,
    policy_violations: list[str] | None = None,
    competitor_position: str | None = None,
    model_version: str = "v1",
    fallback_used: bool = False,
) -> ThreeLevelExplanation:
    """Generate all three explanation levels from recommendation data."""

    discount_from_list = round((1 - recommended_price / list_price) * 100, 1) if list_price else 0

    # ── Quick Summary ──────────────────────────────────
    margin_word = "healthy" if margin_percent >= 15 else ("acceptable" if margin_percent >= 10 else "thin")
    quick = f"Recommended RM {recommended_price:,.2f} for '{product_name}' — {margin_word} margin at {margin_percent:.1f}%."
    if risk_level == "high":
        quick += " ⚠️ Approval required."
    elif confidence >= 0.8:
        quick += " High confidence."

    # ── Business Explanation ───────────────────────────
    parts = []
    parts.append(f"The AI recommends pricing '{product_name}' at RM {recommended_price:,.2f}, which is {discount_from_list:.1f}% below the list price of RM {list_price:,.2f}.")

    if margin_percent >= 20:
        parts.append(f"This preserves a strong {margin_percent:.1f}% margin, well above minimum thresholds.")
    elif margin_percent >= 10:
        parts.append(f"This yields a {margin_percent:.1f}% margin, which is within acceptable range but could be improved.")
    else:
        parts.append(f"⚠️ Warning: margin is only {margin_percent:.1f}%, which is below typical targets. Consider negotiating for a higher price.")

    channel_label = {"direct": "direct sales", "distributor": "distributor", "project": "project/bulk"}.get(channel, channel)
    parts.append(f"Channel: {channel_label}.")

    if competitor_position:
        parts.append(f"Market position: {competitor_position}.")

    if win_probability is not None:
        parts.append(f"Estimated win probability: {win_probability*100:.0f}%.")

    if policy_violations:
        parts.append(f"⚠️ Policy concerns: {'; '.join(policy_violations[:3])}.")

    business = " ".join(parts)

    # ── Detailed Trace ─────────────────────────────────
    trace_lines = [
        f"Product: {product_name}",
        f"List Price: RM {list_price:,.2f}",
        f"Unit Cost: RM {unit_cost:,.2f}",
        f"Recommended Price: RM {recommended_price:,.2f}",
        f"Discount from List: {discount_from_list:.1f}%",
        f"Gross Margin: {margin_percent:.1f}%",
        f"Channel: {channel}",
        f"Risk Level: {risk_level}",
        f"Confidence: {confidence*100:.1f}%",
        f"Model Version: {model_version}",
        f"Fallback Used: {'Yes' if fallback_used else 'No'}",
    ]
    if win_probability is not None:
        trace_lines.append(f"Win Probability: {win_probability*100:.1f}%")
    if policy_violations:
        trace_lines.append(f"Policy Violations: {', '.join(policy_violations)}")
    if competitor_position:
        trace_lines.append(f"Competitor Position: {competitor_position}")

    detailed = "\n".join(trace_lines)

    return ThreeLevelExplanation(
        quick_summary=quick,
        business_explanation=business,
        detailed_trace=detailed,
    )

import uuid
from datetime import date
from typing import Any

from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.models import (
    Approval,
    ApprovalStatus,
    Customer,
    Inventory,
    PricingRule,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
    Recommendation,
    RiskLevel,
    StrategyMode,
)
from app.schemas.quote import RecommendationResponse
from app.services.audit_logger import log_audit
from app.services.feature_builder import build_feature_context, hash_features
from app.services.foundry_client import FoundryScoringClient
from app.services.foundry_gpt_client import FoundryClient
from app.services.finance_engine import compute_true_margin
from app.services.optimization_engine import (
    OptimizerInput,
    generate_candidate_prices,
    optimize_expected_profit,
)
from app.services.policy_enforcement import evaluate_quote_policies
from app.services.recommendation_trace_service import (
    create_ai_recommendation_trace,
    update_quote_trace_status,
)
from app.services.risk_engine import RiskInputs, requires_approval, score_risk


class PricingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.scoring_client = FoundryScoringClient()
        self.explainer = FoundryClient()

    def _historical_discount_tolerance(self, customer: Customer) -> float:
        by_tier = {
            "strategic": 6.5,
            "core": 10.0,
            "growth": 14.0,
        }
        return by_tier.get(customer.tier.value, 10.0)

    def _manager_override_rate(self, db: Session, user_id: uuid.UUID) -> float:
        total = db.scalar(select(func.count(Quote.id)).where(Quote.created_by_user_id == user_id)) or 0
        if total == 0:
            return 0.0

        overridden = db.scalar(
            select(func.count(Quote.id)).where(
                Quote.created_by_user_id == user_id,
                Quote.status.in_([QuoteStatus.approval_pending, QuoteStatus.approved, QuoteStatus.rejected]),
            )
        ) or 0
        return float(overridden / total)

    def _load_quote(self, db: Session, quote_id: str) -> Quote:
        quote = db.scalar(
            select(Quote)
            .where(Quote.id == uuid.UUID(quote_id))
            .options(
                selectinload(Quote.items),
                selectinload(Quote.customer),
                selectinload(Quote.recommendations),
            )
        )
        if not quote:
            raise ValueError("Quote not found")
        if not quote.items:
            raise ValueError("Quote has no item")
        return quote

    def _load_rule(self, db: Session, channel: str, category: str) -> PricingRule:
        rule = db.scalar(
            select(PricingRule).where(
                PricingRule.channel == channel,
                PricingRule.category == category,
            )
        )
        if rule:
            return rule

        fallback = db.scalar(select(PricingRule).where(PricingRule.channel == channel))
        if fallback:
            return fallback
        raise ValueError(f"No pricing rule configured for channel={channel} category={category}")

    def _resolve_inventory(self, db: Session, product_id: uuid.UUID) -> Inventory:
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product_id))
        if not inventory:
            raise ValueError("Inventory row missing for product")
        return inventory

    def recommend(self, db: Session, quote_id: str, actor_user_id: str, request_id: str) -> RecommendationResponse:
        quote = self._load_quote(db, quote_id)
        item = quote.items[0]

        product = db.scalar(select(Product).where(Product.id == item.product_id))
        if not product:
            raise ValueError("Product missing")

        inventory = self._resolve_inventory(db, product.id)
        rule = self._load_rule(db, quote.channel, product.category)

        delivery_days = None
        if item.requested_price and item.requested_price > 0:
            delivery_days = 14
        elif isinstance(getattr(item, "delivery_date", None), date):
            delivery_days = max(0, (item.delivery_date - date.today()).days)

        historical_tolerance = self._historical_discount_tolerance(quote.customer)
        feature_context = build_feature_context(
            customer=quote.customer,
            product=product,
            channel=quote.channel,
            quantity=item.quantity,
            stock_age_days=inventory.stock_age_days_avg,
            stock_on_hand=inventory.on_hand,
            days_to_delivery=delivery_days,
            strategy_mode=quote.strategy_mode,
            historical_discount_tolerance=historical_tolerance,
        )
        feature_context["list_price"] = float(product.list_price)

        candidates = generate_candidate_prices(
            list_price=float(product.list_price),
            max_discount_percent=float(rule.max_discount_percent),
            step_percent=self.settings.candidate_step_percent,
        )

        probabilities, confidence, model_version, scored_rows = self.scoring_client.score_win_probability(
            features=feature_context,
            candidate_prices=candidates,
            request_id=request_id,
        )

        optimization = optimize_expected_profit(
            OptimizerInput(
                list_price=float(product.list_price),
                unit_cost=float(product.unit_cost),
                quantity=item.quantity,
                max_discount_percent=float(rule.max_discount_percent),
                margin_floor_percent=float(rule.margin_floor_percent),
                candidate_step_percent=self.settings.candidate_step_percent,
                probabilities=probabilities,
                confidence=confidence,
                strategy_mode=quote.strategy_mode,
                stock_age_days=inventory.stock_age_days_avg,
                tolerance=self.settings.recommendation_tolerance,
            ),
            candidate_prices=candidates,
        )

        best = optimization["best"]
        override_rate = self._manager_override_rate(db, quote.created_by_user_id)
        risk_level = score_risk(
            RiskInputs(
                margin_percent=float(best["margin_percent"]),
                margin_floor_percent=float(rule.margin_floor_percent),
                discount_percent=float(best["discount_percent"]),
                ai_discount_center=float(
                    (optimization["suggested_discount_low"] + optimization["suggested_discount_high"]) / 2
                ),
                stock_age_days=inventory.stock_age_days_avg,
                customer_tier=quote.customer.tier.value,
                confidence=float(optimization["confidence"]),
                manager_override_rate=override_rate,
            )
        )

        zone = "green"
        if risk_level == RiskLevel.medium:
            zone = "yellow"
        elif risk_level == RiskLevel.high:
            zone = "red"

        explanation_payload = {
            "best_price": float(best["price"]),
            "band_low": float(optimization["band_low"]),
            "band_high": float(optimization["band_high"]),
            "win_probability": float(best["win_probability"]),
            "expected_profit": float(best["expected_profit"]),
            "margin_percent": float(best["margin_percent"]),
            "strategy_mode": quote.strategy_mode.value,
            "risk_level": risk_level.value,
            "stock_age_days": inventory.stock_age_days_avg,
            "top_feature_snapshot": feature_context,
        }
        explanation = self.explainer.generate_explanation(explanation_payload, request_id=request_id)

        item.recommended_price = best["price"]
        item.recommended_band_low = optimization["band_low"]
        item.recommended_band_high = optimization["band_high"]
        item.recommended_discount_low = optimization["suggested_discount_low"]
        item.recommended_discount_high = optimization["suggested_discount_high"]
        item.win_probability = best["win_probability"]
        item.confidence = optimization["confidence"]
        item.margin_percent = best["margin_percent"]
        item.expected_profit = best["expected_profit"]
        item.risk_level = risk_level
        quote.status = QuoteStatus.recommended

        feature_hash = hash_features(feature_context)
        recommendation = Recommendation(
            quote_id=quote.id,
            model_version=model_version,
            feature_schema_version=self.settings.feature_schema_version,
            xgb_outputs_json={
                "feature_hash": feature_hash,
                "rows": scored_rows,
                "probabilities": probabilities,
                "confidence": confidence,
            },
            optimizer_outputs_json=optimization,
            gpt_outputs_json=explanation,
        )
        db.add(recommendation)
        fallback_used = model_version == "deterministic-fallback-v1"
        create_ai_recommendation_trace(
            db=db,
            quote_id=quote.id,
            product_id=product.id,
            recommended_price=float(best["price"]),
            recommended_price_low=float(optimization["band_low"]),
            recommended_price_high=float(optimization["band_high"]),
            win_probability=float(best["win_probability"]),
            confidence=float(optimization["confidence"]),
            model_version=model_version,
            model_provider="deterministic_local" if fallback_used else self.settings.active_ai_provider,
            fallback_used=fallback_used,
            explanation_json=explanation,
            risk_level=risk_level.value,
        )

        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="recommendation_generated",
            entity_type="quote",
            entity_id=str(quote.id),
            old_json=None,
            new_json={
                "risk_level": risk_level.value,
                "best_price": best["price"],
                "band": [optimization["band_low"], optimization["band_high"]],
                "feature_hash": feature_hash,
                "ai_output": explanation,
            },
            model_version=model_version,
        )

        policy_result = evaluate_quote_policies(
            db=db,
            quote=quote,
            actor_user_id=None,
            price_override=float(best["price"]),
        )
        finance_snapshot = compute_true_margin(
            db=db,
            quote_id=str(quote.id),
            proposed_price=float(best["price"]),
            actor_user_id=None,
        )

        db.commit()
        db.refresh(item)

        market_summary = policy_result["market_comparison_summary"]
        true_margin_summary = {
            "proposed_price": float(finance_snapshot.proposed_price),
            "list_revenue_total": float(finance_snapshot.list_revenue_total),
            "revenue_total": float(finance_snapshot.revenue_total),
            "cogs_total": float(finance_snapshot.cogs_total),
            "rebate_amount": float(finance_snapshot.rebate_amount),
            "gift_cost_amount": float(finance_snapshot.gift_cost_amount),
            "bundle_cost_amount": float(finance_snapshot.bundle_cost_amount),
            "promotion_allocation_amount": float(finance_snapshot.promotion_allocation_amount),
            "campaign_cost_amount": float(finance_snapshot.campaign_cost_amount),
            "freight_amount": float(finance_snapshot.freight_amount),
            "fees_amount": float(finance_snapshot.fees_amount),
            "contract_effect_amount": float(finance_snapshot.contract_effect_amount),
            "list_margin_amount": float(finance_snapshot.list_margin_amount),
            "price_discount_amount": float(finance_snapshot.price_discount_amount),
            "gross_margin_amount": float(finance_snapshot.gross_margin_amount),
            "net_margin_amount": float(finance_snapshot.net_margin_amount),
            "net_margin_percent": float(finance_snapshot.net_margin_percent),
            "leakage_amount": float(finance_snapshot.leakage_amount),
            "leakage_reasons": finance_snapshot.leakage_reasons_json,
            "contract_summary": finance_snapshot.leakage_flags_json.get("contract_summary"),
        }

        return RecommendationResponse(
            quote_id=str(quote.id),
            band_low=float(optimization["band_low"]),
            band_high=float(optimization["band_high"]),
            best_price=float(best["price"]),
            suggested_discount_low=float(optimization["suggested_discount_low"]),
            suggested_discount_high=float(optimization["suggested_discount_high"]),
            win_probability=float(best["win_probability"]),
            expected_profit=float(best["expected_profit"]),
            margin_percent=float(best["margin_percent"]),
            confidence=float(optimization["confidence"]),
            risk_level=risk_level,
            safe_band=zone,
            explanation=explanation,
            candidates=optimization["points"],
            safe_price_range={
                "low": float(optimization["band_low"]),
                "high": float(optimization["band_high"]),
            },
            true_margin_snapshot_summary=true_margin_summary,
            policy_entitlements_summary=policy_result["entitlements"],
            pricebook_compliance_summary=policy_result["pricebook_compliance_summary"],
            contract_pricing_summary=policy_result["contract_pricing_summary"],
            campaign_summary=policy_result["campaign_summary"],
            campaign_evaluations=policy_result["campaign_evaluations"],
            market_comparison_summary=market_summary,
            value_positioning_label=market_summary["value_positioning_label"] if market_summary else None,
            next_best_action=policy_result["recommended_action"],
        )

    def finalize_quote(
        self,
        db: Session,
        quote_id: str,
        actor_user_id: str,
        final_price: float,
        reason: str | None,
    ) -> Quote:
        quote = self._load_quote(db, quote_id)
        item = quote.items[0]
        product = db.scalar(select(Product).where(Product.id == item.product_id))
        if not product:
            raise ValueError("Product missing")
        rule = self._load_rule(db, quote.channel, product.category)

        if item.recommended_price is None:
            raise ValueError("Generate recommendation before finalizing")

        margin_percent = ((final_price - float(product.unit_cost)) / final_price) * 100
        final_discount = ((float(product.list_price) - final_price) / float(product.list_price)) * 100
        expected_profit = (final_price - float(product.unit_cost)) * item.quantity * float(item.win_probability or 0.5)

        policy_result = evaluate_quote_policies(
            db=db,
            quote=quote,
            actor_user_id=None,
            price_override=final_price,
        )
        finance_snapshot = compute_true_margin(
            db=db,
            quote_id=str(quote.id),
            proposed_price=final_price,
            actor_user_id=None,
        )
        leakage_flags = finance_snapshot.leakage_flags_json.get("flags", [])
        has_high_policy_violation = any(v.get("severity") == "high" for v in policy_result["violations"])
        has_high_leakage_flag = any(flag.get("severity") == "high" for flag in leakage_flags)

        approval_needed = requires_approval(
            risk_level=item.risk_level or RiskLevel.medium,
            chosen_price=final_price,
            band_low=float(item.recommended_band_low or item.recommended_price),
            band_high=float(item.recommended_band_high or item.recommended_price),
            margin_percent=margin_percent,
            margin_floor_percent=float(rule.margin_floor_percent),
            approval_buffer=float(rule.approval_required_below_margin_buffer),
        )
        approval_needed = approval_needed or has_high_policy_violation or has_high_leakage_flag

        approved_decision = db.scalar(
            select(Approval)
            .where(
                Approval.quote_id == quote.id,
                Approval.status == ApprovalStatus.approved,
            )
            .order_by(desc(Approval.decided_at))
        )
        if (
            quote.status == QuoteStatus.approved
            and approved_decision
            and approved_decision.requested_price is not None
            and abs(final_price - float(approved_decision.requested_price)) > 0.01
        ):
            raise ValueError("Final price differs from approved price. Submit a new approval request.")

        if approval_needed and quote.status != QuoteStatus.approved:
            raise ValueError("Approval required before finalize due to risk, policy, or leakage flags")

        old = {
            "status": quote.status.value,
            "final_price": float(item.final_price or 0),
        }

        item.final_price = round(final_price, 2)
        item.final_discount = round(final_discount, 2)
        item.margin_percent = round(margin_percent, 2)
        item.expected_profit = round(expected_profit, 2)
        quote.status = QuoteStatus.finalized
        update_quote_trace_status(
            db=db,
            quote_id=quote.id,
            approval_status=ApprovalStatus.approved,
            approved_by_user_id=uuid.UUID(actor_user_id),
        )

        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="quote_finalized",
            entity_type="quote",
            entity_id=str(quote.id),
            old_json=old,
            new_json={
                "status": quote.status.value,
                "final_price": item.final_price,
                "final_discount": item.final_discount,
                "margin_percent": item.margin_percent,
            },
            reason=reason,
        )
        db.commit()
        db.refresh(quote)
        return quote

    def request_approval(
        self,
        db: Session,
        quote_id: str,
        actor_user_id: str,
        requested_price: float,
        requested_discount: float | None,
        justification: str,
    ) -> Approval:
        quote = self._load_quote(db, quote_id)
        item = quote.items[0]

        old_status = quote.status.value
        quote.status = QuoteStatus.approval_pending

        approval = Approval(
            quote_id=quote.id,
            requested_by_user_id=uuid.UUID(actor_user_id),
            requested_price=requested_price,
            requested_discount=requested_discount,
            request_justification=justification,
            status=ApprovalStatus.pending,
        )
        db.add(approval)

        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="approval_requested",
            entity_type="quote",
            entity_id=str(quote.id),
            old_json={"status": old_status},
            new_json={
                "status": quote.status.value,
                "requested_price": requested_price,
                "requested_discount": requested_discount,
                "recommended_price": float(item.recommended_price or 0),
            },
            reason=justification,
        )

        db.commit()
        db.refresh(approval)
        return approval

    def decide_approval(
        self,
        db: Session,
        approval_id: str,
        actor_user_id: str,
        approve: bool,
        decision_reason: str,
    ) -> Approval:
        approval = db.scalar(select(Approval).where(Approval.id == uuid.UUID(approval_id)))
        if not approval:
            raise ValueError("Approval not found")

        quote = db.scalar(
            select(Quote)
            .where(Quote.id == approval.quote_id)
            .options(selectinload(Quote.items))
        )
        if not quote:
            raise ValueError("Quote not found for approval")
        old_status = approval.status.value

        approval.status = ApprovalStatus.approved if approve else ApprovalStatus.rejected
        approval.approver_user_id = uuid.UUID(actor_user_id)
        approval.decision_reason = decision_reason
        approval.decided_at = datetime.now(timezone.utc)

        quote.status = QuoteStatus.approved if approve else QuoteStatus.rejected
        update_quote_trace_status(
            db=db,
            quote_id=quote.id,
            approval_status=approval.status,
            approved_by_user_id=approval.approver_user_id,
        )

        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="approval_decision",
            entity_type="approval",
            entity_id=str(approval.id),
            old_json={"status": old_status},
            new_json={"status": approval.status.value, "quote_status": quote.status.value},
            reason=decision_reason,
        )

        db.commit()
        db.refresh(approval)
        return approval

    def save_draft(
        self,
        db: Session,
        quote_id: str,
        actor_user_id: str,
        requested_price: float,
        strategy_mode: StrategyMode | None = None,
    ) -> Quote:
        quote = self._load_quote(db, quote_id)
        if quote.status not in {QuoteStatus.draft, QuoteStatus.recommended, QuoteStatus.rejected}:
            raise ValueError(f"Cannot save draft for a quote with status {quote.status.value}")

        item = quote.items[0]
        product = db.scalar(select(Product).where(Product.id == item.product_id))
        if not product:
            raise ValueError("Product missing")

        old_json = {
            "requested_price": float(item.requested_price) if item.requested_price is not None else None,
            "strategy_mode": quote.strategy_mode.value if quote.strategy_mode else None,
        }

        # Update requested price and calculate requested discount
        item.requested_price = round(requested_price, 2)
        item.requested_discount = round(
            ((float(product.list_price) - requested_price) / float(product.list_price)) * 100, 2
        )
        if strategy_mode:
            quote.strategy_mode = strategy_mode

        log_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="quote_draft_saved",
            entity_type="quote",
            entity_id=str(quote.id),
            old_json=old_json,
            new_json={
                "requested_price": float(item.requested_price),
                "strategy_mode": quote.strategy_mode.value,
            },
        )

        evaluate_quote_policies(
            db=db,
            quote=quote,
            actor_user_id=None,
            price_override=requested_price,
        )
        compute_true_margin(
            db=db,
            quote_id=str(quote.id),
            proposed_price=requested_price,
            actor_user_id=None,
        )

        db.commit()
        db.refresh(quote)
        return quote


pricing_service = PricingService()

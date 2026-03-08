"""Uploaded-data-first market comparison and value positioning engine."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompetitorProduct, Product, ProductValueProfile

logger = logging.getLogger("app")


def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


class MarketObservationAdapter(Protocol):
    def load_observations(self, db: Session, product: Product) -> list[CompetitorProduct]: ...


@dataclass
class CompetitorMatch:
    competitor_id: str
    competitor_name: str
    product_name: str
    competitor_price: float
    chin_hin_price: float
    price_gap_rm: float
    price_gap_percent: float
    position: str
    match_score: float
    quality_proxy_score: float
    warranty_months: int | None = None
    feature_count: int | None = None
    brand_tier: str | None = None
    specification_score: float | None = None


@dataclass
class ValueAnalysis:
    product_id: str
    product_name: str
    category: str
    chin_hin_price: float
    competitor_count: int
    avg_competitor_price: float
    min_competitor_price: float
    max_competitor_price: float
    price_gap_percent: float
    positioning_label: str
    value_positioning_label: str
    value_score: float
    recommendation_confidence: float
    recommended_strategy: str
    market_comparison_summary: str
    reasoning: str = ""
    matches: list[CompetitorMatch] = field(default_factory=list)


class UploadedCompetitorAdapter:
    """Primary adapter that only uses uploaded competitor data."""

    def load_observations(self, db: Session, product: Product) -> list[CompetitorProduct]:
        direct_matches = list(
            db.scalars(
                select(CompetitorProduct).where(CompetitorProduct.matched_product_id == product.id)
            ).all()
        )
        if direct_matches:
            return direct_matches

        category_matches = list(
            db.scalars(
                select(CompetitorProduct).where(CompetitorProduct.category == product.category)
            ).all()
        )
        if not category_matches:
            return []

        target_name = _normalize_text(product.name)
        filtered: list[tuple[float, CompetitorProduct]] = []
        for competitor in category_matches:
            score = _name_similarity(target_name, _normalize_text(competitor.product_name))
            price_band_ok = _in_price_band(
                chin_hin_price=float(product.list_price),
                competitor_price=float(competitor.price),
            )
            if score >= 0.35 or price_band_ok:
                filtered.append((score, competitor))
        filtered.sort(key=lambda item: item[0], reverse=True)
        return [competitor for _, competitor in filtered[:10]]


def _normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def _name_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _in_price_band(chin_hin_price: float, competitor_price: float) -> bool:
    if chin_hin_price <= 0 or competitor_price <= 0:
        return False
    ratio = competitor_price / chin_hin_price
    return 0.5 <= ratio <= 1.5


def _as_float(value: object | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object | None) -> int | None:
    parsed = _as_float(value)
    return int(parsed) if parsed is not None else None


def _quality_proxy_score(features: dict) -> float:
    brand_tier = str(features.get("brand_tier") or "").strip().lower()
    brand_score = {
        "value": 30.0,
        "standard": 45.0,
        "premium": 65.0,
        "flagship": 80.0,
    }.get(brand_tier, 50.0)
    feature_count = _as_int(features.get("feature_count") or features.get("features_count")) or 0
    warranty_months = _as_int(features.get("warranty_months")) or 0
    specification_score = _as_float(features.get("specification_score")) or 0.0
    proxy = brand_score + min(feature_count * 2.5, 15.0) + min(warranty_months / 6, 12.0) + min(specification_score, 20.0)
    return round(min(proxy, 100.0), 1)


def _extract_feature_count(features: dict) -> int | None:
    feature_count = _as_int(features.get("feature_count") or features.get("features_count"))
    if feature_count is not None:
        return feature_count
    if isinstance(features.get("features"), list):
        return len(features["features"])
    if isinstance(features.get("features"), str):
        return len([item for item in re.split(r"[|,;/]+", features["features"]) if item.strip()])
    return None


def _value_positioning_label(gap_pct: float) -> str:
    if gap_pct <= -10:
        return "best_value"
    if gap_pct < -2:
        return "competitive_value"
    if gap_pct <= 4:
        return "market_parity"
    if gap_pct <= 12:
        return "premium_value"
    return "premium_risk"


def _position_label(gap_pct: float) -> str:
    if gap_pct < -15:
        return "cheaper"
    if gap_pct < -5:
        return "competitive"
    if gap_pct <= 5:
        return "equal"
    if gap_pct <= 20:
        return "premium"
    return "high_premium"


def _strategy(gap_pct: float, value_score: float, competitor_count: int) -> str:
    if competitor_count == 0:
        return "hold_price"
    if gap_pct > 12 and value_score < 52:
        return "reduce_price"
    if gap_pct > 6 and value_score >= 52:
        return "justify_premium"
    if gap_pct < -8 and value_score > 70:
        return "hold_price"
    if -5 <= gap_pct <= 6:
        return "bundle"
    return "hold_price"


def _recommendation_confidence(matches: list[CompetitorMatch]) -> float:
    if not matches:
        return 0.25
    avg_match_score = sum(match.match_score for match in matches) / len(matches)
    density_bonus = min(len(matches) * 0.06, 0.25)
    return round(min(0.95, 0.35 + avg_match_score * 0.4 + density_bonus), 2)


def _value_score(gap_pct: float, matches: list[CompetitorMatch]) -> float:
    if not matches:
        return 50.0
    avg_quality = sum(match.quality_proxy_score for match in matches) / len(matches)
    price_component = max(0.0, min(100.0, 55.0 - gap_pct))
    return round(max(0.0, min(100.0, price_component * 0.7 + avg_quality * 0.3)), 1)


def _market_summary(
    product: Product,
    avg_price: float,
    gap_pct: float,
    value_score: float,
    strategy: str,
    competitor_count: int,
) -> str:
    if competitor_count == 0:
        return "No competitor pricing has been uploaded for this product yet."

    if strategy == "reduce_price":
        action = "Reduce price or secure an approval-backed exception before competing head-on."
    elif strategy == "justify_premium":
        action = "Hold price and justify the premium with warranty, specification, or service value."
    elif strategy == "bundle":
        action = "Use bundle or campaign support instead of a deeper price cut."
    else:
        action = "Hold price and monitor market movement."

    return (
        f"{product.name} is RM {float(product.list_price):,.2f} versus an uploaded market average of "
        f"RM {avg_price:,.2f}. Price gap is {gap_pct:.1f}% and the value score is {value_score:.1f}. {action}"
    )


def analyze_product_market_position(
    db: Session,
    product_id: str | uuid.UUID,
    adapter: MarketObservationAdapter | None = None,
) -> ValueAnalysis | None:
    try:
        parsed_product_id = _parse_uuid(product_id)
    except ValueError:
        return None

    product = db.get(Product, parsed_product_id)
    if not product:
        return None

    market_adapter = adapter or UploadedCompetitorAdapter()
    competitors = market_adapter.load_observations(db=db, product=product)
    chin_hin_price = float(product.list_price)

    if not competitors:
        return ValueAnalysis(
            product_id=str(product.id),
            product_name=product.name,
            category=product.category,
            chin_hin_price=chin_hin_price,
            competitor_count=0,
            avg_competitor_price=0,
            min_competitor_price=0,
            max_competitor_price=0,
            price_gap_percent=0,
            positioning_label="no_competitor_data",
            value_positioning_label="insufficient_market_data",
            value_score=50.0,
            recommendation_confidence=0.25,
            recommended_strategy="hold_price",
            market_comparison_summary="No competitor pricing has been uploaded for this product category yet.",
            reasoning=(
                "No uploaded competitor observations matched this product. Upload competitor price data in CSV, "
                "XLSX, PDF export, or JSON format to enable market comparison and value positioning."
            ),
            matches=[],
        )

    target_name = _normalize_text(product.name)
    matches: list[CompetitorMatch] = []
    for competitor in competitors:
        features = competitor.features_json or {}
        competitor_price = float(competitor.price)
        name_score = _name_similarity(target_name, _normalize_text(competitor.product_name))
        quality_score = _quality_proxy_score(features)
        gap_rm = round(chin_hin_price - competitor_price, 2)
        gap_pct = round((gap_rm / competitor_price) * 100, 1) if competitor_price else 0.0
        position = "cheaper" if chin_hin_price < competitor_price * 0.98 else ("premium" if chin_hin_price > competitor_price * 1.02 else "equal")
        matches.append(
            CompetitorMatch(
                competitor_id=str(competitor.id),
                competitor_name=competitor.competitor_name,
                product_name=competitor.product_name,
                competitor_price=competitor_price,
                chin_hin_price=chin_hin_price,
                price_gap_rm=gap_rm,
                price_gap_percent=gap_pct,
                position=position,
                match_score=round(max(name_score, 0.4 if competitor.category == product.category else 0.0), 2),
                quality_proxy_score=quality_score,
                warranty_months=_as_int(features.get("warranty_months")),
                feature_count=_extract_feature_count(features),
                brand_tier=str(features.get("brand_tier")) if features.get("brand_tier") else None,
                specification_score=_as_float(features.get("specification_score")),
            )
        )

    matches.sort(key=lambda item: (item.match_score, -abs(item.price_gap_percent), item.quality_proxy_score), reverse=True)
    prices = [match.competitor_price for match in matches]
    avg_price = sum(prices) / len(prices)
    gap_pct = round(((chin_hin_price - avg_price) / avg_price) * 100, 1) if avg_price else 0.0
    value_score = _value_score(gap_pct, matches)
    positioning_label = _position_label(gap_pct)
    value_positioning_label = _value_positioning_label(gap_pct)
    strategy = _strategy(gap_pct, value_score, len(matches))
    recommendation_confidence = _recommendation_confidence(matches)

    summary = _market_summary(
        product=product,
        avg_price=avg_price,
        gap_pct=gap_pct,
        value_score=value_score,
        strategy=strategy,
        competitor_count=len(matches),
    )
    reasoning = (
        f"Matched {len(matches)} uploaded competitor observation(s) for category '{product.category}'. "
        f"Average competitor price is RM {avg_price:,.2f} with a range of RM {min(prices):,.2f} to RM {max(prices):,.2f}. "
        f"Chin Hin is positioned as '{positioning_label}' with value positioning '{value_positioning_label}'."
    )

    return ValueAnalysis(
        product_id=str(product.id),
        product_name=product.name,
        category=product.category,
        chin_hin_price=chin_hin_price,
        competitor_count=len(matches),
        avg_competitor_price=round(avg_price, 2),
        min_competitor_price=round(min(prices), 2),
        max_competitor_price=round(max(prices), 2),
        price_gap_percent=gap_pct,
        positioning_label=positioning_label,
        value_positioning_label=value_positioning_label,
        value_score=value_score,
        recommendation_confidence=recommendation_confidence,
        recommended_strategy=strategy,
        market_comparison_summary=summary,
        reasoning=reasoning,
        matches=matches[:8],
    )


def update_product_value_profile(
    db: Session,
    product_id: str | uuid.UUID,
    adapter: MarketObservationAdapter | None = None,
    *,
    commit: bool = True,
) -> ProductValueProfile | None:
    analysis = analyze_product_market_position(db=db, product_id=product_id, adapter=adapter)
    if not analysis:
        return None

    parsed_product_id = _parse_uuid(product_id)

    profile = db.scalar(
        select(ProductValueProfile).where(ProductValueProfile.product_id == parsed_product_id)
    )
    if not profile:
        profile = ProductValueProfile(product_id=parsed_product_id)
        db.add(profile)

    profile.value_score = analysis.value_score
    profile.positioning_label = analysis.value_positioning_label
    profile.price_band = (
        f"RM {analysis.min_competitor_price:,.0f} - RM {analysis.max_competitor_price:,.0f}"
        if analysis.competitor_count
        else None
    )
    profile.competitor_count = analysis.competitor_count
    profile.avg_competitor_price = analysis.avg_competitor_price or None
    profile.price_gap_percent = analysis.price_gap_percent
    profile.recommended_strategy = analysis.recommended_strategy
    profile.analysis_json = {
        "market_comparison_summary": analysis.market_comparison_summary,
        "reasoning": analysis.reasoning,
        "positioning_label": analysis.positioning_label,
        "value_positioning_label": analysis.value_positioning_label,
        "recommendation_confidence": analysis.recommendation_confidence,
        "matches": [
            {
                "competitor_id": match.competitor_id,
                "competitor_name": match.competitor_name,
                "product_name": match.product_name,
                "competitor_price": match.competitor_price,
                "price_gap_rm": match.price_gap_rm,
                "price_gap_percent": match.price_gap_percent,
                "position": match.position,
                "match_score": match.match_score,
                "quality_proxy_score": match.quality_proxy_score,
                "warranty_months": match.warranty_months,
                "feature_count": match.feature_count,
                "brand_tier": match.brand_tier,
                "specification_score": match.specification_score,
            }
            for match in analysis.matches
        ],
    }

    if commit:
        db.commit()
        db.refresh(profile)
    else:
        db.flush()
    return profile

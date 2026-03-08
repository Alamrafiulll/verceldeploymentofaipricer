"""Smart document extraction service.

After a file is uploaded, this service:
1. Extracts text using file_text_extractor
2. Generates a plain-language summary
3. Identifies extracted entities (products, prices, rules, dates)
4. Returns structured extraction result for UI display
"""
import re
import logging
from dataclasses import dataclass, field

from app.db.models import UploadType

logger = logging.getLogger("app")


@dataclass
class ExtractionResult:
    summary: str
    entities_found: list[dict] = field(default_factory=list)
    entities_count: int = 0
    detected_type: str = ""
    confidence: float = 0.0
    suggested_rules: list[str] = field(default_factory=list)
    raw_text_preview: str = ""


def _count_data_rows(text: str) -> int:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return max(0, len(lines) - 1)  # subtract header


def _extract_prices(text: str) -> list[dict]:
    prices = []
    for m in re.finditer(r"(?:RM|MYR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE):
        try:
            val = float(m.group(1).replace(",", ""))
            prices.append({"value": val, "currency": "RM", "context": text[max(0, m.start()-30):m.end()+30].strip()})
        except ValueError:
            pass
    return prices[:20]


def _extract_dates(text: str) -> list[str]:
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    ]
    dates = []
    for pat in patterns:
        dates.extend(re.findall(pat, text, re.IGNORECASE))
    return dates[:10]


def _extract_skus(text: str) -> list[str]:
    return list(set(re.findall(r"\b[A-Z]{2,4}[-_][A-Z0-9]{2,}[-_]?[A-Z0-9]*\b", text)))[:30]


def _extract_percentages(text: str) -> list[dict]:
    results = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", text):
        ctx = text[max(0, m.start()-40):m.end()+20].strip()
        results.append({"value": float(m.group(1)), "context": ctx})
    return results[:20]


def _detect_document_type(text: str, upload_type: UploadType) -> str:
    """Returns a human-friendly detected type string."""
    lower = text.lower()
    if upload_type == UploadType.competitor_price_data:
        return "Competitor Price Data"
    if upload_type == UploadType.product_catalog:
        return "Product Catalog"
    if "rebate" in lower or "incentive" in lower:
        return "Rebate / Incentive Document"
    if "campaign" in lower or "promotion" in lower or "free gift" in lower:
        return "Campaign / Promotion Memo"
    if "price list" in lower or "pricebook" in lower:
        return "Price List"
    if "trading terms" in lower:
        return "Trading Terms Agreement"
    if "contract" in lower:
        return "Contract Pricing Document"
    return UploadType(upload_type).value.replace("_", " ").title()


def extract_document_intelligence(
    text: str,
    upload_type: UploadType,
    filename: str = "",
) -> ExtractionResult:
    """Extract structured business intelligence from uploaded document text."""
    if not text.strip():
        return ExtractionResult(
            summary="The uploaded file appears to be empty or could not be read.",
            confidence=0.0,
        )

    detected_type = _detect_document_type(text, upload_type)
    prices = _extract_prices(text)
    dates = _extract_dates(text)
    skus = _extract_skus(text)
    percentages = _extract_percentages(text)
    data_rows = _count_data_rows(text)

    entities: list[dict] = []
    if skus:
        entities.append({"type": "SKUs / Product Codes", "count": len(skus), "samples": skus[:5]})
    if prices:
        entities.append({"type": "Prices", "count": len(prices), "samples": [f"RM {p['value']}" for p in prices[:5]]})
    if dates:
        entities.append({"type": "Dates", "count": len(dates), "samples": dates[:5]})
    if percentages:
        entities.append({"type": "Percentages", "count": len(percentages), "samples": [f"{p['value']}%" for p in percentages[:5]]})

    # Build plain-language summary
    parts = [f"Detected document type: **{detected_type}**."]
    if data_rows > 0:
        parts.append(f"Contains approximately {data_rows} data rows.")
    if skus:
        parts.append(f"Found {len(skus)} product codes/SKUs.")
    if prices:
        vals = [p["value"] for p in prices]
        parts.append(f"Found {len(prices)} price references (range: RM {min(vals):,.2f} – RM {max(vals):,.2f}).")
    if dates:
        parts.append(f"Found {len(dates)} date references.")
    if percentages:
        parts.append(f"Found {len(percentages)} percentage values (e.g. discounts, margins, rebates).")

    # Suggest business rules
    rules: list[str] = []
    lower = text.lower()
    if upload_type == UploadType.competitor_price_data:
        rules.append("Create competitor product entries for market comparison")
    if upload_type == UploadType.product_catalog:
        rules.append("Import products into product catalog")
    if upload_type in (UploadType.current_price_list, UploadType.pricing_policy):
        rules.append("Create or update pricebook entries")
    if "campaign" in lower or "promotion" in lower or "free gift" in lower:
        rules.append("Create campaign with eligibility rules")
    if "rebate" in lower or "incentive" in lower:
        rules.append("Update rebate program rates")
    if "trading terms" in lower:
        rules.append("Extract trading terms and incentive structure")
    if "contract" in lower:
        rules.append("Create customer-specific contract pricing rules")
    if upload_type == UploadType.margin_target_sheet:
        rules.append("Update pricing rules with margin targets")

    total_entities = sum(e["count"] for e in entities)
    confidence = min(0.95, 0.5 + (0.1 * min(len(entities), 4)) + (0.01 * min(data_rows, 10)))

    summary = " ".join(parts)

    return ExtractionResult(
        summary=summary,
        entities_found=entities,
        entities_count=total_entities,
        detected_type=detected_type,
        confidence=round(confidence, 2),
        suggested_rules=rules,
        raw_text_preview=text[:500],
    )

import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.models import Inventory, PricingRule, Product, RoleEnum, User

logger = logging.getLogger("app")

router = APIRouter(prefix="/bulk-import", tags=["bulk-import"])

ALLOWED_EXTENSIONS = {"xlsx", "csv"}
REQUIRED_COLUMNS = {"sku", "name", "category", "unit_cost", "list_price"}


def _parse_csv(file_bytes: bytes) -> list[dict[str, Any]]:
    import csv

    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        cleaned = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
        rows.append(cleaned)
    return rows


def _parse_xlsx(file_bytes: bytes) -> list[dict[str, Any]]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    if not ws:
        return []

    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_raw = next(rows_iter)
    except StopIteration:
        return []

    headers = [str(h).strip().lower().replace(" ", "_") if h else "" for h in header_raw]
    rows = []
    for row_values in rows_iter:
        row_dict = {}
        for idx, value in enumerate(row_values):
            if idx < len(headers) and headers[idx]:
                row_dict[headers[idx]] = str(value).strip() if value is not None else ""
        if any(row_dict.values()):
            rows.append(row_dict)
    wb.close()
    return rows


@router.post("/products", status_code=status.HTTP_200_OK)
async def bulk_import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> dict[str, Any]:
    """
    Import products from an Excel (.xlsx) or CSV (.csv) file.
    Required columns: sku, name, category, unit_cost, list_price.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        rows = _parse_xlsx(file_bytes) if ext == "xlsx" else _parse_csv(file_bytes)
    except Exception as exc:
        logger.exception({"event": "bulk_import_parse_error", "error": str(exc)})
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}") from exc

    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in file")

    # Validate columns
    first_row_keys = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - first_row_keys
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}. Found: {', '.join(sorted(first_row_keys))}",
        )

    imported = 0
    skipped = 0
    errors: list[dict[str, str]] = []

    for idx, row in enumerate(rows, start=2):
        sku = row.get("sku", "").strip()
        name = row.get("name", "").strip()
        category = row.get("category", "").strip()
        unit_cost_str = row.get("unit_cost", "").strip()
        list_price_str = row.get("list_price", "").strip()

        if not sku or not name:
            errors.append({"row": str(idx), "error": "Missing sku or name"})
            continue

        # Check for duplicate
        existing = db.scalar(select(Product).where(Product.sku == sku))
        if existing:
            skipped += 1
            continue

        try:
            unit_cost = float(unit_cost_str)
            list_price = float(list_price_str)
        except (ValueError, TypeError):
            errors.append({"row": str(idx), "error": f"Invalid numeric values for sku={sku}"})
            continue

        if unit_cost <= 0 or list_price <= 0:
            errors.append({"row": str(idx), "error": f"Prices must be > 0 for sku={sku}"})
            continue

        product = Product(
            sku=sku,
            name=name,
            category=category or "general",
            unit_cost=unit_cost,
            list_price=list_price,
        )
        db.add(product)
        db.flush()

        # Create inventory record
        db.add(Inventory(product_id=product.id, on_hand=100, stock_age_days_avg=30))

        # Ensure pricing rule exists
        channel = "direct"
        rule_exists = db.scalar(
            select(PricingRule).where(
                PricingRule.channel == channel,
                PricingRule.category == product.category,
            )
        )
        if not rule_exists:
            db.add(
                PricingRule(
                    channel=channel,
                    category=product.category,
                    margin_floor_percent=10.0,
                    max_discount_percent=30.0,
                    approval_required_below_margin_buffer=2.0,
                )
            )

        imported += 1

    db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "total_rows": len(rows),
    }

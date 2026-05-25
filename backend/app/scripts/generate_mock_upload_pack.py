from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import select

from app.db.models import Customer, Product
from app.db.session import SessionLocal


ROOT_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT_DIR / "docs" / "mock-uploads"
VALID_DIR = OUTPUT_DIR / "valid"
INVALID_DIR = OUTPUT_DIR / "invalid"


def _load_products(limit: int = 8) -> list[dict[str, object]]:
    fallback = [
        {"sku": "PLATZ-DC-35", "name": "PLATZ DC Pump Water Heater 35L", "category": "water_heater", "list_price": 1299.0},
        {"sku": "QUATEK-50", "name": "QUATEK Water Heater 50L", "category": "water_heater", "list_price": 1399.0},
        {"sku": "STARKER-80", "name": "STARKER Water Heater 80L", "category": "water_heater", "list_price": 1699.0},
        {"sku": "EDGE-60", "name": "EDGE Water Heater 60L", "category": "water_heater", "list_price": 1499.0},
        {"sku": "STIQ-45", "name": "STIQ Water Heater 45L", "category": "water_heater", "list_price": 1199.0},
        {"sku": "ZETA-HB-01", "name": "ZETA Hand Bidet 01", "category": "hand_bidet", "list_price": 299.0},
    ]

    try:
        db = SessionLocal()
        rows = db.execute(
            select(Product.sku, Product.name, Product.category, Product.list_price)
            .order_by(Product.created_at.asc())
            .limit(limit)
        ).all()
        db.close()
        if not rows:
            return fallback

        samples: list[dict[str, object]] = []
        for sku, name, category, list_price in rows:
            value = float(list_price if isinstance(list_price, Decimal) else list_price or 0)
            samples.append(
                {
                    "sku": sku,
                    "name": name,
                    "category": category,
                    "list_price": round(value, 2),
                }
            )
        return samples
    except Exception:
        return fallback


def _load_customers(limit: int = 4) -> list[str]:
    fallback = ["Customer 1", "Customer 2", "Customer 3", "Customer 4"]
    try:
        db = SessionLocal()
        rows = db.execute(select(Customer.name).order_by(Customer.created_at.asc()).limit(limit)).all()
        db.close()
        if not rows:
            return fallback
        return [name for (name,) in rows]
    except Exception:
        return fallback


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(lines: list[str]) -> bytes:
    y = 760
    commands = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index == 0:
            commands.append(f"({_escape_pdf_text(line)}) Tj")
        else:
            y -= 16
            commands.append(f"72 {y} Td")
            commands.append(f"({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    stream_text = "\n".join(commands) + "\n"
    stream_bytes = stream_text.encode("latin-1", errors="ignore")

    objects: list[bytes] = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        (
            "3 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\n"
            "endobj\n"
        ).encode("ascii")
    )
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    objects.append(
        (
            f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"endstream\nendobj\n"
        )
    )

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def _write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _write_xlsx(path: Path, sheet_name: str, headers: list[str], rows: list[list[object]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_sales_pack(products: list[dict[str, object]], customers: list[str]) -> None:
    sales_rows = []
    for index, product in enumerate(products[:5]):
        sales_rows.append(
            [
                f"SO-2026-{1001 + index}",
                customers[index % len(customers)],
                product["sku"],
                product["name"],
                4 + index,
                round(float(product["list_price"]) * 0.92, 2),
                "project" if index % 2 == 0 else "direct",
                f"2026-02-{10 + index:02d}",
            ]
        )
    _write_csv(
        VALID_DIR / "sales_history_q1_2026.csv",
        ["order_no", "customer_name", "sku", "product_name", "qty", "net_price", "channel", "order_date"],
        sales_rows,
    )

    catalog_rows = [
        [product["sku"], product["name"], product["category"], product["list_price"], "2", 4 + index, "mid"]
        for index, product in enumerate(products[:6])
    ]
    _write_xlsx(
        VALID_DIR / "product_catalog_2026.xlsx",
        "Catalog",
        ["sku", "product_name", "category", "list_price", "warranty_years", "feature_count", "brand_tier"],
        catalog_rows,
    )

    pricebook_rows = []
    for product in products[:6]:
        list_price = float(product["list_price"])
        pricebook_rows.append(
            [
                product["sku"],
                round(list_price, 2),
                round(list_price * 0.95, 2),
                round(list_price * 0.92, 2),
                "2026-01-01",
                "2026-12-31",
            ]
        )
    _write_xlsx(
        VALID_DIR / "current_price_list_channels.xlsx",
        "Pricebook",
        ["sku", "lsp_price", "wm_price", "em_price", "effective_start", "effective_end"],
        pricebook_rows,
    )

    competitor_rows = []
    for index, product in enumerate(products[:5]):
        list_price = float(product["list_price"])
        competitor_rows.append(
            [
                "Competitor A" if index % 2 == 0 else "Competitor B",
                f"CMP-{index + 1:03d}",
                product["name"],
                product["category"],
                round(list_price * (0.9 + index * 0.02), 2),
                3 + index % 3,
                5 + index,
                "premium" if index % 2 == 0 else "value",
                70 + index * 4,
            ]
        )
    _write_csv(
        VALID_DIR / "competitor_pricing_market_scan.csv",
        ["competitor_name", "competitor_sku", "product_name", "category", "price", "warranty_years", "feature_count", "brand_tier", "spec_score"],
        competitor_rows,
    )

    promo_rows = [
        ["2026-Q3 Water Heater Bundle", "water_heater", "bundle", "2026-07-01", "2026-09-30", "Bundle valve kit", "Project sales excluded"],
        ["2026-Q2 Hand Bidet Push", "hand_bidet", "discount", "2026-04-01", "2026-06-30", "5% off selected lines", "Corporate accounts only"],
    ]
    _write_xlsx(
        VALID_DIR / "promotion_calendar_2026.xlsx",
        "Calendar",
        ["campaign_name", "product_category", "benefit_type", "effective_start", "effective_end", "benefit_detail", "exclusions"],
        promo_rows,
    )


def _write_approver_pack(products: list[dict[str, object]]) -> None:
    approval_rows = [
        ["APR-1001", "Customer 1", products[0]["sku"], 8, 1180.0, 1260.0, "Below EM reference", "High"],
        ["APR-1002", "Customer 2", products[1]["sku"], 12, 1325.0, 1399.0, "Margin compression", "Medium"],
    ]
    _write_xlsx(
        VALID_DIR / "pricing_approval_sheet_q2.xlsx",
        "Approvals",
        ["approval_no", "customer_name", "sku", "qty", "requested_price", "recommended_price", "reason", "priority"],
        approval_rows,
    )

    guideline_lines = [
        "Strategic Pricing Guideline FY2026",
        "Project channel quotes below EM require sales director approval.",
        "Target true margin for water heater category is at least 18 percent.",
        "Exception risk is high when channel reference pricing is missing.",
        "Use policy source reference in every approval decision.",
    ]
    (VALID_DIR / "strategic_pricing_guideline_2026.pdf").write_bytes(_build_simple_pdf(guideline_lines))

    quarterly_rows = [
        ["water_heater", "project", 18.0, 7.0, "Protect premium positioning while clearing old stock"],
        ["hand_bidet", "direct", 20.0, 6.0, "Defend margin with selective bundle offers"],
    ]
    _write_xlsx(
        VALID_DIR / "quarterly_pricing_plan_q3.xlsx",
        "QuarterlyPlan",
        ["category", "channel", "target_margin_percent", "max_discount_percent", "guidance"],
        quarterly_rows,
    )

    margin_rows = [
        ["water_heater", 18.0, 21.0, "Monitor leakage weekly"],
        ["hand_bidet", 20.0, 23.0, "Use premium positioning"],
    ]
    _write_xlsx(
        VALID_DIR / "margin_target_sheet_2026.xlsx",
        "Targets",
        ["category", "floor_margin_percent", "target_margin_percent", "notes"],
        margin_rows,
    )


def _write_executive_pack() -> None:
    _write_csv(
        VALID_DIR / "strategic_targets_2026.csv",
        ["metric", "target_value", "period", "owner"],
        [
            ["revenue", "12500000", "FY2026", "Executive Office"],
            ["true_margin_percent", "19.5", "FY2026", "Commercial Finance"],
            ["leakage_amount", "450000", "FY2026", "Pricing Office"],
        ],
    )

    market_report_lines = [
        "Market Report 2026 Water Heater Segment",
        "Competitor pricing remains aggressive in the entry and mid bands.",
        "Premium lines retain pricing power when warranty and feature count are highlighted.",
        "Channel discounting pressure is highest in project sales.",
        "Use value positioning instead of blanket discounting.",
    ]
    (VALID_DIR / "market_report_water_heaters_2026.pdf").write_bytes(_build_simple_pdf(market_report_lines))


def _write_admin_pack(products: list[dict[str, object]], customers: list[str]) -> None:
    policy_lines = [
        "Pricing Policy FY2026",
        "Quotes below EM or WM reference price require approval governance.",
        "Not applicable for special price purchase unless finance approves the exception.",
        "Campaign eligibility must be checked before rebate programs are applied.",
        "Decision traceability must store source documents and finance snapshot references.",
    ]
    (VALID_DIR / "pricing_policy_master_2026.pdf").write_bytes(_build_simple_pdf(policy_lines))

    campaign_lines = [
        "Campaign Memo Q3 2026",
        "Free gift for DC pump water heater with minimum two units.",
        "Excluded: project sales, special price purchase, FLUSSO series.",
        "Gift SKU: RPG-BAG-NB and RPG-BAG-GR.",
        "Campaign cost per eligible quote estimated at RM 18.",
    ]
    (VALID_DIR / "campaign_memo_dc_pump_q3_2026.pdf").write_bytes(_build_simple_pdf(campaign_lines))

    trading_terms_lines = [
        "Trading Terms FY2026",
        "Annual rebate tier: core 2.5 percent, strategic 3.5 percent, growth 1.5 percent.",
        "Display incentive: 1.0 percent.",
        "Retroactive incentive allowed for quarterly target achievement.",
        "Manager discretion rebate up to 0.5 percent requires finance review.",
    ]
    (VALID_DIR / "trading_terms_fy2026.pdf").write_bytes(_build_simple_pdf(trading_terms_lines))

    _write_csv(
        VALID_DIR / "rebate_agreement_fy2026.csv",
        ["channel", "customer_tier", "rebate_percent", "display_incentive_percent", "retroactive_rate_percent", "manager_discretion_percent"],
        [
            ["direct", "strategic", 3.5, 1.0, 1.0, 0.5],
            ["direct", "core", 2.5, 1.0, 0.8, 0.5],
            ["project", "growth", 1.5, 0.5, 0.5, 0.25],
        ],
    )

    contract_rows = [
        [customers[0], products[0]["sku"], 1180.0, 1350.0, 12.0, "2026-01-01", "2026-12-31"],
        [customers[1], products[1]["sku"], 1285.0, 1450.0, 10.0, "2026-01-01", "2026-12-31"],
    ]
    _write_xlsx(
        VALID_DIR / "contract_pricing_strategic_accounts.xlsx",
        "Contracts",
        ["customer_name", "sku", "floor_price", "ceiling_price", "discount_cap_percent", "effective_start", "effective_end"],
        contract_rows,
    )

    _write_json(
        VALID_DIR / "model_configuration_control_tower.json",
        {
            "pricing_model": {
                "provider": "openai",
                "model_name": "gpt-5.4-mini",
                "fallback_enabled": True,
                "confidence_floor": 0.55,
            },
            "finance_engine": {
                "true_margin_enabled": True,
                "leakage_control_enabled": True,
            },
        },
    )

    _write_csv(
        VALID_DIR / "rule_mapping_template.csv",
        ["document_type", "field_name", "target_rule", "required"],
        [
            ["campaign_memo", "gift_sku", "campaign_rule.entitlement_json", "yes"],
            ["pricing_policy", "approval_limit", "policy_clause.structured_json", "yes"],
            ["contract_pricing", "floor_price", "contract_line.floor_price", "yes"],
        ],
    )

    _write_csv(
        VALID_DIR / "user_role_config.csv",
        ["name", "email", "role", "account_status"],
        [
            ["Admin User", "admin@gmail.com", "admin", "active"],
            ["Sales Manager", "salesmanager@gmail.com", "sales", "active"],
            ["Sales Director", "salesdirector@gmail.com", "approver", "active"],
            ["Executive Viewer", "executiveviewer@gmail.com", "executive", "active"],
        ],
    )

    _write_csv(
        VALID_DIR / "audit_log_archive_sample.csv",
        ["action", "entity_type", "entity_id", "reason", "created_at"],
        [
            ["quote_created", "quote", "Q-1001", "Initial mock archive row", "2026-03-01T09:00:00Z"],
            ["approval_requested", "approval", "A-1001", "Mock archive review", "2026-03-01T10:00:00Z"],
        ],
    )


def _write_invalid_pack() -> None:
    _write_csv(
        INVALID_DIR / "current_price_list_invalid_headers.csv",
        ["sku", "price", "effective_start"],
        [["SKU-UNKNOWN", "ABC", "2026-01-01"]],
    )
    (INVALID_DIR / "campaign_memo_empty.txt").write_text("", encoding="utf-8")
    _write_json(
        INVALID_DIR / "model_configuration_invalid.json",
        {"pricing_model": {"provider": None, "model_name": 123}},
    )


def _write_readme() -> None:
    content = """# Mock Upload Pack

This folder contains realistic sample files for the RevenueMind upload flows.

## Valid files

- `sales_history_q1_2026.csv` -> upload as `sales_history`
- `product_catalog_2026.xlsx` -> upload as `product_catalog`
- `current_price_list_channels.xlsx` -> upload as `current_price_list`
- `competitor_pricing_market_scan.csv` -> upload as `competitor_price_data`
- `promotion_calendar_2026.xlsx` -> upload as `promotion_calendar`
- `pricing_approval_sheet_q2.xlsx` -> upload as `pricing_approval_sheet`
- `strategic_pricing_guideline_2026.pdf` -> upload as `strategic_pricing_guideline`
- `quarterly_pricing_plan_q3.xlsx` -> upload as `quarterly_pricing_plan`
- `margin_target_sheet_2026.xlsx` -> upload as `margin_target_sheet`
- `strategic_targets_2026.csv` -> upload as `strategic_targets`
- `market_report_water_heaters_2026.pdf` -> upload as `market_reports`
- `pricing_policy_master_2026.pdf` -> upload as `pricing_policy`
- `campaign_memo_dc_pump_q3_2026.pdf` -> upload as `campaign_memo`
- `trading_terms_fy2026.pdf` -> upload as `trading_terms`
- `rebate_agreement_fy2026.csv` -> upload as `rebate_agreement`
- `contract_pricing_strategic_accounts.xlsx` -> upload as `contract_pricing`
- `model_configuration_control_tower.json` -> upload as `model_configuration`
- `rule_mapping_template.csv` -> upload as `rule_mapping_template`
- `user_role_config.csv` -> upload as `user_role_config`
- `audit_log_archive_sample.csv` -> upload as `audit_log_archive`

## Invalid files

- `current_price_list_invalid_headers.csv` -> test pricebook validation failure
- `campaign_memo_empty.txt` -> test empty-file handling
- `model_configuration_invalid.json` -> test invalid config parsing

## Suggested manual upload order

1. `product_catalog_2026.xlsx`
2. `current_price_list_channels.xlsx`
3. `competitor_pricing_market_scan.csv`
4. `promotion_calendar_2026.xlsx`
5. `pricing_policy_master_2026.pdf`
6. `campaign_memo_dc_pump_q3_2026.pdf`
7. `trading_terms_fy2026.pdf`
8. `rebate_agreement_fy2026.csv`
9. `contract_pricing_strategic_accounts.xlsx`
10. `strategic_targets_2026.csv`

These files are designed to help you see:

- upload governance
- extracted summaries
- policy ingestion
- campaign eligibility
- rebate and contract linkage
- market comparison with uploaded competitor data
- recommendation traceability after running quote recommendations
"""
    (OUTPUT_DIR / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    VALID_DIR.mkdir(parents=True, exist_ok=True)
    INVALID_DIR.mkdir(parents=True, exist_ok=True)

    products = _load_products(limit=8)
    customers = _load_customers(limit=4)

    _write_sales_pack(products, customers)
    _write_approver_pack(products)
    _write_executive_pack()
    _write_admin_pack(products, customers)
    _write_invalid_pack()
    _write_readme()

    print(f"Generated mock upload pack in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

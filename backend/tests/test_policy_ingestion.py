import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Product
from app.services.policy_ingestion import validate_clause_schema


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_can_upload_policy_and_view_details(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "FY2025 Toiletries Bag Free Gift Campaign",
            "doc_type": "memo",
            "text": "Effective from 1 Jul 2025 to 16 Sep 2025. Not applicable for Corporate Account. Free gift RPG-BAG-NB.",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["title"] == "FY2025 Toiletries Bag Free Gift Campaign"
    assert body["status"] == "draft"
    assert body["review_status"] == "needs_review"
    assert body["clause_count"] >= 1
    assert body["policy_source_reference"].startswith("POL-")
    assert body["clauses"][0]["policy_source_reference"].startswith("POL-")
    assert len(body["clauses"]) >= 1

    list_resp = client.get("/api/policies", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    policy_id = body["id"]
    detail = client.get(f"/api/policies/{policy_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert detail.status_code == 200
    assert detail.json()["id"] == policy_id


def test_admin_can_review_policy_and_activate_campaign_rule(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "FY2025 Toiletries Bag Free Gift Campaign",
            "doc_type": "memo",
            "status": "active",
            "text": (
                "FY2025 Toiletries Bag Free Gift Campaign for DC pump water heater, "
                "excluding FLUSSO series. Effective from 1 Jul 2025 to 16 Sep 2025. "
                "Not applicable for Corporate Account, Project Sales, Special Price Purchase. "
                "Free gift codes RPG-BAG-NB and RPG-BAG-GR."
            ),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    policy_id = upload.json()["id"]

    review = client.patch(
        f"/api/policies/{policy_id}/review",
        json={
            "review_notes": "Reviewed and approved for activation.",
            "auto_create_campaign": True,
            "action": "activate",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review.status_code == 200
    review_body = review.json()
    assert review_body["status"] == "active"
    assert review_body["review_status"] == "active"
    assert review_body["review_notes"] == "Reviewed and approved for activation."

    campaigns = client.get("/api/campaigns", headers={"Authorization": f"Bearer {admin_token}"})
    assert campaigns.status_code == 200
    assert len(campaigns.json()) == 1
    campaign = campaigns.json()[0]
    assert campaign["name"] == "FY2025 Toiletries Bag Free Gift Campaign"
    assert len(campaign["rules"]) == 1
    rule = campaign["rules"][0]
    assert rule["rule_type"] == "free_gift"
    assert "FLUSSO" in rule["exclusion_json"]["series_excluded"]
    assert "RPG-BAG-NB" in rule["entitlement_json"]["gift_skus"]


def test_admin_can_activate_campaign_memo_with_discount_and_bundle_rules(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "FY2025 Growth Campaign",
            "doc_type": "memo",
            "status": "active",
            "text": (
                "Campaign discount 5% for DC pump water heater.\n"
                "Bundle with BUNDLE-VALVE-01 at RM 12.\n"
                "Free gift RPG-BAG-NB for qualifying orders."
            ),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    policy_id = upload.json()["id"]

    review = client.patch(
        f"/api/policies/{policy_id}/review",
        json={"auto_create_campaign": True, "action": "activate"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review.status_code == 200

    campaigns = client.get("/api/campaigns", headers={"Authorization": f"Bearer {admin_token}"})
    assert campaigns.status_code == 200
    campaign = next(row for row in campaigns.json() if row["name"] == "FY2025 Growth Campaign")
    rule_types = {rule["rule_type"] for rule in campaign["rules"]}
    assert {"free_gift", "discount", "bundle"} <= rule_types
    discount_rule = next(rule for rule in campaign["rules"] if rule["rule_type"] == "discount")
    assert discount_rule["entitlement_json"]["discount_percent"] == 5.0
    bundle_rule = next(rule for rule in campaign["rules"] if rule["rule_type"] == "bundle")
    assert bundle_rule["entitlement_json"]["bundle_skus"] == ["BUNDLE-VALVE-01"]


def test_admin_can_activate_trading_terms_and_create_rebate_program(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "FY2025 Trading Terms",
            "doc_type": "trading_terms",
            "status": "active",
            "text": (
                "Direct channel annual incentive rebate strategic 12%, core 10%, growth 8%.\n"
                "Display incentive 2% for showroom execution.\n"
                "MDF 1% for approved launches.\n"
                "Manager discretion 0.5% requires finance approval.\n"
                "Retroactive rebate 1% applies after annual target confirmation."
            ),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    policy_id = upload.json()["id"]

    review = client.patch(
        f"/api/policies/{policy_id}/review",
        json={"review_notes": "Trading terms approved.", "action": "activate"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review.status_code == 200

    programs = client.get("/api/rebate-programs", headers={"Authorization": f"Bearer {admin_token}"})
    assert programs.status_code == 200
    assert len(programs.json()) == 1
    program = programs.json()[0]
    assert program["name"] == "FY2025 Trading Terms"
    assert program["channel"] == "direct"
    assert program["tier_rates_json"]["core"] == 10.0
    assert program["display_incentive_percent"] == 2.0
    assert program["mdf_percent"] == 1.0
    assert program["retroactive_incentive"] is True
    assert "finance approval" in program["manager_discretion_warning"].lower()


def test_sales_can_upload_policy(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "Sales Upload",
            "doc_type": "memo",
            "text": "Some policy text.",
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 201
    assert upload.json()["status"] == "draft"


def test_approver_can_read_policy_list(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")
    approver_token = _token(client, "salesdirector@gmail.com", "123456")

    client.post(
        "/api/policies/upload",
        json={
            "title": "Trading Terms 2025",
            "doc_type": "trading_terms",
            "text": "Rebate tier applies by annual turnover.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    list_resp = client.get("/api/policies", headers={"Authorization": f"Bearer {approver_token}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    campaigns = client.get("/api/campaigns", headers={"Authorization": f"Bearer {approver_token}"})
    assert campaigns.status_code == 200


def test_sales_can_upload_pricebook_with_items(client: TestClient, db_session: Session, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-001",
        name="PLATZ HTR-100",
        category="water_heater",
        list_price=1234.0,
        unit_cost=700.0,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    upload = client.post(
        "/api/pricebooks/upload",
        json={
            "name": "FY2025 Water Heater WM",
            "channel": "wm",
            "currency": "rm",
            "items": [
                {
                    "product_id": str(product.id),
                    "list_price": 1199.0,
                    "notes": "Special WM list",
                }
            ],
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 201
    payload = upload.json()
    assert payload["channel"] == "wm"
    assert payload["currency"] == "RM"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["product_id"] == str(product.id)


def test_pricebook_upload_rejects_invalid_effective_window(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-DATE-001",
        name="Date Guard Heater",
        category="water_heater",
        list_price=1250.0,
        unit_cost=760.0,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    upload = client.post(
        "/api/pricebooks/upload",
        json={
            "name": "Invalid Date Book",
            "channel": "lsp",
            "currency": "rm",
            "effective_start": "2026-06-01T00:00:00+00:00",
            "effective_end": "2026-05-01T00:00:00+00:00",
            "items": [
                {
                    "product_id": str(product.id),
                    "list_price": 1199.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 400
    assert "effective_end" in upload.json()["detail"]


def test_non_sales_cannot_upload_pricebook(client: TestClient, seeded_users):
    approver_token = _token(client, "salesdirector@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    blocked = client.post(
        "/api/pricebooks/upload",
        json={
            "name": "Blocked",
            "channel": "lsp",
            "items": [],
        },
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert blocked.status_code == 403
    blocked_admin = client.post(
        "/api/pricebooks/upload",
        json={
            "name": "Blocked",
            "channel": "lsp",
            "items": [],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert blocked_admin.status_code == 403


def test_sales_can_upload_pricebook_from_csv(client: TestClient, db_session: Session, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-CSV-001",
        name="STARKER HTR-200",
        category="water_heater",
        list_price=1450.0,
        unit_cost=900.0,
    )
    db_session.add(product)
    db_session.commit()

    response = client.post(
        "/api/pricebooks/upload",
        data={"name": "CSV LSP Pricebook", "channel": "lsp", "currency": "RM"},
        files={
            "file": (
                "prices.csv",
                b"sku,list_price,notes\nSKU-PB-CSV-001,1399.00,FY2025 LSP\n",
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "CSV LSP Pricebook"
    assert body["channel"] == "lsp"
    assert len(body["items"]) == 1


def test_sales_can_upload_pricebook_from_xlsx(client: TestClient, db_session: Session, seeded_users):
    openpyxl = pytest.importorskip("openpyxl")
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-XLSX-001",
        name="PLATO HTR-300",
        category="water_heater",
        list_price=1680.0,
        unit_cost=980.0,
    )
    db_session.add(product)
    db_session.commit()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prices"
    ws.append(["sku", "list_price", "notes"])
    ws.append(["SKU-PB-XLSX-001", "1599.00", "FY2025 XLSX"])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    response = client.post(
        "/api/pricebooks/upload",
        data={"name": "XLSX WM Pricebook", "channel": "wm", "currency": "RM"},
        files={
            "file": (
                "prices.xlsx",
                stream.read(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "XLSX WM Pricebook"
    assert body["channel"] == "wm"
    assert len(body["items"]) == 1


def test_admin_can_view_and_delete_sales_uploaded_pricebook(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-DEL-001",
        name="Delete Me",
        category="water_heater",
        list_price=1200.0,
        unit_cost=800.0,
    )
    db_session.add(product)
    db_session.commit()

    upload = client.post(
        "/api/pricebooks/upload",
        data={"name": "Delete Target", "channel": "lsp", "currency": "RM"},
        files={
            "file": (
                "prices.csv",
                b"sku,list_price,notes\nSKU-PB-DEL-001,1150.00,delete test\n",
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 201
    pricebook_id = upload.json()["id"]

    listed = client.get("/api/pricebooks", headers={"Authorization": f"Bearer {admin_token}"})
    assert listed.status_code == 200
    assert any(row["id"] == pricebook_id for row in listed.json())

    deleted = client.delete(f"/api/pricebooks/{pricebook_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert deleted.status_code == 204

    listed_after = client.get("/api/pricebooks", headers={"Authorization": f"Bearer {admin_token}"})
    assert listed_after.status_code == 200
    assert all(row["id"] != pricebook_id for row in listed_after.json())


def test_sales_cannot_delete_pricebook(client: TestClient, db_session: Session, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    product = Product(
        sku="SKU-PB-NODEL-001",
        name="No Delete",
        category="water_heater",
        list_price=1200.0,
        unit_cost=800.0,
    )
    db_session.add(product)
    db_session.commit()

    upload = client.post(
        "/api/pricebooks/upload",
        data={"name": "No Delete Target", "channel": "lsp", "currency": "RM"},
        files={
            "file": (
                "prices.csv",
                b"sku,list_price,notes\nSKU-PB-NODEL-001,1150.00,delete forbidden\n",
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 201
    pricebook_id = upload.json()["id"]

    blocked = client.delete(f"/api/pricebooks/{pricebook_id}", headers={"Authorization": f"Bearer {sales_token}"})
    assert blocked.status_code == 403

    cleanup = client.delete(f"/api/pricebooks/{pricebook_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert cleanup.status_code == 204


def test_clause_schema_validation_rejects_invalid_payload():
    with pytest.raises(Exception):
        validate_clause_schema({"clauses": [{"clause_type": "bad-type", "raw_text": "x", "confidence": 1}]})


def test_sales_cannot_review_policy_document(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    upload = client.post(
        "/api/policies/upload",
        json={
            "title": "Sales Review Block",
            "doc_type": "memo",
            "text": "Simple policy text for review permissions.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    policy_id = upload.json()["id"]

    review = client.patch(
        f"/api/policies/{policy_id}/review",
        json={"review_notes": "Trying to review", "action": "activate"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert review.status_code == 403


def test_admin_can_upload_policy_from_text_file_multipart(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")
    memo_text = (
        "FY2025 Toiletries Bag Free Gift Campaign for DC pump water heater excluding FLUSSO series. "
        "Not applicable for Corporate Account."
    )

    response = client.post(
        "/api/policies/upload",
        data={
            "title": "FY2025 Memo Upload",
            "doc_type": "memo",
            "status": "active",
            "auto_create_campaign": "true",
        },
        files={"file": ("memo.txt", memo_text.encode("utf-8"), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "FY2025 Memo Upload"
    assert body["status"] == "draft"
    assert len(body["clauses"]) >= 1


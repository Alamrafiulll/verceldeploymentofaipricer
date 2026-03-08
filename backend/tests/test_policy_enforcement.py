from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    Campaign,
    CampaignRule,
    CampaignRuleType,
    CampaignStatus,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    PriceBook,
    PriceBookChannel,
    PriceBookItem,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
)


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _setup_policy_data(db_session: Session, seeded_users, product_name: str, requested_price: float) -> Quote:
    admin = seeded_users["admin"]
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]

    product = Product(
        sku=f"SKU-{abs(hash(product_name)) % 100000}",
        name=product_name,
        category="water_heater",
        list_price=1300.0,
        unit_cost=800.0,
    )
    db_session.add(product)
    db_session.flush()

    quote = Quote(
        created_by_user_id=sales.id,
        customer_id=customer.id,
        channel="direct",
        status=QuoteStatus.recommended,
    )
    db_session.add(quote)
    db_session.flush()
    db_session.add(
        QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=5,
            requested_price=requested_price,
            recommended_price=1050.0,
        )
    )

    document = PolicyDocument(
        title="FY2025 Memo",
        doc_type=PolicyDocumentType.memo,
        source_uri="internal://memo",
        file_hash=f"hash-{product.sku}",
        uploaded_by_user_id=admin.id,
        status=PolicyDocumentStatus.active,
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(document)
    db_session.flush()

    pricebook = PriceBook(
        name="LSP Book",
        channel=PriceBookChannel.lsp,
        currency="RM",
        source_document_id=document.id,
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(pricebook)
    db_session.flush()
    db_session.add(
        PriceBookItem(
            price_book_id=pricebook.id,
            product_id=product.id,
            list_price=1000.0,
            notes="LSP control",
        )
    )

    campaign = Campaign(
        name="FY2025 Toiletries Bag Free Gift Campaign",
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
        status=CampaignStatus.active,
        source_document_id=document.id,
    )
    db_session.add(campaign)
    db_session.flush()
    db_session.add(
        CampaignRule(
            campaign_id=campaign.id,
            rule_type=CampaignRuleType.free_gift,
            eligibility_json={"product_category": "water_heater", "model_type": "dc_pump"},
            exclusion_json={"series_excluded": ["FLUSSO"]},
            entitlement_json={
                "gift_skus": ["RPG-BAG-NB", "RPG-BAG-GR"],
                "quantity_per_quote": 1,
                "gift_cost_amount": 8.0,
            },
        )
    )

    db_session.commit()
    db_session.refresh(quote)
    return quote


def test_policy_check_returns_entitlements_and_pricebook_violation(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _setup_policy_data(
        db_session=db_session,
        seeded_users=seeded_users,
        product_name="PLATZ DC Pump Water Heater 35L",
        requested_price=900.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.get(
        f"/api/quotes/{quote.id}/policy-check",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    violation_codes = {item["code"] for item in payload["violations"]}
    assert "below_pricebook_list" in violation_codes
    assert len(payload["entitlements"]) == 1
    assert "RPG-BAG-NB" in payload["entitlements"][0]["sku_codes"]
    assert payload["campaign_summary"]["eligible_campaign_count"] == 1
    assert payload["pricebook_compliance_summary"]["reference_label"] == "LSP"
    assert payload["pricebook_compliance_summary"]["status"] == "below_reference_price"


def test_policy_check_marks_campaign_excluded_when_series_matches(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _setup_policy_data(
        db_session=db_session,
        seeded_users=seeded_users,
        product_name="FLUSSO DC Pump Water Heater 35L",
        requested_price=1100.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.get(
        f"/api/quotes/{quote.id}/policy-check",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    codes = {item["code"] for item in payload["violations"]}
    assert "campaign_excluded" in codes
    assert payload["entitlements"] == []


def test_policy_check_reports_missing_active_pricebook_when_effective_window_is_future(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    admin = seeded_users["admin"]
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]

    product = Product(
        sku="SKU-FUTURE-PB-001",
        name="Future Start Heater",
        category="water_heater",
        list_price=1300.0,
        unit_cost=800.0,
    )
    db_session.add(product)
    db_session.flush()

    quote = Quote(
        created_by_user_id=sales.id,
        customer_id=customer.id,
        channel="project",
        status=QuoteStatus.recommended,
    )
    db_session.add(quote)
    db_session.flush()
    db_session.add(
        QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=5,
            requested_price=1000.0,
            recommended_price=1050.0,
        )
    )

    document = PolicyDocument(
        title="Future EM Book",
        doc_type=PolicyDocumentType.price_list,
        source_uri="internal://future-em",
        file_hash="future-em-hash",
        uploaded_by_user_id=admin.id,
        status=PolicyDocumentStatus.active,
        effective_start=datetime.now(timezone.utc) + timedelta(days=2),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(document)
    db_session.flush()

    pricebook = PriceBook(
        name="Future EM Book",
        channel=PriceBookChannel.em,
        currency="RM",
        source_document_id=document.id,
        effective_start=datetime.now(timezone.utc) + timedelta(days=2),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(pricebook)
    db_session.flush()
    db_session.add(
        PriceBookItem(
            price_book_id=pricebook.id,
            product_id=product.id,
            list_price=1020.0,
            notes="Future EM reference",
        )
    )
    db_session.commit()

    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.get(
        f"/api/quotes/{quote.id}/policy-check",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["pricebook_compliance_summary"]["reference_label"] == "EM"
    assert payload["pricebook_compliance_summary"]["status"] == "no_active_pricebook"
    assert "starts on" in payload["pricebook_compliance_summary"]["message"].lower()
    assert any(item["code"] == "pricebook_missing" for item in payload["violations"])


def test_policy_check_returns_discount_and_bundle_campaign_context(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _setup_policy_data(
        db_session=db_session,
        seeded_users=seeded_users,
        product_name="PLATZ DC Pump Water Heater 50L",
        requested_price=980.0,
    )

    campaign = db_session.query(Campaign).filter(Campaign.name == "FY2025 Toiletries Bag Free Gift Campaign").one()
    db_session.add(
        CampaignRule(
            campaign_id=campaign.id,
            rule_type=CampaignRuleType.discount,
            eligibility_json={"product_category": "water_heater", "quote_channel_in": ["direct"]},
            exclusion_json={},
            entitlement_json={"discount_percent": 5.0, "applies_to": "quote"},
        )
    )
    db_session.add(
        CampaignRule(
            campaign_id=campaign.id,
            rule_type=CampaignRuleType.bundle,
            eligibility_json={"product_category": "water_heater"},
            exclusion_json={},
            entitlement_json={
                "bundle_skus": ["BUNDLE-VALVE-01"],
                "bundle_cost_amount": 12.0,
                "bundle_discount_percent": 3.0,
            },
        )
    )
    db_session.commit()

    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.get(
        f"/api/quotes/{quote.id}/policy-check",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    rule_types = {item["rule_type"] for item in payload["entitlements"]}
    assert {"free_gift", "discount", "bundle"} <= rule_types
    assert payload["campaign_summary"]["eligible_campaign_count"] == 3
    assert payload["campaign_summary"]["estimated_campaign_cost"] == 20.0
    discount_entry = next(item for item in payload["entitlements"] if item["rule_type"] == "discount")
    assert discount_entry["discount_percent"] == 5.0
    bundle_entry = next(item for item in payload["entitlements"] if item["rule_type"] == "bundle")
    assert bundle_entry["estimated_campaign_cost"] == 12.0
    assert bundle_entry["bundle_skus"] == ["BUNDLE-VALVE-01"]


from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    Approval,
    ApprovalStatus,
    Inventory,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    PriceBook,
    PriceBookChannel,
    PriceBookItem,
    PricingRule,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
    RiskLevel,
)


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_pricing_quote(
    db_session: Session,
    seeded_users,
    *,
    quote_status: QuoteStatus = QuoteStatus.recommended,
    recommended_price: float = 900.0,
    band_low: float = 850.0,
    band_high: float = 950.0,
    add_policy_book: bool = False,
    policy_list_price: float = 950.0,
    quote_channel: str = "direct",
    pricebook_channel: PriceBookChannel = PriceBookChannel.lsp,
) -> Quote:
    sales = seeded_users["sales"]
    admin = seeded_users["admin"]
    customer = seeded_users["customer"]

    product = Product(
        sku=f"SKU-ENT-{abs(hash((recommended_price, policy_list_price, quote_status.value))) % 100000}",
        name="Enterprise Water Heater",
        category="water_heater",
        list_price=1000.0,
        unit_cost=600.0,
    )
    db_session.add(product)
    db_session.flush()

    db_session.add(
        Inventory(
            product_id=product.id,
            on_hand=120,
            stock_age_days_avg=90,
        )
    )
    db_session.add(
        PricingRule(
            channel=quote_channel,
            category="water_heater",
            margin_floor_percent=10.0,
            max_discount_percent=20.0,
            approval_required_below_margin_buffer=2.0,
        )
    )

    quote = Quote(
        created_by_user_id=sales.id,
        customer_id=customer.id,
        channel=quote_channel,
        status=quote_status,
    )
    db_session.add(quote)
    db_session.flush()
    db_session.add(
        QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=10,
            requested_price=recommended_price,
            recommended_price=recommended_price,
            recommended_band_low=band_low,
            recommended_band_high=band_high,
            win_probability=0.7,
            confidence=0.8,
            risk_level=RiskLevel.low,
        )
    )

    if add_policy_book:
        document = PolicyDocument(
            title="Enterprise Price Policy",
            doc_type=PolicyDocumentType.price_list,
            source_uri="internal://enterprise-pricebook",
            file_hash=f"ent-{product.sku}",
            uploaded_by_user_id=admin.id,
            status=PolicyDocumentStatus.active,
            effective_start=datetime.now(timezone.utc) - timedelta(days=1),
            effective_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(document)
        db_session.flush()
        book = PriceBook(
            name="Enterprise LSP",
            channel=pricebook_channel,
            currency="RM",
            source_document_id=document.id,
            effective_start=datetime.now(timezone.utc) - timedelta(days=1),
            effective_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(book)
        db_session.flush()
        db_session.add(
            PriceBookItem(
                price_book_id=book.id,
                product_id=product.id,
                list_price=policy_list_price,
                notes="Enterprise policy list price",
            )
        )

    db_session.commit()
    db_session.refresh(quote)
    return quote


def test_recommendation_response_includes_true_margin_and_policy_summary(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.draft,
        add_policy_book=True,
        policy_list_price=880.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        f"/api/quotes/{quote.id}/recommend",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["true_margin_snapshot_summary"] is not None
    assert isinstance(payload["policy_entitlements_summary"], list)
    assert payload["pricebook_compliance_summary"] is not None
    assert payload["pricebook_compliance_summary"]["reference_label"] == "LSP"
    assert payload["contract_pricing_summary"] is not None
    assert payload["contract_pricing_summary"]["status"] == "no_contract"
    assert payload["true_margin_snapshot_summary"]["contract_summary"]["status"] == "no_contract"
    assert "list_revenue_total" in payload["true_margin_snapshot_summary"]
    assert "leakage_amount" in payload["true_margin_snapshot_summary"]
    assert isinstance(payload["true_margin_snapshot_summary"]["leakage_reasons"], list)


def test_finalize_requires_approval_when_policy_violation_is_high(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.recommended,
        recommended_price=900.0,
        band_low=880.0,
        band_high=920.0,
        add_policy_book=True,
        policy_list_price=980.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        f"/api/quotes/{quote.id}/finalize",
        json={"final_price": 900.0, "reason": "test finalize"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 400
    assert "approval required" in response.json()["detail"].lower()


def test_finalize_rejects_price_if_it_differs_from_approved_price(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.approved,
        recommended_price=900.0,
        band_low=850.0,
        band_high=950.0,
        add_policy_book=True,
        policy_list_price=850.0,
    )
    sales = seeded_users["sales"]
    approver = seeded_users["approver"]
    db_session.add(
        Approval(
            quote_id=quote.id,
            requested_by_user_id=sales.id,
            approver_user_id=approver.id,
            requested_price=900.0,
            requested_discount=10.0,
            status=ApprovalStatus.approved,
            request_justification="Approved once",
            decision_reason="Approved",
            decided_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.post(
        f"/api/quotes/{quote.id}/finalize",
        json={"final_price": 880.0, "reason": "changed after approval"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 400
    assert "differs from approved price" in response.json()["detail"].lower()


def test_sales_can_request_approval_and_approver_can_see_pending_request(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.recommended,
        recommended_price=900.0,
        band_low=880.0,
        band_high=920.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    approver_token = _token(client, "salesdirector@gmail.com", "123456")

    request_response = client.post(
        f"/api/quotes/{quote.id}/request-approval",
        json={
            "requested_price": 860.0,
            "requested_discount": 14.0,
            "justification": "Customer is pushing below safe band due to competitive pressure.",
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert request_response.status_code == 200
    assert request_response.json()["status"] == "pending"

    db_session.refresh(quote)
    assert quote.status == QuoteStatus.approval_pending

    inbox_response = client.get(
        "/api/approvals?status=pending",
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert inbox_response.status_code == 200
    payload = inbox_response.json()
    assert len(payload) == 1
    assert payload[0]["quote_id"] == str(quote.id)
    assert payload[0]["status"] == "pending"


def test_recommendation_uses_wm_pricebook_for_distributor_quotes(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.draft,
        add_policy_book=True,
        policy_list_price=910.0,
        quote_channel="distributor",
        pricebook_channel=PriceBookChannel.wm,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        f"/api/quotes/{quote.id}/recommend",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["pricebook_compliance_summary"]["reference_channel"] == "wm"
    assert payload["pricebook_compliance_summary"]["reference_label"] == "WM"


def test_save_draft_quote(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote = _seed_pricing_quote(
        db_session=db_session,
        seeded_users=seeded_users,
        quote_status=QuoteStatus.recommended,
        recommended_price=900.0,
        band_low=880.0,
        band_high=920.0,
    )
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        f"/api/quotes/{quote.id}/save-draft",
        json={
            "requested_price": 870.0,
            "strategy_mode": "clear_inventory",
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recommended"

    # Refresh quote detail and verify that requested_price and strategy_mode are updated
    db_session.refresh(quote)
    db_session.refresh(quote.items[0])
    assert float(quote.items[0].requested_price) == 870.0
    assert quote.strategy_mode.value == "clear_inventory"



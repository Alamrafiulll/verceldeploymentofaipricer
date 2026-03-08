from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Product, Quote, QuoteItem, QuoteStatus


def test_negotiation_assistant_returns_guardrailed_ladder(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]

    product = Product(
        sku="SKU-NEG-001",
        name="PLATZ DC Pump Water Heater",
        category="water_heater",
        list_price=1200.0,
        unit_cost=700.0,
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
            quantity=4,
            requested_price=1100.0,
            recommended_price=1080.0,
            recommended_band_low=1040.0,
            recommended_band_high=1120.0,
        )
    )
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "salesmanager@gmail.com", "password": "123456"})
    token = login.json()["access_token"]

    response = client.get(
        f"/api/quotes/{quote.id}/negotiation-assistant",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["quote_id"] == str(quote.id)
    assert len(payload["concession_ladder"]) >= 1
    for step in payload["concession_ladder"]:
        assert 1040.0 <= step["target_price"] <= 1120.0


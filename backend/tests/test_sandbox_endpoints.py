from fastapi.testclient import TestClient


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_sandbox_product_create_and_list(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    create_resp = client.post(
        "/api/sandbox/products",
        json={
            "sku": "SBX-001",
            "name": "Sandbox Product",
            "category": "demo",
            "base_cost": 50.0,
            "current_price": 70.0,
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["sku"] == "SBX-001"
    assert created["base_cost"] == 50.0

    list_resp = client.get(
        "/api/sandbox/products",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert list_resp.status_code == 200
    assert any(product["sku"] == "SBX-001" for product in list_resp.json())


def test_sandbox_pricing_recommendation(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    create_resp = client.post(
        "/api/sandbox/products",
        json={
            "sku": "SBX-002",
            "name": "Sandbox Product 2",
            "category": "demo",
            "base_cost": 80.0,
            "current_price": 100.0,
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]

    recommend_resp = client.post(
        f"/api/sandbox/pricing/recommend/{product_id}",
        json={"discount_percent": 5},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert recommend_resp.status_code == 200
    body = recommend_resp.json()
    assert body["product_id"] == product_id
    assert body["predicted_price"] > 0
    assert 0 <= body["confidence"] <= 1
    assert body["model_version"]

    traces = client.get("/api/admin/ai-recommendations", headers={"Authorization": f"Bearer {admin_token}"})
    assert traces.status_code == 200
    assert any(row["product_id"] == product_id for row in traces.json())


def test_sandbox_dashboard_summary(client: TestClient, seeded_users):
    executive_token = _token(client, "executiveviewer@gmail.com", "123456")
    summary_resp = client.get(
        "/api/sandbox/dashboard/summary",
        headers={"Authorization": f"Bearer {executive_token}"},
    )
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert "total_products" in body
    assert "average_price" in body
    assert "predictions_made" in body


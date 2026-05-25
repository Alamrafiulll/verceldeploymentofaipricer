from fastapi.testclient import TestClient


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_enterprise_readiness_returns_scored_control_map(client: TestClient, seeded_users):
    admin_token = _token(client, "admin@gmail.com", "123456")

    response = client.get(
        "/api/admin/enterprise-readiness",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["score"] <= 100
    assert payload["status"] in {"enterprise_ready", "attention_needed", "not_ready"}
    assert {"Security", "Deployment", "Data Governance", "AI Governance", "Commercial Controls"}.issubset(
        set(payload["categories"].keys())
    )
    assert any(check["id"] == "auth_bypass_disabled" for check in payload["checks"])
    assert all(check["status"] in {"pass", "warning", "fail"} for check in payload["checks"])


def test_enterprise_readiness_requires_admin(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.get(
        "/api/admin/enterprise-readiness",
        headers={"Authorization": f"Bearer {sales_token}"},
    )

    assert response.status_code == 403

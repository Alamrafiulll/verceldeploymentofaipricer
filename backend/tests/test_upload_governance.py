from fastapi.testclient import TestClient


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_role_upload_matrix_endpoint(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.get("/api/uploads/matrix", headers={"Authorization": f"Bearer {sales_token}"})
    assert response.status_code == 200
    body = response.json()
    assert "sales_history" in body["sales"]
    assert "pricing_policy" in body["admin"]


def test_sales_can_upload_operational_csv(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.post(
        "/api/uploads",
        data={"upload_type": "sales_history", "description": "Weekly sales dump"},
        files={"file": ("sales_history.csv", b"sku,qty\nSKU-1,100\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["upload_type"] == "sales_history"
    assert body["file_ext"] == "csv"
    assert body["review_status"] == "draft"


def test_legacy_upload_rejects_empty_file(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.post(
        "/api/uploads",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_sales_cannot_upload_admin_document_type(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.post(
        "/api/uploads",
        data={"upload_type": "pricing_policy"},
        files={"file": ("policy.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 400
    assert "cannot upload" in response.json()["detail"]


def test_approver_executive_admin_upload_types(client: TestClient, seeded_users):
    approver_token = _token(client, "salesdirector@gmail.com", "123456")
    executive_token = _token(client, "executiveviewer@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    approver_upload = client.post(
        "/api/uploads",
        data={"upload_type": "strategic_pricing_guideline"},
        files={"file": ("guideline.pdf", b"%PDF-1.4 guideline", "application/pdf")},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert approver_upload.status_code == 201

    executive_upload = client.post(
        "/api/uploads",
        data={"upload_type": "market_reports"},
        files={"file": ("market.pdf", b"%PDF-1.4 market", "application/pdf")},
        headers={"Authorization": f"Bearer {executive_token}"},
    )
    assert executive_upload.status_code == 201

    admin_upload = client.post(
        "/api/uploads",
        data={"upload_type": "model_configuration"},
        files={"file": ("model.json", b"{\"model\":\"v1\"}", "application/json")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_upload.status_code == 201


def test_admin_can_list_all_and_delete_upload(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    admin_token = _token(client, "admin@gmail.com", "123456")

    upload = client.post(
        "/api/uploads",
        data={"upload_type": "product_catalog"},
        files={"file": ("catalog.xlsx", b"fake-binary", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 201
    upload_id = upload.json()["id"]

    list_all = client.get("/api/uploads?mine=false", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_all.status_code == 200
    assert any(row["id"] == upload_id for row in list_all.json())

    deleted = client.delete(f"/api/uploads/{upload_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert deleted.status_code == 204


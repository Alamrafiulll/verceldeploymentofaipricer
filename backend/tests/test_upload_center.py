from fastapi.testclient import TestClient


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_sales_can_upload_document_through_upload_center(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"sku,qty,price\nSKU-100,10,RM 99.90\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["upload_type"] == "sales_history"
    assert body["status"] == "draft"
    assert body["review_status"] == "draft"
    assert body["extraction"]["entities_count"] >= 1
    assert "review the extraction" in body["next_step"].lower()

    files_response = client.get(
        "/api/upload-center/files",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert files_response.status_code == 200
    assert any(row["id"] == body["file_id"] for row in files_response.json())


def test_sales_can_submit_review_for_uploaded_document(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    upload = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"sku,qty\nSKU-100,10\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 200
    file_id = upload.json()["file_id"]

    review = client.get(
        f"/api/upload-center/files/{file_id}/review",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "draft"

    submit = client.patch(
        f"/api/upload-center/files/{file_id}/review",
        json={
            "summary": "Sales history file reviewed by sales manager.",
            "detected_type": "Sales History",
            "confidence": 0.82,
            "entities": [
                {"type": "SKUs / Product Codes", "count": 1, "samples": ["SKU-100"]},
                {"type": "Rows", "count": 1, "samples": ["1 transaction row"]},
            ],
            "suggested_rules": ["Use this file for downstream sales history analysis"],
            "review_notes": "Checked before submission.",
            "action": "submit_for_review",
        },
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert submit.status_code == 200
    body = submit.json()
    assert body["status"] == "needs_review"
    assert body["review_status"] == "needs_review"
    assert body["review_notes"] == "Checked before submission."
    assert body["current_extraction"]["summary"] == "Sales history file reviewed by sales manager."


def test_approver_can_activate_reviewed_upload_center_file(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    approver_token = _token(client, "salesdirector@gmail.com", "123456")

    upload = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"sku,qty\nSKU-1,100\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 200
    file_id = upload.json()["file_id"]

    submit = client.patch(
        f"/api/upload-center/files/{file_id}/review",
        json={"action": "submit_for_review"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert submit.status_code == 200

    activate = client.patch(
        f"/api/upload-center/files/{file_id}/review",
        json={"action": "activate"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert activate.status_code == 200
    assert activate.json()["status"] == "active"
    assert activate.json()["review_status"] == "active"


def test_sales_cannot_activate_upload_center_file(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    upload = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"sku,qty\nSKU-1,100\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 200
    file_id = upload.json()["file_id"]

    activate = client.patch(
        f"/api/upload-center/files/{file_id}/review",
        json={"action": "activate"},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert activate.status_code == 403
    assert "cannot perform" in activate.json()["detail"].lower()


def test_upload_center_rejects_legacy_xls_extension(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")

    response = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.xls", b"legacy-xls", "application/vnd.ms-excel")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 400
    assert "accepted" in response.json()["detail"].lower()


def test_approver_cannot_archive_upload_center_file(client: TestClient, seeded_users):
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    approver_token = _token(client, "salesdirector@gmail.com", "123456")

    upload = client.post(
        "/api/upload-center/upload",
        data={"upload_type": "sales_history"},
        files={"file": ("sales_history.csv", b"sku,qty\nSKU-1,100\n", "text/csv")},
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert upload.status_code == 200
    file_id = upload.json()["file_id"]

    archive = client.patch(
        f"/api/upload-center/files/{file_id}/status",
        params={"status": "archived"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert archive.status_code == 403
    assert "cannot set upload status" in archive.json()["detail"].lower()


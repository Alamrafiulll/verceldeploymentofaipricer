from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    Contract,
    ContractLine,
    ContractStatus,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
    RoleEnum,
    UploadedFile,
    UploadStatus,
    UploadType,
)


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_contract_context(
    db_session: Session,
    seeded_users,
    *,
    requested_price: float,
    recommended_price: float,
) -> tuple[Quote, Product, PolicyDocument]:
    admin = seeded_users["admin"]
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]

    product = Product(
        sku=f"SKU-CON-{abs(hash((requested_price, recommended_price))) % 100000}",
        name="Contract Controlled Water Heater",
        category="water_heater",
        list_price=100.0,
        unit_cost=65.0,
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
            requested_price=requested_price,
            recommended_price=recommended_price,
        )
    )

    document = PolicyDocument(
        title="Customer Contract Source",
        doc_type=PolicyDocumentType.price_list,
        source_uri="internal://customer-contract",
        file_hash=f"contract-{product.sku}",
        uploaded_by_user_id=admin.id,
        status=PolicyDocumentStatus.active,
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(quote)
    db_session.refresh(product)
    db_session.refresh(document)
    return quote, product, document


def test_admin_can_upload_contract_and_list_it_with_traceability(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    admin = seeded_users["admin"]
    customer = seeded_users["customer"]
    _, product, document = _seed_contract_context(
        db_session=db_session,
        seeded_users=seeded_users,
        requested_price=96.0,
        recommended_price=96.0,
    )
    uploaded_file = UploadedFile(
        uploaded_by_user_id=admin.id,
        uploaded_by_role=RoleEnum.admin,
        upload_type=UploadType.contract_pricing,
        file_name="customer-contract.pdf",
        file_ext=".pdf",
        mime_type="application/pdf",
        file_hash="customer-contract-upload-hash",
        file_size_bytes=1024,
        source_uri="upload://customer-contract.pdf",
        status=UploadStatus.parsed,
        meta_json={},
        extraction_summary="Customer contract parsed",
        extracted_entities_count=1,
        review_status="parsed",
    )
    db_session.add(uploaded_file)
    db_session.commit()

    admin_token = _token(client, "admin@gmail.com", "123456")
    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.post(
        "/api/contracts/upload",
        json={
            "customer_id": str(customer.id),
            "name": "Strategic Account Contract",
            "source_document_id": str(document.id),
            "source_uploaded_file_id": str(uploaded_file.id),
            "lines": [
                {
                    "product_id": str(product.id),
                    "floor_price": 92.0,
                    "ceiling_price": 108.0,
                    "discount_cap_percent": 8.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["customer_name"] == customer.name
    assert payload["source_document_id"] == str(document.id)
    assert payload["source_uploaded_file_id"] == str(uploaded_file.id)
    assert payload["contract_source_reference"].startswith("CON-")
    assert payload["lines"][0]["discount_cap_percent"] == 8.0

    db_session.refresh(uploaded_file)
    assert str(uploaded_file.linked_contract_id) == payload["id"]

    listing = client.get(
        f"/api/contracts?customer_id={customer.id}",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert listing.status_code == 200
    contracts = listing.json()
    assert len(contracts) == 1
    assert contracts[0]["id"] == payload["id"]
    assert contracts[0]["contract_source_reference"].startswith("CON-")


def test_policy_check_reports_contract_floor_violation_with_source_reference(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote, product, document = _seed_contract_context(
        db_session=db_session,
        seeded_users=seeded_users,
        requested_price=84.0,
        recommended_price=84.0,
    )
    db_session.add(
        Contract(
            customer_id=quote.customer_id,
            name="Strategic Contract",
            status=ContractStatus.active,
            source_document_id=document.id,
        )
    )
    db_session.flush()
    contract = db_session.query(Contract).filter(Contract.customer_id == quote.customer_id).one()
    db_session.add(
        ContractLine(
            contract_id=contract.id,
            product_id=product.id,
            floor_price=95.0,
            ceiling_price=110.0,
            discount_cap_percent=10.0,
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
    assert payload["contract_pricing_summary"]["status"] == "below_contract_floor"
    assert payload["contract_pricing_summary"]["source_references"][0].startswith("CON-")
    assert any(item["code"] == "below_contract_floor" for item in payload["violations"])


def test_quote_detail_and_finance_include_contract_pricing_summary(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    quote, product, document = _seed_contract_context(
        db_session=db_session,
        seeded_users=seeded_users,
        requested_price=98.0,
        recommended_price=98.0,
    )
    contract = Contract(
        customer_id=quote.customer_id,
        name="Standard Contract",
        status=ContractStatus.active,
        source_document_id=document.id,
    )
    db_session.add(contract)
    db_session.flush()
    db_session.add(
        ContractLine(
            contract_id=contract.id,
            product_id=product.id,
            floor_price=95.0,
            ceiling_price=110.0,
            discount_cap_percent=8.0,
        )
    )
    db_session.commit()

    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    detail_response = client.get(
        f"/api/quotes/{quote.id}",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["contract_pricing_summary"]["status"] == "within_contract_bounds"
    assert detail_payload["contract_pricing_summary"]["source_references"][0].startswith("CON-")

    finance_response = client.get(
        f"/api/quotes/{quote.id}/finance",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert finance_response.status_code == 200
    finance_payload = finance_response.json()
    assert finance_payload["contract_pricing_summary"]["status"] == "within_contract_bounds"
    assert finance_payload["leakage_flags_json"]["contract_summary"]["status"] == "within_contract_bounds"


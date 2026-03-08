from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    AIRecommendation,
    Approval,
    ApprovalStatus,
    CompetitorProduct,
    ModelRun,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    PricingRule,
    Product,
    ProductValueProfile,
    Quote,
    QuoteFinanceSnapshot,
    QuoteItem,
    QuoteStatus,
    RoleEnum,
    UploadStatus,
    UploadType,
    UploadedFile,
)


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_market_compare_returns_value_positioning(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    product = Product(
        sku="SKU-MARKET-001",
        name="Alpha Water Heater 35L",
        category="water_heater",
        list_price=1000.0,
        unit_cost=620.0,
    )
    db_session.add(product)
    db_session.flush()

    db_session.add_all(
        [
            CompetitorProduct(
                competitor_name="Brand A",
                product_name="Alpha Water Heater 35L",
                category="water_heater",
                price=950.0,
                features_json={"feature_count": 6, "warranty_months": 24, "brand_tier": "premium"},
                matched_product_id=product.id,
            ),
            CompetitorProduct(
                competitor_name="Brand B",
                product_name="Alpha Water Heater 36L",
                category="water_heater",
                price=980.0,
                features_json={"feature_count": 5, "warranty_months": 18, "brand_tier": "standard"},
                matched_product_id=product.id,
            ),
        ]
    )
    db_session.commit()

    sales_token = _token(client, "salesmanager@gmail.com", "123456")
    response = client.get(
        f"/api/market/compare/{product.id}",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == str(product.id)
    assert payload["competitor_count"] == 2
    assert payload["recommended_strategy"] in {"hold_price", "bundle", "justify_premium", "reduce_price"}
    assert payload["value_positioning_label"] != "insufficient_market_data"
    assert len(payload["matches"]) == 2


def test_approval_context_returns_finance_market_and_similar_cases(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    sales = seeded_users["sales"]
    approver = seeded_users["approver"]
    customer = seeded_users["customer"]

    product = Product(
        sku="SKU-APPROVAL-001",
        name="Approval Heater 50L",
        category="water_heater",
        list_price=1200.0,
        unit_cost=700.0,
    )
    db_session.add(product)
    db_session.flush()
    db_session.add(
        PricingRule(
            channel="direct",
            category="water_heater",
            margin_floor_percent=10.0,
            max_discount_percent=20.0,
            approval_required_below_margin_buffer=2.0,
        )
    )

    quote = Quote(
        created_by_user_id=sales.id,
        customer_id=customer.id,
        channel="direct",
        status=QuoteStatus.approval_pending,
    )
    db_session.add(quote)
    db_session.flush()
    db_session.add(
        QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=8,
            requested_price=1040.0,
            recommended_price=1080.0,
            recommended_band_low=1060.0,
            recommended_band_high=1100.0,
        )
    )
    approval = Approval(
        quote_id=quote.id,
        requested_by_user_id=sales.id,
        requested_price=1020.0,
        requested_discount=15.0,
        request_justification="Strategic account requested a deeper discount.",
        status=ApprovalStatus.pending,
    )
    db_session.add(approval)
    db_session.add(
        AIRecommendation(
            quote_id=quote.id,
            product_id=product.id,
            recommended_price=1080.0,
            recommended_price_low=1060.0,
            recommended_price_high=1100.0,
            confidence=0.81,
            win_probability=0.62,
            model_version="pricing-control-v2",
            model_provider="deterministic_local",
            fallback_used=True,
            explanation_json={"quick_summary": "Recommendation created."},
            source_rule_ids_json=[],
            source_document_ids_json=[],
            competitor_comparison_summary_json={},
            value_positioning_label="market_parity",
            risk_level="medium",
        )
    )
    db_session.commit()

    approver_token = _token(client, "salesdirector@gmail.com", "123456")
    response = client.get(
        f"/api/approvals/{approval.id}/context",
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["approval"]["id"] == str(approval.id)
    assert payload["requested_finance"]["proposed_price"] == 1020.0
    assert payload["current_finance"]["proposed_price"] >= 1020.0
    assert payload["requested_finance"]["leakage_amount"] >= 0
    assert payload["market_comparison_summary"]["value_positioning_label"] == "insufficient_market_data"
    assert len(payload["similar_cases"]) == 1
    assert payload["recommended_action"]


def test_admin_governance_endpoints_return_summary_quality_and_trace_fields(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    admin = seeded_users["admin"]
    product = Product(
        sku="SKU-ADMIN-TRACE-001",
        name="Trace Heater 30L",
        category="water_heater",
        list_price=800.0,
        unit_cost=500.0,
    )
    db_session.add(product)
    db_session.flush()

    upload = UploadedFile(
        uploaded_by_user_id=admin.id,
        uploaded_by_role=RoleEnum.admin,
        upload_type=UploadType.pricing_policy,
        file_name="pricing-policy.pdf",
        file_ext=".pdf",
        mime_type="application/pdf",
        file_hash="hash-admin-upload",
        file_size_bytes=1024,
        status=UploadStatus.needs_review,
        meta_json={},
        validation_issues={"next_step": "Review extracted clauses before activation."},
    )
    db_session.add(upload)
    db_session.flush()

    policy = PolicyDocument(
        title="Draft Policy",
        doc_type=PolicyDocumentType.memo,
        source_uri="internal://draft-policy",
        file_hash="draft-policy-hash",
        uploaded_by_user_id=admin.id,
        status=PolicyDocumentStatus.draft,
    )
    db_session.add(policy)
    db_session.add(
        CompetitorProduct(
            competitor_name="Brand C",
            product_name="Unmatched Heater",
            category="water_heater",
            price=900.0,
            features_json={},
        )
    )
    db_session.add(
        AIRecommendation(
            product_id=product.id,
            recommended_price=500.0,
            recommended_price_low=480.0,
            recommended_price_high=520.0,
            confidence=0.5,
            win_probability=0.4,
            model_version="trace-v2",
            model_provider="deterministic_local",
            fallback_used=True,
            explanation_json={"quick_summary": "Fallback trace."},
            source_rule_ids_json=["rule-1"],
            source_document_ids_json=["doc-1"],
            competitor_comparison_summary_json={"market_comparison_summary": "No uploaded market data."},
            value_positioning_label="insufficient_market_data",
            risk_level="medium",
        )
    )
    db_session.add(
        ModelRun(
            run_type="pricing_recommendation",
            model_name="pricing_control_tower",
            model_version="trace-v2",
            model_provider="deterministic_local",
            status="failed",
            fallback_used=True,
            meta_json={},
        )
    )
    db_session.commit()

    admin_token = _token(client, "admin@gmail.com", "123456")
    summary = client.get("/api/admin/governance-summary", headers={"Authorization": f"Bearer {admin_token}"})
    queue = client.get("/api/admin/document-review-queue", headers={"Authorization": f"Bearer {admin_token}"})
    quality = client.get("/api/admin/data-quality", headers={"Authorization": f"Bearer {admin_token}"})
    traces = client.get("/api/admin/ai-recommendations", headers={"Authorization": f"Bearer {admin_token}"})
    runs = client.get("/api/admin/model-runs", headers={"Authorization": f"Bearer {admin_token}"})

    assert summary.status_code == 200
    assert summary.json()["pending_upload_reviews"] == 1
    assert summary.json()["pending_policy_reviews"] == 1
    assert summary.json()["model_run_failures"] == 1
    assert summary.json()["unmatched_competitor_records"] == 1

    assert queue.status_code == 200
    assert any(item["item_type"] == "uploaded_file" for item in queue.json())
    assert any(item["item_type"] == "policy_document" for item in queue.json())

    assert quality.status_code == 200
    assert quality.json()["uploads_needing_review"] == 1
    assert quality.json()["recommendations_with_fallback"] == 1

    assert traces.status_code == 200
    assert traces.json()[0]["recommended_price_low"] == 480.0
    assert traces.json()[0]["fallback_used"] is True
    assert traces.json()[0]["model_provider"] == "deterministic_local"

    assert runs.status_code == 200
    assert runs.json()[0]["fallback_used"] is True
    assert runs.json()[0]["model_provider"] == "deterministic_local"


def test_analytics_extended_endpoints_return_business_series(
    client: TestClient,
    db_session: Session,
    seeded_users,
):
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]

    product = Product(
        sku="SKU-ANALYTICS-001",
        name="Analytics Heater 35L",
        category="water_heater",
        list_price=1000.0,
        unit_cost=600.0,
    )
    db_session.add(product)
    db_session.flush()

    quote = Quote(
        created_by_user_id=sales.id,
        customer_id=customer.id,
        channel="direct",
        status=QuoteStatus.finalized,
    )
    db_session.add(quote)
    db_session.flush()
    db_session.add(
        QuoteItem(
            quote_id=quote.id,
            product_id=product.id,
            quantity=5,
            recommended_price=950.0,
            final_price=950.0,
            final_discount=5.0,
            margin_percent=18.0,
        )
    )
    db_session.add(
        QuoteFinanceSnapshot(
            quote_id=quote.id,
            proposed_price=950.0,
            list_revenue_total=5000.0,
            revenue_total=4750.0,
            cogs_total=3000.0,
            rebate_amount=50.0,
            gift_cost_amount=10.0,
            bundle_cost_amount=0.0,
            promotion_allocation_amount=0.0,
            campaign_cost_amount=10.0,
            freight_amount=20.0,
            fees_amount=5.0,
            mdf_amount=15.0,
            contract_effect_amount=0.0,
            list_margin_amount=2000.0,
            price_discount_amount=250.0,
            gross_margin_amount=1750.0,
            net_margin_amount=1650.0,
            net_margin_percent=34.74,
            leakage_amount=350.0,
            leakage_reasons_json=[{"label": "rebate_cost", "amount": 50.0}],
            leakage_flags_json={"flags": [{"code": "rebate_cost", "severity": "medium", "message": "Rebate applied"}]},
        )
    )
    db_session.add(
        ProductValueProfile(
            product_id=product.id,
            value_score=61.0,
            positioning_label="premium_value",
            price_band="RM 900 - RM 980",
            competitor_count=2,
            avg_competitor_price=940.0,
            price_gap_percent=1.1,
            recommended_strategy="hold_price",
            analysis_json={"market_comparison_summary": "Price is near market parity."},
        )
    )
    db_session.commit()

    executive_token = _token(client, "executiveviewer@gmail.com", "123456")
    leakage = client.get("/api/analytics/leakage-sources", headers={"Authorization": f"Bearer {executive_token}"})
    positioning = client.get("/api/analytics/competitor-positioning", headers={"Authorization": f"Bearer {executive_token}"})
    profitability = client.get("/api/analytics/category-profitability", headers={"Authorization": f"Bearer {executive_token}"})
    turnaround = client.get("/api/analytics/approval-turnaround", headers={"Authorization": f"Bearer {executive_token}"})
    acceptance = client.get("/api/analytics/recommendation-acceptance", headers={"Authorization": f"Bearer {executive_token}"})

    assert leakage.status_code == 200
    assert leakage.json()[0]["label"] == "rebate_cost"

    assert positioning.status_code == 200
    assert any(item["label"] == "premium_value" for item in positioning.json())

    assert profitability.status_code == 200
    assert profitability.json()[0]["label"] == "water_heater"

    assert turnaround.status_code == 200
    assert turnaround.json()[0]["label"] == "direct"

    assert acceptance.status_code == 200
    assert any(item["label"] == "accepted" and item["value"] >= 1 for item in acceptance.json())


from datetime import datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import (
    Campaign,
    CampaignRule,
    CampaignRuleType,
    CampaignStatus,
    Contract,
    ContractLine,
    ContractStatus,
    Customer,
    CustomerTier,
    FreightAndFeesPolicy,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
    RebateProgram,
    RoleEnum,
    User,
    UserAccountStatus,
    UserApprovalStatus,
)
from app.services.finance_engine import compute_true_margin


def _seed_quote_finance_context(db_session: Session) -> str:
    admin = User(
        name="Admin",
        email="admin.finance@test.local",
        password_hash="x",
        role=RoleEnum.admin,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    sales = User(
        name="Sales",
        email="sales.finance@test.local",
        password_hash="x",
        role=RoleEnum.sales,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    customer = Customer(name="Finance Cust", tier=CustomerTier.core, region="North")
    product = Product(
        sku="SKU-FIN-001",
        name="Finance Product",
        category="water_heater",
        list_price=100.0,
        unit_cost=60.0,
    )
    db_session.add_all([admin, sales, customer, product])
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
            quantity=10,
            requested_price=100.0,
            recommended_price=100.0,
        )
    )

    db_session.add(FreightAndFeesPolicy(channel="direct", freight_percent=2.0, fees_percent=1.0))
    db_session.add(
        RebateProgram(
            name="Core Rebate",
            channel="direct",
            tier_rates_json={"core": 10},
            mdf_percent=5,
            effective_start=datetime.now(timezone.utc) - timedelta(days=1),
            effective_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
    db_session.commit()
    return str(quote.id)


def test_finance_engine_margin_math_and_rebate_application(db_session: Session):
    quote_id = _seed_quote_finance_context(db_session)

    snapshot = compute_true_margin(
        db=db_session,
        quote_id=quote_id,
        proposed_price=100.0,
        actor_user_id=None,
    )

    assert float(snapshot.revenue_total) == 1000.0
    assert float(snapshot.cogs_total) == 600.0
    assert float(snapshot.gross_margin_amount) == 400.0
    assert float(snapshot.rebate_amount) == 100.0
    assert float(snapshot.mdf_amount) == 50.0
    assert float(snapshot.freight_amount) == 20.0
    assert float(snapshot.fees_amount) == 10.0
    assert float(snapshot.list_revenue_total) == 1000.0
    assert float(snapshot.list_margin_amount) == 400.0
    assert float(snapshot.price_discount_amount) == 0.0
    assert float(snapshot.leakage_amount) == 180.0
    assert float(snapshot.net_margin_amount) == 220.0
    assert float(snapshot.net_margin_percent) == 22.0
    reason_codes = {reason["code"] for reason in snapshot.leakage_reasons_json}
    assert {"rebate_cost", "mdf_allocation_cost", "freight_cost", "fees_cost"} <= reason_codes


def test_finance_engine_applies_campaign_cost_to_true_margin(db_session: Session):
    quote_id = _seed_quote_finance_context(db_session)
    quote = db_session.get(Quote, uuid.UUID(quote_id))
    admin_user = db_session.query(User).filter(User.email == "admin.finance@test.local").one()

    document = PolicyDocument(
        title="Campaign Source",
        doc_type=PolicyDocumentType.memo,
        source_uri="internal://campaign",
        file_hash="campaign-hash",
        uploaded_by_user_id=admin_user.id,
        status=PolicyDocumentStatus.active,
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(document)
    db_session.flush()

    campaign = Campaign(
        name="Water Heater Growth Push",
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
            eligibility_json={"product_category": "water_heater"},
            exclusion_json={},
            entitlement_json={"gift_skus": ["RPG-BAG-NB"], "quantity_per_quote": 1, "gift_cost_amount": 10.0},
        )
    )
    db_session.add(
        CampaignRule(
            campaign_id=campaign.id,
            rule_type=CampaignRuleType.bundle,
            eligibility_json={"product_category": "water_heater"},
            exclusion_json={},
            entitlement_json={"bundle_skus": ["BUNDLE-VALVE-01"], "bundle_cost_amount": 7.0},
        )
    )
    db_session.commit()

    snapshot = compute_true_margin(
        db=db_session,
        quote_id=quote_id,
        proposed_price=100.0,
        actor_user_id=None,
    )

    assert float(snapshot.campaign_cost_amount) == 17.0
    assert float(snapshot.gift_cost_amount) == 10.0
    assert float(snapshot.bundle_cost_amount) == 7.0
    assert float(snapshot.promotion_allocation_amount) == 0.0
    assert float(snapshot.leakage_amount) == 197.0
    assert float(snapshot.net_margin_amount) == 203.0
    assert snapshot.leakage_flags_json["campaign_summary"]["eligible_campaign_count"] == 2


def test_finance_engine_applies_display_and_retroactive_rebate_costs(db_session: Session):
    quote_id = _seed_quote_finance_context(db_session)
    quote = db_session.get(Quote, uuid.UUID(quote_id))
    admin_user = db_session.query(User).filter(User.email == "admin.finance@test.local").one()

    document = PolicyDocument(
        title="Trading Terms Source",
        doc_type=PolicyDocumentType.trading_terms,
        source_uri="internal://trading-terms",
        file_hash="trading-terms-hash",
        uploaded_by_user_id=admin_user.id,
        status=PolicyDocumentStatus.active,
        effective_start=datetime.now(timezone.utc) - timedelta(days=1),
        effective_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(document)
    db_session.flush()

    db_session.add(
        RebateProgram(
            name="Direct Trading Terms",
            channel="direct",
            tier_rates_json={"core": 10.0},
            mdf_percent=1.0,
            display_incentive_percent=2.0,
            manager_discretion_warning="Manager discretion requires finance approval.",
            retroactive_incentive=True,
            program_meta_json={"retroactive_rate_percent": 1.0, "manager_discretion_percent": 0.5},
            effective_start=datetime.now(timezone.utc) - timedelta(days=1),
            effective_end=datetime.now(timezone.utc) + timedelta(days=30),
            source_document_id=document.id,
        )
    )
    db_session.commit()

    snapshot = compute_true_margin(
        db=db_session,
        quote_id=quote_id,
        proposed_price=100.0,
        actor_user_id=None,
    )

    assert float(snapshot.rebate_amount) == 115.0
    assert float(snapshot.mdf_amount) == 30.0
    assert float(snapshot.leakage_amount) == 175.0
    assert float(snapshot.net_margin_amount) == 225.0
    rebate_summary = snapshot.leakage_flags_json["rebate_summary"]
    assert rebate_summary["standard_rebate_amount"] == 100.0
    assert rebate_summary["standard_mdf_amount"] == 10.0
    assert rebate_summary["display_incentive_amount"] == 20.0
    assert rebate_summary["retroactive_rebate_amount"] == 10.0
    assert rebate_summary["manager_discretion_amount"] == 5.0
    codes = {flag["code"] for flag in snapshot.leakage_flags_json["flags"]}
    assert "manager_discretion_rebate_warning" in codes
    assert "retroactive_incentive_applied" in codes


def test_finance_engine_flags_contract_floor_violation(db_session: Session):
    quote_id = _seed_quote_finance_context(db_session)

    quote = db_session.get(Quote, uuid.UUID(quote_id))
    customer_id = quote.customer_id
    product_id = quote.items[0].product_id
    admin_user = db_session.query(User).filter(User.email == "admin.finance@test.local").one()

    document = PolicyDocument(
        title="Contract Source",
        doc_type=PolicyDocumentType.trading_terms,
        source_uri="internal://contract",
        file_hash="contract-hash",
        uploaded_by_user_id=admin_user.id,
        status=PolicyDocumentStatus.active,
    )
    db_session.add(document)
    db_session.flush()

    contract = Contract(
        customer_id=customer_id,
        name="Strict Contract",
        status=ContractStatus.active,
        source_document_id=document.id,
    )
    db_session.add(contract)
    db_session.flush()
    db_session.add(
        ContractLine(
            contract_id=contract.id,
            product_id=product_id,
            floor_price=95.0,
            ceiling_price=120.0,
            discount_cap_percent=10,
        )
    )
    db_session.commit()

    snapshot = compute_true_margin(
        db=db_session,
        quote_id=quote_id,
        proposed_price=80.0,
        actor_user_id=None,
    )

    flags = snapshot.leakage_flags_json.get("flags", [])
    codes = {flag["code"] for flag in flags}
    assert "violates_contract_floor" in codes


def test_finance_simulation_endpoint_returns_snapshot(client: TestClient, db_session: Session, seeded_users):
    sales = seeded_users["sales"]
    customer = seeded_users["customer"]
    product = Product(
        sku="SKU-FIN-API-001",
        name="Finance API Product",
        category="water_heater",
        list_price=200.0,
        unit_cost=120.0,
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
            quantity=3,
            requested_price=190.0,
            recommended_price=190.0,
        )
    )
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "salesmanager@gmail.com", "password": "123456"})
    token = login.json()["access_token"]
    simulate = client.post(
        f"/api/quotes/{quote.id}/simulate-finance",
        json={"proposed_price": 180.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert simulate.status_code == 200
    payload = simulate.json()
    assert payload["quote_id"] == str(quote.id)
    assert payload["proposed_price"] == 180.0
    assert payload["list_revenue_total"] == 600.0
    assert payload["discounted_revenue_total"] == 540.0
    assert payload["price_discount_amount"] == 60.0
    assert payload["leakage_amount"] == 60.0
    assert "campaign_cost_amount" in payload
    assert "rebate_summary" in payload
    assert "contract_pricing_summary" in payload
    assert "leakage_reasons_json" in payload
    assert payload["contract_pricing_summary"]["status"] == "no_contract"


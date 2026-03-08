import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.security import get_password_hash
from app.db.models import (
    Approval,
    ApprovalStatus,
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
    Inventory,
    PolicyClause,
    PolicyClauseType,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyDocumentType,
    PricingRule,
    Product,
    Quote,
    QuoteItem,
    QuoteStatus,
    PriceBook,
    PriceBookChannel,
    PriceBookItem,
    QuoteFinanceSnapshot,
    RebateProgram,
    Recommendation,
    RoleEnum,
    RiskLevel,
    StrategyMode,
    User,
    UserAccountStatus,
    UserApprovalStatus,
)
from app.db.session import SessionLocal


def seed() -> None:
    db = SessionLocal()
    try:
        db.execute(delete(QuoteFinanceSnapshot))
        db.execute(delete(ContractLine))
        db.execute(delete(Contract))
        db.execute(delete(RebateProgram))
        db.execute(delete(FreightAndFeesPolicy))
        db.execute(delete(CampaignRule))
        db.execute(delete(Campaign))
        db.execute(delete(PriceBookItem))
        db.execute(delete(PriceBook))
        db.execute(delete(PolicyClause))
        db.execute(delete(PolicyDocument))
        db.execute(delete(Approval))
        db.execute(delete(Recommendation))
        db.execute(delete(QuoteItem))
        db.execute(delete(Quote))
        db.execute(delete(Inventory))
        db.execute(delete(PricingRule))
        db.execute(delete(Product))
        db.execute(delete(Customer))
        db.execute(delete(User))
        db.commit()

        users = [
            User(
                name="Sales Manager",
                email="salesmanager@gmail.com",
                password_hash=get_password_hash("123456"),
                role=RoleEnum.sales,
                approval_status=UserApprovalStatus.approved,
                account_status=UserAccountStatus.active,
            ),
            User(
                name="Sales Director",
                email="salesdirector@gmail.com",
                password_hash=get_password_hash("123456"),
                role=RoleEnum.approver,
                approval_status=UserApprovalStatus.approved,
                account_status=UserAccountStatus.active,
            ),
            User(
                name="Executive Viewer",
                email="executiveviewer@gmail.com",
                password_hash=get_password_hash("123456"),
                role=RoleEnum.executive,
                approval_status=UserApprovalStatus.approved,
                account_status=UserAccountStatus.active,
            ),
            User(
                name="Admin User",
                email="admin@gmail.com",
                password_hash=get_password_hash("123456"),
                role=RoleEnum.admin,
                approval_status=UserApprovalStatus.approved,
                account_status=UserAccountStatus.active,
            ),
        ]
        db.add_all(users)
        db.flush()

        regions = ["North", "South", "East", "West"]
        tiers = [CustomerTier.strategic, CustomerTier.core, CustomerTier.growth]
        customers = [
            Customer(name=f"Customer {i+1}", tier=tiers[i % len(tiers)], region=regions[i % len(regions)])
            for i in range(10)
        ]
        db.add_all(customers)
        db.flush()

        categories = ["cement", "steel", "roofing", "finishes"]
        products = []
        for i in range(20):
            category = categories[i % len(categories)]
            list_price = round(random.uniform(100, 800), 2)
            unit_cost = round(list_price * random.uniform(0.55, 0.78), 2)
            products.append(
                Product(
                    sku=f"SKU-{1000 + i}",
                    name=f"Product {i+1}",
                    category=category,
                    list_price=list_price,
                    unit_cost=unit_cost,
                )
            )

        products.extend(
            [
                Product(
                    sku="PLATZ-DC-35",
                    name="PLATZ DC Pump Water Heater 35L",
                    category="water_heater",
                    list_price=1299.00,
                    unit_cost=820.00,
                ),
                Product(
                    sku="QUATEK-50",
                    name="QUATEK Water Heater 50L",
                    category="water_heater",
                    list_price=1399.00,
                    unit_cost=890.00,
                ),
                Product(
                    sku="STARKER-80",
                    name="STARKER Water Heater 80L",
                    category="water_heater",
                    list_price=1699.00,
                    unit_cost=1100.00,
                ),
                Product(
                    sku="EDGE-60",
                    name="EDGE Water Heater 60L",
                    category="water_heater",
                    list_price=1499.00,
                    unit_cost=960.00,
                ),
                Product(
                    sku="STIQ-45",
                    name="STIQ Water Heater 45L",
                    category="water_heater",
                    list_price=1199.00,
                    unit_cost=760.00,
                ),
                Product(
                    sku="ZETA-HB-01",
                    name="ZETA Hand Bidet 01",
                    category="hand_bidet",
                    list_price=299.00,
                    unit_cost=160.00,
                ),
            ]
        )
        db.add_all(products)
        db.flush()

        inventory_rows = []
        for product in products:
            inventory_rows.append(
                Inventory(
                    product_id=product.id,
                    on_hand=random.randint(30, 350),
                    stock_age_days_avg=random.randint(15, 220),
                )
            )
        db.add_all(inventory_rows)

        channels = ["direct", "distributor", "project"]
        rules = []
        for channel in channels:
            for category in categories:
                rules.append(
                    PricingRule(
                        channel=channel,
                        category=category,
                        margin_floor_percent=random.choice([10, 12, 14, 16]),
                        max_discount_percent=random.choice([8, 10, 12, 15]),
                        approval_required_below_margin_buffer=2,
                    )
                )
        db.add_all(rules)
        db.flush()

        db.add_all(
            [
                FreightAndFeesPolicy(channel="direct", freight_percent=1.2, fees_percent=0.5),
                FreightAndFeesPolicy(channel="distributor", freight_percent=1.0, fees_percent=0.4),
                FreightAndFeesPolicy(channel="project", freight_percent=1.5, fees_percent=0.7),
            ]
        )

        db.add(
            RebateProgram(
                name="Dealer Tier Rebate FY2025",
                channel="direct",
                tier_rates_json={"strategic": 3.5, "core": 2.5, "growth": 1.5},
                mdf_percent=0.8,
                effective_start=datetime.now(timezone.utc) - timedelta(days=30),
                effective_end=datetime.now(timezone.utc) + timedelta(days=365),
            )
        )

        sales_user = next(u for u in users if u.role == RoleEnum.sales)
        approver_user = next(u for u in users if u.role == RoleEnum.approver)
        admin_user = next(u for u in users if u.role == RoleEnum.admin)

        policy_document = PolicyDocument(
            title="FY2025 Water Heater Master Price List",
            doc_type=PolicyDocumentType.price_list,
            source_uri="internal://fy2025-water-heater-price-list.xlsx",
            file_hash="seed-fy2025-pricebook",
            uploaded_by_user_id=admin_user.id,
            effective_start=datetime.now(timezone.utc) - timedelta(days=5),
            effective_end=datetime.now(timezone.utc) + timedelta(days=180),
            status=PolicyDocumentStatus.active,
        )
        db.add(policy_document)
        db.flush()

        db.add(
            PolicyClause(
                policy_document_id=policy_document.id,
                clause_type=PolicyClauseType.pricing,
                structured_json={
                    "channels": ["lsp", "wm", "em"],
                    "note": "Seed clause for channel pricebook enforcement",
                },
                raw_text="Price list must follow LSP, WM, and EM channel books during effective period.",
                confidence=1.0,
            )
        )

        campaign = Campaign(
            name="FY2025 Toiletries Bag Free Gift Campaign",
            effective_start=datetime.now(timezone.utc) - timedelta(days=2),
            effective_end=datetime.now(timezone.utc) + timedelta(days=90),
            status=CampaignStatus.active,
            source_document_id=policy_document.id,
        )
        db.add(campaign)
        db.flush()
        db.add(
            CampaignRule(
                campaign_id=campaign.id,
                rule_type=CampaignRuleType.free_gift,
                eligibility_json={"product_category": "water_heater", "model_type": "dc_pump"},
                exclusion_json={
                    "series_excluded": ["FLUSSO"],
                    "not_applicable_for": [
                        "corporate_account",
                        "project_sales",
                        "special_price_purchase",
                    ],
                },
                entitlement_json={"gift_skus": ["RPG-BAG-NB", "RPG-BAG-GR"], "quantity_per_quote": 1},
            )
        )

        channel_multipliers = {
            PriceBookChannel.lsp: 1.0,
            PriceBookChannel.wm: 0.95,
            PriceBookChannel.em: 0.92,
        }
        showcase_skus = ["PLATZ-DC-35", "QUATEK-50", "STARKER-80", "EDGE-60", "STIQ-45", "ZETA-HB-01"]
        sku_to_product = {product.sku: product for product in products}

        for channel, multiplier in channel_multipliers.items():
            book = PriceBook(
                name=f"FY2025 {channel.value.upper()} Price Book",
                channel=channel,
                currency="RM",
                effective_start=datetime.now(timezone.utc) - timedelta(days=5),
                effective_end=datetime.now(timezone.utc) + timedelta(days=180),
                source_document_id=policy_document.id,
                uploaded_by_user_id=sales_user.id,
            )
            db.add(book)
            db.flush()

            for sku in showcase_skus:
                product = sku_to_product[sku]
                db.add(
                    PriceBookItem(
                        price_book_id=book.id,
                        product_id=product.id,
                        list_price=round(float(product.list_price) * multiplier, 2),
                        notes="Seeded from FY2025 series showcase",
                    )
                )

        contract_customer = customers[0]
        contract_product = products[0]
        contract = Contract(
            customer_id=contract_customer.id,
            name="FY2025 Strategic Contract",
            effective_start=datetime.now(timezone.utc) - timedelta(days=10),
            effective_end=datetime.now(timezone.utc) + timedelta(days=180),
            status=ContractStatus.active,
            source_document_id=policy_document.id,
        )
        db.add(contract)
        db.flush()
        db.add(
            ContractLine(
                contract_id=contract.id,
                product_id=contract_product.id,
                floor_price=round(float(contract_product.list_price) * 0.85, 2),
                ceiling_price=round(float(contract_product.list_price) * 1.05, 2),
                discount_cap_percent=15,
            )
        )

        for i in range(8):
            customer = random.choice(customers)
            product = random.choice(products)
            qty = random.randint(5, 40)
            strategy = random.choice(list(StrategyMode))
            status = random.choice([QuoteStatus.finalized, QuoteStatus.recommended, QuoteStatus.approved])
            quote = Quote(
                created_by_user_id=sales_user.id,
                customer_id=customer.id,
                channel=random.choice(channels),
                strategy_mode=strategy,
                status=status,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5)),
            )
            db.add(quote)
            db.flush()

            discount = random.uniform(3, 12)
            rec_price = float(product.list_price) * (1 - discount / 100)
            final_price = rec_price * random.uniform(0.98, 1.03)
            margin = ((final_price - float(product.unit_cost)) / final_price) * 100
            expected_profit = (final_price - float(product.unit_cost)) * qty * random.uniform(0.35, 0.75)
            item = QuoteItem(
                quote_id=quote.id,
                product_id=product.id,
                quantity=qty,
                requested_discount=discount,
                recommended_price=rec_price,
                recommended_band_low=rec_price * 0.98,
                recommended_band_high=rec_price * 1.02,
                recommended_discount_low=discount - 1,
                recommended_discount_high=discount + 1,
                final_price=final_price,
                final_discount=((float(product.list_price) - final_price) / float(product.list_price)) * 100,
                win_probability=random.uniform(0.35, 0.8),
                confidence=random.uniform(0.55, 0.9),
                margin_percent=margin,
                expected_profit=expected_profit,
                risk_level=random.choice([RiskLevel.low, RiskLevel.medium]),
            )
            db.add(item)

            rec = Recommendation(
                quote_id=quote.id,
                model_version="foundry-v1",
                feature_schema_version="schema-v1",
                foundry_outputs_json={"seed": True},
                optimizer_outputs_json={"seed": True},
                gpt_outputs_json={
                    "short_reason": "Seed recommendation for analytics demo.",
                    "top_drivers": ["margin", "stock age", "customer tier"],
                    "negotiation_tips": ["Anchor high", "Use volume", "Protect margin"],
                },
            )
            db.add(rec)

            if quote.status == QuoteStatus.approved:
                db.add(
                    Approval(
                        quote_id=quote.id,
                        requested_by_user_id=sales_user.id,
                        approver_user_id=approver_user.id,
                        requested_price=final_price,
                        requested_discount=((float(product.list_price) - final_price) / float(product.list_price)) * 100,
                        status=ApprovalStatus.approved,
                        request_justification="Strategic account retention",
                        decision_reason="Approved for account retention with acceptable risk",
                    )
                )

        db.commit()
        print("Seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

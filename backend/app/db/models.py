import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    JSON,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class RoleEnum(str, Enum):
    sales = "sales"
    approver = "approver"
    executive = "executive"
    admin = "admin"


class CustomerTier(str, Enum):
    strategic = "strategic"
    core = "core"
    growth = "growth"


class QuoteStatus(str, Enum):
    draft = "draft"
    recommended = "recommended"
    approval_pending = "approval_pending"
    approved = "approved"
    rejected = "rejected"
    finalized = "finalized"


class StrategyMode(str, Enum):
    maximize_profit = "maximize_profit"
    clear_inventory = "clear_inventory"
    market_expansion = "market_expansion"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UserApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UserAccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class PriceBookChannel(str, Enum):
    lsp = "lsp"
    wm = "wm"
    em = "em"


class PolicyDocumentType(str, Enum):
    memo = "memo"
    price_list = "price_list"
    trading_terms = "trading_terms"
    finance = "finance"


class UploadType(str, Enum):
    sales_history = "sales_history"
    product_catalog = "product_catalog"
    current_price_list = "current_price_list"
    competitor_price_data = "competitor_price_data"
    promotion_calendar = "promotion_calendar"
    pricing_approval_sheet = "pricing_approval_sheet"
    strategic_pricing_guideline = "strategic_pricing_guideline"
    quarterly_pricing_plan = "quarterly_pricing_plan"
    strategic_targets = "strategic_targets"
    market_reports = "market_reports"
    user_role_config = "user_role_config"
    pricing_policy = "pricing_policy"
    audit_log_archive = "audit_log_archive"
    model_configuration = "model_configuration"
    rule_mapping_template = "rule_mapping_template"
    campaign_memo = "campaign_memo"
    trading_terms = "trading_terms"
    rebate_agreement = "rebate_agreement"
    contract_pricing = "contract_pricing"
    margin_target_sheet = "margin_target_sheet"


class UploadStatus(str, Enum):
    draft = "draft"
    parsed = "parsed"
    needs_review = "needs_review"
    active = "active"
    rejected = "rejected"
    archived = "archived"


class PolicyDocumentStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class PolicyClauseType(str, Enum):
    eligibility = "eligibility"
    exclusion = "exclusion"
    entitlement = "entitlement"
    pricing = "pricing"
    rebate = "rebate"
    incentive = "incentive"
    payment_terms = "payment_terms"
    returns = "returns"
    exchange = "exchange"
    other = "other"


class CampaignStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class CampaignRuleType(str, Enum):
    free_gift = "free_gift"
    discount = "discount"
    bundle = "bundle"


class ContractStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class PasswordChangeRequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), nullable=False)
    approval_status: Mapped[UserApprovalStatus] = mapped_column(
        SAEnum(UserApprovalStatus), nullable=False, default=UserApprovalStatus.approved
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_status: Mapped[UserAccountStatus] = mapped_column(
        SAEnum(UserAccountStatus), nullable=False, default=UserAccountStatus.active
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    quotes: Mapped[list["Quote"]] = relationship(back_populates="created_by")
    uploaded_policy_documents: Mapped[list["PolicyDocument"]] = relationship(
        back_populates="uploaded_by",
        foreign_keys="PolicyDocument.uploaded_by_user_id",
    )
    uploaded_price_books: Mapped[list["PriceBook"]] = relationship(
        back_populates="uploaded_by",
        foreign_keys="PriceBook.uploaded_by_user_id",
    )
    password_change_requests: Mapped[list["PasswordChangeRequest"]] = relationship(
        foreign_keys="PasswordChangeRequest.requested_by_user_id",
        back_populates="requested_by",
        cascade="all, delete-orphan",
    )
    password_change_decisions: Mapped[list["PasswordChangeRequest"]] = relationship(
        foreign_keys="PasswordChangeRequest.decided_by_user_id",
        back_populates="decided_by",
    )
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(back_populates="uploaded_by")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[PolicyDocumentType] = mapped_column(SAEnum(PolicyDocumentType), nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    source_uploaded_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_create_campaign: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PolicyDocumentStatus] = mapped_column(
        SAEnum(PolicyDocumentStatus), nullable=False, default=PolicyDocumentStatus.draft
    )

    uploaded_by: Mapped["User"] = relationship(
        back_populates="uploaded_policy_documents",
        foreign_keys=[uploaded_by_user_id],
    )
    clauses: Mapped[list["PolicyClause"]] = relationship(
        back_populates="policy_document", cascade="all, delete-orphan"
    )
    price_books: Mapped[list["PriceBook"]] = relationship(back_populates="source_document")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="source_document")
    rebate_programs: Mapped[list["RebateProgram"]] = relationship(back_populates="source_document")

    @property
    def clause_count(self) -> int:
        return len(self.clauses or [])

    @property
    def average_clause_confidence(self) -> float:
        clauses = self.clauses or []
        if not clauses:
            return 0.0
        return round(sum(float(clause.confidence) for clause in clauses) / len(clauses), 4)

    @property
    def review_status(self) -> str:
        if self.status == PolicyDocumentStatus.active:
            return "active"
        if self.status == PolicyDocumentStatus.archived:
            return "archived"
        if self.clause_count > 0:
            return "needs_review"
        return "draft"

    @property
    def policy_source_reference(self) -> str:
        return f"POL-{str(self.id).split('-')[0].upper()}"

    @property
    def next_step(self) -> str:
        if self.status == PolicyDocumentStatus.active:
            return "This policy is active and can be used for pricing governance."
        if self.status == PolicyDocumentStatus.archived:
            return "This policy is archived. Reactivate only after review of the source document."
        return "Review the extracted clauses, correct them if needed, then activate the policy."


class PolicyClause(Base):
    __tablename__ = "policy_clauses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    policy_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="CASCADE"), nullable=False
    )
    clause_type: Mapped[PolicyClauseType] = mapped_column(SAEnum(PolicyClauseType), nullable=False)
    structured_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)

    policy_document: Mapped["PolicyDocument"] = relationship(back_populates="clauses")

    @property
    def policy_source_reference(self) -> str:
        return (
            f"POL-{str(self.policy_document_id).split('-')[0].upper()}-"
            f"CLA-{str(self.id).split('-')[0].upper()}"
        )


class PriceBook(Base):
    __tablename__ = "price_books"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[PriceBookChannel] = mapped_column(SAEnum(PriceBookChannel), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="RM")
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    source_document: Mapped["PolicyDocument | None"] = relationship(back_populates="price_books")
    uploaded_by: Mapped["User | None"] = relationship(
        back_populates="uploaded_price_books",
        foreign_keys=[uploaded_by_user_id],
    )
    items: Mapped[list["PriceBookItem"]] = relationship(
        back_populates="price_book", cascade="all, delete-orphan"
    )

    @property
    def uploaded_by_email(self) -> str | None:
        return self.uploaded_by.email if self.uploaded_by else None

    @property
    def uploaded_by_name(self) -> str | None:
        return self.uploaded_by.name if self.uploaded_by else None


class PriceBookItem(Base):
    __tablename__ = "price_book_items"
    __table_args__ = (
        UniqueConstraint("price_book_id", "product_id", name="uq_price_book_items_book_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    price_book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("price_books.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    list_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    price_book: Mapped["PriceBook"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), nullable=False, default=CampaignStatus.active
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="RESTRICT"), nullable=False
    )

    source_document: Mapped["PolicyDocument"] = relationship(back_populates="campaigns")
    rules: Mapped[list["CampaignRule"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignRule(Base):
    __tablename__ = "campaign_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    rule_type: Mapped[CampaignRuleType] = mapped_column(SAEnum(CampaignRuleType), nullable=False)
    eligibility_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    exclusion_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    entitlement_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    campaign: Mapped["Campaign"] = relationship(back_populates="rules")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ContractStatus] = mapped_column(
        SAEnum(ContractStatus), nullable=False, default=ContractStatus.active
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    source_uploaded_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    customer: Mapped["Customer"] = relationship()
    lines: Mapped[list["ContractLine"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )

    @property
    def contract_source_reference(self) -> str:
        return f"CON-{str(self.id).split('-')[0].upper()}"

    @property
    def customer_name(self) -> str | None:
        return self.customer.name if self.customer else None


class ContractLine(Base):
    __tablename__ = "contract_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    floor_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    ceiling_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_cap_percent: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="lines")
    product: Mapped["Product"] = relationship()


class RebateProgram(Base):
    __tablename__ = "rebate_programs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tier_rates_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    mdf_percent: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    display_incentive_percent: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    manager_discretion_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    retroactive_incentive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    program_meta_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    source_document: Mapped["PolicyDocument | None"] = relationship(back_populates="rebate_programs")


class FreightAndFeesPolicy(Base):
    __tablename__ = "freight_fees_policies"
    __table_args__ = (
        UniqueConstraint("channel", name="uq_freight_fees_policies_channel"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    freight_percent: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    fees_percent: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    effective_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class QuoteFinanceSnapshot(Base):
    __tablename__ = "quote_finance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    proposed_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    list_revenue_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    revenue_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    cogs_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    rebate_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    gift_cost_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    bundle_cost_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    promotion_allocation_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    campaign_cost_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    freight_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    fees_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    mdf_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    contract_effect_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    list_margin_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    price_discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    gross_margin_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    net_margin_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    net_margin_percent: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    leakage_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    leakage_reasons_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    leakage_flags_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    quote: Mapped["Quote"] = relationship()


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[CustomerTier] = mapped_column(SAEnum(CustomerTier), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    list_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_age_days_avg: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    product: Mapped["Product"] = relationship()


class PricingRule(Base):
    __tablename__ = "pricing_rules"
    __table_args__ = (
        UniqueConstraint("channel", "category", name="uq_pricing_rules_channel_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    margin_floor_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    approval_required_below_margin_buffer: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=2
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy_mode: Mapped[StrategyMode] = mapped_column(
        SAEnum(StrategyMode), nullable=False, default=StrategyMode.maximize_profit
    )
    status: Mapped[QuoteStatus] = mapped_column(
        SAEnum(QuoteStatus), nullable=False, default=QuoteStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    created_by: Mapped["User"] = relationship(back_populates="quotes")
    customer: Mapped["Customer"] = relationship()
    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan"
    )
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan"
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    requested_discount: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    recommended_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    recommended_band_low: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    recommended_band_high: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    recommended_discount_low: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    recommended_discount_high: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    final_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    final_discount: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    win_probability: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    margin_percent: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    expected_profit: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    risk_level: Mapped[RiskLevel | None] = mapped_column(SAEnum(RiskLevel), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    quote: Mapped["Quote"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    foundry_outputs_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    optimizer_outputs_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    gpt_outputs_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    quote: Mapped["Quote"] = relationship(back_populates="recommendations")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    recommended_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    recommended_price_low: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    recommended_price_high: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    confidence: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    win_probability: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    explanation_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_rule_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_document_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    finance_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quote_finance_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    competitor_comparison_summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    value_positioning_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    quote: Mapped["Quote | None"] = relationship(back_populates="ai_recommendations")
    product: Mapped["Product"] = relationship()
    approved_by: Mapped["User | None"] = relationship()


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approver_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    requested_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    requested_discount: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending
    )
    request_justification: Mapped[str] = mapped_column(Text, nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quote: Mapped["Quote"] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    old_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    actor: Mapped["User"] = relationship()


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    run_type: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    input_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_quote_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True
    )
    related_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    related_recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_recommendations.id", ondelete="SET NULL"), nullable=True
    )
    meta_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PasswordChangeRequest(Base):
    __tablename__ = "password_change_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    requested_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    request_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PasswordChangeRequestStatus] = mapped_column(
        SAEnum(PasswordChangeRequestStatus), nullable=False, default=PasswordChangeRequestStatus.pending
    )
    admin_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requested_by: Mapped["User"] = relationship(
        foreign_keys=[requested_by_user_id], back_populates="password_change_requests"
    )
    decided_by: Mapped["User | None"] = relationship(
        foreign_keys=[decided_by_user_id], back_populates="password_change_decisions"
    )


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_by_role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), nullable=False)
    upload_type: Mapped[UploadType] = mapped_column(SAEnum(UploadType), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(16), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[UploadStatus] = mapped_column(
        SAEnum(UploadStatus), nullable=False, default=UploadStatus.draft
    )
    meta_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extraction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_entities_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linked_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policy_documents.id", ondelete="SET NULL"), nullable=True
    )
    linked_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    linked_pricebook_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("price_books.id", ondelete="SET NULL"), nullable=True
    )
    linked_contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True
    )
    linked_rebate_program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rebate_programs.id", ondelete="SET NULL"), nullable=True
    )
    validation_issues: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    uploaded_by: Mapped["User | None"] = relationship(back_populates="uploaded_files")


class CompetitorProduct(Base):
    __tablename__ = "competitor_products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    competitor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="RM")
    features_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_uploaded_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True
    )
    matched_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    matched_product: Mapped["Product | None"] = relationship()


class ProductValueProfile(Base):
    __tablename__ = "product_value_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    value_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    positioning_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    price_band: Mapped[str | None] = mapped_column(String(40), nullable=True)
    competitor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_competitor_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_gap_percent: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    recommended_strategy: Mapped[str | None] = mapped_column(String(80), nullable=True)
    analysis_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    product: Mapped["Product"] = relationship()


class DocumentExtractionReview(Base):
    __tablename__ = "document_extraction_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    original_extraction_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    corrected_extraction_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

"""initial_schema

Revision ID: 20260219_0001
Revises: 
Create Date: 2026-02-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260219_0001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum("sales", "approver", "executive", "admin", name="roleenum")
customer_tier_enum = sa.Enum("strategic", "core", "growth", name="customertier")
quote_status_enum = sa.Enum(
    "draft",
    "recommended",
    "approval_pending",
    "approved",
    "rejected",
    "finalized",
    name="quotestatus",
)
strategy_mode_enum = sa.Enum(
    "maximize_profit",
    "clear_inventory",
    "market_expansion",
    name="strategymode",
)
risk_level_enum = sa.Enum("low", "medium", "high", name="risklevel")
approval_status_enum = sa.Enum("pending", "approved", "rejected", name="approvalstatus")


def upgrade() -> None:
    # Enum creation is handled by sa.Enum in create_table for SQLite (check constraint)
    # For Postgres, it would be handled if we used create_type=True (default), but here we just rely on inline definition

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("tier", customer_tier_enum, nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("list_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )

    op.create_table(
        "inventory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("on_hand", sa.Integer(), nullable=False),
        sa.Column("stock_age_days_avg", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("margin_floor_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_discount_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("approval_required_below_margin_buffer", sa.Numeric(5, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "category", name="uq_pricing_rules_channel_category"),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=100), nullable=False),
        sa.Column("strategy_mode", strategy_mode_enum, nullable=False),
        sa.Column("status", quote_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quote_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("requested_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("requested_discount", sa.Numeric(6, 2), nullable=True),
        sa.Column("recommended_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("recommended_band_low", sa.Numeric(12, 2), nullable=True),
        sa.Column("recommended_band_high", sa.Numeric(12, 2), nullable=True),
        sa.Column("recommended_discount_low", sa.Numeric(6, 2), nullable=True),
        sa.Column("recommended_discount_high", sa.Numeric(6, 2), nullable=True),
        sa.Column("final_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("final_discount", sa.Numeric(6, 2), nullable=True),
        sa.Column("win_probability", sa.Numeric(8, 6), nullable=True),
        sa.Column("confidence", sa.Numeric(8, 6), nullable=True),
        sa.Column("margin_percent", sa.Numeric(6, 2), nullable=True),
        sa.Column("expected_profit", sa.Numeric(14, 2), nullable=True),
        sa.Column("risk_level", risk_level_enum, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=100), nullable=False),
        sa.Column("xgb_outputs_json", sa.JSON(), nullable=False),
        sa.Column("optimizer_outputs_json", sa.JSON(), nullable=False),
        sa.Column("gpt_outputs_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("approver_user_id", sa.Uuid(), nullable=True),
        sa.Column("requested_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("requested_discount", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", approval_status_enum, nullable=False),
        sa.Column("request_justification", sa.Text(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approver_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("old_json", sa.JSON(), nullable=True),
        sa.Column("new_json", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("approvals")
    op.drop_table("recommendations")
    op.drop_table("quote_items")
    op.drop_table("quotes")
    op.drop_table("pricing_rules")
    op.drop_table("inventory")
    op.drop_table("products")
    op.drop_table("customers")
    op.drop_table("users")

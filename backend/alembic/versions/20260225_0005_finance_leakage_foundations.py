"""finance_leakage_foundations

Revision ID: 20260225_0005
Revises: 20260225_0004
Create Date: 2026-02-25 00:05:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260225_0005"
down_revision = "20260225_0004"
branch_labels = None
depends_on = None

contract_status_enum = postgresql.ENUM(
    "active",
    "inactive",
    name="contractstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    contract_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "contracts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", contract_status_enum, nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["policy_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contract_lines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("floor_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("ceiling_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_cap_percent", sa.Numeric(6, 2), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rebate_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=100), nullable=True),
        sa.Column("tier_rates_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mdf_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["policy_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "freight_fees_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=100), nullable=False),
        sa.Column("freight_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("fees_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", name="uq_freight_fees_policies_channel"),
    )

    op.create_table(
        "quote_finance_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("revenue_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("cogs_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("rebate_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("freight_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("fees_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("mdf_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gross_margin_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_margin_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_margin_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("leakage_flags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quote_id"),
    )


def downgrade() -> None:
    op.drop_table("quote_finance_snapshots")
    op.drop_table("freight_fees_policies")
    op.drop_table("rebate_programs")
    op.drop_table("contract_lines")
    op.drop_table("contracts")

    bind = op.get_bind()
    contract_status_enum.drop(bind, checkfirst=True)

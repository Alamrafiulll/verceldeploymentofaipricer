"""Expand quote finance snapshots for true margin and leakage control."""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0016"
down_revision = "20260308_0015"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "quote_finance_snapshots"):
        return

    columns = {
        "list_revenue_total": sa.Column("list_revenue_total", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "gift_cost_amount": sa.Column("gift_cost_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "bundle_cost_amount": sa.Column("bundle_cost_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "promotion_allocation_amount": sa.Column("promotion_allocation_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "contract_effect_amount": sa.Column("contract_effect_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "list_margin_amount": sa.Column("list_margin_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "price_discount_amount": sa.Column("price_discount_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "leakage_amount": sa.Column("leakage_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        "leakage_reasons_json": sa.Column("leakage_reasons_json", sa.JSON(), nullable=False, server_default="[]"),
    }
    for column_name, column in columns.items():
        if not _has_column(inspector, "quote_finance_snapshots", column_name):
            op.add_column("quote_finance_snapshots", column)

    op.execute(
        """
        UPDATE quote_finance_snapshots
        SET
            list_revenue_total = revenue_total,
            gift_cost_amount = 0,
            bundle_cost_amount = 0,
            promotion_allocation_amount = 0,
            contract_effect_amount = 0,
            list_margin_amount = gross_margin_amount,
            price_discount_amount = 0,
            leakage_amount = COALESCE(rebate_amount, 0)
                + COALESCE(campaign_cost_amount, 0)
                + COALESCE(freight_amount, 0)
                + COALESCE(fees_amount, 0)
                + COALESCE(mdf_amount, 0),
            leakage_reasons_json = '[]'
        """
    )

    for column_name in columns:
        op.alter_column("quote_finance_snapshots", column_name, server_default=None)


def downgrade() -> None:
    op.drop_column("quote_finance_snapshots", "leakage_reasons_json")
    op.drop_column("quote_finance_snapshots", "leakage_amount")
    op.drop_column("quote_finance_snapshots", "price_discount_amount")
    op.drop_column("quote_finance_snapshots", "list_margin_amount")
    op.drop_column("quote_finance_snapshots", "contract_effect_amount")
    op.drop_column("quote_finance_snapshots", "promotion_allocation_amount")
    op.drop_column("quote_finance_snapshots", "bundle_cost_amount")
    op.drop_column("quote_finance_snapshots", "gift_cost_amount")
    op.drop_column("quote_finance_snapshots", "list_revenue_total")

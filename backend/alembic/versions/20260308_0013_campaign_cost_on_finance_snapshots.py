"""campaign cost on finance snapshots

Revision ID: 20260308_0013
Revises: 20260308_0012
Create Date: 2026-03-08 22:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0013"
down_revision = "20260308_0012"
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

    if not _has_column(inspector, "quote_finance_snapshots", "campaign_cost_amount"):
        op.add_column(
            "quote_finance_snapshots",
            sa.Column("campaign_cost_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        )
    op.execute(
        "UPDATE quote_finance_snapshots SET campaign_cost_amount = 0 WHERE campaign_cost_amount IS NULL"
    )
    op.alter_column("quote_finance_snapshots", "campaign_cost_amount", server_default=None)


def downgrade() -> None:
    op.drop_column("quote_finance_snapshots", "campaign_cost_amount")

"""campaign_tables

Revision ID: 20260225_0004
Revises: 20260225_0003
Create Date: 2026-02-25 00:04:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260225_0004"
down_revision = "20260225_0003"
branch_labels = None
depends_on = None

campaign_status_enum = postgresql.ENUM(
    "active",
    "inactive",
    name="campaignstatus",
    create_type=False,
)
campaign_rule_type_enum = postgresql.ENUM(
    "free_gift",
    "discount",
    "bundle",
    name="campaignruletype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    campaign_status_enum.create(bind, checkfirst=True)
    campaign_rule_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", campaign_status_enum, nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["policy_documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "campaign_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("rule_type", campaign_rule_type_enum, nullable=False),
        sa.Column("eligibility_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("exclusion_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("entitlement_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("campaign_rules")
    op.drop_table("campaigns")

    bind = op.get_bind()
    campaign_rule_type_enum.drop(bind, checkfirst=True)
    campaign_status_enum.drop(bind, checkfirst=True)

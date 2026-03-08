"""campaign_tables

Revision ID: 20260225_0004
Revises: 20260225_0003
Create Date: 2026-02-25 00:04:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260225_0004"
down_revision = "20260225_0003"
branch_labels = None
depends_on = None

campaign_status_enum = sa.Enum(
    "active",
    "inactive",
    name="campaignstatus",
)
campaign_rule_type_enum = sa.Enum(
    "free_gift",
    "discount",
    "bundle",
    name="campaignruletype",
)


def upgrade() -> None:
    # Enum creation skipped

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
        sa.Column("eligibility_json", sa.JSON(), nullable=False),
        sa.Column("exclusion_json", sa.JSON(), nullable=False),
        sa.Column("entitlement_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("campaign_rules")
    op.drop_table("campaigns")

    # Enum drop skipped

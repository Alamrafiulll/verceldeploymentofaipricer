"""upload_registry_and_ai_trace

Revision ID: 20260307_0009
Revises: 20260307_0008
Create Date: 2026-03-07 16:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260307_0009"
down_revision = "20260307_0008"
branch_labels = None
depends_on = None


upload_type_enum = postgresql.ENUM(
    "sales_history",
    "product_catalog",
    "current_price_list",
    "competitor_price_data",
    "promotion_calendar",
    "pricing_approval_sheet",
    "strategic_pricing_guideline",
    "quarterly_pricing_plan",
    "strategic_targets",
    "market_reports",
    "user_role_config",
    "pricing_policy",
    "audit_log_archive",
    "model_configuration",
    name="uploadtype",
    create_type=False,
)
upload_status_enum = postgresql.ENUM("active", "archived", name="uploadstatus", create_type=False)
role_enum = postgresql.ENUM("sales", "approver", "executive", "admin", name="roleenum", create_type=False)
approval_status_enum = postgresql.ENUM(
    "pending", "approved", "rejected", name="approvalstatus", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    upload_type_enum.create(bind, checkfirst=True)
    upload_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("uploaded_by_role", role_enum, nullable=False),
        sa.Column("upload_type", upload_type_enum, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_ext", sa.String(length=16), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=True),
        sa.Column("status", upload_status_enum, nullable=False),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("recommended_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("confidence", sa.Numeric(8, 6), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approval_status", approval_status_enum, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_recommendations")
    op.drop_table("uploaded_files")

    bind = op.get_bind()
    upload_status_enum.drop(bind, checkfirst=True)
    upload_type_enum.drop(bind, checkfirst=True)

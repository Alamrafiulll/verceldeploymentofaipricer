"""policy review traceability

Revision ID: 20260308_0012
Revises: 20260308_0011
Create Date: 2026-03-08 21:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0012"
down_revision = "20260308_0011"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_foreign_key(inspector, table_name: str, constraint_name: str) -> bool:
    return constraint_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "policy_documents"):
        return

    if not _has_column(inspector, "policy_documents", "source_uploaded_file_id"):
        op.add_column(
            "policy_documents",
            sa.Column("source_uploaded_file_id", sa.Uuid(), nullable=True),
        )
    if not _has_column(inspector, "policy_documents", "auto_create_campaign"):
        op.add_column(
            "policy_documents",
            sa.Column("auto_create_campaign", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column(inspector, "policy_documents", "review_notes"):
        op.add_column(
            "policy_documents",
            sa.Column("review_notes", sa.Text(), nullable=True),
        )
    if not _has_column(inspector, "policy_documents", "reviewed_by_user_id"):
        op.add_column(
            "policy_documents",
            sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        )
    if not _has_column(inspector, "policy_documents", "reviewed_at"):
        op.add_column(
            "policy_documents",
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        )

    inspector = sa.inspect(bind)
    if not _has_foreign_key(inspector, "policy_documents", "fk_policy_documents_source_uploaded_file_id"):
        op.create_foreign_key(
            "fk_policy_documents_source_uploaded_file_id",
            "policy_documents",
            "uploaded_files",
            ["source_uploaded_file_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _has_foreign_key(inspector, "policy_documents", "fk_policy_documents_reviewed_by_user_id"):
        op.create_foreign_key(
            "fk_policy_documents_reviewed_by_user_id",
            "policy_documents",
            "users",
            ["reviewed_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.execute("UPDATE policy_documents SET auto_create_campaign = false WHERE auto_create_campaign IS NULL")
    op.alter_column("policy_documents", "auto_create_campaign", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_policy_documents_reviewed_by_user_id", "policy_documents", type_="foreignkey")
    op.drop_constraint("fk_policy_documents_source_uploaded_file_id", "policy_documents", type_="foreignkey")
    op.drop_column("policy_documents", "reviewed_at")
    op.drop_column("policy_documents", "reviewed_by_user_id")
    op.drop_column("policy_documents", "review_notes")
    op.drop_column("policy_documents", "auto_create_campaign")
    op.drop_column("policy_documents", "source_uploaded_file_id")

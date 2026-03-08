"""Align upload, market comparison, and extraction review schema.

Revision ID: 20260308_0011
Revises: 20260308_0010
Create Date: 2026-03-08 18:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260308_0011"
down_revision = "20260308_0010"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _add_postgres_enum_values(bind: sa.Connection, enum_name: str, values: list[str]) -> None:
    if bind.dialect.name != "postgresql":
        return
    for value in values:
        op.execute(sa.text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _add_postgres_enum_values(
        bind,
        "uploadtype",
        [
            "rule_mapping_template",
            "campaign_memo",
            "trading_terms",
            "rebate_agreement",
            "contract_pricing",
            "margin_target_sheet",
        ],
    )
    _add_postgres_enum_values(
        bind,
        "uploadstatus",
        ["draft", "parsed", "needs_review", "rejected"],
    )

    if _has_table(inspector, "uploaded_files"):
        with op.batch_alter_table("uploaded_files") as batch_op:
            if not _has_column(inspector, "uploaded_files", "extraction_summary"):
                batch_op.add_column(sa.Column("extraction_summary", sa.Text(), nullable=True))
            if not _has_column(inspector, "uploaded_files", "extracted_entities_count"):
                batch_op.add_column(sa.Column("extracted_entities_count", sa.Integer(), nullable=True))
            if not _has_column(inspector, "uploaded_files", "linked_policy_id"):
                batch_op.add_column(sa.Column("linked_policy_id", sa.Uuid(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_uploaded_files_linked_policy_id",
                    "policy_documents",
                    ["linked_policy_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
            if not _has_column(inspector, "uploaded_files", "linked_campaign_id"):
                batch_op.add_column(sa.Column("linked_campaign_id", sa.Uuid(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_uploaded_files_linked_campaign_id",
                    "campaigns",
                    ["linked_campaign_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
            if not _has_column(inspector, "uploaded_files", "linked_pricebook_id"):
                batch_op.add_column(sa.Column("linked_pricebook_id", sa.Uuid(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_uploaded_files_linked_pricebook_id",
                    "price_books",
                    ["linked_pricebook_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
            if not _has_column(inspector, "uploaded_files", "validation_issues"):
                batch_op.add_column(sa.Column("validation_issues", sa.JSON(), nullable=True))
            if not _has_column(inspector, "uploaded_files", "review_status"):
                batch_op.add_column(sa.Column("review_status", sa.String(length=40), nullable=True))

    if not _has_table(inspector, "competitor_products"):
        op.create_table(
            "competitor_products",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("competitor_name", sa.String(length=255), nullable=False),
            sa.Column("product_name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=120), nullable=False),
            sa.Column("price", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(length=16), nullable=False, server_default="RM"),
            sa.Column("features_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("source_uploaded_file_id", sa.Uuid(), nullable=True),
            sa.Column("matched_product_id", sa.Uuid(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["matched_product_id"], ["products.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(
                ["source_uploaded_file_id"], ["uploaded_files.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table(inspector, "product_value_profiles"):
        op.create_table(
            "product_value_profiles",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("product_id", sa.Uuid(), nullable=False),
            sa.Column("value_score", sa.Numeric(6, 2), nullable=True),
            sa.Column("positioning_label", sa.String(length=40), nullable=True),
            sa.Column("price_band", sa.String(length=40), nullable=True),
            sa.Column("competitor_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_competitor_price", sa.Numeric(12, 2), nullable=True),
            sa.Column("price_gap_percent", sa.Numeric(6, 2), nullable=True),
            sa.Column("recommended_strategy", sa.String(length=80), nullable=True),
            sa.Column("analysis_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("product_id", name="uq_product_value_profiles_product_id"),
        )

    if not _has_table(inspector, "document_extraction_reviews"):
        op.create_table(
            "document_extraction_reviews",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("uploaded_file_id", sa.Uuid(), nullable=False),
            sa.Column("reviewer_user_id", sa.Uuid(), nullable=True),
            sa.Column(
                "original_extraction_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            ),
            sa.Column("corrected_extraction_json", sa.JSON(), nullable=True),
            sa.Column("review_status", sa.String(length=40), nullable=False, server_default="pending"),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["uploaded_file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "document_extraction_reviews"):
        op.drop_table("document_extraction_reviews")
    if _has_table(inspector, "product_value_profiles"):
        op.drop_table("product_value_profiles")
    if _has_table(inspector, "competitor_products"):
        op.drop_table("competitor_products")

    if _has_table(inspector, "uploaded_files"):
        with op.batch_alter_table("uploaded_files") as batch_op:
            if _has_column(inspector, "uploaded_files", "review_status"):
                batch_op.drop_column("review_status")
            if _has_column(inspector, "uploaded_files", "validation_issues"):
                batch_op.drop_column("validation_issues")
            if _has_column(inspector, "uploaded_files", "linked_pricebook_id"):
                batch_op.drop_constraint("fk_uploaded_files_linked_pricebook_id", type_="foreignkey")
                batch_op.drop_column("linked_pricebook_id")
            if _has_column(inspector, "uploaded_files", "linked_campaign_id"):
                batch_op.drop_constraint("fk_uploaded_files_linked_campaign_id", type_="foreignkey")
                batch_op.drop_column("linked_campaign_id")
            if _has_column(inspector, "uploaded_files", "linked_policy_id"):
                batch_op.drop_constraint("fk_uploaded_files_linked_policy_id", type_="foreignkey")
                batch_op.drop_column("linked_policy_id")
            if _has_column(inspector, "uploaded_files", "extracted_entities_count"):
                batch_op.drop_column("extracted_entities_count")
            if _has_column(inspector, "uploaded_files", "extraction_summary"):
                batch_op.drop_column("extraction_summary")

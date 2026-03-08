"""policy_pricebook_foundations

Revision ID: 20260225_0003
Revises: 20260223_0002
Create Date: 2026-02-25 00:03:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260225_0003"
down_revision = "20260223_0002"
branch_labels = None
depends_on = None

price_book_channel_enum = sa.Enum(
    "lsp",
    "wm",
    "em",
    name="pricebookchannel",
)
policy_document_type_enum = sa.Enum(
    "memo",
    "price_list",
    "trading_terms",
    "finance",
    name="policydocumenttype",
)
policy_document_status_enum = sa.Enum(
    "draft",
    "active",
    "archived",
    name="policydocumentstatus",
)
policy_clause_type_enum = sa.Enum(
    "eligibility",
    "exclusion",
    "entitlement",
    "pricing",
    "rebate",
    "incentive",
    "payment_terms",
    "returns",
    "exchange",
    "other",
    name="policyclausetype",
)


def upgrade() -> None:
    # Enum creation skipped for generic sa.Enum

    op.create_table(
        "policy_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("doc_type", policy_document_type_enum, nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", policy_document_status_enum, nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_clauses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_document_id", sa.Uuid(), nullable=False),
        sa.Column("clause_type", policy_clause_type_enum, nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.ForeignKeyConstraint(["policy_document_id"], ["policy_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "price_books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("channel", price_book_channel_enum, nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["source_document_id"], ["policy_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "price_book_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("price_book_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("list_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["price_book_id"], ["price_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("price_book_id", "product_id", name="uq_price_book_items_book_product"),
    )


def downgrade() -> None:
    op.drop_table("price_book_items")
    op.drop_table("price_books")
    op.drop_table("policy_clauses")
    op.drop_table("policy_documents")

    # Enum drop skipped

"""policy_pricebook_foundations

Revision ID: 20260225_0003
Revises: 20260223_0002
Create Date: 2026-02-25 00:03:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260225_0003"
down_revision = "20260223_0002"
branch_labels = None
depends_on = None

price_book_channel_enum = postgresql.ENUM(
    "lsp",
    "wm",
    "em",
    name="pricebookchannel",
    create_type=False,
)
policy_document_type_enum = postgresql.ENUM(
    "memo",
    "price_list",
    "trading_terms",
    "finance",
    name="policydocumenttype",
    create_type=False,
)
policy_document_status_enum = postgresql.ENUM(
    "draft",
    "active",
    "archived",
    name="policydocumentstatus",
    create_type=False,
)
policy_clause_type_enum = postgresql.ENUM(
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
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    price_book_channel_enum.create(bind, checkfirst=True)
    policy_document_type_enum.create(bind, checkfirst=True)
    policy_document_status_enum.create(bind, checkfirst=True)
    policy_clause_type_enum.create(bind, checkfirst=True)

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
        sa.Column("structured_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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

    bind = op.get_bind()
    policy_clause_type_enum.drop(bind, checkfirst=True)
    policy_document_status_enum.drop(bind, checkfirst=True)
    policy_document_type_enum.drop(bind, checkfirst=True)
    price_book_channel_enum.drop(bind, checkfirst=True)

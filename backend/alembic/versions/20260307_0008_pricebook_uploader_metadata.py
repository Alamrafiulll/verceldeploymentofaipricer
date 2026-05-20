"""pricebook_uploader_metadata

Revision ID: 20260307_0008
Revises: 20260304_0007
Create Date: 2026-03-07 12:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260307_0008"
down_revision = "20260304_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("price_books", sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "price_books",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_foreign_key(
        "fk_price_books_uploaded_by_user_id",
        "price_books",
        "users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_price_books_uploaded_by_user_id", "price_books", type_="foreignkey")
    op.drop_column("price_books", "created_at")
    op.drop_column("price_books", "uploaded_by_user_id")

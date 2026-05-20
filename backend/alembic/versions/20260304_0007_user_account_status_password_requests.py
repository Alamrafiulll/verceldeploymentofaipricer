"""user_account_status_password_requests

Revision ID: 20260304_0007
Revises: 20260225_0006
Create Date: 2026-03-04 00:07:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260304_0007"
down_revision = "20260225_0006"
branch_labels = None
depends_on = None

user_account_status_enum = postgresql.ENUM(
    "active",
    "inactive",
    name="useraccountstatus",
    create_type=False,
)

password_change_request_status_enum = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="passwordchangerequeststatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_account_status_enum.create(bind, checkfirst=True)
    password_change_request_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "account_status",
            user_account_status_enum,
            nullable=False,
            server_default="active",
        ),
    )
    op.alter_column("users", "account_status", server_default=None)

    op.create_table(
        "password_change_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("requested_password_hash", sa.String(length=255), nullable=False),
        sa.Column("request_reason", sa.Text(), nullable=True),
        sa.Column("status", password_change_request_status_enum, nullable=False),
        sa.Column("admin_reason", sa.Text(), nullable=True),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("password_change_requests")
    op.drop_column("users", "account_status")

    bind = op.get_bind()
    password_change_request_status_enum.drop(bind, checkfirst=True)
    user_account_status_enum.drop(bind, checkfirst=True)


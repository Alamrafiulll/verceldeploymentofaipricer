"""user_account_status_password_requests

Revision ID: 20260304_0007
Revises: 20260225_0006
Create Date: 2026-03-04 00:07:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260304_0007"
down_revision = "20260225_0006"
branch_labels = None
depends_on = None

user_account_status_enum = sa.Enum(
    "active",
    "inactive",
    name="useraccountstatus",
)

password_change_request_status_enum = sa.Enum(
    "pending",
    "approved",
    "rejected",
    name="passwordchangerequeststatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    user_account_status_enum.create(bind, checkfirst=True)

    # SQLite does not support adding a column with a server default and then dropping the default
    # in the same way as Postgres, nor does it support standalone enum creation.
    # We use batch_alter_table to handle the schema changes.

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "account_status",
                user_account_status_enum,
                nullable=False,
                server_default="active",
            )
        )
        # In SQLite, we can't easily drop the server default immediately in the same transaction 
        # without recreating the table, but batch_alter_table handles the recreation.
        batch_op.alter_column("account_status", server_default=None)

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
    
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("account_status")

    bind = op.get_bind()
    user_account_status_enum.drop(bind, checkfirst=True)

"""user_approval_status

Revision ID: 20260223_0002
Revises: 20260219_0001
Create Date: 2026-02-23 00:02:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260223_0002"
down_revision = "20260219_0001"
branch_labels = None
depends_on = None

user_approval_status_enum = sa.Enum(
    "pending",
    "approved",
    "rejected",
    name="userapprovalstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    user_approval_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "approval_status",
            user_approval_status_enum,
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column("users", sa.Column("approved_by_user_id", sa.Uuid(), nullable=True))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("approval_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_users_approved_by_user_id",
        "users",
        "users",
        ["approved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Remove server default after population if needed, but here we just set it initially
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("approval_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_users_approved_by_user_id", "users", type_="foreignkey")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("approval_reason")
        batch_op.drop_column("approved_at")
        batch_op.drop_column("approved_by_user_id")
        batch_op.drop_column("approval_status")

    bind = op.get_bind()
    user_approval_status_enum.drop(bind, checkfirst=True)

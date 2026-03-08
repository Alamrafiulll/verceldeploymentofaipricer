"""rebate program enrichment

Revision ID: 20260308_0014
Revises: 20260308_0013
Create Date: 2026-03-08 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0014"
down_revision = "20260308_0013"
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

    if _has_table(inspector, "rebate_programs"):
        if not _has_column(inspector, "rebate_programs", "display_incentive_percent"):
            op.add_column(
                "rebate_programs",
                sa.Column("display_incentive_percent", sa.Numeric(6, 2), nullable=False, server_default="0"),
            )
        if not _has_column(inspector, "rebate_programs", "manager_discretion_warning"):
            op.add_column(
                "rebate_programs",
                sa.Column("manager_discretion_warning", sa.Text(), nullable=True),
            )
        if not _has_column(inspector, "rebate_programs", "retroactive_incentive"):
            op.add_column(
                "rebate_programs",
                sa.Column("retroactive_incentive", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if not _has_column(inspector, "rebate_programs", "program_meta_json"):
            op.add_column(
                "rebate_programs",
                sa.Column("program_meta_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            )

    if _has_table(inspector, "uploaded_files") and not _has_column(inspector, "uploaded_files", "linked_rebate_program_id"):
        op.add_column(
            "uploaded_files",
            sa.Column("linked_rebate_program_id", sa.Uuid(), nullable=True),
        )

    inspector = sa.inspect(bind)
    if _has_table(inspector, "uploaded_files") and not _has_foreign_key(
        inspector, "uploaded_files", "fk_uploaded_files_linked_rebate_program_id"
    ):
        op.create_foreign_key(
            "fk_uploaded_files_linked_rebate_program_id",
            "uploaded_files",
            "rebate_programs",
            ["linked_rebate_program_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.execute(
        "UPDATE rebate_programs SET display_incentive_percent = 0, retroactive_incentive = false "
        "WHERE display_incentive_percent IS NULL OR retroactive_incentive IS NULL"
    )
    op.execute(
        "UPDATE rebate_programs SET program_meta_json = '{}' WHERE program_meta_json IS NULL"
    )
    op.alter_column("rebate_programs", "display_incentive_percent", server_default=None)
    op.alter_column("rebate_programs", "retroactive_incentive", server_default=None)
    op.alter_column("rebate_programs", "program_meta_json", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_uploaded_files_linked_rebate_program_id", "uploaded_files", type_="foreignkey")
    op.drop_column("uploaded_files", "linked_rebate_program_id")
    op.drop_column("rebate_programs", "program_meta_json")
    op.drop_column("rebate_programs", "retroactive_incentive")
    op.drop_column("rebate_programs", "manager_discretion_warning")
    op.drop_column("rebate_programs", "display_incentive_percent")

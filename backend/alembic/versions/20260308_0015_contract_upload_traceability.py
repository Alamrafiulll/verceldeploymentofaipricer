"""contract upload traceability

Revision ID: 20260308_0015
Revises: 20260308_0014
Create Date: 2026-03-08 23:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0015"
down_revision = "20260308_0014"
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

    if _has_table(inspector, "contracts") and not _has_column(inspector, "contracts", "source_uploaded_file_id"):
        op.add_column(
            "contracts",
            sa.Column("source_uploaded_file_id", sa.Uuid(), nullable=True),
        )
    if _has_table(inspector, "uploaded_files") and not _has_column(inspector, "uploaded_files", "linked_contract_id"):
        op.add_column(
            "uploaded_files",
            sa.Column("linked_contract_id", sa.Uuid(), nullable=True),
        )

    inspector = sa.inspect(bind)
    if _has_table(inspector, "contracts") and not _has_foreign_key(
        inspector, "contracts", "fk_contracts_source_uploaded_file_id"
    ):
        op.create_foreign_key(
            "fk_contracts_source_uploaded_file_id",
            "contracts",
            "uploaded_files",
            ["source_uploaded_file_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if _has_table(inspector, "uploaded_files") and not _has_foreign_key(
        inspector, "uploaded_files", "fk_uploaded_files_linked_contract_id"
    ):
        op.create_foreign_key(
            "fk_uploaded_files_linked_contract_id",
            "uploaded_files",
            "contracts",
            ["linked_contract_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint("fk_uploaded_files_linked_contract_id", "uploaded_files", type_="foreignkey")
    op.drop_column("uploaded_files", "linked_contract_id")
    op.drop_constraint("fk_contracts_source_uploaded_file_id", "contracts", type_="foreignkey")
    op.drop_column("contracts", "source_uploaded_file_id")

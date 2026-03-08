"""Expand AI recommendation traceability and model observability."""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0017"
down_revision = "20260308_0016"
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

    if _has_table(inspector, "ai_recommendations"):
        ai_columns = {
            "recommended_price_low": sa.Column("recommended_price_low", sa.Numeric(12, 2), nullable=True),
            "recommended_price_high": sa.Column("recommended_price_high", sa.Numeric(12, 2), nullable=True),
            "win_probability": sa.Column("win_probability", sa.Numeric(8, 6), nullable=True),
            "model_provider": sa.Column("model_provider", sa.String(length=80), nullable=True),
            "fallback_used": sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            "explanation_json": sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
            "source_rule_ids_json": sa.Column("source_rule_ids_json", sa.JSON(), nullable=False, server_default="[]"),
            "source_document_ids_json": sa.Column("source_document_ids_json", sa.JSON(), nullable=False, server_default="[]"),
            "finance_snapshot_id": sa.Column("finance_snapshot_id", sa.Uuid(), nullable=True),
            "risk_level": sa.Column("risk_level", sa.String(length=40), nullable=True),
            "competitor_comparison_summary_json": sa.Column("competitor_comparison_summary_json", sa.JSON(), nullable=False, server_default="{}"),
            "value_positioning_label": sa.Column("value_positioning_label", sa.String(length=80), nullable=True),
        }
        for column_name, column in ai_columns.items():
            if not _has_column(inspector, "ai_recommendations", column_name):
                op.add_column("ai_recommendations", column)

    if _has_table(inspector, "model_runs"):
        model_run_columns = {
            "model_provider": sa.Column("model_provider", sa.String(length=80), nullable=True),
            "fallback_used": sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            "related_quote_id": sa.Column("related_quote_id", sa.Uuid(), nullable=True),
            "related_product_id": sa.Column("related_product_id", sa.Uuid(), nullable=True),
            "related_recommendation_id": sa.Column("related_recommendation_id", sa.Uuid(), nullable=True),
        }
        for column_name, column in model_run_columns.items():
            if not _has_column(inspector, "model_runs", column_name):
                op.add_column("model_runs", column)

    inspector = sa.inspect(bind)
    if _has_table(inspector, "ai_recommendations") and not _has_foreign_key(
        inspector, "ai_recommendations", "fk_ai_recommendations_finance_snapshot_id"
    ):
        op.create_foreign_key(
            "fk_ai_recommendations_finance_snapshot_id",
            "ai_recommendations",
            "quote_finance_snapshots",
            ["finance_snapshot_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if _has_table(inspector, "model_runs") and not _has_foreign_key(
        inspector, "model_runs", "fk_model_runs_related_quote_id"
    ):
        op.create_foreign_key(
            "fk_model_runs_related_quote_id",
            "model_runs",
            "quotes",
            ["related_quote_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if _has_table(inspector, "model_runs") and not _has_foreign_key(
        inspector, "model_runs", "fk_model_runs_related_product_id"
    ):
        op.create_foreign_key(
            "fk_model_runs_related_product_id",
            "model_runs",
            "products",
            ["related_product_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if _has_table(inspector, "model_runs") and not _has_foreign_key(
        inspector, "model_runs", "fk_model_runs_related_recommendation_id"
    ):
        op.create_foreign_key(
            "fk_model_runs_related_recommendation_id",
            "model_runs",
            "ai_recommendations",
            ["related_recommendation_id"],
            ["id"],
            ondelete="SET NULL",
        )

    for column_name in (
        "fallback_used",
        "explanation_json",
        "source_rule_ids_json",
        "source_document_ids_json",
        "competitor_comparison_summary_json",
    ):
        if _has_column(inspector, "ai_recommendations", column_name):
            op.alter_column("ai_recommendations", column_name, server_default=None)
    if _has_table(inspector, "model_runs") and _has_column(inspector, "model_runs", "fallback_used"):
        op.alter_column("model_runs", "fallback_used", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_model_runs_related_recommendation_id", "model_runs", type_="foreignkey")
    op.drop_constraint("fk_model_runs_related_product_id", "model_runs", type_="foreignkey")
    op.drop_constraint("fk_model_runs_related_quote_id", "model_runs", type_="foreignkey")
    op.drop_column("model_runs", "related_recommendation_id")
    op.drop_column("model_runs", "related_product_id")
    op.drop_column("model_runs", "related_quote_id")
    op.drop_column("model_runs", "fallback_used")
    op.drop_column("model_runs", "model_provider")

    op.drop_constraint("fk_ai_recommendations_finance_snapshot_id", "ai_recommendations", type_="foreignkey")
    op.drop_column("ai_recommendations", "value_positioning_label")
    op.drop_column("ai_recommendations", "competitor_comparison_summary_json")
    op.drop_column("ai_recommendations", "risk_level")
    op.drop_column("ai_recommendations", "finance_snapshot_id")
    op.drop_column("ai_recommendations", "source_document_ids_json")
    op.drop_column("ai_recommendations", "source_rule_ids_json")
    op.drop_column("ai_recommendations", "explanation_json")
    op.drop_column("ai_recommendations", "fallback_used")
    op.drop_column("ai_recommendations", "model_provider")
    op.drop_column("ai_recommendations", "win_probability")
    op.drop_column("ai_recommendations", "recommended_price_high")
    op.drop_column("ai_recommendations", "recommended_price_low")

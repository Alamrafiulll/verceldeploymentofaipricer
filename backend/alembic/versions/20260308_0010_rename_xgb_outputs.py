"""rename xgb_outputs_json to foundry_outputs_json

Revision ID: 20260308_0010
Revises: 20260307_0009
Create Date: 2026-03-08 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260308_0010'
down_revision = '20260307_0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.alter_column('xgb_outputs_json', new_column_name='foundry_outputs_json')


def downgrade() -> None:
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.alter_column('foundry_outputs_json', new_column_name='xgb_outputs_json')

"""add_dataset_baselines_table

Revision ID: 5a1e8c9d2b3f
Revises: 347b291747e2
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '5a1e8c9d2b3f'
down_revision: Union[str, Sequence[str], None] = '347b291747e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if 'dataset_baselines' not in insp.get_table_names():
        op.create_table(
            'dataset_baselines',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('dataset_path', sa.String(length=500), nullable=False),
            sa.Column('expected_schema', sa.JSON(), nullable=False),
            sa.Column('reference_sample', sa.JSON(), nullable=True),
            sa.Column('numeric_summary', sa.JSON(), nullable=True),
            sa.Column('quality_score', sa.Float(), nullable=False, server_default='100.0'),
            sa.Column('sample_row_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('dataset_path')
        )
        op.create_index(op.f('ix_dataset_baselines_dataset_path'), 'dataset_baselines', ['dataset_path'], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if 'dataset_baselines' in insp.get_table_names():
        op.drop_index(op.f('ix_dataset_baselines_dataset_path'), table_name='dataset_baselines')
        op.drop_table('dataset_baselines')

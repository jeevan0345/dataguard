"""add mldetectionproofs table for individual ML and statistical detection evidence

Revision ID: 8d4e1f2a5c3b
Revises: 7c3d9e1a4b2f
Create Date: 2026-10-06 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '8d4e1f2a5c3b'
down_revision: Union[str, Sequence[str], None] = '7c3d9e1a4b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)

    if 'mldetectionproofs' not in insp.get_table_names():
        op.create_table(
            'mldetectionproofs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('dataset_path', sa.String(length=500), nullable=False),
            sa.Column('method', sa.String(length=50), nullable=False),
            sa.Column('agent', sa.String(length=50), nullable=False),
            sa.Column('column_name', sa.String(length=200), nullable=True),
            sa.Column('execution_status', sa.String(length=50), nullable=False, server_default='EXECUTED'),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('sample_size', sa.Integer(), nullable=True),
            sa.Column('baseline_sample_size', sa.Integer(), nullable=True),
            sa.Column('current_sample_size', sa.Integer(), nullable=True),
            sa.Column('mean', sa.Float(), nullable=True),
            sa.Column('std_dev', sa.Float(), nullable=True),
            sa.Column('q1', sa.Float(), nullable=True),
            sa.Column('q3', sa.Float(), nullable=True),
            sa.Column('iqr', sa.Float(), nullable=True),
            sa.Column('lower_bound', sa.Float(), nullable=True),
            sa.Column('upper_bound', sa.Float(), nullable=True),
            sa.Column('ks_statistic', sa.Float(), nullable=True),
            sa.Column('p_value', sa.Float(), nullable=True),
            sa.Column('threshold', sa.String(length=100), nullable=True),
            sa.Column('anomaly_score', sa.Float(), nullable=True),
            sa.Column('prediction', sa.Integer(), nullable=True),
            sa.Column('contamination', sa.String(length=50), nullable=True),
            sa.Column('flagged_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('execution_time_ms', sa.Float(), nullable=True),
            sa.Column('evidence', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('finding_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.ForeignKeyConstraint(['inspection_id'], ['inspectionruns.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['finding_id'], ['inspectionfindings.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_mldetectionproofs_inspection_id'), 'mldetectionproofs', ['inspection_id'], unique=False)
        op.create_index(op.f('ix_mldetectionproofs_dataset_path'), 'mldetectionproofs', ['dataset_path'], unique=False)
        op.create_index(op.f('ix_mldetectionproofs_method'), 'mldetectionproofs', ['method'], unique=False)
        op.create_index(op.f('ix_mldetectionproofs_column_name'), 'mldetectionproofs', ['column_name'], unique=False)
        op.create_index(op.f('ix_mldetectionproofs_finding_id'), 'mldetectionproofs', ['finding_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    if 'mldetectionproofs' in insp.get_table_names():
        op.drop_table('mldetectionproofs')

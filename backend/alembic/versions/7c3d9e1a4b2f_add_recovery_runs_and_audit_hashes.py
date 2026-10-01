"""add recovery_runs table and audit hashes on inspectionruns

Revision ID: 7c3d9e1a4b2f
Revises: 5a1e8c9d2b3f
Create Date: 2026-10-01 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '7c3d9e1a4b2f'
down_revision: Union[str, Sequence[str], None] = '5a1e8c9d2b3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    
    # 1. Add audit_hash and audit_hmac to inspectionruns
    inspectionruns_cols = [c['name'] for c in insp.get_columns('inspectionruns')]
    if 'audit_hash' not in inspectionruns_cols:
        op.add_column('inspectionruns', sa.Column('audit_hash', sa.String(length=64), nullable=True))
        op.create_index(op.f('ix_inspectionruns_audit_hash'), 'inspectionruns', ['audit_hash'], unique=False)
    if 'audit_hmac' not in inspectionruns_cols:
        op.add_column('inspectionruns', sa.Column('audit_hmac', sa.String(length=64), nullable=True))

    # 2. Create recoveryruns table
    if 'recoveryruns' not in insp.get_table_names():
        op.create_table(
            'recoveryruns',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('dataset_path', sa.String(length=500), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='RECOVERY_APPLIED'),
            sa.Column('verdict', sa.String(length=50), nullable=False, server_default='PASS'),
            sa.Column('original_row_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('remediated_row_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('actions_executed', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('remediated_file_path', sa.String(length=500), nullable=True),
            sa.Column('remediated_file_hash', sa.String(length=64), nullable=True),
            sa.Column('executed_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.ForeignKeyConstraint(['inspection_id'], ['inspectionruns.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['executed_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_recoveryruns_inspection_id'), 'recoveryruns', ['inspection_id'], unique=False)
        op.create_index(op.f('ix_recoveryruns_dataset_path'), 'recoveryruns', ['dataset_path'], unique=False)
        op.create_index(op.f('ix_recoveryruns_status'), 'recoveryruns', ['status'], unique=False)
        op.create_index(op.f('ix_recoveryruns_verdict'), 'recoveryruns', ['verdict'], unique=False)
        op.create_index(op.f('ix_recoveryruns_executed_by'), 'recoveryruns', ['executed_by'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    if 'recoveryruns' in insp.get_table_names():
        op.drop_table('recoveryruns')
    
    inspectionruns_cols = [c['name'] for c in insp.get_columns('inspectionruns')]
    if 'audit_hmac' in inspectionruns_cols:
        op.drop_column('inspectionruns', 'audit_hmac')
    if 'audit_hash' in inspectionruns_cols:
        op.drop_index(op.f('ix_inspectionruns_audit_hash'), table_name='inspectionruns')
        op.drop_column('inspectionruns', 'audit_hash')

"""add_users_table

Revision ID: 347b291747e2
Revises: 43a230dc2944
Create Date: 2026-09-29 11:47:04.180817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '347b291747e2'
down_revision: Union[str, Sequence[str], None] = '43a230dc2944'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if 'users' not in insp.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=False),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False, server_default='DATA_ENGINEER'),
            sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if 'users' in insp.get_table_names():
        op.drop_index(op.f('ix_users_role'), table_name='users')
        op.drop_index(op.f('ix_users_email'), table_name='users')
        op.drop_table('users')

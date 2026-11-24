"""add user roles column

Revision ID: 006_add_user_roles
Revises: 005_latest_revision
Create Date: 2026-11-24 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '006_add_user_roles'
down_revision: str | None = '005_latest_revision'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'user'"),
        ),
    )
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin IS TRUE")
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_column('users', 'role')

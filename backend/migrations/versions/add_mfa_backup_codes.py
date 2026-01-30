"""Add mfa_backup_codes to users table

Revision ID: d4e5f6a7b8c9
Revises: c1104acd2fa6
Create Date: 2026-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c1104acd2fa6'
branch_labels = None
depends_on = None


def upgrade():
    """Add mfa_backup_codes JSONB column to auth.users table"""
    op.add_column(
        'users',
        sa.Column('mfa_backup_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema='auth'
    )


def downgrade():
    """Remove mfa_backup_codes column from auth.users table"""
    op.drop_column('users', 'mfa_backup_codes', schema='auth')

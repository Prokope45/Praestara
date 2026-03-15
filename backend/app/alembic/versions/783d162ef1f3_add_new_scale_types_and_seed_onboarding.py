"""add_new_scale_types_and_seed_onboarding

Revision ID: 783d162ef1f3
Revises: 89376142313e
Create Date: 2026-03-15 12:50:51.233528

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import text
import uuid


# revision identifiers, used by Alembic.
revision = '783d162ef1f3'
down_revision = '89376142313e'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to ScaleType
    # Note: Enum values must be added outside of a transaction in PostgreSQL
    conn = op.get_bind()
    
    # Commit any pending transaction and add enum values
    conn.execute(text("COMMIT"))
    conn.execute(text("ALTER TYPE scaletype ADD VALUE IF NOT EXISTS 'TEXT'"))
    conn.execute(text("ALTER TYPE scaletype ADD VALUE IF NOT EXISTS 'FREQUENCY'"))
    conn.execute(text("ALTER TYPE scaletype ADD VALUE IF NOT EXISTS 'DOMAIN_RATING'"))


def downgrade():
    # Note: We cannot remove enum values in PostgreSQL easily, so we leave them
    # If you need to remove them, you would need to recreate the enum type
    pass

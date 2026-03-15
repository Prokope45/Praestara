"""merge fitness and onboarding heads

Revision ID: 741e3547b3ea
Revises: 014459b76db9, dab98d5cebd7
Create Date: 2026-03-15 17:24:59.145918

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '741e3547b3ea'
down_revision = ('014459b76db9', 'dab98d5cebd7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

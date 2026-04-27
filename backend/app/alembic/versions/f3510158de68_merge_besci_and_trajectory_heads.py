"""merge besci and trajectory heads

Revision ID: f3510158de68
Revises: 89c1eeb8f588, a20e49758210
Create Date: 2026-04-26 11:49:35.762321

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'f3510158de68'
down_revision = ('89c1eeb8f588', 'a20e49758210')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

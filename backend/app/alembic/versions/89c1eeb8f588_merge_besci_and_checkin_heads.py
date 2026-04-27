"""merge_besci_and_checkin_heads

Revision ID: 89c1eeb8f588
Revises: 258ee14f025b, 7fbe6d4d7a10
Create Date: 2026-04-26 11:22:07.257661

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '89c1eeb8f588'
down_revision = ('258ee14f025b', '7fbe6d4d7a10')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

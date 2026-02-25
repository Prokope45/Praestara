"""empty message

Revision ID: 13b198069976
Revises: 4a4b7b9e3a91, 6bce073103ce
Create Date: 2026-02-07 14:33:06.276874

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '13b198069976'
down_revision = ('4a4b7b9e3a91', '6bce073103ce')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

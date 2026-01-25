"""add_profile_image_to_user

Revision ID: c7e75ff4957f
Revises: c2351d7ba607
Create Date: 2026-01-25 01:30:51.733284

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'c7e75ff4957f'
down_revision = 'c2351d7ba607'
branch_labels = None
depends_on = None


def upgrade():
    # Add profile_image column to user table
    op.add_column('user', sa.Column('profile_image', sa.String(length=500), nullable=True))


def downgrade():
    # Remove profile_image column from user table
    op.drop_column('user', 'profile_image')

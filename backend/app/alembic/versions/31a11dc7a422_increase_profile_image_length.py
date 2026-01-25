"""increase_profile_image_length

Revision ID: 31a11dc7a422
Revises: c7e75ff4957f
Create Date: 2026-01-25 01:44:38.716032

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '31a11dc7a422'
down_revision = 'c7e75ff4957f'
branch_labels = None
depends_on = None


def upgrade():
    # Alter profile_image column to use TEXT type (unlimited length)
    op.alter_column('user', 'profile_image',
                    type_=sa.Text(),
                    existing_type=sa.String(length=500),
                    existing_nullable=True)


def downgrade():
    # Revert profile_image column back to VARCHAR(500)
    op.alter_column('user', 'profile_image',
                    type_=sa.String(length=500),
                    existing_type=sa.Text(),
                    existing_nullable=True)

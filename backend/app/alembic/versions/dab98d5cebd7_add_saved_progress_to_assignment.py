"""add_saved_progress_to_assignment

Revision ID: dab98d5cebd7
Revises: 906df335c844
Create Date: 2026-03-15 13:34:40.661197

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'dab98d5cebd7'
down_revision = '906df335c844'
branch_labels = None
depends_on = None


def upgrade():
    # Add saved_progress column to questionnaireassignment table
    op.add_column('questionnaireassignment', sa.Column('saved_progress', sa.JSON(), nullable=True))


def downgrade():
    # Remove saved_progress column from questionnaireassignment table
    op.drop_column('questionnaireassignment', 'saved_progress')

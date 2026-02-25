"""merge_questionnaire_systems

Revision ID: ada407d6ccbe
Revises: 13b198069976
Create Date: 2026-02-07 14:33:10.864224

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ada407d6ccbe'
down_revision = '13b198069976'
branch_labels = None
depends_on = None


def upgrade():
    # This migration merges two branches that have already been applied to the database:
    # - 4a4b7b9e3a91: Added engine89result table and onboarding_completed_at
    # - 6bce073103ce: Added comprehensive questionnaire system
    # 
    # Since both branches have been applied, the database is already in the correct state.
    # This is just a merge point in the migration history.
    pass


def downgrade():
    # This is a merge migration, downgrade is not supported
    pass

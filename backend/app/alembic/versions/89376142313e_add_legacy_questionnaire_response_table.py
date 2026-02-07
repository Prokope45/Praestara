"""add_legacy_questionnaire_response_table

Revision ID: 89376142313e
Revises: ada407d6ccbe
Create Date: 2026-02-07 15:48:33.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '89376142313e'
down_revision = 'ada407d6ccbe'
branch_labels = None
depends_on = None


def upgrade():
    # Create legacyquestionnaireresponse table for checkins, onboarding, and engine89
    op.create_table('legacyquestionnaireresponse',
        sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('schema_version', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('legacyquestionnaireresponse')

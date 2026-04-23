"""seed_onboarding_questionnaire

Revision ID: 906df335c844
Revises: 783d162ef1f3
Create Date: 2026-03-15 13:02:16.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import uuid


# revision identifiers, used by Alembic.
revision = '906df335c844'
down_revision = 'ea0ea4bbd5b4'
branch_labels = None
depends_on = None


def upgrade():
    # Seeding has been moved to backend/app/core/seed_data.py
    # which is called by initial_data.py
    pass


def downgrade():
    # Remove the Praestara Onboarding questionnaire
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM questionnairetemplate WHERE title = 'Praestara Onboarding'")
    )

"""track fitness trend counters

Revision ID: 1d456d33d35c
Revises: be54e6ea79b3
Create Date: 2026-02-27 16:31:27.526059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d456d33d35c'
down_revision = 'be54e6ea79b3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("burnout_trend_weeks", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("adherence_trend_weeks", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("gs_fitness_state", "adherence_trend_weeks")
    op.drop_column("gs_fitness_state", "burnout_trend_weeks")

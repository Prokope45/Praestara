"""add fitness plan version fields

Revision ID: 5a4024a6a3ab
Revises: 1de6dae55597
Create Date: 2026-02-27 15:07:43.161078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a4024a6a3ab'
down_revision = '1de6dae55597'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_weekly_fitness_plan",
        sa.Column("engine_version", sa.String(length=50), server_default="v1.0.0", nullable=False),
    )
    op.add_column(
        "gs_weekly_fitness_plan",
        sa.Column("allocation_version", sa.String(length=50), server_default="v1.0.0", nullable=False),
    )
    op.add_column(
        "gs_weekly_fitness_plan",
        sa.Column("progression_version", sa.String(length=50), server_default="v1.0.0", nullable=False),
    )
    op.drop_column("gs_weekly_fitness_plan", "fitness_engine_version")


def downgrade():
    op.add_column(
        "gs_weekly_fitness_plan",
        sa.Column("fitness_engine_version", sa.String(length=50), server_default="v1.0.0", nullable=False),
    )
    op.drop_column("gs_weekly_fitness_plan", "progression_version")
    op.drop_column("gs_weekly_fitness_plan", "allocation_version")
    op.drop_column("gs_weekly_fitness_plan", "engine_version")

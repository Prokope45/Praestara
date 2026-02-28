"""add fitness ceilings

Revision ID: 2cc5acb9feff
Revises: f6abbf023897
Create Date: 2026-02-27 16:53:52.759654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cc5acb9feff'
down_revision = 'f6abbf023897'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("endurance_ceiling", sa.Float(), server_default="1.0", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("skeletal_ceiling", sa.Float(), server_default="1.0", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("mobility_ceiling", sa.Float(), server_default="1.0", nullable=False),
    )


def downgrade():
    op.drop_column("gs_fitness_state", "mobility_ceiling")
    op.drop_column("gs_fitness_state", "skeletal_ceiling")
    op.drop_column("gs_fitness_state", "endurance_ceiling")

"""update fitness state fields

Revision ID: be54e6ea79b3
Revises: 5a4024a6a3ab
Create Date: 2026-02-27 15:12:49.847427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be54e6ea79b3'
down_revision = '5a4024a6a3ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("endurance_capacity_score", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("skeletal_capacity_score", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("mobility_capacity_score", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("self_efficacy_score", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("burnout_index", sa.Float(), server_default="0.3", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("stress_tolerance_score", sa.Float(), server_default="0.5", nullable=False),
    )
    op.execute(
        """
        UPDATE gs_fitness_state
        SET
            endurance_capacity_score = endurance_level,
            skeletal_capacity_score = skeletal_muscular_level,
            mobility_capacity_score = mobility_level,
            self_efficacy_score = self_efficacy
        """
    )
    op.drop_column("gs_fitness_state", "endurance_level")
    op.drop_column("gs_fitness_state", "skeletal_muscular_level")
    op.drop_column("gs_fitness_state", "mobility_level")
    op.drop_column("gs_fitness_state", "self_efficacy")


def downgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("self_efficacy", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("mobility_level", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("skeletal_muscular_level", sa.Float(), server_default="0.5", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("endurance_level", sa.Float(), server_default="0.5", nullable=False),
    )
    op.execute(
        """
        UPDATE gs_fitness_state
        SET
            endurance_level = endurance_capacity_score,
            skeletal_muscular_level = skeletal_capacity_score,
            mobility_level = mobility_capacity_score,
            self_efficacy = self_efficacy_score
        """
    )
    op.drop_column("gs_fitness_state", "stress_tolerance_score")
    op.drop_column("gs_fitness_state", "burnout_index")
    op.drop_column("gs_fitness_state", "self_efficacy_score")
    op.drop_column("gs_fitness_state", "mobility_capacity_score")
    op.drop_column("gs_fitness_state", "skeletal_capacity_score")
    op.drop_column("gs_fitness_state", "endurance_capacity_score")

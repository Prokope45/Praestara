"""persist fitness bias state

Revision ID: f6abbf023897
Revises: 1d456d33d35c
Create Date: 2026-02-27 16:41:33.636150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6abbf023897'
down_revision = '1d456d33d35c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("active_bias_domain", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("active_bias_strength", sa.Float(), server_default="0.0", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("bias_weeks_remaining", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("deload_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade():
    op.drop_column("gs_fitness_state", "deload_active")
    op.drop_column("gs_fitness_state", "bias_weeks_remaining")
    op.drop_column("gs_fitness_state", "active_bias_strength")
    op.drop_column("gs_fitness_state", "active_bias_domain")

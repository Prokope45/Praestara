"""add fitness session definitions

Revision ID: ddbf538dfac1
Revises: 2cc5acb9feff
Create Date: 2026-02-27 17:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ddbf538dfac1"
down_revision = "2cc5acb9feff"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gs_fitness_session_definition",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_index", sa.Integer(), nullable=False),
        sa.Column("total_estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("domain_minutes_breakdown", sa.JSON(), nullable=False),
        sa.Column("difficulty_rating", sa.Float(), nullable=False),
        sa.Column("notes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["gs_weekly_fitness_plan.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "gs_fitness_exercise_assignment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps_or_time", sa.String(length=120), nullable=False),
        sa.Column("rest_seconds", sa.Integer(), nullable=False),
        sa.Column("intensity_modifier", sa.Float(), nullable=False),
        sa.Column("scaling_variant", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["gs_fitness_session_definition.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("gs_fitness_exercise_assignment")
    op.drop_table("gs_fitness_session_definition")

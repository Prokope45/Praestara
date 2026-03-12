"""add fitness engagement models

Revision ID: 014459b76db9
Revises: ddbf538dfac1
Create Date: 2026-02-28 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "014459b76db9"
down_revision = "ddbf538dfac1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gs_fitness_state",
        sa.Column("active_weeks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "gs_fitness_state",
        sa.Column("active_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("gs_fitness_state", "active_weeks", server_default=None)
    op.alter_column("gs_fitness_state", "active_minutes", server_default=None)

    op.add_column(
        "gs_fitness_session_log",
        sa.Column("session_definition_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "gs_fitness_session_log",
        sa.Column("adherence_flag", sa.String(length=20), nullable=False, server_default="full"),
    )
    op.add_column(
        "gs_fitness_session_log",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "gs_fitness_session_log",
        sa.Column("executed_stress", sa.Float(), nullable=True),
    )
    op.create_foreign_key(
        "fk_gs_fitness_session_log_session_definition_id",
        "gs_fitness_session_log",
        "gs_fitness_session_definition",
        ["session_definition_id"],
        ["id"],
    )
    op.alter_column("gs_fitness_session_log", "adherence_flag", server_default=None)

    op.create_table(
        "gs_fitness_exposure_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("week_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("planned_stress", sa.Float(), nullable=False),
        sa.Column("executed_stress", sa.Float(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("adherence_flag", sa.String(length=20), nullable=False),
        sa.Column("energy_state_snapshot", sa.Float(), nullable=True),
        sa.Column("burnout_snapshot", sa.Float(), nullable=True),
        sa.Column("domain_distribution", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "gs_daily_projection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("projection_date", sa.Date(), nullable=False),
        sa.Column("weekly_goal_reference", sa.Uuid(), nullable=True),
        sa.Column("selected_commitments", sa.JSON(), nullable=False),
        sa.Column("constraint_snapshot", sa.JSON(), nullable=False),
        sa.Column("projected_difficulty", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "gs_daily_reflection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reflection_date", sa.Date(), nullable=False),
        sa.Column("commitments_completed", sa.JSON(), nullable=False),
        sa.Column("friction_reason", sa.String(length=50), nullable=True),
        sa.Column("constraint_mismatch_flag", sa.Boolean(), nullable=False),
        sa.Column("perceived_alignment_score", sa.Float(), nullable=False),
        sa.Column("exposure_event_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "gs_weekly_realignment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("week_id", sa.Uuid(), nullable=False),
        sa.Column("prior_target_sessions", sa.Integer(), nullable=False),
        sa.Column("adjusted_target_sessions", sa.Integer(), nullable=False),
        sa.Column("reason_for_adjustment", sa.String(length=50), nullable=True),
        sa.Column("constraint_changes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("gs_weekly_realignment")
    op.drop_table("gs_daily_reflection")
    op.drop_table("gs_daily_projection")
    op.drop_table("gs_fitness_exposure_event")

    op.drop_constraint(
        "fk_gs_fitness_session_log_session_definition_id",
        "gs_fitness_session_log",
        type_="foreignkey",
    )
    op.drop_column("gs_fitness_session_log", "executed_stress")
    op.drop_column("gs_fitness_session_log", "duration_minutes")
    op.drop_column("gs_fitness_session_log", "adherence_flag")
    op.drop_column("gs_fitness_session_log", "session_definition_id")

    op.drop_column("gs_fitness_state", "active_minutes")
    op.drop_column("gs_fitness_state", "active_weeks")

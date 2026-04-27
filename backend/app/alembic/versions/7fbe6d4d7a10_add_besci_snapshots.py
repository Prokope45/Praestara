"""add_besci_snapshots

Revision ID: 7fbe6d4d7a10
Revises: 25804c55c61c
Create Date: 2026-04-25 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "7fbe6d4d7a10"
down_revision = "25804c55c61c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "besci_snapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("checkin_sample_count", sa.Integer(), nullable=False),
        sa.Column("chat_sample_count", sa.Integer(), nullable=False),
        sa.Column("trajectory_score", sa.Float(), nullable=False),
        sa.Column("current_state", sa.JSON(), nullable=False),
        sa.Column("baseline_state", sa.JSON(), nullable=False),
        sa.Column("change_from_baseline", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_besci_snapshot_computed_at"), "besci_snapshot", ["computed_at"], unique=False)
    op.create_index(op.f("ix_besci_snapshot_user_id"), "besci_snapshot", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_besci_snapshot_user_id"), table_name="besci_snapshot")
    op.drop_index(op.f("ix_besci_snapshot_computed_at"), table_name="besci_snapshot")
    op.drop_table("besci_snapshot")

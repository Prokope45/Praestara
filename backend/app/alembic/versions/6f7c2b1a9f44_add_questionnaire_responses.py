"""Add questionnaire responses and onboarding flag

Revision ID: 6f7c2b1a9f44
Revises: 31a11dc7a422
Create Date: 2026-01-27 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f7c2b1a9f44"
down_revision = "31a11dc7a422"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "questionnaireresponse",
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("questionnaireresponse")
    op.drop_column("user", "onboarding_completed_at")

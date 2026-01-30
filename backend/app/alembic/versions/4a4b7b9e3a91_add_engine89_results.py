"""Add Engine89 results table

Revision ID: 4a4b7b9e3a91
Revises: 6f7c2b1a9f44
Create Date: 2026-01-27 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4a4b7b9e3a91"
down_revision = "6f7c2b1a9f44"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "engine89result",
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
    op.drop_table("engine89result")

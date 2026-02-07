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
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    if 'onboarding_completed_at' not in columns:
        op.add_column(
            "user",
            sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Check if table already exists before creating
    tables = inspector.get_table_names()
    if 'questionnaireresponse' in tables:
        # Table exists, check if it's the old simple version or new comprehensive version
        qr_columns = [col['name'] for col in inspector.get_columns('questionnaireresponse')]
        if 'assignment_id' in qr_columns:
            # This is the new comprehensive system, skip - it will be handled by merge migration
            pass
        # else: This is already the legacy table from a previous run, skip creation
    else:
        # Create the legacy questionnaireresponse table
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

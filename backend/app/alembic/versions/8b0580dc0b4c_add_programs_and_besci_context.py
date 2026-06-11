"""add_programs_and_besci_context

Revision ID: 8b0580dc0b4c
Revises: f6abbf023897
Create Date: 2026-06-07 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '8b0580dc0b4c'
down_revision = 'f6abbf023897'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- program table ---
    op.create_table(
        'program',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_program_name', 'program', ['name'])

    # --- program_membership table ---
    op.create_table(
        'program_membership',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('program_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='member'),
        sa.Column('is_graduated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('graduated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['program_id'], ['program.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('program_id', 'user_id', name='uq_program_membership'),
    )
    op.create_index('ix_program_membership_program_id', 'program_membership', ['program_id'])
    op.create_index('ix_program_membership_user_id', 'program_membership', ['user_id'])

    # --- extend gs_qualitative_observation.context enum to include new contexts ---
    # The context column is a varchar — new ObservationContext values work without DDL change.


def downgrade() -> None:
    op.drop_index('ix_program_membership_user_id', table_name='program_membership')
    op.drop_index('ix_program_membership_program_id', table_name='program_membership')
    op.drop_table('program_membership')
    op.drop_index('ix_program_name', table_name='program')
    op.drop_table('program')

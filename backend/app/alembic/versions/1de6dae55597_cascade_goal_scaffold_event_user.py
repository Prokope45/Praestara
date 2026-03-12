"""cascade goal_scaffold_event user

Revision ID: 1de6dae55597
Revises: 3af11da704ca
Create Date: 2026-02-27 15:02:42.428372

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '1de6dae55597'
down_revision = '3af11da704ca'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "goal_scaffold_event_user_id_fkey",
        "goal_scaffold_event",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "goal_scaffold_event_user_id_fkey",
        "goal_scaffold_event",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "goal_scaffold_event_user_id_fkey",
        "goal_scaffold_event",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "goal_scaffold_event_user_id_fkey",
        "goal_scaffold_event",
        "user",
        ["user_id"],
        ["id"],
    )

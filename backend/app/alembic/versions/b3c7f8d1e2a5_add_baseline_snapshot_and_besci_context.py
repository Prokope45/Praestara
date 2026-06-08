"""add baseline snapshot flag and besci context text

Revision ID: b3c7f8d1e2a5
Revises: a1f3c9e2d047
Create Date: 2026-06-07

- gs_self_concept_snapshot.is_baseline (bool, default False):
    Marks the snapshot taken at onboarding survey completion.
    All future snapshots are diffed against this to track growth.

- gs_user_resource_profile.besci_context_text (text, nullable):
    Structured user-profile string built from all survey answers.
    Prepended to every BeSci /mind-state call so the LLM interprets
    behavioral signals through this specific person's values, identity,
    coping patterns, and psychological baseline.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3c7f8d1e2a5"
down_revision = "a1f3c9e2d047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gs_self_concept_snapshot",
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "gs_user_resource_profile",
        sa.Column("besci_context_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gs_user_resource_profile", "besci_context_text")
    op.drop_column("gs_self_concept_snapshot", "is_baseline")

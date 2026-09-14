"""add index on workspaces.owner_id

Revision ID: 4c070f74c5a3
Revises: 6e071d2fd401
Create Date: 2026-09-14

"""

from typing import Sequence, Union

from alembic import op


revision: str = "4c070f74c5a3"
down_revision: Union[str, Sequence[str], None] = "6e071d2fd401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_workspaces_owner_id",
        "workspaces",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspaces_owner_id",
        table_name="workspaces",
    )

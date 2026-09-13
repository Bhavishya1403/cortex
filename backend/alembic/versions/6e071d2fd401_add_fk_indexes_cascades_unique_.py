"""add fk indexes cascades unique constraint role check

Revision ID: 6e071d2fd401
Revises: 6e14b55d2964
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6e071d2fd401'
down_revision: Union[str, Sequence[str], None] = '6e14b55d2964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _drop_fk_by_columns(inspector, table: str, local_cols: list[str]) -> None:
    """Find the (unnamed/auto-named) FK constraint on `table` whose local
    columns match `local_cols`, and drop it by its real, discovered name.
    Raises if none is found, so we fail loudly instead of silently no-op'ing."""
    for fk in inspector.get_foreign_keys(table):
        if set(fk["constrained_columns"]) == set(local_cols):
            op.drop_constraint(fk["name"], table, type_="foreignkey")
            return
    raise RuntimeError(f"No existing FK found on {table} for columns {local_cols}")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- documents.workspace_id ---
    _drop_fk_by_columns(inspector, "documents", ["workspace_id"])
    op.create_foreign_key(
        "fk_documents_workspace_id_workspaces",
        "documents", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])

    # --- chat_sessions.workspace_id ---
    _drop_fk_by_columns(inspector, "chat_sessions", ["workspace_id"])
    op.create_foreign_key(
        "fk_chat_sessions_workspace_id_workspaces",
        "chat_sessions", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_chat_sessions_workspace_id", "chat_sessions", ["workspace_id"])

    # --- chat_messages.session_id ---
    _drop_fk_by_columns(inspector, "chat_messages", ["session_id"])
    op.create_foreign_key(
        "fk_chat_messages_session_id_chat_sessions",
        "chat_messages", "chat_sessions",
        ["session_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # --- workspace_members.workspace_id ---
    _drop_fk_by_columns(inspector, "workspace_members", ["workspace_id"])
    op.create_foreign_key(
        "fk_workspace_members_workspace_id_workspaces",
        "workspace_members", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])

    # --- workspace_members.user_id ---
    _drop_fk_by_columns(inspector, "workspace_members", ["user_id"])
    op.create_foreign_key(
        "fk_workspace_members_user_id_users",
        "workspace_members", "users",
        ["user_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    # --- workspace_members: unique + check constraints ---
    op.create_unique_constraint(
        "uq_workspace_user", "workspace_members", ["workspace_id", "user_id"]
    )
    op.create_check_constraint(
        "ck_workspace_member_role", "workspace_members", "role IN ('admin', 'member')"
    )

    # --- usage_logs.user_id: nullable + SET NULL ---
    _drop_fk_by_columns(inspector, "usage_logs", ["user_id"])
    op.alter_column(
        "usage_logs", "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_usage_logs_user_id_users",
        "usage_logs", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])

    # --- usage_logs.workspace_id: SET NULL ---
    _drop_fk_by_columns(inspector, "usage_logs", ["workspace_id"])
    op.create_foreign_key(
        "fk_usage_logs_workspace_id_workspaces",
        "usage_logs", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_usage_logs_workspace_id", "usage_logs", ["workspace_id"])


def downgrade() -> None:
    # Reverse order of upgrade(): drop newest additions first, then restore
    # each FK to its original (no ondelete) behavior with an explicit name.

    # --- usage_logs.workspace_id: restore plain FK, no ondelete ---
    op.drop_constraint("fk_usage_logs_workspace_id_workspaces", "usage_logs", type_="foreignkey")
    op.drop_index("ix_usage_logs_workspace_id", table_name="usage_logs")
    op.create_foreign_key(
        "fk_usage_logs_workspace_id_workspaces",
        "usage_logs", "workspaces",
        ["workspace_id"], ["id"],
    )

    # --- usage_logs.user_id: restore plain FK + NOT NULL ---
    op.drop_constraint("fk_usage_logs_user_id_users", "usage_logs", type_="foreignkey")
    op.drop_index("ix_usage_logs_user_id", table_name="usage_logs")
    op.alter_column(
        "usage_logs", "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_usage_logs_user_id_users",
        "usage_logs", "users",
        ["user_id"], ["id"],
    )

    # --- workspace_members: drop check + unique constraints ---
    op.drop_constraint("ck_workspace_member_role", "workspace_members", type_="check")
    op.drop_constraint("uq_workspace_user", "workspace_members", type_="unique")

    # --- workspace_members.user_id: restore plain FK ---
    op.drop_constraint("fk_workspace_members_user_id_users", "workspace_members", type_="foreignkey")
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.create_foreign_key(
        "fk_workspace_members_user_id_users",
        "workspace_members", "users",
        ["user_id"], ["id"],
    )

    # --- workspace_members.workspace_id: restore plain FK ---
    op.drop_constraint("fk_workspace_members_workspace_id_workspaces", "workspace_members", type_="foreignkey")
    op.drop_index("ix_workspace_members_workspace_id", table_name="workspace_members")
    op.create_foreign_key(
        "fk_workspace_members_workspace_id_workspaces",
        "workspace_members", "workspaces",
        ["workspace_id"], ["id"],
    )

    # --- chat_messages.session_id: restore plain FK ---
    op.drop_constraint("fk_chat_messages_session_id_chat_sessions", "chat_messages", type_="foreignkey")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.create_foreign_key(
        "fk_chat_messages_session_id_chat_sessions",
        "chat_messages", "chat_sessions",
        ["session_id"], ["id"],
    )

    # --- chat_sessions.workspace_id: restore plain FK ---
    op.drop_constraint("fk_chat_sessions_workspace_id_workspaces", "chat_sessions", type_="foreignkey")
    op.drop_index("ix_chat_sessions_workspace_id", table_name="chat_sessions")
    op.create_foreign_key(
        "fk_chat_sessions_workspace_id_workspaces",
        "chat_sessions", "workspaces",
        ["workspace_id"], ["id"],
    )

    # --- documents.workspace_id: restore plain FK ---
    op.drop_constraint("fk_documents_workspace_id_workspaces", "documents", type_="foreignkey")
    op.drop_index("ix_documents_workspace_id", table_name="documents")
    op.create_foreign_key(
        "fk_documents_workspace_id_workspaces",
        "documents", "workspaces",
        ["workspace_id"], ["id"],
    )
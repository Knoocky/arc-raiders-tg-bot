from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_chat_timezone_settings"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_timezone_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("timezone", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", name="uq_chat_timezone_settings_chat"),
    )
    op.create_index(
        op.f("ix_chat_timezone_settings_chat_id"),
        "chat_timezone_settings",
        ["chat_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_timezone_settings_chat_id"), table_name="chat_timezone_settings")
    op.drop_table("chat_timezone_settings")

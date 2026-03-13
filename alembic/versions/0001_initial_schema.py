from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_catalog",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index(op.f("ix_event_catalog_canonical_name"), "event_catalog", ["canonical_name"], unique=False)
    op.create_index(op.f("ix_event_catalog_external_id"), "event_catalog", ["external_id"], unique=False)

    op.create_table(
        "map_catalog",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index(op.f("ix_map_catalog_canonical_name"), "map_catalog", ["canonical_name"], unique=False)
    op.create_index(op.f("ix_map_catalog_external_id"), "map_catalog", ["external_id"], unique=False)

    op.create_table(
        "chat_notification_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("minutes_before", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", "minutes_before", name="uq_chat_notification_settings_chat_minutes"),
    )
    op.create_index(
        op.f("ix_chat_notification_settings_chat_id"),
        "chat_notification_settings",
        ["chat_id"],
        unique=False,
    )

    op.create_table(
        "scheduled_events_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("event_catalog_id", sa.Integer(), nullable=True),
        sa.Column("map_catalog_id", sa.Integer(), nullable=True),
        sa.Column("event_display_name", sa.String(length=255), nullable=False),
        sa.Column("map_display_name", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_catalog_id"], ["event_catalog.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["map_catalog_id"], ["map_catalog.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id"),
    )
    op.create_index(op.f("ix_scheduled_events_cache_event_catalog_id"), "scheduled_events_cache", ["event_catalog_id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_cache_map_catalog_id"), "scheduled_events_cache", ["map_catalog_id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_cache_source_id"), "scheduled_events_cache", ["source_id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_cache_starts_at"), "scheduled_events_cache", ["starts_at"], unique=False)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("scope_type", sa.Enum("all", "map", "event", "event_map", name="subscriptionscope"), nullable=False),
        sa.Column("event_catalog_id", sa.Integer(), nullable=True),
        sa.Column("map_catalog_id", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_catalog_id"], ["event_catalog.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["map_catalog_id"], ["map_catalog.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_chat_id"), "subscriptions", ["chat_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_event_catalog_id"), "subscriptions", ["event_catalog_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_is_enabled"), "subscriptions", ["is_enabled"], unique=False)
    op.create_index(op.f("ix_subscriptions_map_catalog_id"), "subscriptions", ["map_catalog_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_scope_type"), "subscriptions", ["scope_type"], unique=False)

    op.create_table(
        "notification_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("scheduled_event_id", sa.Integer(), nullable=False),
        sa.Column("minutes_before", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scheduled_event_id"], ["scheduled_events_cache.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chat_id",
            "scheduled_event_id",
            "minutes_before",
            name="uq_notification_log_chat_event_minutes",
        ),
    )
    op.create_index(op.f("ix_notification_log_chat_id"), "notification_log", ["chat_id"], unique=False)
    op.create_index(
        op.f("ix_notification_log_scheduled_event_id"),
        "notification_log",
        ["scheduled_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_log_scheduled_event_id"), table_name="notification_log")
    op.drop_index(op.f("ix_notification_log_chat_id"), table_name="notification_log")
    op.drop_table("notification_log")

    op.drop_index(op.f("ix_subscriptions_scope_type"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_map_catalog_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_is_enabled"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_event_catalog_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_chat_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.execute("DROP TYPE subscriptionscope")

    op.drop_index(op.f("ix_scheduled_events_cache_starts_at"), table_name="scheduled_events_cache")
    op.drop_index(op.f("ix_scheduled_events_cache_source_id"), table_name="scheduled_events_cache")
    op.drop_index(op.f("ix_scheduled_events_cache_map_catalog_id"), table_name="scheduled_events_cache")
    op.drop_index(op.f("ix_scheduled_events_cache_event_catalog_id"), table_name="scheduled_events_cache")
    op.drop_table("scheduled_events_cache")

    op.drop_index(op.f("ix_chat_notification_settings_chat_id"), table_name="chat_notification_settings")
    op.drop_table("chat_notification_settings")

    op.drop_index(op.f("ix_map_catalog_external_id"), table_name="map_catalog")
    op.drop_index(op.f("ix_map_catalog_canonical_name"), table_name="map_catalog")
    op.drop_table("map_catalog")

    op.drop_index(op.f("ix_event_catalog_external_id"), table_name="event_catalog")
    op.drop_index(op.f("ix_event_catalog_canonical_name"), table_name="event_catalog")
    op.drop_table("event_catalog")

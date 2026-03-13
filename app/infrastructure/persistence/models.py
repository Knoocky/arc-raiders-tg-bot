from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.common.time_utils import utc_now
from app.domain.enums.subscription_scope import SubscriptionScope


class Base(DeclarativeBase):
    pass


def _enum_values(enum_cls: type[SubscriptionScope]) -> list[str]:
    return [item.value for item in enum_cls]


class EventCatalogModel(Base):
    __tablename__ = "event_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class MapCatalogModel(Base):
    __tablename__ = "map_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ScheduledEventCacheModel(Base):
    __tablename__ = "scheduled_events_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    event_catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    map_catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("map_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    map_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    event_catalog = relationship("EventCatalogModel")
    map_catalog = relationship("MapCatalogModel")


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    scope_type: Mapped[SubscriptionScope] = mapped_column(
        Enum(
            SubscriptionScope,
            native_enum=False,
            values_callable=_enum_values,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    event_catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    map_catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("map_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    event_catalog = relationship("EventCatalogModel")
    map_catalog = relationship("MapCatalogModel")


class ChatNotificationSettingModel(Base):
    __tablename__ = "chat_notification_settings"
    __table_args__ = (
        UniqueConstraint("chat_id", "minutes_before", name="uq_chat_notification_settings_chat_minutes"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    minutes_before: Mapped[int] = mapped_column(Integer, nullable=False)


class ChatTimezoneSettingModel(Base):
    __tablename__ = "chat_timezone_settings"
    __table_args__ = (
        UniqueConstraint("chat_id", name="uq_chat_timezone_settings_chat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(255), nullable=False)


class NotificationLogModel(Base):
    __tablename__ = "notification_log"
    __table_args__ = (
        UniqueConstraint(
            "chat_id",
            "scheduled_event_id",
            "minutes_before",
            name="uq_notification_log_chat_event_minutes",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    scheduled_event_id: Mapped[int] = mapped_column(
        ForeignKey("scheduled_events_cache.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    minutes_before: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    scheduled_event = relationship("ScheduledEventCacheModel")

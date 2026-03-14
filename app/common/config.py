from __future__ import annotations

import os
from typing import Self
from dotenv import load_dotenv

from pydantic import BaseModel, Field


class ProviderSettings(BaseModel):
    base_url: str = "https://metaforge.app/api/arc-raiders"
    schedule_path: str = "/events-schedule"
    events_catalog_path: str = "/events"
    timeout_seconds: float = 10.0


class SchedulerSettings(BaseModel):
    catalogs_refresh_minutes: int = 30
    schedule_refresh_minutes: int = 1
    notification_poll_seconds: int = 60


class AppSettings(BaseModel):
    bot_token: str | None = None
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/arc_raiders_bot"
    log_level: str = "INFO"
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)

    @classmethod
    def from_env(cls) -> Self:
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        env = os.environ
        return cls(
            bot_token=env.get("BOT_TOKEN"),
            database_url=env.get("DATABASE_URL", cls.model_fields["database_url"].default),
            log_level=env.get("LOG_LEVEL", cls.model_fields["log_level"].default),
            provider=ProviderSettings(
                base_url=env.get(
                    "PROVIDER_BASE_URL",
                    ProviderSettings.model_fields["base_url"].default,
                ),
                schedule_path=env.get(
                    "PROVIDER_SCHEDULE_PATH",
                    ProviderSettings.model_fields["schedule_path"].default,
                ),
                events_catalog_path=env.get(
                    "PROVIDER_EVENTS_CATALOG_PATH",
                    ProviderSettings.model_fields["events_catalog_path"].default,
                ),
                timeout_seconds=float(
                    env.get(
                        "PROVIDER_TIMEOUT_SECONDS",
                        ProviderSettings.model_fields["timeout_seconds"].default,
                    ),
                ),
            ),
            scheduler=SchedulerSettings(
                catalogs_refresh_minutes=int(
                    env.get(
                        "CATALOGS_REFRESH_MINUTES",
                        SchedulerSettings.model_fields["catalogs_refresh_minutes"].default,
                    ),
                ),
                schedule_refresh_minutes=int(
                    env.get(
                        "SCHEDULE_REFRESH_MINUTES",
                        SchedulerSettings.model_fields["schedule_refresh_minutes"].default,
                    ),
                ),
                notification_poll_seconds=int(
                    env.get(
                        "NOTIFICATION_POLL_SECONDS",
                        SchedulerSettings.model_fields["notification_poll_seconds"].default,
                    ),
                ),
            ),
        )

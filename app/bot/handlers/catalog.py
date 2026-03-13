from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.application.services.catalog_service import CatalogService


def register_catalog_handlers(
    router: Router,
    *,
    catalog_service: CatalogService,
) -> None:
    @router.message(Command("maps"))
    async def maps_handler(message: Message) -> None:
        maps_catalog = await catalog_service.list_maps_catalog()
        if not maps_catalog:
            await message.answer("Maps catalog is empty.")
            return
        await message.answer("Maps:\n" + "\n".join(f"- {map_item.display_name}" for map_item in maps_catalog))

    @router.message(Command("events_catalog"))
    async def events_catalog_handler(message: Message) -> None:
        events_catalog = await catalog_service.list_events_catalog()
        if not events_catalog:
            await message.answer("Events catalog is empty.")
            return
        await message.answer("Events:\n" + "\n".join(f"- {event.display_name}" for event in events_catalog))


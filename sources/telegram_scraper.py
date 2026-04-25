"""Telegram channel scraper using Telethon."""

from __future__ import annotations

import logging

from config import Settings
from models import Listing
from sources.base import BaseSource


logger = logging.getLogger(__name__)


class TelegramChannelSource(BaseSource):
    name = "Telegram"

    def __init__(self, settings: Settings) -> None:
        self.api_id = settings.telethon_api_id
        self.api_hash = settings.telethon_api_hash
        self.session_name = settings.telethon_session_name
        self.phone = settings.telethon_phone
        self.bot_token = settings.telegram_scraper_bot_token
        self.channels = settings.telegram_channels
        self.limit = settings.telegram_messages_per_channel
        self._client = None

    async def fetch(self) -> list[Listing]:
        if not self.channels:
            logger.warning("No Telegram channels configured; Telegram source disabled for this cycle")
            return []

        client = await self._get_client()
        if client is None:
            return []

        listings: list[Listing] = []
        for channel in self.channels:
            try:
                logger.info("Reading Telegram channel=%s", channel)
                entity = await client.get_entity(channel)
                username = getattr(entity, "username", None)
                async for message in client.iter_messages(entity, limit=self.limit):
                    text = message.message or ""
                    if not text.strip():
                        continue

                    title = self._title_from_message(text)
                    link = self._message_link(channel, username, message.id)
                    listings.append(
                        Listing(
                            title=title,
                            link=link,
                            price="",
                            source=self.name,
                            description=text,
                            location="",
                            raw={"channel": channel, "message_id": message.id},
                        )
                    )
            except Exception as exc:
                logger.exception("Telegram channel read failed for %s: %s", channel, exc)

        return listings

    async def _get_client(self):
        if not self.api_id or not self.api_hash:
            logger.warning("Telethon API ID/hash missing; Telegram source disabled for this cycle")
            return None

        try:
            from telethon import TelegramClient

            if self._client is None:
                self._client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                if self.bot_token:
                    await self._client.start(bot_token=self.bot_token)
                elif self.phone:
                    await self._client.start(phone=self.phone)
                else:
                    await self._client.start()
            elif not self._client.is_connected():
                await self._client.connect()

            return self._client
        except Exception as exc:
            logger.exception("Failed to initialize Telethon client: %s", exc)
            return None

    @staticmethod
    def _title_from_message(text: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_line[:160] if first_line else "Telegram message"

    @staticmethod
    def _message_link(channel: str, username: str | None, message_id: int) -> str:
        if username:
            return f"https://t.me/{username}/{message_id}"
        normalized_channel = channel.lstrip("@").replace("https://t.me/", "").replace("/", "_")
        return f"telegram:{normalized_channel}:{message_id}"

"""Telegram Bot API notification delivery."""

from __future__ import annotations

import logging

import requests

from config import Settings
from models import Listing


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends alerts through a Telegram bot."""

    def __init__(self, settings: Settings) -> None:
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.timeout = settings.request_timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_alert(self, listing: Listing) -> bool:
        if not self.configured:
            logger.warning("Telegram alert bot is not configured; skipping alert for %s", listing.link)
            return False

        message = (
            "🔥 PC/SERVER SCRAP FOUND\n\n"
            f"- Title: {listing.title}\n"
            f"- Source: {listing.source}\n"
            f"- Link: {listing.link}"
        )
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, data=payload, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.exception("Failed to send Telegram alert for %s: %s", listing.link, exc)
            return False

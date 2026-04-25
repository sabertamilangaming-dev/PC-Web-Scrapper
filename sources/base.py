"""Base interfaces and helpers for source scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models import Listing


class BaseSource(ABC):
    """All platform scrapers return normalized Listing objects."""

    name: str

    @abstractmethod
    async def fetch(self) -> list[Listing]:
        """Fetch recent listings/messages/posts from the source."""

"""Shared data models for scraper sources."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Listing:
    """Normalized listing shape used across all platforms."""

    title: str
    link: str
    source: str
    price: str = ""
    description: str = ""
    location: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def searchable_text(self) -> str:
        """Return all user-visible text that should participate in filtering."""
        return " ".join(
            part
            for part in (
                self.title,
                self.price,
                self.description,
                self.location,
                self.link,
            )
            if part
        )

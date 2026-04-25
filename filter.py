"""Strict PC/server component filtering rules."""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import Settings
from models import Listing


@dataclass(frozen=True)
class FilterDecision:
    matched: bool
    reason: str
    matched_components: tuple[str, ...] = ()


class ListingFilter:
    """Applies mandatory component, condition, and location checks."""

    NETWORK_COMPONENTS = {"switch", "router"}
    FREE_PRICE_RE = re.compile(r"(?<![0-9])(?:rs\.?|inr|₹)?\s*0+(?:\.0+)?(?![0-9])", re.IGNORECASE)

    def __init__(self, settings: Settings) -> None:
        self.component_patterns = self._compile_patterns(settings.component_keywords)
        self.condition_patterns = self._compile_patterns(settings.condition_keywords)
        self.location_patterns = self._compile_patterns(settings.location_keywords)
        self.excluded_patterns = self._compile_patterns(settings.excluded_keywords)
        self.enterprise_network_patterns = self._compile_patterns(settings.enterprise_network_keywords)

    def evaluate(self, listing: Listing) -> FilterDecision:
        text = self._normalize(listing.searchable_text())
        price_text = self._normalize(listing.price)

        excluded = self._matches(self.excluded_patterns, text)
        if excluded:
            return FilterDecision(False, f"excluded keyword: {excluded[0]}")

        matched_components = self._matches(self.component_patterns, text)
        if not matched_components:
            return FilterDecision(False, "missing mandatory component keyword")

        matched_conditions = self._matches(self.condition_patterns, text)
        is_free_price = bool(listing.price and self.FREE_PRICE_RE.search(price_text))
        if not matched_conditions and not is_free_price:
            return FilterDecision(False, "missing mandatory condition keyword")

        if self._network_only(matched_components) and not self._matches(self.enterprise_network_patterns, text):
            return FilterDecision(False, "network item lacks enterprise/server context")

        has_location = bool(self._matches(self.location_patterns, text))
        has_free_signal = "free" in matched_conditions or is_free_price
        if not has_location and not has_free_signal:
            return FilterDecision(False, "missing Chennai/Tamil Nadu location and not explicitly free")

        return FilterDecision(True, "matched", tuple(matched_components))

    def matches(self, listing: Listing) -> bool:
        return self.evaluate(listing).matched

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value.lower().replace("-", " ")).strip()

    @classmethod
    def _compile_patterns(cls, keywords: list[str]) -> dict[str, re.Pattern[str]]:
        return {keyword: cls._keyword_pattern(keyword) for keyword in keywords}

    @staticmethod
    def _keyword_pattern(keyword: str) -> re.Pattern[str]:
        normalized = re.escape(keyword.lower().replace("-", " "))
        normalized = normalized.replace(r"\ ", r"\s+")
        return re.compile(rf"(?<![a-z0-9]){normalized}(?![a-z0-9])", re.IGNORECASE)

    @staticmethod
    def _matches(patterns: dict[str, re.Pattern[str]], text: str) -> list[str]:
        return [keyword for keyword, pattern in patterns.items() if pattern.search(text)]

    def _network_only(self, matched_components: list[str]) -> bool:
        component_set = {component.lower() for component in matched_components}
        return bool(component_set) and component_set.issubset(self.NETWORK_COMPONENTS)

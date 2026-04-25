"""OLX HTML scraper for Chennai/Tamil Nadu focused search pages."""

from __future__ import annotations

import asyncio
import json
import logging
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from config import Settings
from models import Listing
from sources.base import BaseSource


logger = logging.getLogger(__name__)


class OLXSource(BaseSource):
    name = "OLX"

    def __init__(self, settings: Settings) -> None:
        self.search_url_template = settings.olx_search_url_template
        self.queries = settings.olx_search_queries
        self.delay_seconds = settings.olx_request_delay_seconds
        self.timeout = settings.request_timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9",
            }
        )

    async def fetch(self) -> list[Listing]:
        listings: list[Listing] = []
        seen_links: set[str] = set()

        for query in self.queries:
            await asyncio.sleep(self.delay_seconds)
            try:
                query_listings = self._fetch_query(query)
            except requests.RequestException as exc:
                logger.warning("OLX request failed for query %r: %s", query, exc)
                continue
            except Exception as exc:
                logger.exception("OLX parse failed for query %r: %s", query, exc)
                continue

            for listing in query_listings:
                if listing.link not in seen_links:
                    seen_links.add(listing.link)
                    listings.append(listing)

        return listings

    def _fetch_query(self, query: str) -> list[Listing]:
        url = self._build_search_url(query)
        logger.info("Scraping OLX query=%r url=%s", query, url)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self._parse_html(response.text, url)

    def _build_search_url(self, query: str) -> str:
        query_slug = quote_plus(query.strip().lower()).replace("+", "-")
        query_plus = quote_plus(query.strip())
        return self.search_url_template.format(
            query=query.strip(),
            query_slug=query_slug,
            query_plus=query_plus,
        )

    def _parse_html(self, html: str, source_url: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        listings = self._parse_item_cards(soup, source_url)

        if not listings:
            listings = self._parse_json_ld(soup, source_url)

        if not listings:
            listings = self._parse_anchor_fallback(soup, source_url)

        logger.info("OLX parsed %d candidate listings", len(listings))
        return listings

    def _parse_item_cards(self, soup: BeautifulSoup, source_url: str) -> list[Listing]:
        cards = soup.select('li[data-aut-id="itemBox"], div[data-aut-id="itemBox"]')
        listings: list[Listing] = []

        for card in cards:
            link_node = card.select_one("a[href]")
            title_node = card.select_one('[data-aut-id="itemTitle"], h2, h3')
            price_node = card.select_one('[data-aut-id="itemPrice"]')
            location_node = card.select_one('[data-aut-id="item-location"], [data-aut-id="itemLocation"]')

            if not link_node:
                continue

            link = self._absolute_url(str(link_node.get("href", "")), source_url)
            title = self._clean_text(title_node.get_text(" ", strip=True) if title_node else link_node.get_text(" ", strip=True))
            price = self._clean_text(price_node.get_text(" ", strip=True) if price_node else "")
            location = self._clean_text(location_node.get_text(" ", strip=True) if location_node else "")
            description = self._clean_text(card.get_text(" ", strip=True))

            if title and link:
                listings.append(
                    Listing(
                        title=title,
                        link=link,
                        price=price,
                        source=self.name,
                        description=description,
                        location=location,
                    )
                )

        return listings

    def _parse_json_ld(self, soup: BeautifulSoup, source_url: str) -> list[Listing]:
        listings: list[Listing] = []

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue

            items = payload.get("itemListElement", []) if isinstance(payload, dict) else []
            for item in items:
                product = item.get("item", item) if isinstance(item, dict) else {}
                if not isinstance(product, dict):
                    continue

                title = self._clean_text(str(product.get("name", "")))
                link = self._absolute_url(str(product.get("url", "")), source_url)
                offers = product.get("offers", {}) if isinstance(product.get("offers"), dict) else {}
                price = self._clean_text(str(offers.get("price", "")))

                if title and link:
                    listings.append(Listing(title=title, link=link, price=price, source=self.name))

        return listings

    def _parse_anchor_fallback(self, soup: BeautifulSoup, source_url: str) -> list[Listing]:
        listings: list[Listing] = []

        for anchor in soup.select('a[href*="/item/"]'):
            title = self._clean_text(anchor.get_text(" ", strip=True))
            link = self._absolute_url(str(anchor.get("href", "")), source_url)
            if title and link:
                listings.append(Listing(title=title, link=link, source=self.name, description=title))

        return listings

    @staticmethod
    def _absolute_url(href: str, source_url: str) -> str:
        if not href:
            return ""
        return urljoin(source_url, href.split("?")[0])

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(value.split())

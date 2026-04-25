"""Main orchestrator for the PC/server scrap finder."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Iterable

from config import Settings, settings
from db import ListingDatabase
from filter import ListingFilter
from models import Listing
from notifier import TelegramNotifier
from sources.base import BaseSource
from sources.olx import OLXSource
from sources.reddit import RedditSource
from sources.telegram_scraper import TelegramChannelSource


logger = logging.getLogger(__name__)


def configure_logging(app_settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_sources(app_settings: Settings) -> list[BaseSource]:
    sources: list[BaseSource] = []
    if app_settings.enable_olx:
        sources.append(OLXSource(app_settings))
    if app_settings.enable_reddit:
        sources.append(RedditSource(app_settings))
    if app_settings.enable_telegram_scraper:
        sources.append(TelegramChannelSource(app_settings))
    return sources


async def fetch_source(source: BaseSource) -> list[Listing]:
    try:
        listings = await source.fetch()
        logger.info("%s returned %d candidate listings", source.name, len(listings))
        return listings
    except Exception as exc:
        logger.exception("%s source failed without stopping the cycle: %s", source.name, exc)
        return []


async def run_cycle(
    sources: Iterable[BaseSource],
    listing_filter: ListingFilter,
    db: ListingDatabase,
    notifier: TelegramNotifier,
) -> None:
    logger.info("Starting scrape cycle")
    new_alerts = 0
    matched_duplicates = 0
    rejected = 0

    for source in sources:
        listings = await fetch_source(source)
        for listing in listings:
            decision = listing_filter.evaluate(listing)
            if not decision.matched:
                rejected += 1
                logger.debug("Rejected %s from %s: %s", listing.link, listing.source, decision.reason)
                continue

            if not db.insert_listing(listing):
                matched_duplicates += 1
                logger.info("Duplicate matched listing skipped: %s", listing.link)
                continue

            sent = notifier.send_alert(listing)
            new_alerts += 1
            logger.info(
                "New matched listing %salerted: source=%s title=%r components=%s link=%s",
                "" if sent else "stored but not ",
                listing.source,
                listing.title,
                ",".join(decision.matched_components),
                listing.link,
            )

    logger.info(
        "Finished scrape cycle | new=%d duplicates=%d rejected=%d",
        new_alerts,
        matched_duplicates,
        rejected,
    )


async def run_forever(app_settings: Settings) -> None:
    configure_logging(app_settings)
    db = ListingDatabase(app_settings.database_path)
    listing_filter = ListingFilter(app_settings)
    notifier = TelegramNotifier(app_settings)
    sources = build_sources(app_settings)

    if not sources:
        logger.warning("No sources are enabled")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    while not stop_event.is_set():
        await run_cycle(sources, listing_filter, db, notifier)
        logger.info("Sleeping for %d seconds", app_settings.scrape_interval_seconds)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=app_settings.scrape_interval_seconds)
        except asyncio.TimeoutError:
            continue

    logger.info("Shutdown requested; exiting")


if __name__ == "__main__":
    asyncio.run(run_forever(settings))

"""Reddit scraper using PRAW."""

from __future__ import annotations

import asyncio
import logging

from config import Settings
from models import Listing
from sources.base import BaseSource


logger = logging.getLogger(__name__)


class RedditSource(BaseSource):
    name = "Reddit"

    def __init__(self, settings: Settings) -> None:
        self.client_id = settings.reddit_client_id
        self.client_secret = settings.reddit_client_secret
        self.user_agent = settings.reddit_user_agent
        self.subreddits = settings.reddit_subreddits
        self.queries = settings.reddit_search_queries
        self.limit_per_query = settings.reddit_limit_per_query
        self.delay_seconds = settings.reddit_request_delay_seconds
        self._reddit = None

    async def fetch(self) -> list[Listing]:
        reddit = self._get_client()
        if reddit is None:
            return []

        subreddit_name = "+".join(self.subreddits)
        subreddit = reddit.subreddit(subreddit_name)
        listings: list[Listing] = []
        seen_links: set[str] = set()

        for query in self.queries:
            await asyncio.sleep(self.delay_seconds)
            logger.info("Searching Reddit subreddits=%s query=%r", subreddit_name, query)
            try:
                submissions = subreddit.search(query, sort="new", time_filter="month", limit=self.limit_per_query)
                for submission in submissions:
                    link = f"https://www.reddit.com{submission.permalink}"
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    listings.append(
                        Listing(
                            title=submission.title or "",
                            link=link,
                            price="",
                            source=self.name,
                            description=getattr(submission, "selftext", "") or "",
                            location="",
                            raw={"id": submission.id, "subreddit": str(submission.subreddit)},
                        )
                    )
            except Exception as exc:
                logger.exception("Reddit search failed for query %r: %s", query, exc)

        return listings

    def _get_client(self):
        if self._reddit is not None:
            return self._reddit

        if not self.client_id or not self.client_secret or not self.user_agent:
            logger.warning("Reddit credentials are missing; Reddit source disabled for this cycle")
            return None

        try:
            import praw

            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            self._reddit.read_only = True
            return self._reddit
        except Exception as exc:
            logger.exception("Failed to initialize Reddit client: %s", exc)
            return None

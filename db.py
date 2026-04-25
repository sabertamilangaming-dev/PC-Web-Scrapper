"""SQLite storage for deduplicating listings before alerting."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from models import Listing


class ListingDatabase:
    """Small SQLite wrapper around the listings table."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    link TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    price TEXT,
                    source TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_listing(self, listing: Listing) -> bool:
        """Insert a listing and return True only when it has not been seen before."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO listings (link, title, price, source)
                VALUES (?, ?, ?, ?)
                """,
                (listing.link, listing.title, listing.price, listing.source),
            )
            conn.commit()
            return cursor.rowcount == 1

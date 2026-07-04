"""SQLite-backed implementation of :class:`CacheRepository`."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from codepulse.domain.exceptions import CacheError
from codepulse.domain.interfaces.cache_repository import CacheRepository
from codepulse.domain.models.cache_entry import CacheEntry
from codepulse.infrastructure.persistence.database import ensure_schema


class SqliteCacheRepository(CacheRepository):
    """Stores JSON payloads in a single-table SQLite database.

    A corrupt row (invalid JSON, written by some future incompatible version
    for instance) is treated as a cache miss rather than a fatal error: it is
    deleted and ``None`` is returned, so the caller falls back to a fresh
    fetch instead of crashing.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        ensure_schema(db_path)

    def get(self, key: str) -> CacheEntry | None:
        try:
            with closing(sqlite3.connect(self._db_path)) as connection:
                row = connection.execute(
                    "SELECT payload, updated_at FROM cache_entries WHERE key = ?",
                    (key,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise CacheError(f"Failed to read cache entry {key!r}") from exc

        if row is None:
            return None

        raw_payload, raw_updated_at = row
        try:
            payload: dict[str, Any] = json.loads(raw_payload)
            updated_at = datetime.fromisoformat(raw_updated_at)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupt cache entry for key {!r}; discarding", key)
            self.clear(key)
            return None

        return CacheEntry(key=key, payload=payload, updated_at=updated_at)

    def set(self, key: str, payload: dict[str, Any]) -> None:
        try:
            with closing(sqlite3.connect(self._db_path)) as connection:
                connection.execute(
                    """
                    INSERT INTO cache_entries (key, payload, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        payload = excluded.payload,
                        updated_at = excluded.updated_at
                    """,
                    (key, json.dumps(payload), datetime.now(UTC).isoformat()),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise CacheError(f"Failed to write cache entry {key!r}") from exc

    def is_stale(self, key: str, max_age: timedelta) -> bool:
        entry = self.get(key)
        if entry is None:
            return True
        return datetime.now(UTC) - entry.updated_at > max_age

    def clear(self, key: str) -> None:
        try:
            with closing(sqlite3.connect(self._db_path)) as connection:
                connection.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                connection.commit()
        except sqlite3.Error as exc:
            raise CacheError(f"Failed to clear cache entry {key!r}") from exc

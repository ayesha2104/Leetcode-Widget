"""Abstract port for persisted, offline-capable caching.

Implemented by :class:`codepulse.infrastructure.persistence.sqlite_cache_repository.SqliteCacheRepository`.
The application layer depends only on this interface, never on SQLite
directly, so the storage backend can change without touching use cases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from codepulse.domain.models.cache_entry import CacheEntry


class CacheRepository(ABC):
    """Stores and retrieves JSON-serializable payloads by key."""

    @abstractmethod
    def get(self, key: str) -> CacheEntry | None:
        """Return the cached entry for ``key``, or ``None`` if absent or corrupt."""

    @abstractmethod
    def set(self, key: str, payload: dict[str, Any]) -> None:
        """Store ``payload`` under ``key``, overwriting any existing entry."""

    @abstractmethod
    def is_stale(self, key: str, max_age: timedelta) -> bool:
        """Return ``True`` if ``key`` is missing or older than ``max_age``."""

    @abstractmethod
    def clear(self, key: str) -> None:
        """Remove the cached entry for ``key``, if any."""

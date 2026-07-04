"""Orchestrates fetching a full dashboard snapshot and caching it.

Implements the offline-first flow from docs/architecture.md: callers load
the cached snapshot instantly for a non-empty first paint via
:meth:`get_cached_snapshot`, then trigger :meth:`refresh_snapshot` in the
background (from a QThread worker, per the threading model) to get live
data and repopulate the cache.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.exceptions import ProviderError
from codepulse.domain.interfaces.cache_repository import CacheRepository
from codepulse.domain.interfaces.provider import ProviderInterface
from codepulse.domain.models.streak import Streak

_CACHE_KEY_TEMPLATE = "{provider}:{username}:snapshot"
DEFAULT_CACHE_DURATION = timedelta(minutes=30)


class StatsService:
    """Fetches and caches a :class:`DashboardSnapshot` for a given username."""

    def __init__(
        self,
        provider: ProviderInterface,
        cache: CacheRepository,
        *,
        provider_name: str,
        cache_duration: timedelta = DEFAULT_CACHE_DURATION,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._provider_name = provider_name
        self._cache_duration = cache_duration

    def _cache_key(self, username: str) -> str:
        return _CACHE_KEY_TEMPLATE.format(provider=self._provider_name, username=username.lower())

    def get_cached_snapshot(self, username: str) -> DashboardSnapshot | None:
        """Return the last cached snapshot for ``username``, if any. No network calls."""
        entry = self._cache.get(self._cache_key(username))
        if entry is None:
            return None
        return DashboardSnapshot.model_validate(entry.payload)

    def is_cache_stale(self, username: str) -> bool:
        """Whether the cached snapshot is missing or older than the cache duration."""
        return self._cache.is_stale(self._cache_key(username), self._cache_duration)

    async def _fetch_streak_or_default(self, username: str) -> Streak:
        # Some accounts (e.g. official/system profiles) restrict calendar
        # access even on LeetCode's public API ("no permission to check the
        # calendar"), confirmed against the live API during development.
        # Streak is a nice-to-have, not core profile data, so degrade to
        # zeros instead of failing the whole refresh over it.
        try:
            return await self._provider.get_streak(username)
        except ProviderError as exc:
            logger.warning("Could not fetch streak for {}: {}", username, exc)
            return Streak()

    async def refresh_snapshot(self, username: str) -> DashboardSnapshot:
        """Fetch fresh data from the provider (concurrently), cache it, and return it."""
        profile, stats, streak, daily_challenge, contest_info = await asyncio.gather(
            self._provider.get_profile(username),
            self._provider.get_stats(username),
            self._fetch_streak_or_default(username),
            self._provider.get_daily_challenge(),
            self._provider.get_contest_info(username),
        )

        snapshot = DashboardSnapshot(
            profile=profile,
            stats=stats,
            streak=streak,
            daily_challenge=daily_challenge,
            contest_info=contest_info,
            fetched_at=datetime.now(UTC),
        )
        self._cache.set(self._cache_key(username), snapshot.model_dump(mode="json"))
        logger.info("Refreshed dashboard snapshot for {}:{}", self._provider_name, username)
        return snapshot

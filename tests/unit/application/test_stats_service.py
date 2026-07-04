from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from codepulse.application.services.stats_service import StatsService
from codepulse.domain.exceptions import ProviderError
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.infrastructure.persistence.sqlite_cache_repository import SqliteCacheRepository


class _FakeProvider:
    """A minimal ProviderInterface implementation returning canned data."""

    async def get_profile(self, username: str) -> Profile:
        return Profile(username=username)

    async def get_stats(self, username: str) -> Stats:
        return Stats(
            easy_solved=20, medium_solved=15, hard_solved=7, total_solved=42, acceptance_rate=60.0
        )

    async def get_contest_info(self, username: str) -> ContestInfo | None:
        return ContestInfo(rating=1500.0, attended_contests_count=3)

    async def get_daily_challenge(self) -> DailyChallenge:
        return DailyChallenge(
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            acceptance_rate=55.0,
            url="https://leetcode.com/problems/two-sum/",
            challenge_date=date(2026, 7, 4),
        )

    async def get_streak(self, username: str) -> Streak:
        return Streak(current_streak=5, longest_streak=10, total_active_days=100)


class _StreakRestrictedProvider(_FakeProvider):
    """Mimics an account whose calendar LeetCode itself refuses to expose."""

    async def get_streak(self, username: str) -> Streak:
        raise ProviderError("no permission to check the calendar.")


@pytest.fixture
def cache(tmp_path: Path) -> SqliteCacheRepository:
    return SqliteCacheRepository(tmp_path / "cache.db")


@pytest.fixture
def service(cache: SqliteCacheRepository) -> StatsService:
    return StatsService(
        _FakeProvider(), cache, provider_name="leetcode", cache_duration=timedelta(minutes=30)
    )


def test_get_cached_snapshot_returns_none_when_nothing_cached(service: StatsService) -> None:
    assert service.get_cached_snapshot("octocat") is None


def test_is_cache_stale_true_before_any_refresh(service: StatsService) -> None:
    assert service.is_cache_stale("octocat") is True


async def test_refresh_snapshot_fetches_all_pieces_concurrently(service: StatsService) -> None:
    snapshot = await service.refresh_snapshot("octocat")

    assert snapshot.profile.username == "octocat"
    assert snapshot.stats.total_solved == 42
    assert snapshot.streak.current_streak == 5
    assert snapshot.daily_challenge.title == "Two Sum"
    assert snapshot.contest_info is not None
    assert snapshot.contest_info.rating == 1500.0


async def test_cached_snapshot_round_trips_after_refresh(service: StatsService) -> None:
    await service.refresh_snapshot("octocat")

    cached = service.get_cached_snapshot("octocat")

    assert cached is not None
    assert cached.stats.total_solved == 42
    assert cached.daily_challenge.challenge_date == date(2026, 7, 4)


async def test_is_cache_stale_false_immediately_after_refresh(service: StatsService) -> None:
    await service.refresh_snapshot("octocat")

    assert service.is_cache_stale("octocat") is False


async def test_cache_keys_are_case_insensitive(service: StatsService) -> None:
    await service.refresh_snapshot("Octocat")

    assert service.get_cached_snapshot("octocat") is not None


async def test_different_usernames_get_independent_cache_entries(service: StatsService) -> None:
    await service.refresh_snapshot("octocat")

    assert service.get_cached_snapshot("someone-else") is None


async def test_refresh_snapshot_degrades_streak_to_zero_instead_of_failing(
    cache: SqliteCacheRepository,
) -> None:
    service = StatsService(_StreakRestrictedProvider(), cache, provider_name="leetcode")

    snapshot = await service.refresh_snapshot("leetcode")

    assert snapshot.streak == Streak()
    assert snapshot.profile.username == "leetcode"

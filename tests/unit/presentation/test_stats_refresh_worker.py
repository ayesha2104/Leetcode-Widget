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
from codepulse.presentation.workers.stats_refresh_worker import StatsRefreshWorker


class _FakeProvider:
    async def get_profile(self, username: str) -> Profile:
        return Profile(username=username)

    async def get_stats(self, username: str) -> Stats:
        return Stats(total_solved=10, acceptance_rate=50.0)

    async def get_contest_info(self, username: str) -> ContestInfo | None:
        return None

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
        return Streak(current_streak=3, longest_streak=5, total_active_days=20)


class _FailingProvider(_FakeProvider):
    async def get_stats(self, username: str) -> Stats:
        raise ProviderError("boom")


@pytest.fixture
def service(tmp_path: Path) -> StatsService:
    cache = SqliteCacheRepository(tmp_path / "cache.db")
    return StatsService(
        _FakeProvider(), cache, provider_name="leetcode", cache_duration=timedelta(minutes=30)
    )


@pytest.fixture
def failing_service(tmp_path: Path) -> StatsService:
    cache = SqliteCacheRepository(tmp_path / "cache.db")
    return StatsService(
        _FailingProvider(), cache, provider_name="leetcode", cache_duration=timedelta(minutes=30)
    )


def test_worker_emits_snapshot_ready_on_success(qtbot, service: StatsService) -> None:
    worker = StatsRefreshWorker(service, "octocat")

    with qtbot.waitSignal(worker.snapshot_ready, timeout=5000) as blocker:
        worker.start()

    (snapshot,) = blocker.args
    assert snapshot.profile.username == "octocat"
    assert snapshot.stats.total_solved == 10
    worker.wait()


def test_worker_emits_refresh_failed_on_provider_error(
    qtbot, failing_service: StatsService
) -> None:
    worker = StatsRefreshWorker(failing_service, "octocat")

    with qtbot.waitSignal(worker.refresh_failed, timeout=5000) as blocker:
        worker.start()

    assert blocker.args == ["boom"]
    worker.wait()

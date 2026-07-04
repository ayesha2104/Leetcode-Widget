from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.services.goal_service import GoalService
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.goal import GoalMetric
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository


@pytest.fixture
def service(tmp_path: Path) -> GoalService:
    return GoalService(JsonGoalRepository(tmp_path / "goals.json"))


def _make_snapshot(*, contest_info: ContestInfo | None = None) -> DashboardSnapshot:
    return DashboardSnapshot(
        profile=Profile(username="octocat"),
        stats=Stats(easy_solved=100, medium_solved=80, hard_solved=20, total_solved=200),
        streak=Streak(current_streak=12, longest_streak=40, total_active_days=90),
        daily_challenge=DailyChallenge(
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            acceptance_rate=55.0,
            url="https://leetcode.com/problems/two-sum/",
            challenge_date=date(2026, 7, 4),
        ),
        contest_info=contest_info,
        fetched_at=datetime.now(UTC),
    )


def test_list_goals_empty_by_default(service: GoalService) -> None:
    assert service.list_goals() == []


def test_add_goal_persists_and_returns_it(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    assert goal.target == 500
    assert service.list_goals() == [goal]


def test_remove_goal_deletes_it(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    service.remove_goal(goal.uid)

    assert service.list_goals() == []


def test_remove_goal_ignores_unknown_uid(service: GoalService) -> None:
    service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    service.remove_goal("does-not-exist")  # must not raise

    assert len(service.list_goals()) == 1


def test_compute_progress_without_snapshot_is_zero(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    progress = service.compute_progress(goal, None)

    assert progress.current_value == 0
    assert progress.percent == 0.0


def test_compute_progress_total_solved(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    progress = service.compute_progress(goal, _make_snapshot())

    assert progress.current_value == 200
    assert progress.percent == 40.0


def test_compute_progress_hard_solved(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.HARD_SOLVED, 100)

    progress = service.compute_progress(goal, _make_snapshot())

    assert progress.current_value == 20
    assert progress.percent == 20.0


def test_compute_progress_streak(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.STREAK, 30)

    progress = service.compute_progress(goal, _make_snapshot())

    assert progress.current_value == 12
    assert progress.percent == 40.0


def test_compute_progress_rating_with_contest_info(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.RATING, 1000)

    progress = service.compute_progress(goal, _make_snapshot(contest_info=ContestInfo(rating=750)))

    assert progress.current_value == 750
    assert progress.percent == 75.0


def test_compute_progress_rating_without_contest_info(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.RATING, 1000)

    progress = service.compute_progress(goal, _make_snapshot(contest_info=None))

    assert progress.current_value == 0


def test_compute_progress_caps_percent_at_100(service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 50)

    progress = service.compute_progress(goal, _make_snapshot())  # 200 solved > 50 target

    assert progress.percent == 100.0

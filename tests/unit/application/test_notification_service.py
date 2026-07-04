from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.application.services.notification_service import NotificationService
from codepulse.domain.interfaces.notifier import Notifier
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.goal import Goal, GoalMetric
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.infrastructure.persistence.json_notification_state_repository import (
    JsonNotificationStateRepository,
)


class _RecordingNotifier(Notifier):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def notify(self, title: str, message: str) -> None:
        self.calls.append((title, message))


@pytest.fixture
def notifier() -> _RecordingNotifier:
    return _RecordingNotifier()


@pytest.fixture
def state_repository(tmp_path: Path) -> JsonNotificationStateRepository:
    return JsonNotificationStateRepository(tmp_path / "state.json")


@pytest.fixture
def service(
    notifier: _RecordingNotifier, state_repository: JsonNotificationStateRepository
) -> NotificationService:
    return NotificationService(notifier, state_repository)


def _make_snapshot(*, current_streak: int, longest_streak: int) -> DashboardSnapshot:
    return DashboardSnapshot(
        profile=Profile(username="octocat"),
        stats=Stats(total_solved=100, acceptance_rate=60.0),
        streak=Streak(
            current_streak=current_streak, longest_streak=longest_streak, total_active_days=50
        ),
        daily_challenge=DailyChallenge(
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            acceptance_rate=55.0,
            url="https://leetcode.com/problems/two-sum/",
            challenge_date=date(2026, 7, 4),
        ),
        contest_info=ContestInfo(rating=1500.0),
        fetched_at=datetime.now(UTC),
    )


def test_streak_record_fires_when_current_equals_longest(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))

    assert any("streak record" in title.lower() for title, _ in notifier.calls)


def test_streak_record_does_not_fire_below_longest(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.on_snapshot_updated(_make_snapshot(current_streak=5, longest_streak=10))

    assert not any("streak record" in title.lower() for title, _ in notifier.calls)


def test_streak_record_does_not_fire_twice_for_same_value(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))
    service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))

    streak_calls = [c for c in notifier.calls if "streak record" in c[0].lower()]
    assert len(streak_calls) == 1


def test_streak_record_refires_for_a_higher_streak(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))
    service.on_snapshot_updated(_make_snapshot(current_streak=11, longest_streak=11))

    streak_calls = [c for c in notifier.calls if "streak record" in c[0].lower()]
    assert len(streak_calls) == 2


def test_daily_reminder_fires_once_per_day(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.on_snapshot_updated(_make_snapshot(current_streak=0, longest_streak=5))
    service.on_snapshot_updated(_make_snapshot(current_streak=0, longest_streak=5))

    reminder_calls = [c for c in notifier.calls if c[0] == "Daily Challenge"]
    assert len(reminder_calls) == 1


def test_disabled_service_sends_no_notifications(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    service.set_enabled(False)

    service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))

    assert notifier.calls == []


def test_goal_achieved_fires_when_percent_reaches_100(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    goal = Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=100)
    progress = GoalProgress(goal=goal, current_value=100, percent=100.0)

    service.on_goal_progress_updated([progress])

    assert any("goal achieved" in title.lower() for title, _ in notifier.calls)


def test_goal_achieved_does_not_fire_below_100_percent(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    goal = Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=100)
    progress = GoalProgress(goal=goal, current_value=50, percent=50.0)

    service.on_goal_progress_updated([progress])

    assert notifier.calls == []


def test_goal_achieved_does_not_refire_for_the_same_goal(
    service: NotificationService, notifier: _RecordingNotifier
) -> None:
    goal = Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=100)
    progress = GoalProgress(goal=goal, current_value=100, percent=100.0)

    service.on_goal_progress_updated([progress])
    service.on_goal_progress_updated([progress])

    achieved_calls = [c for c in notifier.calls if "goal achieved" in c[0].lower()]
    assert len(achieved_calls) == 1


def test_state_persists_across_service_instances(
    notifier: _RecordingNotifier, state_repository: JsonNotificationStateRepository
) -> None:
    first_service = NotificationService(notifier, state_repository)
    first_service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))

    second_service = NotificationService(notifier, state_repository)
    second_service.on_snapshot_updated(_make_snapshot(current_streak=10, longest_streak=10))

    streak_calls = [c for c in notifier.calls if "streak record" in c[0].lower()]
    assert len(streak_calls) == 1  # second instance sees the persisted state, doesn't refire

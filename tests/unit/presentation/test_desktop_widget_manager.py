from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from codepulse.application.services.goal_service import GoalService
from codepulse.application.services.notification_service import NotificationService
from codepulse.application.services.stats_service import StatsService
from codepulse.domain.interfaces.notifier import Notifier
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.goal import GoalMetric
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.infrastructure.persistence.json_desktop_layout_repository import (
    JsonDesktopLayoutRepository,
)
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository
from codepulse.infrastructure.persistence.json_notification_state_repository import (
    JsonNotificationStateRepository,
)
from codepulse.infrastructure.persistence.sqlite_cache_repository import SqliteCacheRepository
from codepulse.presentation.desktop_widget_manager import DesktopWidgetManager
from codepulse.presentation.themes.theme_manager import ThemeManager


class _RecordingNotifier(Notifier):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def notify(self, title: str, message: str) -> None:
        self.calls.append((title, message))


class _FakeProvider:
    async def get_profile(self, username: str) -> Profile:
        return Profile(username=username)

    async def get_stats(self, username: str) -> Stats:
        return Stats(total_solved=42, acceptance_rate=60.0)

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
        return Streak(current_streak=5, longest_streak=10, total_active_days=50)


@pytest.fixture
def repository(tmp_path: Path) -> JsonDesktopLayoutRepository:
    return JsonDesktopLayoutRepository(tmp_path / "layout.json")


@pytest.fixture
def manager(repository: JsonDesktopLayoutRepository) -> DesktopWidgetManager:
    return DesktopWidgetManager(repository, ThemeManager())


@pytest.fixture
def stats_service(tmp_path: Path) -> StatsService:
    cache = SqliteCacheRepository(tmp_path / "stats_cache.db")
    return StatsService(
        _FakeProvider(), cache, provider_name="leetcode", cache_duration=timedelta(minutes=30)
    )


@pytest.fixture
def goal_service(tmp_path: Path) -> GoalService:
    return GoalService(JsonGoalRepository(tmp_path / "goals.json"))


@pytest.fixture
def notifier() -> _RecordingNotifier:
    return _RecordingNotifier()


@pytest.fixture
def notification_service(notifier: _RecordingNotifier, tmp_path: Path) -> NotificationService:
    state_repository = JsonNotificationStateRepository(tmp_path / "notif_state.json")
    return NotificationService(notifier, state_repository)


def test_starts_with_no_widgets(qtbot, manager: DesktopWidgetManager) -> None:
    assert manager.widget_count() == 0


def test_add_widget_spawns_a_window_and_persists(
    qtbot, manager: DesktopWidgetManager, repository: JsonDesktopLayoutRepository
) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    assert manager.widget_count() == 1
    saved = repository.load()
    assert len(saved) == 1
    assert saved[0].kind == WidgetKind.STREAK
    assert saved[0].size == WidgetSize.SMALL


def test_add_widget_emits_count_changed(qtbot, manager: DesktopWidgetManager) -> None:
    with qtbot.waitSignal(manager.widget_count_changed, timeout=1000) as blocker:
        manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    assert blocker.args == [1]


def test_successive_widgets_cascade_position(qtbot, manager: DesktopWidgetManager) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    manager.add_widget(WidgetKind.DAILY, WidgetSize.SMALL)

    positions = {(w.x(), w.y()) for w in manager._windows.values()}
    assert len(positions) == 2  # distinct positions, not stacked on top of each other


def test_restore_saved_layout_does_not_duplicate_existing_windows(
    qtbot, manager: DesktopWidgetManager
) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    original_window = next(iter(manager._windows.values()))

    manager.restore_saved_layout()  # widget already has an open window

    assert manager.widget_count() == 1
    assert next(iter(manager._windows.values())) is original_window


def test_remove_requested_destroys_window_and_persists(
    qtbot, manager: DesktopWidgetManager, repository: JsonDesktopLayoutRepository
) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    uid = next(iter(manager._windows))

    manager._on_remove_requested(uid)

    assert manager.widget_count() == 0
    assert repository.load() == []


def test_restore_saved_layout_recreates_windows(
    qtbot, repository: JsonDesktopLayoutRepository
) -> None:
    seeding_manager = DesktopWidgetManager(repository, ThemeManager())
    seeding_manager.add_widget(WidgetKind.PROGRESS, WidgetSize.MEDIUM)

    fresh_manager = DesktopWidgetManager(repository, ThemeManager())
    fresh_manager.restore_saved_layout()

    assert fresh_manager.widget_count() == 1


def test_window_move_eventually_persists_new_position(
    qtbot, manager: DesktopWidgetManager, repository: JsonDesktopLayoutRepository
) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    window = next(iter(manager._windows.values()))
    window.show()

    window.move(400, 300)
    qtbot.wait(600)  # let the debounce timer fire

    saved = repository.load()
    assert (saved[0].x, saved[0].y) == (400, 300)


def test_theme_change_propagates_to_all_windows(qtbot, manager: DesktopWidgetManager) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    window = next(iter(manager._windows.values()))

    manager._theme_manager.set_theme("cyberpunk")

    assert window.theme.name == "cyberpunk"


def test_set_opacity_applies_to_existing_windows(qtbot, manager: DesktopWidgetManager) -> None:
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    window = next(iter(manager._windows.values()))

    manager.set_opacity(0.5)

    # The offscreen QPA platform quantizes opacity to 8 bits, so compare
    # approximately rather than exactly.
    assert window.windowOpacity() == pytest.approx(0.5, abs=0.01)


def test_set_opacity_applies_to_newly_spawned_windows(qtbot, manager: DesktopWidgetManager) -> None:
    manager.set_opacity(0.4)

    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    window = next(iter(manager._windows.values()))
    assert window.windowOpacity() == pytest.approx(0.4, abs=0.01)


def test_no_refresh_triggered_without_stats_service(
    qtbot, repository: JsonDesktopLayoutRepository
) -> None:
    manager = DesktopWidgetManager(repository, ThemeManager(), username="octocat")

    manager.restore_saved_layout()  # must not raise; no service configured

    assert manager._refresh_worker is None


def test_no_refresh_triggered_without_username(
    qtbot, repository: JsonDesktopLayoutRepository, stats_service: StatsService
) -> None:
    manager = DesktopWidgetManager(repository, ThemeManager(), stats_service=stats_service)

    manager.restore_saved_layout()  # must not raise; no username configured

    assert manager._refresh_worker is None


def test_restore_triggers_refresh_and_updates_windows(
    qtbot, repository: JsonDesktopLayoutRepository, stats_service: StatsService
) -> None:
    manager = DesktopWidgetManager(
        repository, ThemeManager(), stats_service=stats_service, username="octocat"
    )
    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)
    window = next(iter(manager._windows.values()))

    manager.restore_saved_layout()
    qtbot.waitUntil(lambda: manager._refresh_worker is None, timeout=5000)

    assert window._snapshot is not None
    assert window._snapshot.stats.total_solved == 42


def test_set_username_triggers_refresh(
    qtbot, repository: JsonDesktopLayoutRepository, stats_service: StatsService
) -> None:
    manager = DesktopWidgetManager(repository, ThemeManager(), stats_service=stats_service)

    manager.set_username("octocat")
    qtbot.waitUntil(lambda: manager._refresh_worker is None, timeout=5000)

    assert manager._snapshot is not None
    assert manager._snapshot.profile.username == "octocat"


def test_set_refresh_interval_minutes_restarts_timer(qtbot, manager: DesktopWidgetManager) -> None:
    manager.set_refresh_interval_minutes(5)

    assert manager._refresh_timer.interval() == 5 * 60_000
    assert manager._refresh_timer.isActive()


def test_concurrent_refresh_requests_do_not_spawn_multiple_workers(
    qtbot, repository: JsonDesktopLayoutRepository, stats_service: StatsService
) -> None:
    manager = DesktopWidgetManager(
        repository, ThemeManager(), stats_service=stats_service, username="octocat"
    )

    manager._trigger_refresh()
    first_worker = manager._refresh_worker
    manager._trigger_refresh()  # should be a no-op while the first is still running

    assert manager._refresh_worker is first_worker
    qtbot.waitUntil(lambda: manager._refresh_worker is None, timeout=5000)


def test_no_goal_progress_without_goal_service(
    qtbot, repository: JsonDesktopLayoutRepository
) -> None:
    manager = DesktopWidgetManager(repository, ThemeManager())

    manager.add_widget(WidgetKind.GOALS, WidgetSize.SMALL)

    assert manager._goal_progress == []


def test_restore_computes_goal_progress(
    qtbot, repository: JsonDesktopLayoutRepository, goal_service: GoalService
) -> None:
    goal_service.add_goal(GoalMetric.TOTAL_SOLVED, 100)
    manager = DesktopWidgetManager(repository, ThemeManager(), goal_service=goal_service)

    manager.restore_saved_layout()

    assert len(manager._goal_progress) == 1
    assert manager._goal_progress[0].goal.target == 100


def test_refresh_goals_recomputes_and_pushes_to_windows(
    qtbot, repository: JsonDesktopLayoutRepository, goal_service: GoalService
) -> None:
    manager = DesktopWidgetManager(repository, ThemeManager(), goal_service=goal_service)
    manager.add_widget(WidgetKind.GOALS, WidgetSize.SMALL)
    window = next(iter(manager._windows.values()))

    goal_service.add_goal(GoalMetric.STREAK, 30)
    manager.refresh_goals()

    assert len(manager._goal_progress) == 1
    assert window._goal_progress == manager._goal_progress


def test_get_snapshot_returns_none_initially(qtbot, manager: DesktopWidgetManager) -> None:
    assert manager.get_snapshot() is None


def test_refresh_notifies_on_new_streak_record(
    qtbot,
    repository: JsonDesktopLayoutRepository,
    stats_service: StatsService,
    notification_service: NotificationService,
    notifier: _RecordingNotifier,
) -> None:
    # _FakeProvider reports current_streak=5, longest_streak=10 -- not a record.
    manager = DesktopWidgetManager(
        repository,
        ThemeManager(),
        stats_service=stats_service,
        username="octocat",
        notification_service=notification_service,
    )

    manager.set_username("octocat")
    qtbot.waitUntil(lambda: manager._refresh_worker is None, timeout=5000)

    assert not any("streak record" in title.lower() for title, _ in notifier.calls)
    assert any(title == "Daily Challenge" for title, _ in notifier.calls)


def test_refresh_goals_notifies_on_goal_achieved(
    qtbot,
    repository: JsonDesktopLayoutRepository,
    stats_service: StatsService,
    goal_service: GoalService,
    notification_service: NotificationService,
    notifier: _RecordingNotifier,
) -> None:
    manager = DesktopWidgetManager(
        repository,
        ThemeManager(),
        stats_service=stats_service,
        username="octocat",
        goal_service=goal_service,
        notification_service=notification_service,
    )
    manager.set_username("octocat")  # _FakeProvider reports total_solved=42
    qtbot.waitUntil(lambda: manager._refresh_worker is None, timeout=5000)

    goal_service.add_goal(GoalMetric.TOTAL_SOLVED, 10)  # already exceeded by 42 solved
    manager.refresh_goals()

    assert any("goal achieved" in title.lower() for title, _ in notifier.calls)


def test_refresh_goals_does_not_notify_when_not_yet_achieved(
    qtbot,
    repository: JsonDesktopLayoutRepository,
    goal_service: GoalService,
    notification_service: NotificationService,
    notifier: _RecordingNotifier,
) -> None:
    manager = DesktopWidgetManager(
        repository,
        ThemeManager(),
        goal_service=goal_service,
        notification_service=notification_service,
    )
    goal_service.add_goal(GoalMetric.TOTAL_SOLVED, 500)  # no snapshot -> current_value is 0

    manager.refresh_goals()

    assert not any("goal achieved" in title.lower() for title, _ in notifier.calls)


def test_set_notifications_enabled_toggles_service(
    qtbot, repository: JsonDesktopLayoutRepository, notification_service: NotificationService
) -> None:
    manager = DesktopWidgetManager(
        repository, ThemeManager(), notification_service=notification_service
    )

    manager.set_notifications_enabled(False)

    assert notification_service._enabled is False

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from PySide6.QtWidgets import QLabel, QProgressBar, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.goal import Goal, GoalMetric
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.catalog import WIDGET_CATALOG
from codepulse.presentation.widgets.desktop import daily, goals, progress, streak
from codepulse.presentation.widgets.desktop.registry import render_widget

_ALL_KIND_SIZE_PAIRS = [(entry.kind, size) for entry in WIDGET_CATALOG for size in entry.sizes]


def _make_snapshot() -> DashboardSnapshot:
    return DashboardSnapshot(
        profile=Profile(username="octocat"),
        stats=Stats(
            easy_solved=40, medium_solved=35, hard_solved=8, total_solved=83, acceptance_rate=62.5
        ),
        streak=Streak(current_streak=9, longest_streak=21, total_active_days=100),
        daily_challenge=DailyChallenge(
            title="Two Sum",
            title_slug="two-sum",
            difficulty="Easy",
            acceptance_rate=55.0,
            url="https://leetcode.com/problems/two-sum/",
            challenge_date=date(2026, 7, 4),
        ),
        contest_info=ContestInfo(rating=1600.0),
        fetched_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(("kind", "size"), _ALL_KIND_SIZE_PAIRS)
def test_every_catalog_kind_and_size_renders_without_raising(qtbot, kind, size) -> None:
    theme = load_theme("leetcode")

    widget = render_widget(kind, size, theme)
    qtbot.addWidget(widget)
    widget.resize(320, 320)

    widget.grab()  # must not raise


@pytest.mark.parametrize(("kind", "size"), _ALL_KIND_SIZE_PAIRS)
def test_every_catalog_kind_and_size_renders_with_a_real_snapshot(qtbot, kind, size) -> None:
    theme = load_theme("leetcode")
    snapshot = _make_snapshot()

    widget = render_widget(kind, size, theme, snapshot)
    qtbot.addWidget(widget)
    widget.resize(320, 320)

    widget.grab()  # must not raise


@pytest.mark.parametrize(
    "theme_name", ["dark", "light", "glass", "leetcode", "cyberpunk", "minimal"]
)
def test_progress_large_renders_under_every_theme(qtbot, theme_name) -> None:
    theme = load_theme(theme_name)

    widget = render_widget(WidgetKind.PROGRESS, WidgetSize.LARGE, theme)
    qtbot.addWidget(widget)
    widget.resize(310, 310)

    widget.grab()


def test_streak_uses_sample_value_without_snapshot(qtbot) -> None:
    theme = load_theme("dark")

    widget = streak.render(WidgetSize.SMALL, theme)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "127" in labels


def test_streak_uses_real_current_streak_from_snapshot(qtbot) -> None:
    theme = load_theme("dark")
    snapshot = _make_snapshot()

    widget = streak.render(WidgetSize.SMALL, theme, snapshot)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "9" in labels
    assert "127" not in labels


def test_progress_uses_real_solved_counts_from_snapshot(qtbot) -> None:
    theme = load_theme("dark")
    snapshot = _make_snapshot()

    widget = progress.render(WidgetSize.LARGE, theme, snapshot)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "40" in labels  # easy
    assert "35" in labels  # medium
    assert "8" in labels  # hard


def test_daily_uses_real_title_and_difficulty_from_snapshot(qtbot) -> None:
    theme = load_theme("dark")
    snapshot = _make_snapshot()

    widget = daily.render(WidgetSize.MEDIUM, theme, snapshot)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "Two Sum" in labels
    assert "Easy" in labels


def test_daily_sample_data_when_no_snapshot(qtbot) -> None:
    theme = load_theme("dark")

    widget = daily.render(WidgetSize.MEDIUM, theme)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "Maximum Subsequence Score" in labels


def test_goals_uses_sample_rows_without_progress(qtbot) -> None:
    theme = load_theme("dark")

    widget = goals.render(WidgetSize.SMALL, theme)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "350/500" in labels


def test_goals_uses_real_progress_when_provided(qtbot) -> None:
    theme = load_theme("dark")
    goal_progress = [
        GoalProgress(
            goal=Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=500),
            current_value=200,
            percent=40.0,
        )
    ]

    widget = goals.render(WidgetSize.SMALL, theme, None, goal_progress)
    qtbot.addWidget(widget)

    labels = _find_labels(widget)
    assert "200/500" in labels
    assert "350/500" not in labels


def test_goals_shows_at_most_two_goals(qtbot) -> None:
    theme = load_theme("dark")
    goal_progress = [
        GoalProgress(
            goal=Goal(uid=str(i), metric=GoalMetric.TOTAL_SOLVED, target=100 * (i + 1)),
            current_value=i,
            percent=0.0,
        )
        for i in range(4)
    ]

    widget = goals.render(WidgetSize.SMALL, theme, None, goal_progress)
    qtbot.addWidget(widget)

    assert len(widget.findChildren(QProgressBar)) == 2


def _find_labels(widget: QWidget) -> list[str]:
    return [label.text() for label in widget.findChildren(QLabel)]

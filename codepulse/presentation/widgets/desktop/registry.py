"""Maps a widget kind to its rendering function.

Used by both the widget picker's preview pane (always ``snapshot=None``,
``goal_progress=None`` -- previews show representative sample data) and the
floating widget windows, which pass the latest fetched
:class:`DashboardSnapshot` and computed :class:`GoalProgress` list once
they exist. Neither caller needs to know how any individual widget kind is
drawn, or which kinds actually use live data yet.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.desktop import (
    activity,
    badges,
    contest,
    daily,
    goals,
    progress,
    rating,
    streak,
)


def render_widget(
    kind: WidgetKind,
    size: WidgetSize,
    theme: Theme,
    snapshot: DashboardSnapshot | None = None,
    goal_progress: list[GoalProgress] | None = None,
) -> QWidget:
    """Render the content widget for ``kind`` at ``size``, styled for ``theme``.

    ``snapshot`` supplies live data where a renderer supports it (currently
    Streak, Progress, and Daily Challenge). ``goal_progress`` is used only
    by the Goals renderer. Other kinds ignore both and always render sample
    data until their backing provider data exists.
    """
    if kind == WidgetKind.GOALS:
        return goals.render(size, theme, snapshot, goal_progress)

    renderer = {
        WidgetKind.STREAK: streak.render,
        WidgetKind.PROGRESS: progress.render,
        WidgetKind.CONTEST: contest.render,
        WidgetKind.RATING: rating.render,
        WidgetKind.DAILY: daily.render,
        WidgetKind.ACTIVITY: activity.render,
        WidgetKind.BADGES: badges.render,
    }[kind]
    return renderer(size, theme, snapshot)

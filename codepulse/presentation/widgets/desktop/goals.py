"""Goals widget: user-defined solving targets (e.g. "500 problems").

Small size, reused for medium too. Shows real progress for up to the
first two goals once :class:`GoalProgress` values are supplied (computed
by :class:`~codepulse.application.services.goal_service.GoalService` from
the current :class:`DashboardSnapshot`); falls back to representative
sample goals otherwise -- on first launch, before any goals are defined,
or in the picker preview.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.models.goal import GoalMetric
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme

_MAX_GOALS_SHOWN = 2
_SAMPLE_ROWS = (("Problems", 350, 500), ("Day Streak", 18, 30))
_METRIC_LABELS = {
    GoalMetric.TOTAL_SOLVED: "Problems",
    GoalMetric.HARD_SOLVED: "Hard Problems",
    GoalMetric.STREAK: "Day Streak",
    GoalMetric.RATING: "Rating",
}


def render(
    size: WidgetSize,
    theme: Theme,
    snapshot: DashboardSnapshot | None = None,
    goal_progress: list[GoalProgress] | None = None,
) -> QWidget:
    """Build the goals widget content (same layout for small/medium)."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(16, 0, 16, 0)
    layout.setSpacing(12)

    if goal_progress:
        for progress in goal_progress[:_MAX_GOALS_SHOWN]:
            label = _METRIC_LABELS.get(progress.goal.metric, progress.goal.metric.value)
            layout.addLayout(_goal_row(theme, label, progress.current_value, progress.goal.target))
    else:
        for label, current, target in _SAMPLE_ROWS:
            layout.addLayout(_goal_row(theme, label, current, target))

    return container


def _goal_row(theme: Theme, label: str, current: int, target: int) -> QVBoxLayout:
    column = QVBoxLayout()
    column.setSpacing(4)

    header = QHBoxLayout()
    name_label = QLabel(label)
    name_label.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    header.addWidget(name_label)
    header.addStretch()
    value_label = QLabel(f"{current}/{target}")
    value_label.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_primary};")
    header.addWidget(value_label)
    column.addLayout(header)

    bar = QProgressBar()
    bar.setRange(0, target)
    bar.setValue(current)
    bar.setTextVisible(False)
    bar.setFixedHeight(6)
    bar.setStyleSheet(f"""
        QProgressBar {{
            border: none;
            border-radius: 3px;
            background: {theme.colors.surface_alt};
        }}
        QProgressBar::chunk {{
            border-radius: 3px;
            background: {theme.colors.warning};
        }}
        """)
    column.addWidget(bar)

    return column

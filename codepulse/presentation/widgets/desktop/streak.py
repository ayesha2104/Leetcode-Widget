"""Streak widget: current solving streak, small and medium sizes.

Shows the real current streak once a :class:`DashboardSnapshot` is
available (wired up via :class:`DesktopWidgetManager`'s refresh worker);
falls back to a representative sample value beforehand -- on first launch,
with no username configured, or while a refresh is still in flight. The
weekly tracker dots are always decorative: no per-weekday activity data is
modeled.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme

_SAMPLE_STREAK = 127
_WEEKDAY_LABELS = ("M", "T", "W", "T", "F", "S", "S")
_DAYS_COMPLETE = 5


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the streak widget content for the given size."""
    current_streak = snapshot.streak.current_streak if snapshot is not None else _SAMPLE_STREAK
    if size == WidgetSize.MEDIUM:
        return _render_medium(theme, current_streak)
    return _render_small(theme, current_streak)


def _flame_label(theme: Theme, font_size: int) -> QLabel:
    label = QLabel("\U0001f525")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(f"font-size: {font_size}px;")
    return label


def _render_small(theme: Theme, current_streak: int) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(2)

    layout.addWidget(_flame_label(theme, 32))

    value_label = QLabel(str(current_streak))
    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value_label.setStyleSheet(
        f"font-size: 28px; font-weight: 800; color: {theme.colors.text_primary};"
    )
    layout.addWidget(value_label)

    caption = QLabel("day streak")
    caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caption.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    layout.addWidget(caption)

    return container


def _render_medium(theme: Theme, current_streak: int) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(16, 0, 16, 0)
    layout.setSpacing(16)

    left = QVBoxLayout()
    left.setAlignment(Qt.AlignmentFlag.AlignCenter)
    left.setSpacing(2)
    left.addWidget(_flame_label(theme, 36))
    value_label = QLabel(str(current_streak))
    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value_label.setStyleSheet(
        f"font-size: 32px; font-weight: 800; color: {theme.colors.text_primary};"
    )
    left.addWidget(value_label)
    caption = QLabel("day streak")
    caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caption.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    left.addWidget(caption)
    layout.addLayout(left)

    week_row = QHBoxLayout()
    week_row.setSpacing(6)
    for index, day_label in enumerate(_WEEKDAY_LABELS):
        day_column = QVBoxLayout()
        day_column.setSpacing(4)

        dot = QLabel("✓" if index < _DAYS_COMPLETE else "")
        dot.setFixedSize(22, 22)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        background = theme.colors.warning if index < _DAYS_COMPLETE else theme.colors.surface_alt
        text_color = (
            theme.colors.background if index < _DAYS_COMPLETE else theme.colors.text_secondary
        )
        dot.setStyleSheet(
            f"background: {background}; color: {text_color}; border-radius: 11px; font-size: 11px;"
        )
        day_column.addWidget(dot)

        weekday = QLabel(day_label)
        weekday.setAlignment(Qt.AlignmentFlag.AlignCenter)
        weekday.setStyleSheet(f"font-size: 9px; color: {theme.colors.text_secondary};")
        day_column.addWidget(weekday)

        week_row.addLayout(day_column)

    layout.addLayout(week_row, stretch=1)
    return container

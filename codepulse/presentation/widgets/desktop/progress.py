"""Progress widget: problems solved with an activity heatmap.

Small/medium/large sizes, reusing :class:`ProgressRing` and
:class:`HeatmapGrid`. Solved counts, per-difficulty breakdown, and the
ring's fill (acceptance rate) are real once a :class:`DashboardSnapshot`
is available; the heatmap stays sample/decorative regardless, since no
domain data models day-by-day activity (only aggregate current/longest
streak and total active days).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.desktop.heatmap_grid import HeatmapGrid
from codepulse.presentation.widgets.progress_ring import ProgressRing

_MONTHS = ("Feb", "Mar", "Apr", "May", "Jun", "Jul")


@dataclass(frozen=True, slots=True)
class _ProgressData:
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    acceptance_rate: float


_SAMPLE_DATA = _ProgressData(
    total_solved=203, easy_solved=89, medium_solved=94, hard_solved=20, acceptance_rate=51.0
)


def _resolve_data(snapshot: DashboardSnapshot | None) -> _ProgressData:
    if snapshot is None:
        return _SAMPLE_DATA
    stats = snapshot.stats
    return _ProgressData(
        total_solved=stats.total_solved,
        easy_solved=stats.easy_solved,
        medium_solved=stats.medium_solved,
        hard_solved=stats.hard_solved,
        acceptance_rate=stats.acceptance_rate,
    )


def _sample_heatmap(cell_count: int) -> list[int]:
    rng = random.Random(42)  # noqa: S311 - deterministic sample data, not security-sensitive
    return [rng.choice([0, 0, 0, 1, 2, 3, 4]) for _ in range(cell_count)]


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the progress widget content for the given size."""
    data = _resolve_data(snapshot)
    if size == WidgetSize.LARGE:
        return _render_large(theme, data)
    if size == WidgetSize.MEDIUM:
        return _render_medium(theme, data)
    return _render_small(theme, data)


def _render_small(theme: Theme, data: _ProgressData) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    ring = ProgressRing(theme, thickness=6)
    ring.setFixedSize(88, 88)
    ring.set_center_text(f"{data.total_solved}\nsolved")
    ring.set_progress(data.acceptance_rate, animate=False)
    layout.addWidget(ring)

    return container


def _progress_label(theme: Theme) -> QLabel:
    label = QLabel("PROGRESS")
    label.setStyleSheet(
        f"color: {theme.colors.success}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
    )
    return label


def _solved_count_label(theme: Theme, data: _ProgressData, font_size: int) -> QLabel:
    label = QLabel(
        f"{data.total_solved} "
        f"<span style='color:{theme.colors.text_secondary};font-weight:400;'>"
        f"{data.acceptance_rate:.0f}% accepted</span>"
    )
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setStyleSheet(
        f"font-size: {font_size}px; font-weight: 800; color: {theme.colors.text_primary};"
    )
    return label


def _month_row(theme: Theme, months: tuple[str, ...]) -> QHBoxLayout:
    row = QHBoxLayout()
    for month in months:
        label = QLabel(month)
        label.setStyleSheet(f"font-size: 8px; color: {theme.colors.text_secondary};")
        row.addWidget(label)
    return row


def _render_medium(theme: Theme, data: _ProgressData) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(8)

    header = QHBoxLayout()
    text_column = QVBoxLayout()
    text_column.setSpacing(2)
    text_column.addWidget(_progress_label(theme))
    text_column.addWidget(_solved_count_label(theme, data, 26))
    header.addLayout(text_column)
    header.addStretch()

    ring = ProgressRing(theme, thickness=4)
    ring.setFixedSize(40, 40)
    ring.set_center_text("")
    ring.set_progress(data.acceptance_rate, animate=False)
    header.addWidget(ring)
    layout.addLayout(header)

    heatmap = HeatmapGrid(theme, levels=_sample_heatmap(56))
    heatmap.setMinimumHeight(48)
    layout.addWidget(heatmap, stretch=1)
    layout.addLayout(_month_row(theme, _MONTHS[2:6]))

    return container


def _difficulty_card(theme: Theme, label: str, value: int, color_role: str) -> QWidget:
    color = getattr(theme.colors, color_role)
    card = QWidget()
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    card.setStyleSheet(
        f"background: {theme.colors.surface_alt}; border: 1px solid {theme.colors.border};"
        f"border-radius: 10px;"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(2)

    value_label = QLabel(str(value))
    value_label.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {color};")
    layout.addWidget(value_label)

    name_label = QLabel(label)
    name_label.setStyleSheet(f"font-size: 9px; color: {color};")
    layout.addWidget(name_label)

    return card


def _render_large(theme: Theme, data: _ProgressData) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(10)

    header = QHBoxLayout()
    text_column = QVBoxLayout()
    text_column.setSpacing(2)
    text_column.addWidget(_progress_label(theme))
    text_column.addWidget(_solved_count_label(theme, data, 32))
    header.addLayout(text_column)
    header.addStretch()

    ring = ProgressRing(theme, thickness=5)
    ring.setFixedSize(56, 56)
    ring.set_progress(data.acceptance_rate, animate=False)
    header.addWidget(ring)
    layout.addLayout(header)

    breakdown_row = QGridLayout()
    breakdown_row.setSpacing(8)
    breakdown = (
        ("Easy", data.easy_solved, "success"),
        ("Medium", data.medium_solved, "warning"),
        ("Hard", data.hard_solved, "error"),
    )
    for column, (label, value, color_role) in enumerate(breakdown):
        breakdown_row.addWidget(_difficulty_card(theme, label, value, color_role), 0, column)
    layout.addLayout(breakdown_row)

    heatmap = HeatmapGrid(theme, levels=_sample_heatmap(84))
    heatmap.setMinimumHeight(72)
    layout.addWidget(heatmap, stretch=1)
    layout.addLayout(_month_row(theme, _MONTHS))

    return container

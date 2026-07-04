"""Rating widget: contest rating trend. Medium and large share one layout.

Uses a representative sample rating history -- no provider currently
exposes historical contest-by-contest rating, only the current snapshot
via :meth:`ProviderInterface.get_contest_info`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.desktop.mini_line_chart import MiniLineChart

_SAMPLE_HISTORY = (1680, 1720, 1695, 1760, 1740, 1810, 1788, 1852, 1830, 1897)
_SAMPLE_DELTA = 47
_SAMPLE_PEAK = "1924"
_SAMPLE_GLOBAL_RANK = "#8.2K"


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the rating widget content (same layout for medium and large).

    ``snapshot`` is accepted for interface uniformity but ignored -- no
    provider exposes historical contest-by-contest rating yet, only the
    current single value (:attr:`ContestInfo.rating`).
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    header = QHBoxLayout()
    text_column = QVBoxLayout()
    text_column.setSpacing(2)
    label = QLabel("CONTEST RATING")
    label.setStyleSheet(
        f"font-size: 10px; color: {theme.colors.text_secondary}; letter-spacing: 1px;"
    )
    text_column.addWidget(label)
    rating = QLabel(str(_SAMPLE_HISTORY[-1]))
    rating.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {theme.colors.accent};")
    text_column.addWidget(rating)
    header.addLayout(text_column)
    header.addStretch()

    delta = QLabel(f"↑ +{_SAMPLE_DELTA}")
    delta.setStyleSheet(f"font-size: 11px; color: {theme.colors.success}; font-weight: 600;")
    header.addWidget(delta)
    layout.addLayout(header)

    chart = MiniLineChart(theme, values=list(_SAMPLE_HISTORY))
    chart.setMinimumHeight(48)
    layout.addWidget(chart, stretch=1)

    stats_row = QGridLayout()
    stats_row.setSpacing(6)
    for column, (name, value) in enumerate(
        (("Peak", _SAMPLE_PEAK), ("Global", _SAMPLE_GLOBAL_RANK))
    ):
        stats_row.addWidget(_stat_box(theme, name, value), 0, column)
    layout.addLayout(stats_row)

    return container


def _stat_box(theme: Theme, name: str, value: str) -> QWidget:
    box = QWidget()
    box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    box.setStyleSheet(f"background: {theme.colors.surface_alt}; border-radius: 8px;")
    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(8, 6, 8, 6)
    box_layout.setSpacing(1)

    value_label = QLabel(value)
    value_label.setStyleSheet(
        f"font-size: 12px; font-weight: 700; color: {theme.colors.text_primary};"
    )
    box_layout.addWidget(value_label)

    name_label = QLabel(name)
    name_label.setStyleSheet(f"font-size: 9px; color: {theme.colors.text_secondary};")
    box_layout.addWidget(name_label)

    return box

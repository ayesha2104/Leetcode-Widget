"""Recent Activity widget: a timeline of solved problems and achievements.

Medium and large share one layout. Purely sample data -- no provider or
service currently tracks a per-submission activity history; LeetCode's
public API only exposes aggregate stats, not a submission timeline.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme

_SAMPLE_ITEMS = (
    ("✅", "success", "Solved Two Sum", "Easy · 2h ago"),
    ("✅", "warning", "Course Schedule", "Medium · 5h ago"),
    ("\U0001f396", "warning", "50 Days Badge", "1d ago"),
)


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the recent-activity widget content (same layout for medium/large).

    ``snapshot`` is accepted for interface uniformity but ignored -- no
    data source for a submission timeline exists yet.
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)

    label = QLabel("RECENT")
    label.setStyleSheet(
        f"font-size: 10px; color: {theme.colors.text_secondary}; letter-spacing: 1px;"
    )
    layout.addWidget(label)

    for glyph, color_role, text, sub in _SAMPLE_ITEMS:
        layout.addWidget(_activity_row(theme, glyph, color_role, text, sub))

    layout.addStretch()
    return container


def _activity_row(theme: Theme, glyph: str, color_role: str, text: str, sub: str) -> QWidget:
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 4, 0, 4)
    row_layout.setSpacing(10)

    icon = QLabel(glyph)
    icon.setFixedSize(24, 24)
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    icon.setStyleSheet(
        f"background: {theme.colors.surface_alt}; border-radius: 12px; font-size: 11px;"
        f"color: {getattr(theme.colors, color_role)};"
    )
    row_layout.addWidget(icon)

    text_column = QVBoxLayout()
    text_column.setSpacing(0)
    title = QLabel(text)
    title.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {theme.colors.text_primary};")
    text_column.addWidget(title)
    subtitle = QLabel(sub)
    subtitle.setStyleSheet(f"font-size: 9px; color: {theme.colors.text_secondary};")
    text_column.addWidget(subtitle)
    row_layout.addLayout(text_column, stretch=1)

    return row

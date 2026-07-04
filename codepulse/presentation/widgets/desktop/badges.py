"""Badges widget: earned achievement badges showcase.

Small size, reused for medium too. Sample data -- CodePulse has no
achievement/badge system yet; this is a visual placeholder for the
picker gallery.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme

_SAMPLE_BADGES = ("\U0001f525", "\U0001f3c6", "⚡", "♟️")


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the badges widget content (same layout for small/medium).

    ``snapshot`` is accepted for interface uniformity but ignored -- there
    is no achievement/badge system yet.
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(8)

    grid_widget = QWidget()
    grid = QGridLayout(grid_widget)
    grid.setSpacing(6)
    for index, glyph in enumerate(_SAMPLE_BADGES):
        row, column = divmod(index, 2)
        grid.addWidget(_badge_tile(theme, glyph), row, column)
    layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    caption = QLabel(f"{len(_SAMPLE_BADGES)} badges earned")
    caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caption.setStyleSheet(f"font-size: 9px; color: {theme.colors.text_secondary};")
    layout.addWidget(caption)

    return container


def _badge_tile(theme: Theme, glyph: str) -> QLabel:
    tile = QLabel(glyph)
    tile.setFixedSize(36, 36)
    tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tile.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    tile.setStyleSheet(
        f"background: {theme.colors.surface_alt}; border: 1px solid {theme.colors.border};"
        f"border-radius: 10px; font-size: 16px;"
    )
    return tile

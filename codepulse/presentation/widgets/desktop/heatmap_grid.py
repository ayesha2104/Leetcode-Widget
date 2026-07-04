"""A GitHub-style activity heatmap grid, rendered with QPainter.

Cells fill row-major across a fixed column count (matching a CSS
``grid-template-columns: repeat(N, 1fr)`` auto-flow), not a calendar-style
one-column-per-week layout.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from codepulse.presentation.themes.theme import Theme
from codepulse.utils.color import parse_color

_COLUMNS = 14
_CELL_GAP = 2.0
_CELL_RADIUS = 2.0
_LEVEL_ALPHAS = (0.05, 0.25, 0.45, 0.65, 0.88)


class HeatmapGrid(QWidget):
    """Renders a grid of activity-intensity cells (levels 0-4 each)."""

    def __init__(
        self, theme: Theme, *, levels: list[int] | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._levels = levels or []

    def set_levels(self, levels: list[int]) -> None:
        """Replace the displayed activity levels and repaint."""
        self._levels = levels
        self.update()

    def apply_theme(self, theme: Theme) -> None:
        """Restyle the grid for the given theme."""
        self._theme = theme
        self.update()

    def _cell_color(self, level: int) -> QColor:
        if level <= 0:
            return parse_color("rgba(255, 255, 255, 0.05)")
        alpha = _LEVEL_ALPHAS[min(level, len(_LEVEL_ALPHAS) - 1)]
        color = QColor(parse_color(self._theme.colors.success))
        color.setAlphaF(alpha)
        return color

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._levels:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        rows = -(-len(self._levels) // _COLUMNS)  # ceil division
        cell_w = (self.width() - (_COLUMNS - 1) * _CELL_GAP) / _COLUMNS
        cell_h = (self.height() - (rows - 1) * _CELL_GAP) / rows if rows else 0

        for index, level in enumerate(self._levels):
            row, column = divmod(index, _COLUMNS)
            x = column * (cell_w + _CELL_GAP)
            y = row * (cell_h + _CELL_GAP)
            painter.setBrush(self._cell_color(level))
            painter.drawRoundedRect(QRectF(x, y, cell_w, cell_h), _CELL_RADIUS, _CELL_RADIUS)

"""A minimal, axis-free trend line for small stat widgets (e.g. contest rating)."""

from __future__ import annotations

from PySide6.QtGui import QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from codepulse.presentation.themes.theme import Theme
from codepulse.utils.color import parse_color

_PADDING_BELOW_MIN = 50.0
_PADDING_ABOVE_MAX = 30.0


class MiniLineChart(QWidget):
    """Renders an unlabeled trend line through a series of values."""

    def __init__(
        self, theme: Theme, *, values: list[float] | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._values = values or []

    def set_values(self, values: list[float]) -> None:
        """Replace the plotted series and repaint."""
        self._values = values
        self.update()

    def apply_theme(self, theme: Theme) -> None:
        """Restyle the line for the given theme."""
        self._theme = theme
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        if len(self._values) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        low = min(self._values) - _PADDING_BELOW_MIN
        high = max(self._values) + _PADDING_ABOVE_MAX
        span = max(high - low, 1.0)

        width = self.width()
        height = self.height()
        step = width / (len(self._values) - 1)

        path = QPainterPath()
        for index, value in enumerate(self._values):
            x = index * step
            y = height - ((value - low) / span) * height
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(QPen(parse_color(self._theme.colors.accent), 2))
        painter.drawPath(path)

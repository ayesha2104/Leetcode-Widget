"""A circular, animated progress indicator used for goal tracking (Phase 6)."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from codepulse.presentation.animations.transitions import animate_value
from codepulse.presentation.themes.theme import Theme
from codepulse.utils.color import parse_color

_FULL_CIRCLE_16THS = 360 * 16


class ProgressRing(QWidget):
    """A donut-shaped progress indicator showing a 0-100 percentage."""

    def __init__(self, theme: Theme, *, thickness: int = 8, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._thickness = thickness
        self._value = 0.0
        self._center_text_override: str | None = None
        self.setMinimumSize(80, 80)

    @property
    def value(self) -> float:
        """The currently displayed percentage (mid-animation if one is running)."""
        return self._value

    def apply_theme(self, theme: Theme) -> None:
        """Restyle the ring for the given theme."""
        self._theme = theme
        self.update()

    def set_center_text(self, text: str | None) -> None:
        """Override the default ``{percent}%`` center label.

        Pass a string (``""`` included) to show custom text or hide the
        label entirely; pass ``None`` to restore the default percentage.
        """
        self._center_text_override = text
        self.update()

    def set_progress(self, percent: float, *, animate: bool = True) -> None:
        """Set the displayed percentage (clamped to 0-100), animating by default."""
        percent = max(0.0, min(100.0, percent))
        if not animate:
            self._value = percent
            self.update()
            return

        animate_value(self._value, percent, self._on_animated_value, parent=self)
        self._value = percent

    def _on_animated_value(self, value: float) -> None:
        self._value = value
        self.update()

    def _ring_rect(self) -> QRect:
        margin = self._thickness // 2 + 1
        return self.rect().adjusted(margin, margin, -margin, -margin)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self._ring_rect()

        track_pen = QPen(
            parse_color(self._theme.colors.surface_alt),
            self._thickness,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, _FULL_CIRCLE_16THS)

        progress_pen = QPen(
            parse_color(self._theme.colors.accent),
            self._thickness,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(progress_pen)
        span_angle = int(_FULL_CIRCLE_16THS * (self._value / 100))
        painter.drawArc(rect, 90 * 16, -span_angle)

        painter.setPen(parse_color(self._theme.colors.text_primary))
        font: QFont = painter.font()
        font.setBold(True)
        font.setPointSize(max(self.width() // 8, 9))
        painter.setFont(font)
        text = (
            self._center_text_override
            if self._center_text_override is not None
            else f"{round(self._value)}%"
        )
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

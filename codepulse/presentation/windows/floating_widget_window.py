"""A single desktop widget's floating, always-on-top window.

Wraps one :class:`~codepulse.domain.models.widget.PlacedWidget` -- renders
its content via the desktop widget registry, and exposes a hover-to-reveal
remove button plus drag-to-reposition (inherited from
:class:`FramelessWindow`), matching the reference design's placed-widget
card interaction.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QEnterEvent, QMoveEvent
from PySide6.QtWidgets import QPushButton, QVBoxLayout

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.models.widget import PlacedWidget
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.catalog import SIZE_DIMENSIONS
from codepulse.presentation.widgets.desktop.registry import render_widget
from codepulse.presentation.windows.base_frameless_window import FramelessWindow

_REMOVE_BUTTON_SIZE = 20
_REMOVE_BUTTON_STYLE = (
    "background: #ef4444; color: white; border-radius: 10px;"
    "border: 2px solid #0d0d0f; font-size: 10px;"
)


class FloatingWidgetWindow(FramelessWindow):
    """Displays one placed widget's content as an independent floating window."""

    remove_requested = Signal(str)  # uid
    moved = Signal(str, int, int)  # uid, x, y

    def __init__(
        self,
        placed_widget: PlacedWidget,
        theme: Theme,
        snapshot: DashboardSnapshot | None = None,
        goal_progress: list[GoalProgress] | None = None,
    ) -> None:
        super().__init__(theme, always_on_top=True, resizable=False, drag_from_content=True)
        self.placed_widget = placed_widget
        self._snapshot = snapshot
        self._goal_progress = goal_progress
        self.setMouseTracking(True)

        width, height = SIZE_DIMENSIONS[placed_widget.size]
        self.setFixedSize(width, height)

        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._set_content(theme)

        self._remove_button = QPushButton("✕", self)
        self._remove_button.setFixedSize(_REMOVE_BUTTON_SIZE, _REMOVE_BUTTON_SIZE)
        self._remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_button.setStyleSheet(_REMOVE_BUTTON_STYLE)
        self._remove_button.move(width - _REMOVE_BUTTON_SIZE // 2, -_REMOVE_BUTTON_SIZE // 2)
        self._remove_button.hide()
        self._remove_button.clicked.connect(
            lambda: self.remove_requested.emit(self.placed_widget.uid)
        )

    def _set_content(self, theme: Theme) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        content = render_widget(
            self.placed_widget.kind,
            self.placed_widget.size,
            theme,
            self._snapshot,
            self._goal_progress,
        )
        self._content_layout.addWidget(content)
        self.refresh_content_drag_filters()

    def apply_theme(self, theme: Theme) -> None:
        """Restyle the window chrome and re-render the content for the given theme."""
        super().apply_theme(theme)
        self._set_content(theme)

    def set_snapshot(self, snapshot: DashboardSnapshot | None) -> None:
        """Update the displayed data and re-render with the current theme."""
        self._snapshot = snapshot
        self._set_content(self.theme)

    def set_goal_progress(self, goal_progress: list[GoalProgress] | None) -> None:
        """Update the displayed goal progress and re-render with the current theme."""
        self._goal_progress = goal_progress
        self._set_content(self.theme)

    def enterEvent(self, event: QEnterEvent) -> None:
        self._remove_button.show()
        self._remove_button.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._remove_button.hide()
        super().leaveEvent(event)

    def moveEvent(self, event: QMoveEvent) -> None:
        super().moveEvent(event)
        self.moved.emit(self.placed_widget.uid, self.x(), self.y())

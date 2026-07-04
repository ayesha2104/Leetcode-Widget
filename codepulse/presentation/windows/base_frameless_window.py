"""Base class for CodePulse's frameless, glassmorphic, draggable, resizable windows.

Dragging and resizing delegate to the OS via ``QWindow.startSystemMove`` /
``startSystemResize`` rather than manual geometry math -- this gets correct
behavior "for free" across DPI scaling, multi-monitor setups, and Windows'
Aero Snap, and it can't drift out of sync with what the compositor is doing.

Subclasses add their own content by laying widgets into ``self``; this class
owns window chrome only (flags, drag, resize, background paint, blur).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QSize, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QPainterPath, QPaintEvent, QShowEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from codepulse.presentation.themes.theme import Theme
from codepulse.utils.color import parse_color
from codepulse.utils.windows_blur import enable_acrylic_blur

RESIZE_MARGIN_PX = 8
MIN_WINDOW_SIZE = QSize(220, 140)

# Widget types excluded from drag-from-content: pressing on one of these
# should reach its own click/text-entry handling, not start a window move.
_DRAG_EXEMPT_TYPES = (QAbstractButton, QLineEdit, QComboBox, QAbstractSlider, QSpinBox)


def edge_at(pos: QPoint, size: QSize, margin: int = RESIZE_MARGIN_PX) -> Qt.Edge:
    """Return which window edge(s) ``pos`` is near, for resize-cursor purposes."""
    edges = Qt.Edge(0)
    if pos.x() <= margin:
        edges |= Qt.Edge.LeftEdge
    elif pos.x() >= size.width() - margin:
        edges |= Qt.Edge.RightEdge
    if pos.y() <= margin:
        edges |= Qt.Edge.TopEdge
    elif pos.y() >= size.height() - margin:
        edges |= Qt.Edge.BottomEdge
    return edges


def cursor_for_edge(edges: Qt.Edge) -> Qt.CursorShape:
    """Map a set of window edges to the cursor shape that should hover over them."""
    diag_tl_br = (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge)
    diag_tr_bl = (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge)

    if any(edges == combo for combo in diag_tl_br):
        return Qt.CursorShape.SizeFDiagCursor
    if any(edges == combo for combo in diag_tr_bl):
        return Qt.CursorShape.SizeBDiagCursor
    if edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
        return Qt.CursorShape.SizeHorCursor
    if edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
        return Qt.CursorShape.SizeVerCursor
    return Qt.CursorShape.ArrowCursor


class FramelessWindow(QWidget):
    """A frameless top-level window with rounded corners and a glass backdrop."""

    def __init__(
        self,
        theme: Theme,
        *,
        always_on_top: bool = True,
        resizable: bool = True,
        drag_from_content: bool = False,
    ) -> None:
        super().__init__()
        self._theme = theme
        self._resizable = resizable
        self._acrylic_enabled = False
        self._drag_from_content = drag_from_content

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_WINDOW_SIZE)

    @property
    def theme(self) -> Theme:
        """The theme currently painted by this window."""
        return self._theme

    def apply_theme(self, theme: Theme) -> None:
        """Switch to a new theme, re-attempting acrylic blur and repainting."""
        self._theme = theme
        self._acrylic_enabled = False
        if self.isVisible():
            self._try_enable_acrylic()
        self.update()

    def set_opacity(self, opacity: float) -> None:
        """Set overall window opacity, clamped to the range the UI allows (0.2-1.0)."""
        self.setWindowOpacity(max(0.2, min(1.0, opacity)))

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._try_enable_acrylic()

    def _try_enable_acrylic(self) -> None:
        if not self._theme.glass.enabled:
            self._acrylic_enabled = False
            return
        tint = parse_color(self._theme.colors.surface)
        self._acrylic_enabled = enable_acrylic_blur(int(self.winId()), tint)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = self._theme.corner_radius
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), radius, radius)

        if not self._acrylic_enabled:
            painter.fillPath(path, parse_color(self._theme.colors.surface))

        painter.setPen(parse_color(self._theme.colors.border))
        painter.drawPath(path)

    def refresh_content_drag_filters(self) -> None:
        """Let a press on any non-interactive descendant start a system
        move/resize.

        Content widgets (labels, cards, ...) fully cover the window's
        client area, and -- unlike the bare background -- swallow the
        click before it ever reaches this window's own mousePressEvent.
        Only relevant when constructed with ``drag_from_content=True``;
        call this again whenever content is replaced (e.g. re-rendered on
        a data or theme change).
        """
        if not self._drag_from_content:
            return
        for child in self.findChildren(QWidget):
            if not isinstance(child, _DRAG_EXEMPT_TYPES):
                child.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            self._drag_from_content
            and event.type() == QEvent.Type.MouseButtonPress
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._begin_move_or_resize(self.mapFromGlobal(event.globalPosition().toPoint()))
            return True
        return super().eventFilter(watched, event)

    def _begin_move_or_resize(self, pos: QPoint) -> None:
        window_handle = self.windowHandle()
        if window_handle is None:
            return
        edges = edge_at(pos, self.size()) if self._resizable else Qt.Edge(0)
        if edges:
            window_handle.startSystemResize(edges)
        else:
            window_handle.startSystemMove()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_move_or_resize(event.position().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._resizable and event.buttons() == Qt.MouseButton.NoButton:
            edges = edge_at(event.position().toPoint(), self.size())
            self.setCursor(cursor_for_edge(edges))
        super().mouseMoveEvent(event)

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QEvent, QPoint, QPointF, QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QPushButton

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.windows.base_frameless_window import (
    RESIZE_MARGIN_PX,
    FramelessWindow,
    cursor_for_edge,
    edge_at,
)

WINDOW_SIZE = QSize(300, 200)


def _left_press_event(pos: QPointF | None = None) -> QMouseEvent:
    pos = pos if pos is not None else QPointF(5, 5)
    return QMouseEvent(
        QEvent.Type.MouseButtonPress,
        pos,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


def test_edge_at_detects_left_edge() -> None:
    assert edge_at(QPoint(0, 100), WINDOW_SIZE) == Qt.Edge.LeftEdge


def test_edge_at_detects_right_edge() -> None:
    assert edge_at(QPoint(299, 100), WINDOW_SIZE) == Qt.Edge.RightEdge


def test_edge_at_detects_top_edge() -> None:
    assert edge_at(QPoint(150, 0), WINDOW_SIZE) == Qt.Edge.TopEdge


def test_edge_at_detects_bottom_edge() -> None:
    assert edge_at(QPoint(150, 199), WINDOW_SIZE) == Qt.Edge.BottomEdge


def test_edge_at_detects_top_left_corner() -> None:
    assert edge_at(QPoint(0, 0), WINDOW_SIZE) == (Qt.Edge.LeftEdge | Qt.Edge.TopEdge)


def test_edge_at_detects_bottom_right_corner() -> None:
    assert edge_at(QPoint(299, 199), WINDOW_SIZE) == (Qt.Edge.RightEdge | Qt.Edge.BottomEdge)


def test_edge_at_returns_no_edges_in_the_middle() -> None:
    assert edge_at(QPoint(150, 100), WINDOW_SIZE) == Qt.Edge(0)


def test_edge_at_respects_custom_margin() -> None:
    assert edge_at(QPoint(20, 100), WINDOW_SIZE, margin=25) == Qt.Edge.LeftEdge
    assert edge_at(QPoint(30, 100), WINDOW_SIZE, margin=25) == Qt.Edge(0)


def test_cursor_for_edge_diagonal_top_left() -> None:
    assert cursor_for_edge(Qt.Edge.LeftEdge | Qt.Edge.TopEdge) == Qt.CursorShape.SizeFDiagCursor


def test_cursor_for_edge_diagonal_bottom_right() -> None:
    assert cursor_for_edge(Qt.Edge.RightEdge | Qt.Edge.BottomEdge) == Qt.CursorShape.SizeFDiagCursor


def test_cursor_for_edge_diagonal_top_right() -> None:
    assert cursor_for_edge(Qt.Edge.RightEdge | Qt.Edge.TopEdge) == Qt.CursorShape.SizeBDiagCursor


def test_cursor_for_edge_horizontal() -> None:
    assert cursor_for_edge(Qt.Edge.LeftEdge) == Qt.CursorShape.SizeHorCursor


def test_cursor_for_edge_vertical() -> None:
    assert cursor_for_edge(Qt.Edge.TopEdge) == Qt.CursorShape.SizeVerCursor


def test_cursor_for_edge_none_is_arrow() -> None:
    assert cursor_for_edge(Qt.Edge(0)) == Qt.CursorShape.ArrowCursor


def test_frameless_window_has_expected_flags_and_attributes(qtbot) -> None:
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)

    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_frameless_window_enforces_minimum_resize_margin_default() -> None:
    assert RESIZE_MARGIN_PX > 0


def test_apply_theme_updates_theme_property_and_repaints(qtbot) -> None:
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)

    window.apply_theme(load_theme("cyberpunk"))

    assert window.theme.name == "cyberpunk"
    # Must not raise when Qt actually paints the new theme.
    window.grab()


def test_set_opacity_is_clamped_to_allowed_range(qtbot) -> None:
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)

    window.set_opacity(0.05)
    assert window.windowOpacity() == 0.2

    window.set_opacity(5.0)
    assert window.windowOpacity() == 1.0

    window.set_opacity(0.6)
    assert window.windowOpacity() == 0.6


def test_acrylic_disabled_for_themes_that_opt_out(qtbot) -> None:
    window = FramelessWindow(load_theme("minimal"))  # minimal theme has glass.enabled = false
    qtbot.addWidget(window)

    window._try_enable_acrylic()

    assert window._acrylic_enabled is False


def test_theme_property_reflects_current_theme(qtbot) -> None:
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)

    assert window.theme.name == "dark"


def test_drag_from_content_disabled_by_default(qtbot) -> None:
    """Without opting in, a press on a child widget must not start a move --
    this is the pre-fix behavior every other FramelessWindow subclass
    (dialogs, MainWindow) still relies on."""
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)
    label = QLabel("content", window)
    window.refresh_content_drag_filters()  # no-op since drag_from_content=False

    mock_handle = MagicMock()
    window.windowHandle = lambda: mock_handle  # type: ignore[method-assign]

    handled = window.eventFilter(label, _left_press_event())

    assert handled is False
    mock_handle.startSystemMove.assert_not_called()


def test_drag_from_content_starts_system_move_on_child_press(qtbot) -> None:
    """The actual bug fix: content (e.g. a QLabel showing stats) fully
    covers a FloatingWidgetWindow, so a press on it must still be able to
    start dragging the window, not get silently swallowed."""
    window = FramelessWindow(load_theme("dark"), resizable=False, drag_from_content=True)
    qtbot.addWidget(window)
    label = QLabel("content", window)
    window.refresh_content_drag_filters()

    mock_handle = MagicMock()
    window.windowHandle = lambda: mock_handle  # type: ignore[method-assign]

    handled = window.eventFilter(label, _left_press_event())

    assert handled is True
    mock_handle.startSystemMove.assert_called_once()


def test_drag_from_content_does_not_interfere_with_button_clicks(qtbot) -> None:
    """A button inside the content (e.g. the Daily Challenge widget's
    "Solve" button) must keep receiving real clicks instead of every press
    being hijacked into a window drag."""
    window = FramelessWindow(load_theme("dark"), drag_from_content=True)
    qtbot.addWidget(window)
    button = QPushButton("Solve", window)
    window.refresh_content_drag_filters()

    mock_handle = MagicMock()
    window.windowHandle = lambda: mock_handle  # type: ignore[method-assign]
    clicked = MagicMock()
    button.clicked.connect(clicked)

    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    clicked.assert_called_once()
    mock_handle.startSystemMove.assert_not_called()


def test_refresh_content_drag_filters_is_idempotent_for_new_children(qtbot) -> None:
    """Re-rendering content (as FloatingWidgetWindow does on theme/data
    updates) replaces child widgets; calling refresh again must pick up the
    new ones without needing any extra bookkeeping."""
    window = FramelessWindow(load_theme("dark"), resizable=False, drag_from_content=True)
    qtbot.addWidget(window)
    window.refresh_content_drag_filters()

    new_label = QLabel("refreshed content", window)
    window.refresh_content_drag_filters()

    mock_handle = MagicMock()
    window.windowHandle = lambda: mock_handle  # type: ignore[method-assign]
    handled = window.eventFilter(new_label, _left_press_event())

    assert handled is True
    mock_handle.startSystemMove.assert_called_once()


def test_begin_move_or_resize_is_noop_without_a_window_handle(qtbot) -> None:
    window = FramelessWindow(load_theme("dark"))
    qtbot.addWidget(window)
    window.windowHandle = lambda: None  # type: ignore[method-assign]

    window._begin_move_or_resize(QPoint(5, 5))  # must not raise

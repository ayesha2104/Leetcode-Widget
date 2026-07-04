from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.windows.base_frameless_window import (
    RESIZE_MARGIN_PX,
    FramelessWindow,
    cursor_for_edge,
    edge_at,
)

WINDOW_SIZE = QSize(300, 200)


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

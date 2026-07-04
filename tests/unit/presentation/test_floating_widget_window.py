from __future__ import annotations

from codepulse.domain.models.widget import PlacedWidget, WidgetKind, WidgetSize
from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.catalog import SIZE_DIMENSIONS
from codepulse.presentation.windows.floating_widget_window import FloatingWidgetWindow


def _make_window(qtbot, kind: WidgetKind = WidgetKind.STREAK, size: WidgetSize = WidgetSize.SMALL):
    placed = PlacedWidget(uid="abc", kind=kind, size=size)
    window = FloatingWidgetWindow(placed, load_theme("dark"))
    qtbot.addWidget(window)
    return window


def test_window_is_sized_to_match_catalog_dimensions(qtbot) -> None:
    window = _make_window(qtbot, WidgetKind.PROGRESS, WidgetSize.LARGE)

    expected_width, expected_height = SIZE_DIMENSIONS[WidgetSize.LARGE]
    assert window.size().width() == expected_width
    assert window.size().height() == expected_height


def test_remove_button_hidden_until_hover(qtbot) -> None:
    window = _make_window(qtbot)

    assert window._remove_button.isHidden()


def test_remove_button_click_emits_remove_requested(qtbot) -> None:
    window = _make_window(qtbot)

    with qtbot.waitSignal(window.remove_requested, timeout=1000) as blocker:
        window._remove_button.click()

    assert blocker.args == ["abc"]


def test_move_emits_moved_signal_with_uid_and_position(qtbot) -> None:
    window = _make_window(qtbot)
    window.show()

    with qtbot.waitSignal(window.moved, timeout=1000) as blocker:
        window.move(300, 250)

    uid, x, y = blocker.args
    assert uid == "abc"
    assert (x, y) == (300, 250)


def test_apply_theme_rerenders_content_without_raising(qtbot) -> None:
    window = _make_window(qtbot)

    window.apply_theme(load_theme("cyberpunk"))

    assert window.theme.name == "cyberpunk"
    window.grab()

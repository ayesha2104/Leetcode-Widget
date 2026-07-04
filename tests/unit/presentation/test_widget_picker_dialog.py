from __future__ import annotations

from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.presentation.dialogs.widget_picker_dialog import WidgetPickerDialog
from codepulse.presentation.themes.theme_manager import load_theme


def _make_dialog(qtbot) -> WidgetPickerDialog:
    dialog = WidgetPickerDialog(load_theme("leetcode"))
    qtbot.addWidget(dialog)
    return dialog


def test_dialog_constructs_with_fixed_size_and_no_selection(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    assert dialog.size().width() == 760
    assert dialog.size().height() == 560
    assert dialog._active_kind is None


def test_all_catalog_kinds_appear_in_list_by_default(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    assert set(dialog._list_rows) == set(WidgetKind)


def test_search_filters_the_list(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    dialog._search_edit.setText("stre")

    assert set(dialog._list_rows) == {WidgetKind.STREAK}


def test_category_filter_narrows_the_list(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    dialog._on_category_selected("Contest")

    assert set(dialog._list_rows) == {WidgetKind.CONTEST, WidgetKind.RATING}


def test_category_filter_all_restores_full_list(qtbot) -> None:
    dialog = _make_dialog(qtbot)
    dialog._on_category_selected("Contest")

    dialog._on_category_selected("All")

    assert set(dialog._list_rows) == set(WidgetKind)


def test_selecting_a_widget_defaults_to_its_first_size(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    dialog._on_widget_selected(WidgetKind.PROGRESS)

    assert dialog._active_kind == WidgetKind.PROGRESS
    assert dialog._active_size == WidgetSize.SMALL


def test_changing_size_updates_active_size(qtbot) -> None:
    dialog = _make_dialog(qtbot)
    dialog._on_widget_selected(WidgetKind.PROGRESS)

    dialog._set_active_size(WidgetSize.LARGE)

    assert dialog._active_size == WidgetSize.LARGE


def test_add_button_emits_widget_added_and_closes(qtbot) -> None:
    dialog = _make_dialog(qtbot)
    dialog.show()
    dialog._on_widget_selected(WidgetKind.STREAK)

    with qtbot.waitSignal(dialog.widget_added, timeout=1000) as blocker:
        dialog._on_add_clicked()

    assert blocker.args == [WidgetKind.STREAK, WidgetSize.SMALL]
    assert dialog.isHidden()


def test_clicking_a_list_row_selects_it(qtbot) -> None:
    dialog = _make_dialog(qtbot)

    row = dialog._list_rows[WidgetKind.DAILY]
    row.clicked.emit(WidgetKind.DAILY)

    assert dialog._active_kind == WidgetKind.DAILY

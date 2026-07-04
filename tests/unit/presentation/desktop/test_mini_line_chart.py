from __future__ import annotations

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.desktop.mini_line_chart import MiniLineChart


def test_starts_empty_and_paints_without_raising(qtbot) -> None:
    chart = MiniLineChart(load_theme("dark"))
    qtbot.addWidget(chart)
    chart.resize(100, 40)

    chart.grab()  # empty series must not raise


def test_single_value_does_not_raise(qtbot) -> None:
    chart = MiniLineChart(load_theme("dark"), values=[100.0])
    qtbot.addWidget(chart)
    chart.resize(100, 40)

    chart.grab()  # fewer than 2 points must not raise (nothing to draw a line between)


def test_set_values_updates_and_paints(qtbot) -> None:
    chart = MiniLineChart(load_theme("dark"))
    qtbot.addWidget(chart)
    chart.resize(100, 40)

    chart.set_values([1680.0, 1720.0, 1897.0])

    assert chart._values == [1680.0, 1720.0, 1897.0]
    chart.grab()


def test_apply_theme_updates_and_paints(qtbot) -> None:
    chart = MiniLineChart(load_theme("dark"), values=[1.0, 2.0, 3.0])
    qtbot.addWidget(chart)
    chart.resize(100, 40)

    chart.apply_theme(load_theme("cyberpunk"))

    assert chart._theme.name == "cyberpunk"
    chart.grab()

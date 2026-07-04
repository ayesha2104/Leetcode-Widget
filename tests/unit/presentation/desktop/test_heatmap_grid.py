from __future__ import annotations

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.desktop.heatmap_grid import HeatmapGrid


def test_starts_empty_and_paints_without_raising(qtbot) -> None:
    grid = HeatmapGrid(load_theme("dark"))
    qtbot.addWidget(grid)
    grid.resize(140, 40)

    grid.grab()  # empty levels list must not raise


def test_set_levels_updates_and_paints(qtbot) -> None:
    grid = HeatmapGrid(load_theme("dark"))
    qtbot.addWidget(grid)
    grid.resize(140, 40)

    grid.set_levels([0, 1, 2, 3, 4] * 4)

    assert grid._levels == [0, 1, 2, 3, 4] * 4
    grid.grab()


def test_apply_theme_updates_and_paints(qtbot) -> None:
    grid = HeatmapGrid(load_theme("dark"), levels=[1, 2, 3])
    qtbot.addWidget(grid)
    grid.resize(140, 40)

    grid.apply_theme(load_theme("cyberpunk"))

    assert grid._theme.name == "cyberpunk"
    grid.grab()


def test_cell_color_for_zero_level_is_near_transparent(qtbot) -> None:
    grid = HeatmapGrid(load_theme("dark"))

    color = grid._cell_color(0)

    assert color.alpha() < 20


def test_cell_color_for_max_level_uses_theme_success_color(qtbot) -> None:
    theme = load_theme("dark")
    grid = HeatmapGrid(theme)

    color = grid._cell_color(4)

    assert color.alpha() > 200

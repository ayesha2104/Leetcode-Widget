from __future__ import annotations

import pytest

from codepulse.domain.exceptions import ConfigurationError
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.themes.theme_manager import (
    ThemeManager,
    build_stylesheet,
    list_available_themes,
    load_theme,
)

EXPECTED_THEMES = {"cyberpunk", "dark", "glass", "leetcode", "light", "minimal"}


def test_list_available_themes_finds_all_built_in_themes() -> None:
    assert set(list_available_themes()) == EXPECTED_THEMES


@pytest.mark.parametrize("name", sorted(EXPECTED_THEMES))
def test_load_theme_succeeds_for_every_built_in_theme(name: str) -> None:
    theme = load_theme(name)

    assert isinstance(theme, Theme)
    assert theme.name == name
    assert theme.corner_radius > 0


def test_load_theme_raises_for_unknown_name() -> None:
    with pytest.raises(ConfigurationError):
        load_theme("does-not-exist")


def test_build_stylesheet_includes_accent_color() -> None:
    theme = load_theme("dark")

    stylesheet = build_stylesheet(theme)

    assert theme.colors.accent in stylesheet
    assert "QPushButton" in stylesheet


def test_theme_manager_starts_on_default_theme() -> None:
    manager = ThemeManager()

    assert manager.current_theme.name == "dark"


def test_set_theme_emits_signal_and_updates_current(qapp) -> None:
    manager = ThemeManager()
    received: list[Theme] = []
    manager.theme_changed.connect(received.append)

    manager.set_theme("cyberpunk")

    assert manager.current_theme.name == "cyberpunk"
    assert len(received) == 1
    assert received[0].name == "cyberpunk"


def test_set_theme_is_a_noop_when_already_active() -> None:
    manager = ThemeManager()
    received: list[Theme] = []
    manager.theme_changed.connect(received.append)

    manager.set_theme("dark")

    assert received == []


def test_cycle_theme_visits_every_theme_and_wraps_around() -> None:
    manager = ThemeManager()
    seen = {manager.current_theme.name}

    for _ in range(len(EXPECTED_THEMES) - 1):
        manager.cycle_theme()
        seen.add(manager.current_theme.name)

    assert seen == EXPECTED_THEMES

    manager.cycle_theme()
    assert manager.current_theme.name == "dark"

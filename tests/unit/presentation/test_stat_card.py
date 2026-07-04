from __future__ import annotations

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.stat_card import StatCard


def test_stat_card_starts_at_zero(qtbot) -> None:
    card = StatCard("Total Solved", load_theme("dark"))
    qtbot.addWidget(card)

    assert card.displayed_text == "0"
    assert card.current_value == 0.0


def test_set_value_without_animation_updates_immediately(qtbot) -> None:
    card = StatCard("Total Solved", load_theme("dark"))
    qtbot.addWidget(card)

    card.set_value(512, animate=False)

    assert card.displayed_text == "512"
    assert card.current_value == 512


def test_set_value_with_animation_reaches_target(qtbot) -> None:
    card = StatCard("Total Solved", load_theme("dark"))
    qtbot.addWidget(card)

    card.set_value(100, animate=True)

    assert card.current_value == 100
    qtbot.waitUntil(lambda: card.displayed_text == "100", timeout=2000)


def test_custom_value_formatter_is_used(qtbot) -> None:
    card = StatCard("Acceptance Rate", load_theme("dark"), value_formatter=lambda v: f"{v:.1f}%")
    qtbot.addWidget(card)

    card.set_value(63.5, animate=False)

    assert card.displayed_text == "63.5%"


def test_apply_theme_does_not_raise(qtbot) -> None:
    card = StatCard("Total Solved", load_theme("dark"))
    qtbot.addWidget(card)

    card.apply_theme(load_theme("minimal"))
    card.grab()

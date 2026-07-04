from __future__ import annotations

from codepulse.presentation.themes.theme_manager import load_theme
from codepulse.presentation.widgets.progress_ring import ProgressRing


def test_progress_ring_starts_at_zero(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    assert ring.value == 0.0


def test_set_progress_without_animation_updates_immediately(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    ring.set_progress(42, animate=False)

    assert ring.value == 42


def test_set_progress_clamps_above_100(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    ring.set_progress(150, animate=False)

    assert ring.value == 100


def test_set_progress_clamps_below_zero(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    ring.set_progress(-20, animate=False)

    assert ring.value == 0


def test_set_progress_with_animation_reaches_target(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    ring.set_progress(75, animate=True)

    qtbot.waitUntil(lambda: ring.value == 75, timeout=2000)


def test_apply_theme_and_paint_do_not_raise(qtbot) -> None:
    ring = ProgressRing(load_theme("dark"))
    qtbot.addWidget(ring)

    ring.set_progress(50, animate=False)
    ring.apply_theme(load_theme("glass"))
    ring.grab()

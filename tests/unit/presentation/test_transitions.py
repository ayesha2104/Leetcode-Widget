from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QWidget

from codepulse.presentation.animations.transitions import (
    animate_geometry,
    animate_value,
    fade_in,
    fade_out,
)


def test_fade_in_animates_opacity_from_zero_to_one(qtbot) -> None:
    widget = QWidget()
    qtbot.addWidget(widget)

    animation = fade_in(widget, duration_ms=50)

    assert animation.startValue() == 0.0
    assert animation.endValue() == 1.0
    effect = widget.graphicsEffect()
    assert effect is not None
    qtbot.waitUntil(lambda: effect.opacity() == 1.0, timeout=2000)


def test_fade_out_animates_opacity_from_one_to_zero(qtbot) -> None:
    widget = QWidget()
    qtbot.addWidget(widget)

    animation = fade_out(widget, duration_ms=50)

    assert animation.startValue() == 1.0
    assert animation.endValue() == 0.0
    effect = widget.graphicsEffect()
    assert effect is not None
    qtbot.waitUntil(lambda: effect.opacity() == 0.0, timeout=2000)


def test_fade_out_calls_on_finished_callback(qtbot) -> None:
    widget = QWidget()
    qtbot.addWidget(widget)
    called = []

    fade_out(widget, duration_ms=50, on_finished=lambda: called.append(True))

    qtbot.waitUntil(lambda: called == [True], timeout=2000)


def test_animate_geometry_moves_widget_to_end_rect(qtbot) -> None:
    widget = QWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(0, 0, 100, 100)
    end_rect = QRect(50, 50, 200, 200)

    animation = animate_geometry(widget, end_rect, duration_ms=50)

    assert animation.endValue() == end_rect
    qtbot.waitUntil(lambda: widget.geometry() == end_rect, timeout=2000)


def test_animate_value_reaches_end_value(qtbot) -> None:
    widget = QWidget()  # keeps the parentless animation alive for the test's duration
    qtbot.addWidget(widget)
    values: list[float] = []

    animate_value(0.0, 10.0, values.append, duration_ms=50, parent=widget)

    qtbot.waitUntil(lambda: bool(values) and values[-1] == 10.0, timeout=2000)

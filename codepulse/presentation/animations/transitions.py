"""Reusable animation helpers shared by every animated widget.

Every animation is parented to the widget (or an explicit ``parent``) that
owns it so Qt's object tree keeps it alive for the duration of the run --
callers never need to hold their own reference just to prevent garbage
collection.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QRect, QVariantAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

DEFAULT_DURATION_MS = 250


def fade_in(widget: QWidget, duration_ms: int = DEFAULT_DURATION_MS) -> QPropertyAnimation:
    """Fade ``widget`` from transparent to fully opaque."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def fade_out(
    widget: QWidget,
    duration_ms: int = DEFAULT_DURATION_MS,
    on_finished: Callable[[], None] | None = None,
) -> QPropertyAnimation:
    """Fade ``widget`` from fully opaque to transparent, then call ``on_finished``."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.Type.InCubic)
    if on_finished is not None:
        animation.finished.connect(on_finished)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def animate_geometry(
    widget: QWidget,
    end_rect: QRect,
    duration_ms: int = DEFAULT_DURATION_MS,
) -> QPropertyAnimation:
    """Smoothly move/resize ``widget`` to ``end_rect``."""
    animation = QPropertyAnimation(widget, b"geometry", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(widget.geometry())
    animation.setEndValue(end_rect)
    animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def animate_value(
    start: float,
    end: float,
    on_value_changed: Callable[[float], None],
    duration_ms: int = 600,
    parent: QObject | None = None,
) -> QVariantAnimation:
    """Animate a numeric value from ``start`` to ``end``, e.g. for animated counters.

    ``start``/``end`` are always coerced to ``float`` before being handed to
    Qt: ``QVariantAnimation`` infers its interpolator from the *type* of the
    boundary values, and a mismatched int/float pair (e.g. ``0.0`` to ``100``)
    silently produces no interpolation at all rather than raising an error.
    """
    animation = QVariantAnimation(parent)
    animation.setDuration(duration_ms)
    animation.setStartValue(float(start))
    animation.setEndValue(float(end))
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.valueChanged.connect(lambda value: on_value_changed(value))
    animation.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation

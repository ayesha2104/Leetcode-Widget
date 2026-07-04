"""Small shared helpers for desktop widget renderers."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


def make_icon_badge(
    glyph: str,
    size: int,
    background: str,
    *,
    radius: int | None = None,
    parent: QWidget | None = None,
) -> QLabel:
    """A square label showing a glyph/emoji over a rounded colored background."""
    label = QLabel(glyph, parent)
    label.setFixedSize(size, size)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    corner_radius = radius if radius is not None else size // 3
    label.setStyleSheet(
        f"background: {background}; border-radius: {corner_radius}px; font-size: {size // 2}px;"
    )
    return label


def make_pill(text: str, *, color: str, background: str, parent: QWidget | None = None) -> QLabel:
    """A small rounded pill label, e.g. a difficulty badge."""
    label = QLabel(text, parent)
    label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    label.setStyleSheet(
        f"background: {background}; color: {color}; border-radius: 8px;"
        f"padding: 2px 8px; font-size: 10px; font-weight: 600;"
    )
    return label

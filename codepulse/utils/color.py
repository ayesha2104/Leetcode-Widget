"""Parses the CSS-style color strings used in theme JSON files into QColor."""

from __future__ import annotations

import re

from PySide6.QtGui import QColor

_RGBA_PATTERN = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)")


def parse_color(css_color: str) -> QColor:
    """Parse a ``#rrggbb`` or ``rgba(r, g, b, a)`` string into a :class:`QColor`.

    ``a`` in the ``rgba()`` form is a 0-1 float, matching CSS convention and
    the values used throughout ``assets/themes/*.json``.
    """
    match = _RGBA_PATTERN.match(css_color.strip())
    if match:
        r, g, b, a = match.groups()
        return QColor(int(r), int(g), int(b), round(float(a) * 255))
    return QColor(css_color)

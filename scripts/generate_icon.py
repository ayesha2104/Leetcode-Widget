"""Generates CodePulse's application icon.

Draws the same "pulse" glyph used for the tray icon (see
``_build_pulse_icon`` in ``codepulse/presentation/windows/main_window.py``)
and packs it into a multi-size .ico, the format Windows expects for an
.exe's icon and taskbar/shortcut display. Uses Pillow rather than Qt so this
can run in a plain CI/build environment with no display and no QApplication.

Usage::

    python scripts/generate_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

_BASE_SIZE = 256
_ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
_ACCENT = (255, 161, 22, 255)  # LeetCode orange, matches assets/themes/leetcode.json

# An EKG-style heartbeat trace, as fractions of the icon's size: flat, a
# small dip, a tall spike, a deep drop, flat again. Kept in sync with
# _PULSE_TRACE_POINTS in codepulse/presentation/windows/main_window.py so
# the tray icon and this packaged .ico read as the same mark.
_PULSE_TRACE_POINTS = (
    (0.16, 0.50),
    (0.34, 0.50),
    (0.42, 0.34),
    (0.50, 0.66),
    (0.58, 0.14),
    (0.66, 0.72),
    (0.74, 0.50),
    (0.86, 0.50),
)

_OUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "icons" / "codepulse.ico"


def _draw_pulse(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = round(size * 0.0625)
    draw.ellipse((margin, margin, size - margin, size - margin), fill=_ACCENT)

    trace = [(x * size, y * size) for x, y in _PULSE_TRACE_POINTS]
    stroke_width = round(size * 0.09)
    draw.line(trace, fill=(255, 255, 255, 255), width=stroke_width, joint="curve")
    # ImageDraw.line has no round line-cap option, so cap the two open ends
    # (the flat runs on the left/right) with circles to match Qt's RoundCap.
    radius = stroke_width / 2
    for x, y in (trace[0], trace[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, 255))
    return image


def main() -> None:
    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    base = _draw_pulse(_BASE_SIZE)
    base.save(_OUT_PATH, format="ICO", sizes=_ICO_SIZES)
    print(f"Wrote {_OUT_PATH} ({_OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

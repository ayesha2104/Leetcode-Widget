from __future__ import annotations

from codepulse.utils.color import parse_color


def test_parses_hex_color() -> None:
    color = parse_color("#1a1b26")

    assert (color.red(), color.green(), color.blue()) == (0x1A, 0x1B, 0x26)
    assert color.alpha() == 255


def test_parses_rgba_color() -> None:
    color = parse_color("rgba(30, 32, 44, 0.72)")

    assert (color.red(), color.green(), color.blue()) == (30, 32, 44)
    assert color.alpha() == round(0.72 * 255)


def test_parses_rgba_with_whitespace_variations() -> None:
    color = parse_color("rgba(1,2,3,1)")

    assert (color.red(), color.green(), color.blue(), color.alpha()) == (1, 2, 3, 255)

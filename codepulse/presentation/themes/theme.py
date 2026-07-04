"""Typed representation of a theme JSON file under ``assets/themes/``.

Themes are a presentation-only concept -- nothing outside
``codepulse.presentation`` should ever import from this module.
"""

from __future__ import annotations

from pydantic import BaseModel


class ThemeColors(BaseModel):
    """Semantic color tokens every theme must define.

    Widgets read colors by role (``accent``, ``error``, ...) rather than by
    literal value, so swapping themes never requires touching widget code.
    """

    background: str
    surface: str
    surface_alt: str
    border: str
    text_primary: str
    text_secondary: str
    accent: str
    accent_secondary: str
    success: str
    warning: str
    error: str


class GlassConfig(BaseModel):
    """Glassmorphism parameters for the main window backdrop."""

    enabled: bool
    blur_radius: int
    background_alpha: float


class Theme(BaseModel):
    """A complete, validated theme loaded from JSON."""

    name: str
    display_name: str
    colors: ThemeColors
    glass: GlassConfig
    corner_radius: int

"""Best-effort Windows acrylic backdrop blur via the undocumented
``SetWindowCompositionAttribute`` API.

This API is what Windows itself uses for the acrylic blur behind the Start
menu and Action Center. It is undocumented and can change between Windows
releases, so every call here is defensive: failure is logged and swallowed,
and the caller falls back to a plain semi-transparent fill (still
glassmorphic, just without the live backdrop blur).
"""

from __future__ import annotations

import ctypes

from loguru import logger
from PySide6.QtGui import QColor

_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
_WCA_ACCENT_POLICY = 19


class _AccentPolicy(ctypes.Structure):
    _fields_ = (
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int),
    )


class _WindowCompositionAttribData(ctypes.Structure):
    _fields_ = (
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(_AccentPolicy)),
        ("SizeOfData", ctypes.c_size_t),
    )


def _pack_gradient_color(color: QColor) -> int:
    """Pack a QColor into the 0xAABBGGRR format the accent policy expects."""
    return (color.alpha() << 24) | (color.blue() << 16) | (color.green() << 8) | color.red()


def enable_acrylic_blur(window_handle: int, tint: QColor) -> bool:
    """Enable acrylic blur-behind on the window identified by ``window_handle``.

    Returns ``True`` on success, ``False`` if the API is unavailable or the
    call fails for any reason -- callers should treat ``False`` as "fall
    back to plain translucency", not as an error worth surfacing to the user.
    """
    try:
        accent = _AccentPolicy()
        accent.AccentState = _ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.GradientColor = _pack_gradient_color(tint)

        data = _WindowCompositionAttribData()
        data.Attribute = _WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.pointer(accent)

        set_window_composition_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
        result = set_window_composition_attribute(window_handle, ctypes.pointer(data))
        return bool(result)
    except (AttributeError, OSError) as exc:
        logger.warning("Acrylic blur unavailable, falling back to plain translucency: {}", exc)
        return False

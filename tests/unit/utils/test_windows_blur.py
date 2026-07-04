from __future__ import annotations

from PySide6.QtGui import QColor

from codepulse.utils.windows_blur import enable_acrylic_blur


def test_enable_acrylic_blur_never_raises_on_invalid_handle() -> None:
    # Handle 0 is never a valid HWND; this exercises the failure path and
    # proves the caller gets a clean bool back instead of an exception.
    result = enable_acrylic_blur(0, QColor("#1a1b26"))

    assert isinstance(result, bool)

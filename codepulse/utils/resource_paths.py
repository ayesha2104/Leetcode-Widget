"""Resolves the ``assets/`` directory in both source and frozen (PyInstaller) form.

PyInstaller one-file builds unpack bundled data into a temporary directory
exposed as ``sys._MEIPASS``; running from source, assets live at the repo
root next to the ``codepulse`` package. Every module that needs a theme,
icon, font, or animation resource goes through :func:`get_assets_dir` rather
than constructing its own relative path.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_assets_dir() -> Path:
    """Return the absolute path to the ``assets/`` directory."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root is not None:
        return Path(frozen_root) / "assets"

    return Path(__file__).resolve().parent.parent.parent / "assets"

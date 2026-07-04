"""Forces the Qt offscreen platform plugin for the whole test session.

Must run before PySide6 creates its ``QApplication`` (and therefore before
any test module imports widgets), so tests never flash a real window and
pass identically on a machine with no display attached.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

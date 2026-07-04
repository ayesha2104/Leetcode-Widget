"""Dev-only visual QA harness for the MainWindow control panel (Phase 5b).

Not part of the shipped application. Usage::

    python scripts/preview_ui.py --theme leetcode --out preview.png
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from codepulse.infrastructure.persistence.json_desktop_layout_repository import (  # noqa: E402
    JsonDesktopLayoutRepository,
)
from codepulse.presentation.desktop_widget_manager import DesktopWidgetManager  # noqa: E402
from codepulse.presentation.themes.theme_manager import ThemeManager  # noqa: E402
from codepulse.presentation.windows.main_window import MainWindow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Render MainWindow for visual inspection.")
    parser.add_argument("--theme", default="dark")
    parser.add_argument("--out", default="preview.png")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    theme_manager = ThemeManager(args.theme)
    layout_path = Path(tempfile.mkdtemp()) / "layout.json"
    widget_manager = DesktopWidgetManager(JsonDesktopLayoutRepository(layout_path), theme_manager)

    window = MainWindow(theme_manager, widget_manager)
    window.show()
    app.processEvents()

    pixmap = window.grab()
    pixmap.save(args.out)
    print(f"Saved preview to {args.out}")


if __name__ == "__main__":
    main()

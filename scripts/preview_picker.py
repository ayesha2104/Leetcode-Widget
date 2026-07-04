"""Dev-only visual QA harness for the widget picker dialog (Phase 5a).

Not part of the shipped application. Usage::

    python scripts/preview_picker.py --kind progress --size large --out out.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from codepulse.domain.models.widget import WidgetKind  # noqa: E402
from codepulse.presentation.dialogs.widget_picker_dialog import WidgetPickerDialog  # noqa: E402
from codepulse.presentation.themes.theme_manager import ThemeManager  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the widget picker for visual inspection.")
    parser.add_argument("--theme", default="leetcode")
    parser.add_argument(
        "--kind", default=WidgetKind.PROGRESS.value, choices=[k.value for k in WidgetKind]
    )
    parser.add_argument("--out", default="picker_preview.png")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    theme_manager = ThemeManager(args.theme)
    dialog = WidgetPickerDialog(theme_manager.current_theme)
    dialog._on_widget_selected(WidgetKind(args.kind))
    dialog.show()
    app.processEvents()

    pixmap = dialog.grab()
    pixmap.save(args.out)
    print(f"Saved preview to {args.out}")


if __name__ == "__main__":
    main()

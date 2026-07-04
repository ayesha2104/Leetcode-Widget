"""Builds the CodePulse Windows executable.

Thin wrapper around PyInstaller so contributors don't need to remember the
spec file path or clean stale build artifacts by hand.

Usage::

    python scripts/build.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC_FILE = _ROOT / "codepulse.spec"


def main() -> int:
    for stale_dir in ("build", "dist"):
        shutil.rmtree(_ROOT / stale_dir, ignore_errors=True)

    icon_path = _ROOT / "assets" / "icons" / "codepulse.ico"
    if not icon_path.exists():
        print("No icon found; generating one first...")
        subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "generate_icon.py")],
            cwd=_ROOT,
            check=True,
        )

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(_SPEC_FILE)],
        cwd=_ROOT,
    )
    if result.returncode != 0:
        return result.returncode

    exe_path = _ROOT / "dist" / "CodePulse.exe"
    if exe_path.exists():
        print(f"Built {exe_path} ({exe_path.stat().st_size / (1024 * 1024):.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

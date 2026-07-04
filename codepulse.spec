# PyInstaller build spec for CodePulse.
#
# Produces a single-file Windows .exe with no console window. Run via
# `python scripts/build.py`, or directly with `pyinstaller codepulse.spec`.
#
# Bundles assets/ (themes, icons) as data files, resolved at runtime through
# codepulse.utils.resource_paths.get_assets_dir(), which checks
# sys._MEIPASS -- the temp dir PyInstaller's one-file bootloader unpacks
# bundled data into -- before falling back to the source-tree path.

from __future__ import annotations

from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

a = Analysis(
    ["codepulse/main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "assets"), "assets"),
    ],
    hiddenimports=[
        "windows_toasts",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CodePulse",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "icons" / "codepulse.ico"),
)

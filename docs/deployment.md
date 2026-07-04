# Deployment / packaging

How CodePulse goes from source to a distributable Windows `.exe`.

## Building the executable

```powershell
pip install -e ".[dev]"
python scripts/build.py
```

This wraps PyInstaller with `codepulse.spec` and produces
`dist/CodePulse.exe` — a single file, no console window
(`console=False`), with the icon at `assets/icons/codepulse.ico` embedded.
`scripts/build.py` clears stale `build/`/`dist/` directories first and
generates the icon automatically if it's missing
(`scripts/generate_icon.py`, which draws the same "pulse" glyph used for
the tray icon and needs Pillow — included in the `dev` extra).

**Run the build with the same Python environment CodePulse itself runs
in** (the project's `.venv`, with `PySide6`/`loguru`/`pydantic-settings`/
`windows-toasts` installed) — not a bare system Python. PyInstaller only
bundles what it can actually import during analysis; running it from an
environment missing CodePulse's dependencies produces an `.exe` that
launches and immediately crashes with `ModuleNotFoundError` for whatever
wasn't installed.

### How bundled assets are found at runtime

Theme JSON files and the icon are bundled as data via `codepulse.spec`'s
`datas` list (`assets/` → `assets/` inside the bundle). At runtime,
`codepulse/utils/resource_paths.py`'s `get_assets_dir()` checks
`sys._MEIPASS` (the temp directory PyInstaller's one-file bootloader
unpacks bundled data into) first, falling back to the source-tree path when
running unpackaged. No other code should construct an assets path by hand.

### Verifying a build actually works

Passing tests and a successful PyInstaller run are necessary but not
sufficient — always launch the produced `.exe` at least once and confirm:

1. It opens the control-panel window (no immediate crash / traceback).
2. `%LOCALAPPDATA%\CodePulse\` (or `CODEPULSE_DATA_DIR` if set) gets
   populated with `settings.json` and `codepulse.db` — proof composition
   and first-run persistence both worked, not just that the process
   started.
3. **Add Widget** opens the picker and a widget can actually be placed.

To test against a throwaway data directory instead of your real one, set
`CODEPULSE_DATA_DIR` before launching:

```powershell
$env:CODEPULSE_DATA_DIR = "$env:TEMP\codepulse_smoke_test"
.\dist\CodePulse.exe
```

## Code signing

The current build is **not code-signed**. Windows SmartScreen will show an
"unrecognized app" warning on first run for anyone who isn't the person who
built it. This is acceptable for personal/dev use; before any wider
distribution, the `.exe` should be signed with a code-signing certificate
(e.g. via `signtool sign /fd sha256 dist\CodePulse.exe`) — not set up yet,
since there's no distribution channel or certificate for this project yet.

## Starting with Windows

This is a per-user preference, not a packaging step: `SettingsDialog`'s
"Start with Windows" toggle calls
`codepulse.infrastructure.os.windows_startup.set_start_with_windows()`,
which adds/removes a value under
`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` pointing
at the running executable's path (`sys.executable` when frozen). No
separate installer or scheduled task is involved.

## Continuous integration

`.github/workflows/ci.yml` runs on every push/PR: `ruff check .`,
`black --check .`, `mypy codepulse`, and `pytest` on a `windows-latest`
runner with `QT_QPA_PLATFORM=offscreen` (no packaging step — CI verifies
correctness, it doesn't publish artifacts). Building and distributing the
`.exe` is a manual, deliberate step for now (see above), not part of CI.

## What's not automated yet

- No auto-update mechanism (the app doesn't check for or fetch new
  versions).
- No installer (`.msi`/`.exe` installer with Start Menu shortcut,
  uninstall entry) — CodePulse currently ships as one portable `.exe`.
- No signed releases / no publish-to-GitHub-Releases CI step.

These are reasonable next steps once the project moves past "test build for
personal use," not gaps in the current single-user workflow.

# Installation

CodePulse targets Windows 10/11 and Python 3.12+. Two ways to run it: from
source (for development) or as a packaged `.exe` (for everyday use).

## Option A — packaged executable

1. Build it yourself (there is no public release yet — see
   [deployment.md](deployment.md#building-the-executable)), or ask a
   maintainer for `dist/CodePulse.exe`.
2. Copy `CodePulse.exe` anywhere you like and double-click it. No installer,
   no admin rights, no separate Python install required — everything
   (PySide6, themes, the icon) is bundled inside the one file.
3. On first launch, CodePulse creates its data directory under
   `%LOCALAPPDATA%\CodePulse\` (settings, cache database, goals, logs) and
   opens the small control-panel window. Click **+ Add Widget** to open the
   picker gallery and place your first widget.
4. Open **Settings** and enter your LeetCode username so widgets can fetch
   real data instead of sample data.

Windows Defender/SmartScreen may warn about an unrecognized publisher the
first time you run an unsigned `.exe` — this build is not code-signed (see
[deployment.md](deployment.md#code-signing)). Choose "More info → Run
anyway" if you built it yourself and trust the source.

## Option B — from source (development)

```powershell
git clone <repo-url> "CodePulse"
cd CodePulse
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,docs]"
python -m codepulse.main
```

Requirements:

- Windows 10/11 (the acrylic blur effect, startup registry entry, and toast
  notifications are all Win32-specific; CodePulse is not cross-platform)
- Python 3.12 or newer
- No external services or API keys — the LeetCode provider uses LeetCode's
  public GraphQL endpoint

## Configuration

Runtime behavior can be overridden via environment variables (see
`.env.example` in the repository root); copy it to `.env` if you need non-default
values (e.g. a custom `CODEPULSE_DATA_DIR` for isolated test data). This is
separate from user-facing preferences (username, theme, refresh interval,
...), which are configured entirely through the in-app **Settings** dialog
and persisted automatically — nothing to hand-edit for normal use.

## Uninstalling

CodePulse writes no registry keys except the optional "start with Windows"
entry (toggled off automatically when you disable that setting) and its
AUMID registration for toast notifications. To fully remove it: disable
"start with Windows" in Settings, close the app, delete the `.exe`, and
delete `%LOCALAPPDATA%\CodePulse\` if you don't want to keep your cached
stats/goals.

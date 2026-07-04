# CodePulse

> Your coding journey, always in sight.

CodePulse is a lightweight, always-on-top desktop widget system for Windows
that surfaces live coding statistics — streaks, problems solved, contest
rating, daily challenge status — without ever getting in your way. Instead
of one fixed dashboard, you add independent floating widgets one at a time
from a picker gallery, each its own draggable, always-on-top window that
sits on your desktop.

It launches fast, works offline from cache, and never blocks its UI on a
network call.

## Features

- **Pick-your-own widget layout** — add Streak, Progress, Contest, Rating,
  Daily Challenge, Recent Activity, Goals, or Badges widgets one at a time
  from an "Add Widget" gallery, each in small/medium/large sizes
- **Real LeetCode data** — Streak, Progress, Daily Challenge, and Goals
  widgets show your actual stats, refreshed automatically in the
  background
- **Goal tracking** — set targets against total solved, hard solved, day
  streak, or contest rating, and watch progress bars update live
- **Windows toast notifications** — goal achieved, new streak record, and a
  once-daily reminder for today's challenge
- **6 themes**, adjustable opacity, draggable/resizable frameless windows
  with a glassmorphic acrylic-blur look
- **Offline-first** — cached data shows instantly on launch; a failed
  refresh never blanks the screen
- **Start with Windows** toggle, system tray icon, no admin rights required

LeetCode is the first supported platform. The provider layer is designed so
GitHub, Codeforces, CodeChef, HackerRank, and AtCoder can be added later
without touching existing code — see [docs/architecture.md](docs/architecture.md).

**Known limitation:** Contest, Rating, Activity, and Badges widgets
currently show sample data — LeetCode's public API doesn't expose an
upcoming-contest schedule or rating history, and there's no data source at
all for activity/badges yet.

## Install & run

**Option 1 — packaged .exe** (no Python required):

```powershell
git clone https://github.com/ayesha2104/Leetcode-Widget.git
cd Leetcode-Widget
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python scripts/build.py
```

Then double-click `dist\CodePulse.exe`. See [docs/installation.md](docs/installation.md)
for the full walkthrough, including the SmartScreen warning you'll see on
first run (the build isn't code-signed).

**Option 2 — run from source:**

```powershell
git clone https://github.com/ayesha2104/Leetcode-Widget.git
cd Leetcode-Widget
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m codepulse.main
```

Either way: on first launch, open **Settings** and enter your LeetCode
username so widgets fetch real data instead of sample data, then click
**+ Add Widget** to place your first one.

Requires Windows 10/11 and Python 3.12+ (the acrylic blur, startup entry,
and toast notifications are all Win32-specific, so this isn't
cross-platform). No API keys or external services needed.

## Documentation

Full docs (architecture, installation, developer guide, deployment, API
reference) live under [`docs/`](docs/) and build as a static site via
MkDocs (`mkdocs serve`):

- [docs/architecture.md](docs/architecture.md) — clean architecture layers,
  the multi-widget model, threading, caching
- [docs/installation.md](docs/installation.md)
- [docs/developer_guide.md](docs/developer_guide.md) — how to add a widget
  or a new provider
- [docs/deployment.md](docs/deployment.md) — building and shipping the
  `.exe`

## Project layout

```
codepulse/
  domain/            # Entities, value objects, and abstract interfaces. No framework deps.
  application/       # Use-case services orchestrating domain interfaces.
  infrastructure/    # Concrete adapters: providers, persistence, notifications, logging, config.
  presentation/      # PySide6 windows, widgets, dialogs, themes, animations, view models.
  utils/             # Cross-cutting, framework-agnostic helpers.
assets/              # Theme JSON, icons, fonts, animation resources.
tests/               # Unit and integration tests, mirroring the package layout.
docs/                # Architecture, guides, diagrams (MkDocs site).
scripts/             # Build and dev tooling (PyInstaller, icon generation).
```

Full rationale for this structure is in [docs/architecture.md](docs/architecture.md).

## Development

```powershell
pip install -e ".[dev,docs]"
pytest                       # 303 tests, 97.83% coverage (fail_under = 90)
ruff check .
black --check .
mypy codepulse
```

All four are enforced in CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
on every push/PR. Tech stack: Python 3.12+, PySide6, httpx, asyncio +
QThread, SQLite + JSON cache, loguru, pydantic-settings, PyInstaller,
pytest, ruff, black, mypy, MkDocs, GitHub Actions.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, quality gates, and the
architectural rules a PR is expected to follow.

## License

MIT — see [LICENSE](LICENSE).

# Developer guide

This is the practical, day-to-day companion to [architecture.md](architecture.md)
(the "why it's shaped this way") — how to actually build, test, and extend
CodePulse.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,docs]"
```

Run the app: `python -m codepulse.main`. Run it against an isolated data
directory (recommended while developing, so you don't clobber your real
settings/cache) with `CODEPULSE_DATA_DIR` set in `.env` or the environment.

## Quality gates

Every change should pass all four before being committed:

```powershell
ruff check .
black --check .
mypy codepulse
pytest
```

`pytest` runs with `--cov=codepulse --cov-report=term-missing` and
`fail_under = 90` (see `pyproject.toml`); a change that drops coverage below
90% fails the suite. `mypy` runs in `--strict` mode against `codepulse/`
only — `tests/`, `scripts/`, `build/`, and `dist/` are excluded.

Tests run headless via `QT_QPA_PLATFORM=offscreen`, set in
`tests/conftest.py` — you do not need a real display, and CI (a Windows
runner) doesn't have one by default either.

## Rendering something without running the whole app

Two preview scripts render UI in isolation and save a PNG, useful for
visually checking a widget or theme change without clicking through the
picker each time:

```powershell
python scripts/preview_ui.py --theme leetcode --out preview.png
python scripts/preview_picker.py --kind progress --out preview.png
```

`scripts/benchmark_startup.py` measures startup time, memory, and idle CPU
against the project's performance targets (see architecture.md's threading
section) — run it after any change that touches composition-root wiring or
adds a new background timer.

## Adding a new widget kind

1. Add the new value to `WidgetKind` (`codepulse/domain/models/widget.py`).
2. Add a renderer module under `codepulse/presentation/widgets/desktop/`
   matching the existing signature: `render(size, theme, snapshot=None)`
   (or `render(size, theme, snapshot=None, goal_progress=None)` if it needs
   goal data — see the Goals widget for that pattern).
3. Register it in `codepulse/presentation/widgets/desktop/registry.py`'s
   `render_widget()` dispatch and in `WidgetPickerDialog`'s gallery list so
   users can actually add it.
4. If it needs new data, add the field to `DashboardSnapshot`
   (`codepulse/application/dto/dashboard_snapshot.py`) and populate it in
   `StatsService.refresh_snapshot()`. If no provider exposes that data yet,
   say so explicitly in the renderer's docstring rather than silently
   showing sample data forever (see the Contest/Rating widgets for the
   existing convention).
5. Add a test under `tests/unit/presentation/desktop/` rendering it with
   `qtbot` against both a populated snapshot and `snapshot=None` (the
   pre-first-refresh state).

## Adding a new provider (e.g. Codeforces)

1. Create `codepulse/infrastructure/providers/codeforces/` with a client,
   a raw-JSON-to-domain mapper, and a class implementing
   `ProviderInterface` (`codepulse/domain/interfaces/provider.py`).
2. Register it in `codepulse/infrastructure/providers/registry.py`.
3. If the platform exposes a stat type no existing domain model covers,
   add it there (not to a provider-specific model) — the application layer
   should never need to know which provider a `DashboardSnapshot` field
   came from.
4. Nothing in `application/` or `presentation/` should need to change
   beyond an added `"codeforces"` choice in the provider-selection UI, if
   any — that's the point of the interface boundary.

## Where things live, quickly

| Looking for...                          | Look in...                                              |
|------------------------------------------|----------------------------------------------------------|
| A domain model or interface               | `codepulse/domain/`                                       |
| Business rules (goal %, notification logic) | `codepulse/application/services/`                       |
| LeetCode API calls                         | `codepulse/infrastructure/providers/leetcode/`           |
| Where preferences/goals/layout are saved   | `codepulse/infrastructure/persistence/`                  |
| A window, dialog, or widget renderer       | `codepulse/presentation/`                                |
| Theme colors                               | `assets/themes/*.json`                                    |
| Refresh-cycle / threading logic            | `codepulse/presentation/desktop_widget_manager.py`, `codepulse/presentation/workers/stats_refresh_worker.py` |

## Common pitfalls (learned the hard way)

- **`QVariantAnimation`/`QPropertyAnimation` silently do nothing** if the
  start and end values aren't the same type (e.g. `int` vs. `float`) —
  coerce both to `float` explicitly.
- **A parentless animation gets garbage-collected mid-flight.** Always pass
  a `parent` QObject when constructing one, especially in tests.
- **`DeleteWhenStopped` deletes the animation object once it finishes** —
  don't call `.state()` on it afterward; assert on the side effect (opacity,
  geometry) instead.
- **ctypes Win32 calls need explicit `argtypes`/`restype`.** Without them,
  ctypes silently mis-marshals pointers on 64-bit and you get zeroed structs
  with no error — see `scripts/benchmark_startup.py` for the pattern.
- **Toasts can "succeed" and never appear.** `windows-toasts` doesn't
  validate the app ID you give it. If you're touching `WindowsNotifier`,
  verify by actually watching for a toast on a real desktop, not just
  checking that `show_toast()` didn't raise.
- **`coverage.py` can't see inside a `QThread`'s `run()`** — it's a real OS
  thread, not a `threading.Thread`. Mark untestable lines there
  `# pragma: no cover` rather than chasing unreachable coverage.

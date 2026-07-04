# Contributing to CodePulse

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,docs]"
pytest
```

See [docs/developer_guide.md](docs/developer_guide.md) for how the project
is organized, how to add a widget or provider, and known pitfalls; see
[docs/architecture.md](docs/architecture.md) for the reasoning behind the
layer boundaries.

## Before opening a PR

All four must pass — CI (`.github/workflows/ci.yml`) enforces the same:

```powershell
ruff check .
black --check .
mypy codepulse
pytest
```

- `mypy --strict` applies to `codepulse/`; type hints are required on all
  new functions there.
- Coverage must stay at or above 90% (`fail_under = 90` in
  `pyproject.toml`). If a line genuinely can't be covered (e.g. code inside
  a `QThread.run()` — see developer_guide.md), mark it
  `# pragma: no cover` with a one-line reason, don't just leave it uncovered.
- Format with `black .` before committing; `ruff check . --fix` handles
  most lint issues automatically.

## Architectural rules that will get a PR asked to change

- **Dependencies point inward only.** `codepulse/domain/` must never import
  PySide6, httpx, sqlite3, or anything from `application/`,
  `infrastructure/`, or `presentation/`. `application/` may depend on
  `domain/` interfaces but not on concrete `infrastructure/` classes.
- **New providers/widgets are additive**, not conditionals sprinkled through
  existing code — see "Adding a new widget kind" / "Adding a new provider"
  in the developer guide for the exact seams to extend.
- **The UI thread never blocks on network I/O.** Any new network call goes
  through a `QThread` (following `StatsRefreshWorker`'s pattern), reporting
  back via Qt signals only.
- **No feature that only "seems" to work.** If you touch notifications,
  persistence, or anything OS-integration-shaped (registry, toasts, startup
  entry), verify it against the real thing at least once — several bugs in
  this project (notably toast notifications silently not appearing) were
  invisible to unit tests and only caught by running the app for real.

## Commit / PR conventions

- Focused commits over one giant diff; a commit message should explain
  *why*, not restate the diff.
- Don't add speculative abstractions, config flags, or error handling for
  cases that can't currently happen — see the project's general engineering
  guidelines for the reasoning (YAGNI over premature flexibility).
- Update the relevant `docs/*.md` page in the same PR if you change
  behavior it documents — stale docs are worse than no docs.

## Reporting bugs

Include: what you did, what you expected, what happened, and — for
anything UI/notification/OS-integration related — whether you confirmed it
on a real Windows desktop or only in the test suite.

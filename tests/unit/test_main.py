from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import codepulse.main as main_module
from codepulse.infrastructure.config.settings import AppSettings


def test_main_wires_everything_and_returns_exec_exit_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, qapp
) -> None:
    """Exercises the whole composition root without blocking on the real event loop.

    WindowsNotifier is mocked so this never touches the real registry;
    QApplication.exec is mocked so this never blocks waiting for a user to
    close the app.
    """
    monkeypatch.setattr(main_module, "get_app_settings", lambda: AppSettings(data_dir=tmp_path))
    monkeypatch.setattr(main_module, "WindowsNotifier", MagicMock())
    # pytest-qt's `qapp` fixture already constructed the process's one-and-only
    # QApplication; main() must reuse it rather than construct a second one.
    monkeypatch.setattr(main_module, "QApplication", MagicMock(return_value=qapp))
    monkeypatch.setattr(qapp, "exec", lambda: 42)

    exit_code = main_module.main()

    assert exit_code == 42
    # Composition succeeded end-to-end: defaults were persisted on first run.
    assert (tmp_path / "settings.json").exists()

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codepulse.infrastructure.config.settings import AppSettings, get_app_settings


def test_explicit_data_dir_is_respected(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path)

    assert settings.resolved_data_dir == tmp_path
    assert settings.database_path == tmp_path / "codepulse.db"
    assert settings.settings_file_path == tmp_path / "settings.json"
    assert settings.desktop_layout_file_path == tmp_path / "desktop_layout.json"
    assert settings.goals_file_path == tmp_path / "goals.json"
    assert settings.notification_state_file_path == tmp_path / "notification_state.json"
    assert settings.log_dir == tmp_path / "logs"


def test_falls_back_to_local_app_data_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Test\AppData\Local")
    settings = AppSettings(data_dir=None)

    assert settings.resolved_data_dir == Path(os.environ["LOCALAPPDATA"]) / "CodePulse"


def test_falls_back_to_home_dir_when_no_local_app_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    settings = AppSettings(data_dir=None)

    assert settings.resolved_data_dir == Path.home() / ".codepulse"


def test_get_app_settings_returns_a_cached_singleton() -> None:
    assert get_app_settings() is get_app_settings()

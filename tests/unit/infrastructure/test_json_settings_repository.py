from __future__ import annotations

from pathlib import Path

from codepulse.domain.models.preferences import ThemeName, UserPreferences
from codepulse.infrastructure.persistence.json_settings_repository import (
    JsonSettingsRepository,
)


def test_load_creates_file_with_defaults_when_missing(tmp_path: Path) -> None:
    file_path = tmp_path / "settings.json"
    repository = JsonSettingsRepository(file_path)

    preferences = repository.load()

    assert preferences == UserPreferences()
    assert file_path.exists()


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    file_path = tmp_path / "settings.json"
    repository = JsonSettingsRepository(file_path)
    preferences = UserPreferences(username="octocat", theme=ThemeName.CYBERPUNK, opacity=0.7)

    repository.save(preferences)
    loaded = repository.load()

    assert loaded == preferences


def test_corrupt_file_falls_back_to_defaults_and_backs_up(tmp_path: Path) -> None:
    file_path = tmp_path / "settings.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    repository = JsonSettingsRepository(file_path)
    preferences = repository.load()

    assert preferences == UserPreferences()
    backups = list(tmp_path.glob("settings.corrupt-*.json"))
    assert len(backups) == 1


def test_save_is_atomic_no_tmp_file_left_behind(tmp_path: Path) -> None:
    file_path = tmp_path / "settings.json"
    repository = JsonSettingsRepository(file_path)

    repository.save(UserPreferences())

    assert not file_path.with_suffix(".tmp").exists()

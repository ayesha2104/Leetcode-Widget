from __future__ import annotations

from pathlib import Path

import pytest

from codepulse.domain.models.preferences import ThemeName, UserPreferences
from codepulse.infrastructure.persistence.json_settings_repository import (
    JsonSettingsRepository,
)
from codepulse.presentation.dialogs.settings_dialog import SettingsDialog
from codepulse.presentation.themes.theme_manager import ThemeManager


@pytest.fixture
def repository(tmp_path: Path) -> JsonSettingsRepository:
    return JsonSettingsRepository(tmp_path / "settings.json")


def test_dialog_populates_form_from_existing_preferences(
    qtbot, repository: JsonSettingsRepository
) -> None:
    repository.save(UserPreferences(username="octocat", theme=ThemeName.CYBERPUNK, opacity=0.7))

    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)

    assert dialog._username_edit.text() == "octocat"
    assert dialog._theme_combo.currentData() == "cyberpunk"
    assert dialog._opacity_slider.value() == 70


def test_dialog_defaults_when_nothing_saved_yet(qtbot, repository: JsonSettingsRepository) -> None:
    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)

    assert dialog._username_edit.text() == ""
    assert dialog._always_on_top_check.isChecked() is True


def test_save_persists_form_values(qtbot, repository: JsonSettingsRepository) -> None:
    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)

    dialog._username_edit.setText("new-username")
    dialog._opacity_slider.setValue(55)
    dialog._refresh_interval_spin.setValue(20)
    dialog._always_on_top_check.setChecked(False)

    dialog._on_save_clicked()

    saved = repository.load()
    assert saved.username == "new-username"
    assert saved.opacity == 0.55
    assert saved.refresh_interval_minutes == 20
    assert saved.always_on_top is False


def test_save_emits_settings_saved_with_new_preferences(
    qtbot, repository: JsonSettingsRepository
) -> None:
    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)
    dialog._username_edit.setText("octocat")

    with qtbot.waitSignal(dialog.settings_saved, timeout=1000) as blocker:
        dialog._on_save_clicked()

    (preferences,) = blocker.args
    assert preferences.username == "octocat"


def test_save_applies_theme_immediately(qtbot, repository: JsonSettingsRepository) -> None:
    theme_manager = ThemeManager("dark")
    dialog = SettingsDialog(repository, theme_manager)
    qtbot.addWidget(dialog)

    index = dialog._theme_combo.findData("cyberpunk")
    dialog._theme_combo.setCurrentIndex(index)
    dialog._on_save_clicked()

    assert theme_manager.current_theme.name == "cyberpunk"


def test_save_closes_dialog(qtbot, repository: JsonSettingsRepository) -> None:
    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)
    dialog.show()

    dialog._on_save_clicked()

    assert dialog.isHidden()


def test_empty_username_is_stored_as_none(qtbot, repository: JsonSettingsRepository) -> None:
    dialog = SettingsDialog(repository, ThemeManager())
    qtbot.addWidget(dialog)
    dialog._username_edit.setText("   ")

    dialog._on_save_clicked()

    assert repository.load().username is None

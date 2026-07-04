"""JSON-file-backed implementation of :class:`SettingsRepository`."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from codepulse.domain.exceptions import SettingsPersistenceError
from codepulse.domain.interfaces.settings_repository import SettingsRepository
from codepulse.domain.models.preferences import UserPreferences


class JsonSettingsRepository(SettingsRepository):
    """Persists :class:`UserPreferences` as a single JSON file.

    Writes are atomic (write to a temp file, then ``os.replace``) so a crash
    or power loss mid-write cannot leave a half-written, unparsable file
    behind. A corrupt file on read is backed up alongside the original and
    replaced with defaults rather than crashing the application.
    """

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def load(self) -> UserPreferences:
        if not self._file_path.exists():
            defaults = UserPreferences()
            self.save(defaults)
            return defaults

        try:
            raw = self._file_path.read_text(encoding="utf-8")
            return UserPreferences.model_validate_json(raw)
        except (OSError, ValidationError, ValueError) as exc:
            logger.warning(
                "Corrupt settings file at {}: {}; backing up and restoring defaults",
                self._file_path,
                exc,
            )
            self._backup_corrupt_file()
            defaults = UserPreferences()
            self.save(defaults)
            return defaults

    def save(self, preferences: UserPreferences) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._file_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(preferences.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp_path, self._file_path)
        except OSError as exc:
            raise SettingsPersistenceError(f"Failed to save settings to {self._file_path}") from exc

    def _backup_corrupt_file(self) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self._file_path.with_suffix(f".corrupt-{timestamp}.json")
        try:
            shutil.copy2(self._file_path, backup_path)
        except OSError as exc:
            logger.warning("Could not back up corrupt settings file: {}", exc)

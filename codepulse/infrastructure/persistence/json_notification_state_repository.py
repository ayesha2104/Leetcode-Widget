"""JSON-file-backed implementation of :class:`NotificationStateRepository`."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from codepulse.domain.exceptions import NotificationStatePersistenceError
from codepulse.domain.interfaces.notification_state_repository import (
    NotificationStateRepository,
)
from codepulse.domain.models.notification_state import NotificationState


class JsonNotificationStateRepository(NotificationStateRepository):
    """Persists :class:`NotificationState` as a single JSON file.

    Mirrors :class:`~codepulse.infrastructure.persistence.json_settings_repository.JsonSettingsRepository`:
    atomic writes and corrupt-file recovery (back up, then fall back to
    defaults) instead of crashing.
    """

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def load(self) -> NotificationState:
        if not self._file_path.exists():
            return NotificationState()

        try:
            raw = self._file_path.read_text(encoding="utf-8")
            return NotificationState.model_validate_json(raw)
        except (OSError, ValidationError, ValueError) as exc:
            logger.warning(
                "Corrupt notification state file at {}: {}; backing up and restoring defaults",
                self._file_path,
                exc,
            )
            self._backup_corrupt_file()
            return NotificationState()

    def save(self, state: NotificationState) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._file_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp_path, self._file_path)
        except OSError as exc:
            raise NotificationStatePersistenceError(
                f"Failed to save notification state to {self._file_path}"
            ) from exc

    def _backup_corrupt_file(self) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self._file_path.with_suffix(f".corrupt-{timestamp}.json")
        try:
            shutil.copy2(self._file_path, backup_path)
        except OSError as exc:
            logger.warning("Could not back up corrupt notification state file: {}", exc)

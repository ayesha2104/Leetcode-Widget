"""JSON-file-backed implementation of :class:`GoalRepository`."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ValidationError

from codepulse.domain.exceptions import GoalPersistenceError
from codepulse.domain.interfaces.goal_repository import GoalRepository
from codepulse.domain.models.goal import Goal


class _GoalDocument(BaseModel):
    """On-disk envelope for the goal list, versioned for future changes."""

    goals: list[Goal] = []


class JsonGoalRepository(GoalRepository):
    """Persists goals as a single JSON file.

    Mirrors :class:`~codepulse.infrastructure.persistence.json_desktop_layout_repository.JsonDesktopLayoutRepository`:
    atomic writes (temp file + ``os.replace``) and corrupt-file recovery
    (back up, then fall back to an empty list) instead of crashing.
    """

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def load(self) -> list[Goal]:
        if not self._file_path.exists():
            return []

        try:
            raw = self._file_path.read_text(encoding="utf-8")
            return _GoalDocument.model_validate_json(raw).goals
        except (OSError, ValidationError, ValueError) as exc:
            logger.warning(
                "Corrupt goals file at {}: {}; backing up and starting empty",
                self._file_path,
                exc,
            )
            self._backup_corrupt_file()
            return []

    def save(self, goals: list[Goal]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._file_path.with_suffix(".tmp")
        document = _GoalDocument(goals=goals)
        try:
            tmp_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp_path, self._file_path)
        except OSError as exc:
            raise GoalPersistenceError(f"Failed to save goals to {self._file_path}") from exc

    def _backup_corrupt_file(self) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self._file_path.with_suffix(f".corrupt-{timestamp}.json")
        try:
            shutil.copy2(self._file_path, backup_path)
        except OSError as exc:
            logger.warning("Could not back up corrupt goals file: {}", exc)

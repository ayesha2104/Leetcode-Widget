from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from codepulse.domain.exceptions import NotificationStatePersistenceError
from codepulse.domain.models.notification_state import NotificationState
from codepulse.infrastructure.persistence.json_notification_state_repository import (
    JsonNotificationStateRepository,
)


def test_load_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    repository = JsonNotificationStateRepository(tmp_path / "state.json")

    assert repository.load() == NotificationState()


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    repository = JsonNotificationStateRepository(tmp_path / "state.json")
    state = NotificationState(
        last_notified_streak=7, notified_goal_uids=["x"], last_daily_reminder_date=date(2026, 7, 4)
    )

    repository.save(state)
    loaded = repository.load()

    assert loaded == state


def test_corrupt_file_falls_back_to_defaults_and_backs_up(tmp_path: Path) -> None:
    file_path = tmp_path / "state.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    repository = JsonNotificationStateRepository(file_path)
    state = repository.load()

    assert state == NotificationState()
    backups = list(tmp_path.glob("state.corrupt-*.json"))
    assert len(backups) == 1


def test_save_is_atomic_no_tmp_file_left_behind(tmp_path: Path) -> None:
    repository = JsonNotificationStateRepository(tmp_path / "state.json")

    repository.save(NotificationState())

    assert not (tmp_path / "state.tmp").exists()


def test_save_raises_on_os_failure(tmp_path: Path) -> None:
    directory_as_file_path = tmp_path / "state_dir"
    directory_as_file_path.mkdir()
    repository = JsonNotificationStateRepository(directory_as_file_path)

    with pytest.raises(NotificationStatePersistenceError):
        repository.save(NotificationState())

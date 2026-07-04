from __future__ import annotations

from pathlib import Path

import pytest

from codepulse.domain.exceptions import GoalPersistenceError
from codepulse.domain.models.goal import Goal, GoalMetric
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository


def test_load_returns_empty_list_when_file_missing(tmp_path: Path) -> None:
    repository = JsonGoalRepository(tmp_path / "goals.json")

    assert repository.load() == []


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    repository = JsonGoalRepository(tmp_path / "goals.json")
    goals = [
        Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=500),
        Goal(uid="2", metric=GoalMetric.STREAK, target=30),
    ]

    repository.save(goals)
    loaded = repository.load()

    assert loaded == goals


def test_corrupt_file_falls_back_to_empty_list_and_backs_up(tmp_path: Path) -> None:
    file_path = tmp_path / "goals.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    repository = JsonGoalRepository(file_path)
    goals = repository.load()

    assert goals == []
    backups = list(tmp_path.glob("goals.corrupt-*.json"))
    assert len(backups) == 1


def test_save_is_atomic_no_tmp_file_left_behind(tmp_path: Path) -> None:
    repository = JsonGoalRepository(tmp_path / "goals.json")

    repository.save([])

    assert not (tmp_path / "goals.tmp").exists()


def test_save_raises_goal_persistence_error_on_os_failure(tmp_path: Path) -> None:
    directory_as_file_path = tmp_path / "goals_dir"
    directory_as_file_path.mkdir()
    repository = JsonGoalRepository(directory_as_file_path)

    with pytest.raises(GoalPersistenceError):
        repository.save([])

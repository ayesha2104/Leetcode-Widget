from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from codepulse.infrastructure.persistence.sqlite_cache_repository import SqliteCacheRepository


@pytest.fixture
def repository(tmp_path: Path) -> SqliteCacheRepository:
    return SqliteCacheRepository(tmp_path / "cache.db")


def test_get_returns_none_for_missing_key(repository: SqliteCacheRepository) -> None:
    assert repository.get("missing") is None


def test_set_then_get_round_trips_payload(repository: SqliteCacheRepository) -> None:
    payload = {"solved": 512, "streak": 7}

    repository.set("leetcode:octocat:stats", payload)
    entry = repository.get("leetcode:octocat:stats")

    assert entry is not None
    assert entry.payload == payload
    assert entry.key == "leetcode:octocat:stats"


def test_set_overwrites_existing_entry(repository: SqliteCacheRepository) -> None:
    repository.set("key", {"value": 1})
    repository.set("key", {"value": 2})

    entry = repository.get("key")

    assert entry is not None
    assert entry.payload == {"value": 2}


def test_is_stale_true_for_missing_key(repository: SqliteCacheRepository) -> None:
    assert repository.is_stale("missing", timedelta(minutes=30)) is True


def test_is_stale_false_immediately_after_set(repository: SqliteCacheRepository) -> None:
    repository.set("key", {"value": 1})

    assert repository.is_stale("key", timedelta(minutes=30)) is False


def test_clear_removes_entry(repository: SqliteCacheRepository) -> None:
    repository.set("key", {"value": 1})
    repository.clear("key")

    assert repository.get("key") is None


def test_corrupt_payload_is_treated_as_miss_and_purged(
    tmp_path: Path, repository: SqliteCacheRepository
) -> None:
    db_path = tmp_path / "cache.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO cache_entries (key, payload, updated_at) VALUES (?, ?, ?)",
            ("bad", "{not valid json", "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()

    assert repository.get("bad") is None
    # The corrupt row should have been purged, not just skipped.
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT 1 FROM cache_entries WHERE key = ?", ("bad",)).fetchone()
    assert row is None

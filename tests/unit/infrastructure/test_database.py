from __future__ import annotations

import sqlite3
from pathlib import Path

from codepulse.infrastructure.persistence.database import ensure_schema


def test_ensure_schema_creates_cache_entries_table(tmp_path: Path) -> None:
    db_path = tmp_path / "codepulse.db"

    ensure_schema(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "cache_entries" in tables


def test_ensure_schema_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "codepulse.db"

    ensure_schema(db_path)
    ensure_schema(db_path)  # must not raise or duplicate migrations

    with sqlite3.connect(db_path) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    assert version == 1

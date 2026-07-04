"""SQLite schema management.

CodePulse opens a short-lived connection per operation rather than holding
one open for the process lifetime -- writes are infrequent (one per refresh
cycle) and this sidesteps sqlite3's cross-thread connection-sharing pitfalls
entirely, since the refresh worker and the UI thread never touch the same
connection object.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from loguru import logger

_MIGRATIONS: dict[int, str] = {
    1: """
        CREATE TABLE IF NOT EXISTS cache_entries (
            key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """,
}

CURRENT_SCHEMA_VERSION = max(_MIGRATIONS)


def ensure_schema(db_path: Path) -> None:
    """Create the database file and apply any pending migrations.

    Idempotent -- safe to call on every startup. Migrations are plain SQL
    scripts applied in ascending version order, tracked via
    ``PRAGMA user_version`` so no extra bookkeeping table is needed.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path)) as connection:
        current_version = connection.execute("PRAGMA user_version").fetchone()[0]

        for version in sorted(_MIGRATIONS):
            if version <= current_version:
                continue
            logger.info("Applying database migration {} to {}", version, db_path)
            connection.executescript(_MIGRATIONS[version])
            connection.execute(f"PRAGMA user_version = {version}")

        connection.commit()

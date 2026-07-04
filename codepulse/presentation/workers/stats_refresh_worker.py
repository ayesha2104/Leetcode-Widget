"""Bridges Qt's threading model with StatsService's asyncio-based I/O.

Per docs/architecture.md's threading model: network calls happen on a
QThread worker that runs its own asyncio event loop internally. The UI
thread starts this thread and connects to its signals -- it never awaits a
coroutine or touches httpx itself.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QThread, Signal

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.services.stats_service import StatsService
from codepulse.domain.exceptions import ProviderError


class StatsRefreshWorker(QThread):
    """Runs one :meth:`StatsService.refresh_snapshot` call on a background thread."""

    snapshot_ready = Signal(object)  # DashboardSnapshot
    refresh_failed = Signal(str)

    def __init__(self, service: StatsService, username: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._username = username

    def run(self) -> None:  # pragma: no cover - coverage.py can't trace a QThread's OS thread
        try:
            snapshot: DashboardSnapshot = asyncio.run(
                self._service.refresh_snapshot(self._username)
            )
        except ProviderError as exc:
            self.refresh_failed.emit(str(exc))
            return
        self.snapshot_ready.emit(snapshot)

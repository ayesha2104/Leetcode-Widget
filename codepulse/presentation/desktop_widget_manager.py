"""Owns the set of floating widgets currently on the desktop.

Spawns/destroys :class:`FloatingWidgetWindow` instances, keeps them
positioned per the persisted :class:`PlacedWidget` records, and saves
changes via :class:`DesktopLayoutRepository`. This is presentation-layer
orchestration -- it creates and manages QWidgets -- not business logic, so
it lives alongside the windows it manages rather than in the application
layer.

Also owns the (optional) live-data refresh cycle: if a
:class:`StatsService` and username are configured, it loads the cached
snapshot instantly, kicks off a background refresh via
:class:`StatsRefreshWorker`, and repeats that refresh on a timer. If a
:class:`GoalService` is configured, goal progress is recomputed alongside
every snapshot update and whenever goals themselves change. If a
:class:`NotificationService` is configured, it's given every fresh
snapshot and goal-progress list so it can decide whether anything
notification-worthy just happened.
"""

from __future__ import annotations

import uuid

from loguru import logger
from PySide6.QtCore import QObject, QTimer, Signal

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.application.services.goal_service import GoalService
from codepulse.application.services.notification_service import NotificationService
from codepulse.application.services.stats_service import StatsService
from codepulse.domain.interfaces.desktop_layout_repository import DesktopLayoutRepository
from codepulse.domain.models.widget import PlacedWidget, WidgetKind, WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.themes.theme_manager import ThemeManager
from codepulse.presentation.windows.floating_widget_window import FloatingWidgetWindow
from codepulse.presentation.workers.stats_refresh_worker import StatsRefreshWorker

_CASCADE_OFFSET_PX = 32
_DEFAULT_START_POSITION = (120, 120)
_MOVE_SAVE_DEBOUNCE_MS = 400
_MINUTES_TO_MS = 60_000


class DesktopWidgetManager(QObject):
    """Manages the lifecycle of floating desktop widgets."""

    widget_count_changed = Signal(int)

    def __init__(
        self,
        repository: DesktopLayoutRepository,
        theme_manager: ThemeManager,
        *,
        opacity: float = 1.0,
        stats_service: StatsService | None = None,
        username: str | None = None,
        refresh_interval_minutes: int = 15,
        goal_service: GoalService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        super().__init__()
        self._repository = repository
        self._theme_manager = theme_manager
        self._opacity = opacity
        self._stats_service = stats_service
        self._username = username
        self._goal_service = goal_service
        self._notification_service = notification_service
        self._snapshot: DashboardSnapshot | None = None
        self._goal_progress: list[GoalProgress] = []
        self._refresh_worker: StatsRefreshWorker | None = None
        self._windows: dict[str, FloatingWidgetWindow] = {}

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_layout)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._trigger_refresh)
        self.set_refresh_interval_minutes(refresh_interval_minutes)

        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def restore_saved_layout(self) -> None:
        """Spawn a floating window for every previously placed widget.

        Safe to call more than once: widgets that already have an open
        window (e.g. added via :meth:`add_widget` before this ran) are
        skipped rather than spawning a duplicate, leaked window.
        """
        if self._stats_service is not None and self._username:
            self._snapshot = self._stats_service.get_cached_snapshot(self._username)
        self._recompute_goal_progress()

        for placed in self._repository.load():
            if placed.uid in self._windows:
                continue
            self._spawn_window(placed)
        self.widget_count_changed.emit(self.widget_count())
        self._trigger_refresh()

    def add_widget(self, kind: WidgetKind, size: WidgetSize) -> None:
        """Create a new placed widget, show its floating window, and persist it."""
        x, y = self._next_position()
        placed = PlacedWidget(uid=str(uuid.uuid4()), kind=kind, size=size, x=x, y=y)
        self._spawn_window(placed)
        self._save_layout()
        self.widget_count_changed.emit(self.widget_count())

    def widget_count(self) -> int:
        """The number of widgets currently on the desktop."""
        return len(self._windows)

    def get_snapshot(self) -> DashboardSnapshot | None:
        """The most recently fetched dashboard snapshot, if any."""
        return self._snapshot

    def set_opacity(self, opacity: float) -> None:
        """Apply ``opacity`` to every open widget and remember it for new ones."""
        self._opacity = opacity
        for window in self._windows.values():
            window.set_opacity(opacity)

    def set_username(self, username: str | None) -> None:
        """Update the tracked username and immediately trigger a refresh if set."""
        self._username = username
        if username:
            self._trigger_refresh()

    def set_refresh_interval_minutes(self, minutes: int) -> None:
        """Change how often the background refresh repeats."""
        self._refresh_timer.start(minutes * _MINUTES_TO_MS)

    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable all notification triggers."""
        if self._notification_service is not None:
            self._notification_service.set_enabled(enabled)

    def refresh_goals(self) -> None:
        """Recompute goal progress, push it to every open widget, and check for achievements."""
        self._recompute_goal_progress()
        for window in self._windows.values():
            window.set_goal_progress(self._goal_progress)
        if self._notification_service is not None:
            self._notification_service.on_goal_progress_updated(self._goal_progress)

    def _recompute_goal_progress(self) -> None:
        if self._goal_service is None:
            self._goal_progress = []
            return
        goals = self._goal_service.list_goals()
        self._goal_progress = [
            self._goal_service.compute_progress(goal, self._snapshot) for goal in goals
        ]

    def _next_position(self) -> tuple[int, int]:
        base_x, base_y = _DEFAULT_START_POSITION
        offset = len(self._windows) * _CASCADE_OFFSET_PX
        return base_x + offset, base_y + offset

    def _spawn_window(self, placed: PlacedWidget) -> None:
        window = FloatingWidgetWindow(
            placed, self._theme_manager.current_theme, self._snapshot, self._goal_progress
        )
        window.remove_requested.connect(self._on_remove_requested)
        window.moved.connect(self._on_window_moved)
        window.set_opacity(self._opacity)
        window.move(placed.x, placed.y)
        window.show()
        self._windows[placed.uid] = window

    def _on_remove_requested(self, uid: str) -> None:
        window = self._windows.pop(uid, None)
        if window is not None:
            window.close()
            window.deleteLater()
        self._save_layout()
        self.widget_count_changed.emit(self.widget_count())

    def _on_window_moved(self, uid: str, x: int, y: int) -> None:
        window = self._windows.get(uid)
        if window is not None:
            window.placed_widget.x = x
            window.placed_widget.y = y
        self._save_timer.start(_MOVE_SAVE_DEBOUNCE_MS)

    def _on_theme_changed(self, theme: Theme) -> None:
        for window in self._windows.values():
            window.apply_theme(theme)

    def _save_layout(self) -> None:
        widgets = [window.placed_widget for window in self._windows.values()]
        self._repository.save(widgets)

    def _trigger_refresh(self) -> None:
        if self._stats_service is None or not self._username or self._refresh_worker is not None:
            return  # no service/username configured, or a refresh is already running

        worker = StatsRefreshWorker(self._stats_service, self._username, self)
        worker.snapshot_ready.connect(self._on_refresh_succeeded)
        worker.refresh_failed.connect(self._on_refresh_failed)
        worker.finished.connect(self._on_refresh_finished)
        self._refresh_worker = worker
        worker.start()

    def _on_refresh_succeeded(self, snapshot: DashboardSnapshot) -> None:
        self._snapshot = snapshot
        self._recompute_goal_progress()
        for window in self._windows.values():
            window.set_snapshot(snapshot)
            window.set_goal_progress(self._goal_progress)
        if self._notification_service is not None:
            self._notification_service.on_snapshot_updated(snapshot)
            self._notification_service.on_goal_progress_updated(self._goal_progress)
        logger.info("Dashboard snapshot refreshed for {}", self._username)

    def _on_refresh_failed(self, message: str) -> None:
        logger.warning("Stats refresh failed for {}: {}", self._username, message)

    def _on_refresh_finished(self) -> None:
        if self._refresh_worker is not None:
            self._refresh_worker.deleteLater()
        self._refresh_worker = None

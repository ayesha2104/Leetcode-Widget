"""CodePulse's composition root.

Wires configuration, logging, persistence, and the presentation layer
together, then starts the Qt event loop. Nothing here contains business
logic -- it only constructs and connects objects defined elsewhere.
"""

from __future__ import annotations

import sys
from datetime import timedelta

from loguru import logger
from PySide6.QtWidgets import QApplication

from codepulse.application.services.goal_service import GoalService
from codepulse.application.services.notification_service import NotificationService
from codepulse.application.services.stats_service import StatsService
from codepulse.infrastructure.config.settings import get_app_settings
from codepulse.infrastructure.logging.logger import configure_logging
from codepulse.infrastructure.notifications.windows_notifier import WindowsNotifier
from codepulse.infrastructure.persistence.json_desktop_layout_repository import (
    JsonDesktopLayoutRepository,
)
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository
from codepulse.infrastructure.persistence.json_notification_state_repository import (
    JsonNotificationStateRepository,
)
from codepulse.infrastructure.persistence.json_settings_repository import (
    JsonSettingsRepository,
)
from codepulse.infrastructure.persistence.sqlite_cache_repository import (
    SqliteCacheRepository,
)
from codepulse.infrastructure.providers.registry import get_provider
from codepulse.presentation.desktop_widget_manager import DesktopWidgetManager
from codepulse.presentation.themes.theme_manager import ThemeManager
from codepulse.presentation.windows.main_window import MainWindow


def main() -> int:
    """Start CodePulse. Returns the process exit code."""
    settings = get_app_settings()
    configure_logging(settings)
    logger.info("CodePulse starting up")

    settings_repository = JsonSettingsRepository(settings.settings_file_path)
    preferences = settings_repository.load()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # floating widgets/tray keep it alive when hidden

    theme_manager = ThemeManager(preferences.theme.value)

    provider = get_provider(preferences.active_provider)
    cache_repository = SqliteCacheRepository(settings.database_path)
    stats_service = StatsService(
        provider,
        cache_repository,
        provider_name=preferences.active_provider,
        cache_duration=timedelta(minutes=preferences.cache_duration_minutes),
    )

    goal_repository = JsonGoalRepository(settings.goals_file_path)
    goal_service = GoalService(goal_repository)

    notification_state_repository = JsonNotificationStateRepository(
        settings.notification_state_file_path
    )
    notification_service = NotificationService(
        WindowsNotifier(),
        notification_state_repository,
        enabled=preferences.notifications_enabled,
    )

    layout_repository = JsonDesktopLayoutRepository(settings.desktop_layout_file_path)
    widget_manager = DesktopWidgetManager(
        layout_repository,
        theme_manager,
        opacity=preferences.opacity,
        stats_service=stats_service,
        username=preferences.username,
        refresh_interval_minutes=preferences.refresh_interval_minutes,
        goal_service=goal_service,
        notification_service=notification_service,
    )
    widget_manager.restore_saved_layout()

    main_window = MainWindow(
        theme_manager,
        widget_manager,
        settings_repository,
        goal_service,
        always_on_top=preferences.always_on_top,
    )
    main_window.set_opacity(preferences.opacity)
    main_window.show()

    exit_code = app.exec()
    logger.info("CodePulse shutting down (exit code {})", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

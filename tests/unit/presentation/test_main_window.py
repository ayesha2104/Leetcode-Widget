from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QPushButton

from codepulse.application.services.goal_service import GoalService
from codepulse.domain.models.preferences import UserPreferences
from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.infrastructure.persistence.json_desktop_layout_repository import (
    JsonDesktopLayoutRepository,
)
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository
from codepulse.infrastructure.persistence.json_settings_repository import (
    JsonSettingsRepository,
)
from codepulse.presentation.desktop_widget_manager import DesktopWidgetManager
from codepulse.presentation.themes.theme_manager import ThemeManager
from codepulse.presentation.windows.main_window import MainWindow


@pytest.fixture
def widget_manager(tmp_path: Path) -> DesktopWidgetManager:
    repository = JsonDesktopLayoutRepository(tmp_path / "layout.json")
    return DesktopWidgetManager(repository, ThemeManager())


@pytest.fixture
def settings_repository(tmp_path: Path) -> JsonSettingsRepository:
    return JsonSettingsRepository(tmp_path / "settings.json")


@pytest.fixture
def goal_service(tmp_path: Path) -> GoalService:
    return GoalService(JsonGoalRepository(tmp_path / "goals.json"))


def test_main_window_constructs_without_raising(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)

    window.grab()


def test_add_widget_button_click_does_not_raise(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)

    add_button = _find_button_by_text(window, "+ Add Widget")
    add_button.click()  # opens WidgetPickerDialog; must not raise

    assert window._add_widget_button.isEnabled()


def test_manager_add_widget_updates_count(widget_manager: DesktopWidgetManager) -> None:
    widget_manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    assert widget_manager.widget_count() == 1


def test_widget_count_label_updates_when_widget_added(
    qtbot,
    tmp_path: Path,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    repository = JsonDesktopLayoutRepository(tmp_path / "layout.json")
    manager = DesktopWidgetManager(repository, ThemeManager())
    window = MainWindow(ThemeManager(), manager, settings_repository, goal_service)
    qtbot.addWidget(window)

    manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    assert window._count_label.text() == "1 widget active"


def test_settings_button_click_does_not_raise(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)

    settings_button = _find_button_by_tooltip(window, "Settings")
    settings_button.click()  # opens SettingsDialog; must not raise


def test_settings_saved_applies_opacity_to_window_and_widgets(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)
    widget_manager.add_widget(WidgetKind.STREAK, WidgetSize.SMALL)

    window._on_settings_saved(UserPreferences(opacity=0.6))

    # The offscreen QPA platform quantizes opacity to 8 bits, so compare
    # approximately rather than exactly.
    assert window.windowOpacity() == pytest.approx(0.6, abs=0.01)
    floating_window = next(iter(widget_manager._windows.values()))
    assert floating_window.windowOpacity() == pytest.approx(0.6, abs=0.01)


def test_manage_goals_requested_opens_goals_dialog(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)

    window._on_manage_goals_requested()  # must not raise


def test_theme_button_cycles_theme(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    theme_manager = ThemeManager()
    window = MainWindow(theme_manager, widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)
    starting_theme = theme_manager.current_theme.name

    theme_button = _find_button_by_tooltip(window, "Cycle theme")
    theme_button.click()

    assert theme_manager.current_theme.name != starting_theme


def test_hide_button_hides_window(
    qtbot,
    widget_manager: DesktopWidgetManager,
    settings_repository: JsonSettingsRepository,
    goal_service: GoalService,
) -> None:
    window = MainWindow(ThemeManager(), widget_manager, settings_repository, goal_service)
    qtbot.addWidget(window)
    window.show()

    hide_button = _find_button_by_tooltip(window, "Hide to tray")
    hide_button.click()

    assert window.isHidden()


def _find_button_by_tooltip(window: MainWindow, tooltip: str) -> QPushButton:
    for button in window.findChildren(QPushButton):
        if button.toolTip() == tooltip:
            return button
    raise AssertionError(f"No button found with tooltip {tooltip!r}")


def _find_button_by_text(window: MainWindow, text: str) -> QPushButton:
    for button in window.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"No button found with text {text!r}")

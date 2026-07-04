from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QLabel, QProgressBar

from codepulse.application.services.goal_service import GoalService
from codepulse.domain.models.goal import GoalMetric
from codepulse.infrastructure.persistence.json_goal_repository import JsonGoalRepository
from codepulse.presentation.dialogs.goals_dialog import GoalsDialog
from codepulse.presentation.themes.theme_manager import load_theme


@pytest.fixture
def service(tmp_path: Path) -> GoalService:
    return GoalService(JsonGoalRepository(tmp_path / "goals.json"))


def test_dialog_shows_empty_message_when_no_goals(qtbot, service: GoalService) -> None:
    dialog = GoalsDialog(service, load_theme("dark"))
    qtbot.addWidget(dialog)

    labels = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("No goals yet" in text for text in labels)


def test_dialog_lists_existing_goals(qtbot, service: GoalService) -> None:
    service.add_goal(GoalMetric.TOTAL_SOLVED, 500)

    dialog = GoalsDialog(service, load_theme("dark"))
    qtbot.addWidget(dialog)

    assert len(dialog.findChildren(QProgressBar)) == 1


def test_add_goal_persists_and_refreshes_list(qtbot, service: GoalService) -> None:
    dialog = GoalsDialog(service, load_theme("dark"))
    qtbot.addWidget(dialog)

    index = dialog._metric_combo.findData(GoalMetric.STREAK.value)
    dialog._metric_combo.setCurrentIndex(index)
    dialog._target_spin.setValue(30)
    dialog._on_add_clicked()

    assert len(service.list_goals()) == 1
    assert len(dialog.findChildren(QProgressBar)) == 1


def test_add_goal_emits_goals_changed(qtbot, service: GoalService) -> None:
    dialog = GoalsDialog(service, load_theme("dark"))
    qtbot.addWidget(dialog)

    with qtbot.waitSignal(dialog.goals_changed, timeout=1000):
        dialog._on_add_clicked()


def test_remove_goal_deletes_and_emits_goals_changed(qtbot, service: GoalService) -> None:
    goal = service.add_goal(GoalMetric.TOTAL_SOLVED, 500)
    dialog = GoalsDialog(service, load_theme("dark"))
    qtbot.addWidget(dialog)

    with qtbot.waitSignal(dialog.goals_changed, timeout=1000):
        dialog._on_remove_clicked(goal.uid)

    assert service.list_goals() == []

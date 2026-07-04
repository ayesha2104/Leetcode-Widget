"""Manages user-defined goals and computes their progress.

Progress computation depends on :class:`DashboardSnapshot` (application
layer), which is why it lives here rather than on the plain domain
:class:`Goal` model -- domain models stay framework/layer agnostic.
"""

from __future__ import annotations

import uuid

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.interfaces.goal_repository import GoalRepository
from codepulse.domain.models.goal import Goal, GoalMetric


class GoalService:
    """Adds, removes, lists, and computes progress for user-defined goals."""

    def __init__(self, repository: GoalRepository) -> None:
        self._repository = repository

    def list_goals(self) -> list[Goal]:
        """Return every goal the user has defined."""
        return self._repository.load()

    def add_goal(self, metric: GoalMetric, target: int) -> Goal:
        """Create and persist a new goal, returning it."""
        goal = Goal(uid=str(uuid.uuid4()), metric=metric, target=target)
        goals = self._repository.load()
        goals.append(goal)
        self._repository.save(goals)
        return goal

    def remove_goal(self, uid: str) -> None:
        """Delete the goal with the given uid, if it exists."""
        goals = [goal for goal in self._repository.load() if goal.uid != uid]
        self._repository.save(goals)

    @staticmethod
    def compute_progress(goal: Goal, snapshot: DashboardSnapshot | None) -> GoalProgress:
        """Compute ``goal``'s current value and percent-complete from ``snapshot``."""
        current_value = GoalService._current_value(goal.metric, snapshot)
        percent = min(100.0, (current_value / goal.target) * 100) if goal.target else 0.0
        return GoalProgress(goal=goal, current_value=current_value, percent=percent)

    @staticmethod
    def _current_value(metric: GoalMetric, snapshot: DashboardSnapshot | None) -> int:
        if snapshot is None:
            return 0
        if metric == GoalMetric.TOTAL_SOLVED:
            return snapshot.stats.total_solved
        if metric == GoalMetric.HARD_SOLVED:
            return snapshot.stats.hard_solved
        if metric == GoalMetric.STREAK:
            return snapshot.streak.current_streak
        if metric == GoalMetric.RATING:
            return round(snapshot.contest_info.rating) if snapshot.contest_info else 0
        return 0

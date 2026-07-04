"""Abstract port for persisting user-defined goals.

Implemented by :class:`codepulse.infrastructure.persistence.json_goal_repository.JsonGoalRepository`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codepulse.domain.models.goal import Goal


class GoalRepository(ABC):
    """Loads and saves the user's list of :class:`Goal`."""

    @abstractmethod
    def load(self) -> list[Goal]:
        """Return the persisted goals, or an empty list if none exist yet."""

    @abstractmethod
    def save(self, goals: list[Goal]) -> None:
        """Persist ``goals``, replacing whatever was stored before."""

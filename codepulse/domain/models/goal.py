"""User-defined solving goals (e.g. "500 problems", "30-day streak")."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class GoalMetric(StrEnum):
    """Which statistic a goal tracks progress against."""

    TOTAL_SOLVED = "total_solved"
    HARD_SOLVED = "hard_solved"
    STREAK = "streak"
    RATING = "rating"


class Goal(BaseModel):
    """A single user-defined target for one metric."""

    uid: str
    metric: GoalMetric
    target: int = Field(gt=0)

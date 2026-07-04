"""A goal paired with its current progress toward the target."""

from __future__ import annotations

from pydantic import BaseModel

from codepulse.domain.models.goal import Goal


class GoalProgress(BaseModel):
    """How far along ``goal`` is, as of the last computation."""

    goal: Goal
    current_value: int
    percent: float

"""A user's daily-practice streak on a coding platform."""

from __future__ import annotations

from pydantic import BaseModel


class Streak(BaseModel):
    """Current and longest consecutive-day activity streaks."""

    current_streak: int = 0
    longest_streak: int = 0
    total_active_days: int = 0

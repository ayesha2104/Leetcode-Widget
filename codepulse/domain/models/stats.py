"""Problem-solving statistics for a user on a coding platform."""

from __future__ import annotations

from pydantic import BaseModel


class Stats(BaseModel):
    """Aggregate solved-problem counts and acceptance rate."""

    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    total_solved: int = 0
    acceptance_rate: float = 0.0

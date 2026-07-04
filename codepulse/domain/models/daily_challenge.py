"""A platform's daily coding challenge."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DailyChallenge(BaseModel):
    """Today's featured problem, ready to link out to from the UI."""

    title: str
    title_slug: str
    difficulty: str
    acceptance_rate: float
    url: str
    challenge_date: date

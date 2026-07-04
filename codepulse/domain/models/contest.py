"""A user's competitive contest standing on a coding platform."""

from __future__ import annotations

from pydantic import BaseModel


class ContestInfo(BaseModel):
    """Contest rating and ranking. ``None`` at the call site means the user
    has never entered a rated contest -- not every provider guarantees this."""

    rating: float
    global_ranking: int | None = None
    attended_contests_count: int = 0
    top_percentage: float | None = None

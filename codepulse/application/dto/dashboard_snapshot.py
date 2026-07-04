"""A single DTO bundling every piece of provider data the dashboard needs.

Fetched (or loaded from cache) as one unit so the UI never has to reason
about partially-available data from a half-finished refresh.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak


class DashboardSnapshot(BaseModel):
    """Everything the dashboard renders for one user, as of ``fetched_at``."""

    profile: Profile
    stats: Stats
    streak: Streak
    daily_challenge: DailyChallenge
    contest_info: ContestInfo | None = None
    fetched_at: datetime

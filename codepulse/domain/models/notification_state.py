"""Tracks which notifications have already fired, to avoid repeats.

Persisted separately from :class:`UserPreferences` (user-facing settings)
since this is purely internal bookkeeping the user never edits directly.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class NotificationState(BaseModel):
    """De-duplication state for notification triggers."""

    last_notified_streak: int = 0
    notified_goal_uids: list[str] = []
    last_daily_reminder_date: date | None = None

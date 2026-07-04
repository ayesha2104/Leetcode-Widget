"""Decides when to fire a user notification and de-duplicates repeats.

Actually showing a notification is delegated to a :class:`Notifier`
(infrastructure); this class only owns the *decision* of when a real,
meaningful event has occurred -- a goal newly completed, a new personal-best
streak, or the once-a-day nudge to solve today's challenge. "Contest
starting" from the original feature list is not implemented: no provider
exposes an upcoming-contest schedule (see the Contest widget's own
docstring), so there is nothing genuine to trigger it from.
"""

from __future__ import annotations

from datetime import UTC, datetime

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.domain.interfaces.notification_state_repository import (
    NotificationStateRepository,
)
from codepulse.domain.interfaces.notifier import Notifier

_GOAL_ACHIEVED_PERCENT = 100.0


class NotificationService:
    """Triggers goal-achieved, streak-record, and daily-reminder notifications."""

    def __init__(
        self,
        notifier: Notifier,
        state_repository: NotificationStateRepository,
        *,
        enabled: bool = True,
    ) -> None:
        self._notifier = notifier
        self._state_repository = state_repository
        self._enabled = enabled
        self._state = state_repository.load()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all notification triggers."""
        self._enabled = enabled

    def on_snapshot_updated(self, snapshot: DashboardSnapshot) -> None:
        """Check streak-record and daily-reminder triggers against a fresh snapshot."""
        if not self._enabled:
            return

        changed = self._check_streak_record(snapshot)
        changed = self._maybe_send_daily_reminder(snapshot) or changed
        if changed:
            self._state_repository.save(self._state)

    def on_goal_progress_updated(self, goal_progress: list[GoalProgress]) -> None:
        """Check goal-achieved triggers against a fresh progress list."""
        if not self._enabled:
            return

        changed = False
        for progress in goal_progress:
            already_notified = progress.goal.uid in self._state.notified_goal_uids
            if progress.percent >= _GOAL_ACHIEVED_PERCENT and not already_notified:
                self._state.notified_goal_uids.append(progress.goal.uid)
                self._notifier.notify(
                    "Goal achieved! \U0001f389",
                    f"You hit your goal of {progress.goal.target} ({progress.goal.metric.value})!",
                )
                changed = True
        if changed:
            self._state_repository.save(self._state)

    def _check_streak_record(self, snapshot: DashboardSnapshot) -> bool:
        current = snapshot.streak.current_streak
        longest = snapshot.streak.longest_streak
        is_new_record = current > 0 and current >= longest
        if is_new_record and current > self._state.last_notified_streak:
            self._state.last_notified_streak = current
            self._notifier.notify(
                "New streak record! \U0001f525", f"You're on a {current}-day streak!"
            )
            return True
        return False

    def _maybe_send_daily_reminder(self, snapshot: DashboardSnapshot) -> bool:
        today = datetime.now(UTC).date()
        if self._state.last_daily_reminder_date == today:
            return False

        self._state.last_daily_reminder_date = today
        self._notifier.notify(
            "Daily Challenge", f"Today's challenge: {snapshot.daily_challenge.title}"
        )
        return True

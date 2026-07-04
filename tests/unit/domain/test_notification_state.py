from __future__ import annotations

from datetime import date

from codepulse.domain.models.notification_state import NotificationState


def test_defaults() -> None:
    state = NotificationState()

    assert state.last_notified_streak == 0
    assert state.notified_goal_uids == []
    assert state.last_daily_reminder_date is None


def test_round_trips_through_json() -> None:
    state = NotificationState(
        last_notified_streak=12,
        notified_goal_uids=["a", "b"],
        last_daily_reminder_date=date(2026, 7, 4),
    )

    restored = NotificationState.model_validate_json(state.model_dump_json())

    assert restored == state

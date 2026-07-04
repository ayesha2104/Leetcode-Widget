from __future__ import annotations

import pytest
from pydantic import ValidationError

from codepulse.domain.models.goal import Goal, GoalMetric


def test_goal_requires_positive_target() -> None:
    with pytest.raises(ValidationError):
        Goal(uid="1", metric=GoalMetric.TOTAL_SOLVED, target=0)


def test_goal_round_trips_through_json() -> None:
    goal = Goal(uid="abc", metric=GoalMetric.STREAK, target=30)

    restored = Goal.model_validate_json(goal.model_dump_json())

    assert restored == goal


def test_goal_metric_is_a_string_enum() -> None:
    assert GoalMetric.RATING == "rating"

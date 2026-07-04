from __future__ import annotations

from datetime import date

from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak


def test_profile_requires_only_username() -> None:
    profile = Profile(username="octocat")

    assert profile.username == "octocat"
    assert profile.real_name is None
    assert profile.ranking is None


def test_stats_defaults_to_all_zero() -> None:
    stats = Stats()

    assert stats.total_solved == 0
    assert stats.acceptance_rate == 0.0


def test_contest_info_requires_rating() -> None:
    contest_info = ContestInfo(rating=1500.5)

    assert contest_info.rating == 1500.5
    assert contest_info.attended_contests_count == 0
    assert contest_info.global_ranking is None


def test_daily_challenge_round_trips_all_fields() -> None:
    challenge = DailyChallenge(
        title="Two Sum",
        title_slug="two-sum",
        difficulty="Easy",
        acceptance_rate=55.12,
        url="https://leetcode.com/problems/two-sum/",
        challenge_date=date(2026, 7, 4),
    )

    assert challenge.challenge_date == date(2026, 7, 4)


def test_streak_defaults_to_zero() -> None:
    streak = Streak()

    assert streak.current_streak == 0
    assert streak.longest_streak == 0
    assert streak.total_active_days == 0

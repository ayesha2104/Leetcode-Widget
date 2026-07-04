from __future__ import annotations

import json
from datetime import date

import pytest

from codepulse.domain.exceptions import InvalidUsernameError, ProviderError
from codepulse.infrastructure.providers.leetcode import mapper

PROFILE_AND_STATS_RESPONSE = {
    "matchedUser": {
        "username": "octocat",
        "profile": {
            "ranking": 12345,
            "realName": "The Octocat",
            "userAvatar": "https://example.com/avatar.png",
            "countryName": "USA",
        },
        "submitStats": {
            "acSubmissionNum": [
                {"difficulty": "All", "count": 100},
                {"difficulty": "Easy", "count": 50},
                {"difficulty": "Medium", "count": 40},
                {"difficulty": "Hard", "count": 10},
            ],
            "totalSubmissionNum": [
                {"difficulty": "All", "count": 200},
                {"difficulty": "Easy", "count": 80},
                {"difficulty": "Medium", "count": 80},
                {"difficulty": "Hard", "count": 40},
            ],
        },
    }
}


def test_map_profile_extracts_all_fields() -> None:
    profile = mapper.map_profile(PROFILE_AND_STATS_RESPONSE, "octocat")

    assert profile.username == "octocat"
    assert profile.real_name == "The Octocat"
    assert profile.avatar_url == "https://example.com/avatar.png"
    assert profile.ranking == 12345
    assert profile.country == "USA"


def test_map_profile_raises_for_missing_user() -> None:
    with pytest.raises(InvalidUsernameError):
        mapper.map_profile({"matchedUser": None}, "ghost")


def test_map_profile_treats_blank_optional_fields_as_none() -> None:
    data = {
        "matchedUser": {
            "username": "octocat",
            "profile": {"ranking": None, "realName": "", "userAvatar": "", "countryName": None},
        }
    }

    profile = mapper.map_profile(data, "octocat")

    assert profile.real_name is None
    assert profile.avatar_url is None
    assert profile.country is None


def test_map_stats_computes_totals_and_acceptance_rate() -> None:
    stats = mapper.map_stats(PROFILE_AND_STATS_RESPONSE, "octocat")

    assert stats.total_solved == 100
    assert stats.easy_solved == 50
    assert stats.medium_solved == 40
    assert stats.hard_solved == 10
    assert stats.acceptance_rate == 50.0


def test_map_stats_handles_zero_submissions_without_dividing_by_zero() -> None:
    data = {
        "matchedUser": {
            "username": "newbie",
            "submitStats": {"acSubmissionNum": [], "totalSubmissionNum": []},
        }
    }

    stats = mapper.map_stats(data, "newbie")

    assert stats.total_solved == 0
    assert stats.acceptance_rate == 0.0


def test_map_stats_raises_for_missing_user() -> None:
    with pytest.raises(InvalidUsernameError):
        mapper.map_stats({"matchedUser": None}, "ghost")


def test_map_contest_info_returns_none_when_never_rated() -> None:
    assert mapper.map_contest_info({"userContestRanking": None}) is None


def test_map_contest_info_extracts_all_fields() -> None:
    data = {
        "userContestRanking": {
            "rating": 1567.891,
            "globalRanking": 42000,
            "attendedContestsCount": 12,
            "topPercentage": 15.5,
        }
    }

    contest_info = mapper.map_contest_info(data)

    assert contest_info is not None
    assert contest_info.rating == 1567.89
    assert contest_info.global_ranking == 42000
    assert contest_info.attended_contests_count == 12
    assert contest_info.top_percentage == 15.5


def test_map_daily_challenge_extracts_and_builds_absolute_url() -> None:
    data = {
        "activeDailyCodingChallengeQuestion": {
            "date": "2026-07-04",
            "link": "/problems/two-sum/",
            "question": {
                "title": "Two Sum",
                "titleSlug": "two-sum",
                "difficulty": "Easy",
                "acRate": 55.1234,
            },
        }
    }

    challenge = mapper.map_daily_challenge(data)

    assert challenge.title == "Two Sum"
    assert challenge.url == "https://leetcode.com/problems/two-sum/"
    assert challenge.challenge_date == date(2026, 7, 4)
    assert challenge.acceptance_rate == 55.12


def test_map_daily_challenge_raises_when_absent() -> None:
    with pytest.raises(ProviderError):
        mapper.map_daily_challenge({"activeDailyCodingChallengeQuestion": None})


def _calendar_payload(day_counts: dict[int, int]) -> str:
    return json.dumps({str(day): count for day, count in day_counts.items()})


def test_map_streak_uses_reported_current_streak() -> None:
    data = {
        "matchedUser": {
            "userCalendar": {
                "streak": 7,
                "totalActiveDays": 120,
                "submissionCalendar": "{}",
            }
        }
    }

    streak = mapper.map_streak(data, "octocat")

    assert streak.current_streak == 7
    assert streak.total_active_days == 120


def test_map_streak_computes_longest_streak_from_consecutive_days() -> None:
    day = 1_700_000_000  # arbitrary unix day-aligned timestamp
    seconds_per_day = 86400
    # Three consecutive active days, then a gap, then two more consecutive days.
    calendar = {
        day: 1,
        day + seconds_per_day: 1,
        day + 2 * seconds_per_day: 1,
        day + 5 * seconds_per_day: 1,
        day + 6 * seconds_per_day: 1,
    }
    data = {
        "matchedUser": {
            "userCalendar": {
                "streak": 2,
                "totalActiveDays": 5,
                "submissionCalendar": _calendar_payload(calendar),
            }
        }
    }

    streak = mapper.map_streak(data, "octocat")

    assert streak.longest_streak == 3


def test_map_streak_ignores_zero_count_days() -> None:
    day = 1_700_000_000
    calendar = {day: 0, day + 86400: 1}
    data = {
        "matchedUser": {
            "userCalendar": {
                "streak": 1,
                "totalActiveDays": 1,
                "submissionCalendar": _calendar_payload(calendar),
            }
        }
    }

    streak = mapper.map_streak(data, "octocat")

    assert streak.longest_streak == 1


def test_map_streak_handles_corrupt_calendar_gracefully() -> None:
    data = {
        "matchedUser": {
            "userCalendar": {
                "streak": 3,
                "totalActiveDays": 10,
                "submissionCalendar": "{not valid json",
            }
        }
    }

    streak = mapper.map_streak(data, "octocat")

    # Longest can never be reported as less than the current streak.
    assert streak.longest_streak == 3


def test_map_streak_raises_for_missing_user() -> None:
    with pytest.raises(InvalidUsernameError):
        mapper.map_streak({"matchedUser": None}, "ghost")

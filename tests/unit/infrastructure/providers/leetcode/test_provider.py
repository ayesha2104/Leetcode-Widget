from __future__ import annotations

from unittest.mock import AsyncMock

from codepulse.infrastructure.providers.leetcode.provider import LeetCodeProvider

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
            ],
        },
    }
}


def _provider_with_response(response: dict[str, object]) -> LeetCodeProvider:
    client = AsyncMock()
    client.execute.return_value = response
    return LeetCodeProvider(client=client)


async def test_get_profile_maps_client_response() -> None:
    provider = _provider_with_response(PROFILE_AND_STATS_RESPONSE)

    profile = await provider.get_profile("octocat")

    assert profile.username == "octocat"
    assert profile.ranking == 12345


async def test_get_stats_maps_client_response() -> None:
    provider = _provider_with_response(PROFILE_AND_STATS_RESPONSE)

    stats = await provider.get_stats("octocat")

    assert stats.total_solved == 100
    assert stats.acceptance_rate == 50.0


async def test_get_contest_info_returns_none_when_absent() -> None:
    provider = _provider_with_response({"userContestRanking": None})

    assert await provider.get_contest_info("octocat") is None


async def test_get_contest_info_maps_client_response() -> None:
    provider = _provider_with_response(
        {
            "userContestRanking": {
                "rating": 1500.0,
                "globalRanking": 1000,
                "attendedContestsCount": 5,
                "topPercentage": 20.0,
            }
        }
    )

    contest_info = await provider.get_contest_info("octocat")

    assert contest_info is not None
    assert contest_info.rating == 1500.0


async def test_get_daily_challenge_maps_client_response() -> None:
    provider = _provider_with_response(
        {
            "activeDailyCodingChallengeQuestion": {
                "date": "2026-07-04",
                "link": "/problems/two-sum/",
                "question": {
                    "title": "Two Sum",
                    "titleSlug": "two-sum",
                    "difficulty": "Easy",
                    "acRate": 55.0,
                },
            }
        }
    )

    challenge = await provider.get_daily_challenge()

    assert challenge.title == "Two Sum"
    assert challenge.url == "https://leetcode.com/problems/two-sum/"


async def test_get_streak_maps_client_response() -> None:
    provider = _provider_with_response(
        {
            "matchedUser": {
                "userCalendar": {
                    "streak": 7,
                    "totalActiveDays": 120,
                    "submissionCalendar": "{}",
                }
            }
        }
    )

    streak = await provider.get_streak("octocat")

    assert streak.current_streak == 7
    assert streak.total_active_days == 120


async def test_get_streak_passes_username_and_null_year_variables() -> None:
    client = AsyncMock()
    client.execute.return_value = {
        "matchedUser": {
            "userCalendar": {"streak": 0, "totalActiveDays": 0, "submissionCalendar": "{}"}
        }
    }
    provider = LeetCodeProvider(client=client)

    await provider.get_streak("octocat")

    call_args = client.execute.call_args
    assert call_args.args[1] == {"username": "octocat", "year": None}

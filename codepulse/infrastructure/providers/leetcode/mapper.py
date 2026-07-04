"""Maps raw LeetCode GraphQL JSON into CodePulse domain models.

Every function here is pure (no I/O) and takes the already-decoded ``data``
dict returned by :meth:`LeetCodeGraphQLClient.execute`, so they're trivially
testable with hand-built fixtures instead of real network calls.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

from codepulse.domain.exceptions import InvalidUsernameError, ProviderError
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak

_SECONDS_PER_DAY = 86400


def _require_matched_user(data: dict[str, Any], username: str) -> dict[str, Any]:
    matched_user = data.get("matchedUser")
    if matched_user is None:
        raise InvalidUsernameError(f"No LeetCode user found for username {username!r}")
    return cast("dict[str, Any]", matched_user)


def _counts_by_difficulty(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {entry["difficulty"]: entry["count"] for entry in entries}


def map_profile(data: dict[str, Any], username: str) -> Profile:
    """Build a :class:`Profile` from a ``getUserProfile`` response."""
    matched_user = _require_matched_user(data, username)
    profile_data = matched_user.get("profile") or {}

    return Profile(
        username=matched_user["username"],
        real_name=profile_data.get("realName") or None,
        avatar_url=profile_data.get("userAvatar") or None,
        ranking=profile_data.get("ranking"),
        country=profile_data.get("countryName") or None,
    )


def map_stats(data: dict[str, Any], username: str) -> Stats:
    """Build a :class:`Stats` from a ``getUserProfile`` response."""
    matched_user = _require_matched_user(data, username)
    submit_stats = matched_user.get("submitStats") or {}

    solved = _counts_by_difficulty(submit_stats.get("acSubmissionNum") or [])
    submitted = _counts_by_difficulty(submit_stats.get("totalSubmissionNum") or [])

    total_solved = solved.get("All", 0)
    total_submitted = submitted.get("All", 0)
    acceptance_rate = (total_solved / total_submitted * 100) if total_submitted else 0.0

    return Stats(
        easy_solved=solved.get("Easy", 0),
        medium_solved=solved.get("Medium", 0),
        hard_solved=solved.get("Hard", 0),
        total_solved=total_solved,
        acceptance_rate=round(acceptance_rate, 2),
    )


def map_contest_info(data: dict[str, Any]) -> ContestInfo | None:
    """Build a :class:`ContestInfo` from a ``userContestRankingInfo`` response.

    Returns ``None`` if the user has never entered a rated contest -- LeetCode
    itself returns a null ``userContestRanking`` in that case, which is not
    an error.
    """
    ranking = data.get("userContestRanking")
    if ranking is None:
        return None

    return ContestInfo(
        rating=round(ranking["rating"], 2),
        global_ranking=ranking.get("globalRanking"),
        attended_contests_count=ranking.get("attendedContestsCount", 0),
        top_percentage=ranking.get("topPercentage"),
    )


def map_daily_challenge(data: dict[str, Any]) -> DailyChallenge:
    """Build a :class:`DailyChallenge` from a ``questionOfToday`` response."""
    challenge = data.get("activeDailyCodingChallengeQuestion")
    if challenge is None:
        raise ProviderError("LeetCode did not return a daily challenge")

    question = challenge["question"]
    return DailyChallenge(
        title=question["title"],
        title_slug=question["titleSlug"],
        difficulty=question["difficulty"],
        acceptance_rate=round(question["acRate"], 2),
        url=f"https://leetcode.com{challenge['link']}",
        challenge_date=date.fromisoformat(challenge["date"]),
    )


def map_streak(data: dict[str, Any], username: str) -> Streak:
    """Build a :class:`Streak` from a ``userProfileCalendar`` response.

    LeetCode's API reports the *current* streak directly but not the
    longest one; the longest streak is derived here from the raw
    submission calendar (a JSON-encoded ``{unix_day_timestamp: count}`` map).
    """
    matched_user = _require_matched_user(data, username)
    calendar = matched_user.get("userCalendar") or {}

    current_streak = calendar.get("streak", 0)
    total_active_days = calendar.get("totalActiveDays", 0)
    longest_streak = _longest_streak_from_calendar(calendar.get("submissionCalendar"))

    return Streak(
        current_streak=current_streak,
        longest_streak=max(longest_streak, current_streak),
        total_active_days=total_active_days,
    )


def _longest_streak_from_calendar(raw_calendar: str | None) -> int:
    if not raw_calendar:
        return 0

    try:
        calendar: dict[str, int] = json.loads(raw_calendar)
    except json.JSONDecodeError:
        return 0

    active_days = sorted(int(day) for day, count in calendar.items() if count > 0)
    if not active_days:
        return 0

    longest = current = 1
    for previous_day, day in zip(active_days, active_days[1:], strict=False):
        if day - previous_day == _SECONDS_PER_DAY:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest

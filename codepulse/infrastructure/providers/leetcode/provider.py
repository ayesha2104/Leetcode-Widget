"""LeetCode implementation of :class:`ProviderInterface`."""

from __future__ import annotations

from codepulse.domain.interfaces.provider import ProviderInterface
from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak
from codepulse.infrastructure.providers.leetcode import mapper, queries
from codepulse.infrastructure.providers.leetcode.client import LeetCodeGraphQLClient


class LeetCodeProvider(ProviderInterface):
    """Fetches profile, stats, contest, streak, and daily-challenge data from LeetCode."""

    def __init__(self, client: LeetCodeGraphQLClient | None = None) -> None:
        self._client = client or LeetCodeGraphQLClient()

    async def get_profile(self, username: str) -> Profile:
        data = await self._client.execute(queries.PROFILE_AND_STATS_QUERY, {"username": username})
        return mapper.map_profile(data, username)

    async def get_stats(self, username: str) -> Stats:
        data = await self._client.execute(queries.PROFILE_AND_STATS_QUERY, {"username": username})
        return mapper.map_stats(data, username)

    async def get_contest_info(self, username: str) -> ContestInfo | None:
        data = await self._client.execute(queries.CONTEST_RANKING_QUERY, {"username": username})
        return mapper.map_contest_info(data)

    async def get_daily_challenge(self) -> DailyChallenge:
        data = await self._client.execute(queries.DAILY_CHALLENGE_QUERY, {})
        return mapper.map_daily_challenge(data)

    async def get_streak(self, username: str) -> Streak:
        data = await self._client.execute(
            queries.USER_CALENDAR_QUERY, {"username": username, "year": None}
        )
        return mapper.map_streak(data, username)

"""Abstract port every coding-platform provider implements.

Implemented first by :class:`codepulse.infrastructure.providers.leetcode.provider.LeetCodeProvider`.
Adding GitHub, Codeforces, etc. later means adding another implementation of
this interface and registering it in
:mod:`codepulse.infrastructure.providers.registry` -- the application layer
never imports a concrete provider class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codepulse.domain.models.contest import ContestInfo
from codepulse.domain.models.daily_challenge import DailyChallenge
from codepulse.domain.models.profile import Profile
from codepulse.domain.models.stats import Stats
from codepulse.domain.models.streak import Streak


class ProviderInterface(ABC):
    """A coding platform CodePulse can pull statistics from.

    Every method is ``async`` -- providers are only ever awaited from a
    background worker's asyncio event loop (see docs/architecture.md), never
    called from the UI thread.
    """

    @abstractmethod
    async def get_profile(self, username: str) -> Profile:
        """Fetch the public profile for ``username``."""

    @abstractmethod
    async def get_stats(self, username: str) -> Stats:
        """Fetch problem-solving statistics for ``username``."""

    @abstractmethod
    async def get_contest_info(self, username: str) -> ContestInfo | None:
        """Fetch contest rating/ranking for ``username``, or ``None`` if never rated."""

    @abstractmethod
    async def get_daily_challenge(self) -> DailyChallenge:
        """Fetch today's featured daily challenge."""

    @abstractmethod
    async def get_streak(self, username: str) -> Streak:
        """Fetch the current and longest activity streaks for ``username``."""

"""httpx-based GraphQL client for LeetCode's public API.

Translates transport-level failures (timeouts, connection errors, HTTP
status codes, GraphQL-level errors) into the domain exceptions the rest of
the app knows how to handle -- callers never see a raw ``httpx`` exception.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from codepulse.domain.exceptions import NetworkError, ProviderError, RateLimitError

_GRAPHQL_URL = "https://leetcode.com/graphql"
_DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "CodePulse/0.1 (+https://github.com/codepulse/codepulse)",
}


class LeetCodeGraphQLClient:
    """Thin wrapper around LeetCode's public, unauthenticated GraphQL endpoint."""

    def __init__(
        self, *, timeout: float = 10.0, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._timeout = timeout
        self._transport = transport

    async def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Run a GraphQL query and return its ``data`` payload.

        Raises :class:`RateLimitError` on HTTP 429, :class:`NetworkError` on
        timeouts/connection failures, and :class:`ProviderError` on any
        GraphQL-level error or other unexpected HTTP status.
        """
        async with httpx.AsyncClient(
            timeout=self._timeout, headers=_DEFAULT_HEADERS, transport=self._transport
        ) as client:
            try:
                response = await client.post(
                    _GRAPHQL_URL, json={"query": query, "variables": variables}
                )
            except httpx.TimeoutException as exc:
                raise NetworkError("LeetCode request timed out") from exc
            except httpx.ConnectError as exc:
                raise NetworkError(
                    "Could not reach LeetCode; check your internet connection"
                ) from exc

        if response.status_code == 429:
            raise RateLimitError("LeetCode rate limit exceeded; try again later")
        if response.status_code != 200:
            raise ProviderError(f"LeetCode returned HTTP {response.status_code}")

        payload = response.json()
        if payload.get("errors"):
            logger.warning("LeetCode GraphQL errors: {}", payload["errors"])
            raise ProviderError(str(payload["errors"]))

        data: dict[str, Any] = payload.get("data") or {}
        return data

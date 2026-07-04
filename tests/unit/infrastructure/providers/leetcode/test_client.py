from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import httpx
import pytest

from codepulse.domain.exceptions import NetworkError, ProviderError, RateLimitError
from codepulse.infrastructure.providers.leetcode.client import LeetCodeGraphQLClient

Handler = Callable[[httpx.Request], Awaitable[httpx.Response]]


def _client(handler: Handler) -> LeetCodeGraphQLClient:
    return LeetCodeGraphQLClient(transport=httpx.MockTransport(handler))


async def test_execute_returns_data_payload_on_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"hello": "world"}})

    data = await _client(handler).execute("query {}", {})

    assert data == {"hello": "world"}


async def test_execute_sends_query_and_variables_as_json_body() -> None:
    captured: dict[str, bytes] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        return httpx.Response(200, json={"data": {}})

    await _client(handler).execute("query X { y }", {"username": "octocat"})

    body = json.loads(captured["body"])
    assert body == {"query": "query X { y }", "variables": {"username": "octocat"}}


async def test_execute_raises_rate_limit_error_on_429() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    with pytest.raises(RateLimitError):
        await _client(handler).execute("query {}", {})


async def test_execute_raises_provider_error_on_unexpected_status() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with pytest.raises(ProviderError):
        await _client(handler).execute("query {}", {})


async def test_execute_raises_provider_error_on_graphql_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "bad query"}]})

    with pytest.raises(ProviderError):
        await _client(handler).execute("query {}", {})


async def test_execute_raises_network_error_on_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(NetworkError):
        await _client(handler).execute("query {}", {})


async def test_execute_raises_network_error_on_connect_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(NetworkError):
        await _client(handler).execute("query {}", {})


async def test_execute_returns_empty_dict_when_data_is_missing() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    data = await _client(handler).execute("query {}", {})

    assert data == {}

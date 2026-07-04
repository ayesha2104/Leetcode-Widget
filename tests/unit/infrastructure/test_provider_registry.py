from __future__ import annotations

import pytest

from codepulse.domain.exceptions import ConfigurationError
from codepulse.infrastructure.providers.leetcode.provider import LeetCodeProvider
from codepulse.infrastructure.providers.registry import get_provider


def test_get_provider_returns_leetcode_provider() -> None:
    provider = get_provider("leetcode")

    assert isinstance(provider, LeetCodeProvider)


def test_get_provider_returns_same_cached_instance() -> None:
    first = get_provider("leetcode")
    second = get_provider("leetcode")

    assert first is second


def test_get_provider_raises_for_unknown_name() -> None:
    with pytest.raises(ConfigurationError):
        get_provider("does-not-exist")

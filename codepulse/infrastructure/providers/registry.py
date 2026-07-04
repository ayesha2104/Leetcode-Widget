"""Maps a platform identifier to its provider instance.

The application layer asks this registry for "the active provider" by name
and never imports a concrete provider class -- adding GitHub, Codeforces,
etc. later means adding one branch here and a new
``infrastructure/providers/<name>/`` package, nothing else changes.
"""

from __future__ import annotations

from codepulse.domain.exceptions import ConfigurationError
from codepulse.domain.interfaces.provider import ProviderInterface
from codepulse.infrastructure.providers.leetcode.provider import LeetCodeProvider

_providers: dict[str, ProviderInterface] = {}


def get_provider(name: str) -> ProviderInterface:
    """Return the (lazily constructed, cached) provider registered as ``name``."""
    if name not in _providers:
        _providers[name] = _build_provider(name)
    return _providers[name]


def _build_provider(name: str) -> ProviderInterface:
    if name == "leetcode":
        return LeetCodeProvider()
    raise ConfigurationError(f"Unknown provider {name!r}")

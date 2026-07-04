"""Domain-level exceptions.

These are the only error types application and infrastructure code should
raise for expected failure modes. Catching :class:`CodePulseError` at a
boundary (e.g. a QThread worker) is always safe and never swallows a
programming error, since genuine bugs raise unrelated built-in exceptions.
"""

from __future__ import annotations


class CodePulseError(Exception):
    """Base class for all expected, recoverable CodePulse errors."""


class CacheError(CodePulseError):
    """Raised when the cache backend cannot be read from or written to."""


class SettingsPersistenceError(CodePulseError):
    """Raised when user preferences cannot be loaded from or saved to disk."""


class DesktopLayoutError(CodePulseError):
    """Raised when the placed-widget desktop layout cannot be saved to disk."""


class GoalPersistenceError(CodePulseError):
    """Raised when user-defined goals cannot be saved to disk."""


class NotificationStatePersistenceError(CodePulseError):
    """Raised when notification de-duplication state cannot be saved to disk."""


class ConfigurationError(CodePulseError):
    """Raised when application configuration is missing or invalid."""


class ProviderError(CodePulseError):
    """Raised when a coding-platform provider fails to fetch or parse data."""


class InvalidUsernameError(ProviderError):
    """Raised when a provider has no user matching the requested username."""


class RateLimitError(ProviderError):
    """Raised when a provider's API has rate-limited this client."""


class NetworkError(ProviderError):
    """Raised when a provider request fails due to connectivity or timeout."""

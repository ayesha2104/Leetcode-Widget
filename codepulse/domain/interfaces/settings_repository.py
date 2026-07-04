"""Abstract port for persisting user-editable preferences.

Implemented by :class:`codepulse.infrastructure.persistence.json_settings_repository.JsonSettingsRepository`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codepulse.domain.models.preferences import UserPreferences


class SettingsRepository(ABC):
    """Loads and saves the user's :class:`UserPreferences`."""

    @abstractmethod
    def load(self) -> UserPreferences:
        """Return the persisted preferences, or defaults if none exist yet."""

    @abstractmethod
    def save(self, preferences: UserPreferences) -> None:
        """Persist ``preferences``, replacing whatever was stored before."""

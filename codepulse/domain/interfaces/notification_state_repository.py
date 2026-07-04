"""Abstract port for persisting :class:`NotificationState`.

Implemented by :class:`codepulse.infrastructure.persistence.json_notification_state_repository.JsonNotificationStateRepository`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codepulse.domain.models.notification_state import NotificationState


class NotificationStateRepository(ABC):
    """Loads and saves notification de-duplication state."""

    @abstractmethod
    def load(self) -> NotificationState:
        """Return the persisted state, or defaults if none exists yet."""

    @abstractmethod
    def save(self, state: NotificationState) -> None:
        """Persist ``state``, replacing whatever was stored before."""

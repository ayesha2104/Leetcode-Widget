"""Abstract port for sending a user-facing notification.

Implemented by :class:`codepulse.infrastructure.notifications.windows_notifier.WindowsNotifier`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Sends a short title/message notification to the user."""

    @abstractmethod
    def notify(self, title: str, message: str) -> None:
        """Show a notification. Must never raise -- failures are logged and swallowed."""

"""Abstract port for persisting which widgets are on the desktop, and where.

Implemented by :class:`codepulse.infrastructure.persistence.json_desktop_layout_repository.JsonDesktopLayoutRepository`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codepulse.domain.models.widget import PlacedWidget


class DesktopLayoutRepository(ABC):
    """Loads and saves the list of :class:`PlacedWidget` currently on the desktop."""

    @abstractmethod
    def load(self) -> list[PlacedWidget]:
        """Return the persisted widget layout, or an empty list if none exists yet."""

    @abstractmethod
    def save(self, widgets: list[PlacedWidget]) -> None:
        """Persist ``widgets``, replacing whatever layout was stored before."""

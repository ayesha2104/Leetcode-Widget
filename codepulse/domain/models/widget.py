"""Catalog identifiers and layout state for the desktop widget system.

A user assembles their desktop from independent floating widgets (Streak,
Progress, Contest, ...) rather than a single fixed dashboard. ``WidgetKind``
and ``WidgetSize`` identify *what* to render; ``PlacedWidget`` is the
persisted record of *which* widgets currently exist on the desktop and
where.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class WidgetKind(StrEnum):
    """Identifies which piece of LeetCode data a widget displays."""

    STREAK = "streak"
    PROGRESS = "progress"
    CONTEST = "contest"
    RATING = "rating"
    DAILY = "daily"
    ACTIVITY = "activity"
    GOALS = "goals"
    BADGES = "badges"


class WidgetSize(StrEnum):
    """Display density of an individual widget card."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class PlacedWidget(BaseModel):
    """One widget instance the user has added to their desktop."""

    uid: str
    kind: WidgetKind
    size: WidgetSize
    x: int = Field(default=100)
    y: int = Field(default=100)

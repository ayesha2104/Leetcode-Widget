"""Static catalog of available desktop widgets.

Drives the widget picker gallery: names, descriptions, categories, which
sizes each widget kind supports, and the pixel dimensions for each size.
Purely presentation metadata -- it has no opinion on what data a widget
displays, only how it's presented for selection.
"""

from __future__ import annotations

from dataclasses import dataclass

from codepulse.domain.models.widget import WidgetKind, WidgetSize


@dataclass(frozen=True, slots=True)
class WidgetCatalogEntry:
    """One selectable entry in the widget picker gallery."""

    kind: WidgetKind
    name: str
    description: str
    category: str
    icon: str
    sizes: tuple[WidgetSize, ...]


WIDGET_CATALOG: tuple[WidgetCatalogEntry, ...] = (
    WidgetCatalogEntry(
        kind=WidgetKind.STREAK,
        name="Streak",
        description="Current solving streak with flame animation",
        category="Stats",
        icon="\U0001f525",
        sizes=(WidgetSize.SMALL, WidgetSize.MEDIUM),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.PROGRESS,
        name="Progress",
        description="Problems solved with activity heatmap",
        category="Stats",
        icon="\U0001f4ca",
        sizes=(WidgetSize.SMALL, WidgetSize.MEDIUM, WidgetSize.LARGE),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.CONTEST,
        name="Contest",
        description="Upcoming contest with countdown & registration",
        category="Contest",
        icon="\U0001f3c6",
        sizes=(WidgetSize.MEDIUM, WidgetSize.LARGE),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.RATING,
        name="Rating",
        description="Contest rating trend graph",
        category="Contest",
        icon="\U0001f4c8",
        sizes=(WidgetSize.MEDIUM, WidgetSize.LARGE),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.DAILY,
        name="Daily Challenge",
        description="Today's problem with difficulty badge",
        category="Practice",
        icon="⚡",
        sizes=(WidgetSize.SMALL, WidgetSize.MEDIUM),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.ACTIVITY,
        name="Recent Activity",
        description="Timeline of solved problems and achievements",
        category="Practice",
        icon="\U0001f550",
        sizes=(WidgetSize.MEDIUM, WidgetSize.LARGE),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.GOALS,
        name="Goals",
        description="Weekly and monthly solving targets",
        category="Practice",
        icon="\U0001f3af",
        sizes=(WidgetSize.SMALL, WidgetSize.MEDIUM),
    ),
    WidgetCatalogEntry(
        kind=WidgetKind.BADGES,
        name="Badges",
        description="Earned achievement badges showcase",
        category="Achievements",
        icon="\U0001f396",
        sizes=(WidgetSize.SMALL, WidgetSize.MEDIUM),
    ),
)

CATEGORIES: tuple[str, ...] = ("All", "Stats", "Contest", "Practice", "Achievements")

SIZE_DIMENSIONS: dict[WidgetSize, tuple[int, int]] = {
    WidgetSize.SMALL: (150, 150),
    WidgetSize.MEDIUM: (310, 150),
    WidgetSize.LARGE: (310, 310),
}


def get_catalog_entry(kind: WidgetKind) -> WidgetCatalogEntry:
    """Return the catalog entry for ``kind``."""
    for entry in WIDGET_CATALOG:
        if entry.kind == kind:
            return entry
    raise KeyError(f"No catalog entry for widget kind {kind!r}")

from __future__ import annotations

import pytest

from codepulse.domain.models.widget import WidgetKind
from codepulse.presentation.widgets.catalog import (
    CATEGORIES,
    SIZE_DIMENSIONS,
    WIDGET_CATALOG,
    get_catalog_entry,
)


def test_catalog_has_an_entry_for_every_widget_kind() -> None:
    catalog_kinds = {entry.kind for entry in WIDGET_CATALOG}

    assert catalog_kinds == set(WidgetKind)


def test_every_entry_has_at_least_one_size() -> None:
    for entry in WIDGET_CATALOG:
        assert len(entry.sizes) >= 1


def test_every_entry_category_is_a_known_category() -> None:
    for entry in WIDGET_CATALOG:
        assert entry.category in CATEGORIES


def test_get_catalog_entry_returns_matching_entry() -> None:
    entry = get_catalog_entry(WidgetKind.PROGRESS)

    assert entry.kind == WidgetKind.PROGRESS
    assert entry.name == "Progress"


def test_get_catalog_entry_raises_for_unknown_kind() -> None:
    with pytest.raises(KeyError):
        get_catalog_entry("not-a-real-kind")  # type: ignore[arg-type]


def test_size_dimensions_defined_for_every_size_used_in_catalog() -> None:
    used_sizes = {size for entry in WIDGET_CATALOG for size in entry.sizes}

    assert used_sizes <= set(SIZE_DIMENSIONS)

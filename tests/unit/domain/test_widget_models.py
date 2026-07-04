from __future__ import annotations

from codepulse.domain.models.widget import PlacedWidget, WidgetKind, WidgetSize


def test_placed_widget_has_default_position() -> None:
    widget = PlacedWidget(uid="1", kind=WidgetKind.STREAK, size=WidgetSize.SMALL)

    assert widget.x == 100
    assert widget.y == 100


def test_placed_widget_round_trips_through_json() -> None:
    widget = PlacedWidget(uid="abc", kind=WidgetKind.PROGRESS, size=WidgetSize.LARGE, x=42, y=7)

    restored = PlacedWidget.model_validate_json(widget.model_dump_json())

    assert restored == widget


def test_widget_kind_and_size_are_string_enums() -> None:
    assert WidgetKind.STREAK == "streak"
    assert WidgetSize.MEDIUM == "medium"

from __future__ import annotations

from pathlib import Path

import pytest

from codepulse.domain.exceptions import DesktopLayoutError
from codepulse.domain.models.widget import PlacedWidget, WidgetKind, WidgetSize
from codepulse.infrastructure.persistence.json_desktop_layout_repository import (
    JsonDesktopLayoutRepository,
)


def test_load_returns_empty_list_when_file_missing(tmp_path: Path) -> None:
    repository = JsonDesktopLayoutRepository(tmp_path / "layout.json")

    assert repository.load() == []


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    repository = JsonDesktopLayoutRepository(tmp_path / "layout.json")
    widgets = [
        PlacedWidget(uid="1", kind=WidgetKind.STREAK, size=WidgetSize.SMALL, x=10, y=20),
        PlacedWidget(uid="2", kind=WidgetKind.PROGRESS, size=WidgetSize.LARGE, x=200, y=300),
    ]

    repository.save(widgets)
    loaded = repository.load()

    assert loaded == widgets


def test_corrupt_file_falls_back_to_empty_list_and_backs_up(tmp_path: Path) -> None:
    file_path = tmp_path / "layout.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    repository = JsonDesktopLayoutRepository(file_path)
    widgets = repository.load()

    assert widgets == []
    backups = list(tmp_path.glob("layout.corrupt-*.json"))
    assert len(backups) == 1


def test_save_is_atomic_no_tmp_file_left_behind(tmp_path: Path) -> None:
    repository = JsonDesktopLayoutRepository(tmp_path / "layout.json")

    repository.save([])

    assert not (tmp_path / "layout.tmp").exists()


def test_save_raises_desktop_layout_error_on_os_failure(tmp_path: Path) -> None:
    # A directory can never be replaced by a file write -- forces the OSError path.
    directory_as_file_path = tmp_path / "layout_dir"
    directory_as_file_path.mkdir()
    repository = JsonDesktopLayoutRepository(directory_as_file_path)

    with pytest.raises(DesktopLayoutError):
        repository.save([])

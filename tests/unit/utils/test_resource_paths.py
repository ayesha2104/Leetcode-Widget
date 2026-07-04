from __future__ import annotations

import sys

import pytest

from codepulse.utils.resource_paths import get_assets_dir


def test_assets_dir_exists_and_contains_themes() -> None:
    assets_dir = get_assets_dir()

    assert assets_dir.is_dir()
    assert (assets_dir / "themes" / "dark.json").exists()


def test_assets_dir_uses_meipass_when_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", r"C:\frozen\app", raising=False)

    assets_dir = get_assets_dir()

    assert str(assets_dir) == r"C:\frozen\app\assets"

from __future__ import annotations

import winreg
from unittest.mock import MagicMock

import pytest

from codepulse.infrastructure.os.windows_startup import (
    is_start_with_windows_enabled,
    set_start_with_windows,
)

# Every test here mocks winreg entirely -- this must never touch the real
# developer machine's startup registry key.


@pytest.fixture(autouse=True)
def _mock_winreg(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_key = MagicMock()
    mock_key.__enter__ = MagicMock(return_value=mock_key)
    mock_key.__exit__ = MagicMock(return_value=False)

    mock_open_key = MagicMock(return_value=mock_key)
    monkeypatch.setattr(winreg, "OpenKey", mock_open_key)
    monkeypatch.setattr(winreg, "SetValueEx", MagicMock())
    monkeypatch.setattr(winreg, "DeleteValue", MagicMock())
    monkeypatch.setattr(winreg, "QueryValueEx", MagicMock(return_value=("value", 1)))
    return mock_open_key


def test_set_start_with_windows_enabled_writes_registry_value(_mock_winreg: MagicMock) -> None:
    set_start_with_windows(True, executable_path=r"C:\fake\codepulse.exe")

    winreg.SetValueEx.assert_called_once()  # type: ignore[attr-defined]
    args = winreg.SetValueEx.call_args.args  # type: ignore[attr-defined]
    assert args[1] == "CodePulse"
    assert args[4] == r"C:\fake\codepulse.exe"


def test_set_start_with_windows_disabled_deletes_registry_value(_mock_winreg: MagicMock) -> None:
    set_start_with_windows(False)

    winreg.DeleteValue.assert_called_once()  # type: ignore[attr-defined]


def test_set_start_with_windows_disabled_ignores_missing_value(
    monkeypatch: pytest.MonkeyPatch, _mock_winreg: MagicMock
) -> None:
    monkeypatch.setattr(winreg, "DeleteValue", MagicMock(side_effect=FileNotFoundError()))

    set_start_with_windows(False)  # must not raise


def test_set_start_with_windows_swallows_os_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(winreg, "OpenKey", MagicMock(side_effect=OSError("access denied")))

    set_start_with_windows(True)  # must not raise


def test_is_enabled_returns_true_when_value_exists(_mock_winreg: MagicMock) -> None:
    assert is_start_with_windows_enabled() is True


def test_is_enabled_returns_false_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(winreg, "OpenKey", MagicMock(side_effect=FileNotFoundError()))

    assert is_start_with_windows_enabled() is False

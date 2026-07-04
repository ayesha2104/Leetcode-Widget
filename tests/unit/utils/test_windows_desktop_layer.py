from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from codepulse.utils import windows_desktop_layer as layer

# Every test here mocks the user32 calls entirely -- this must never touch
# the real developer machine's Explorer/desktop windows.

_FAKE_WINDOW_HANDLE = 4242


def _fake_find_window_ex(_hwnd_parent, _hwnd_child_after, class_name, _window_name):
    if class_name == "SHELLDLL_DefView":
        return 111
    if class_name == "WorkerW":
        return 222
    return 0


@pytest.fixture(autouse=True)
def _mock_user32(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(layer._user32, "FindWindowW", MagicMock(return_value=999))
    monkeypatch.setattr(layer._user32, "SendMessageTimeoutW", MagicMock(return_value=0))
    monkeypatch.setattr(
        layer._user32, "EnumWindows", MagicMock(side_effect=lambda cb, _lp: cb(888, 0))
    )
    monkeypatch.setattr(layer._user32, "FindWindowExW", MagicMock(side_effect=_fake_find_window_ex))
    monkeypatch.setattr(layer._user32, "SetParent", MagicMock(return_value=1))


def test_pin_to_desktop_reparents_window_into_the_empty_workerw() -> None:
    result = layer.pin_to_desktop(_FAKE_WINDOW_HANDLE)

    assert result is True
    layer._user32.SetParent.assert_called_once_with(_FAKE_WINDOW_HANDLE, 222)  # type: ignore[attr-defined]


def test_pin_to_desktop_returns_false_when_progman_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(layer._user32, "FindWindowW", MagicMock(return_value=0))

    assert layer.pin_to_desktop(_FAKE_WINDOW_HANDLE) is False


def test_pin_to_desktop_returns_false_when_no_workerw_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(layer._user32, "FindWindowExW", MagicMock(return_value=0))

    assert layer.pin_to_desktop(_FAKE_WINDOW_HANDLE) is False
    layer._user32.SetParent.assert_not_called()  # type: ignore[attr-defined]


def test_pin_to_desktop_swallows_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(layer._user32, "FindWindowW", MagicMock(side_effect=OSError("no shell")))

    assert layer.pin_to_desktop(_FAKE_WINDOW_HANDLE) is False

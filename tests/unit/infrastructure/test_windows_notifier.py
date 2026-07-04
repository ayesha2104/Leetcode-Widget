from __future__ import annotations

import winreg
from unittest.mock import MagicMock

import pytest

from codepulse.infrastructure.notifications import windows_notifier as notifier_module
from codepulse.infrastructure.notifications.windows_notifier import WindowsNotifier

# Every test here mocks windows_toasts and the AUMID registration entirely --
# this must never pop a real toast or touch the real registry during an
# automated test run.


@pytest.fixture
def mock_register_aumid(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    monkeypatch.setattr(notifier_module, "_register_aumid", mock)
    return mock


def test_notify_shows_a_toast_with_title_and_message(
    monkeypatch: pytest.MonkeyPatch, mock_register_aumid: MagicMock
) -> None:
    mock_toaster_instance = MagicMock()
    monkeypatch.setattr(
        notifier_module, "WindowsToaster", MagicMock(return_value=mock_toaster_instance)
    )
    mock_toast_cls = MagicMock()
    monkeypatch.setattr(notifier_module, "Toast", mock_toast_cls)

    notifier = WindowsNotifier()
    notifier.notify("Title", "Message")

    mock_toast_cls.assert_called_once_with(["Title", "Message"])
    mock_toaster_instance.show_toast.assert_called_once()


def test_constructor_registers_aumid(mock_register_aumid: MagicMock) -> None:
    WindowsNotifier()

    mock_register_aumid.assert_called_once()


def test_constructor_failure_degrades_to_logged_noop(
    monkeypatch: pytest.MonkeyPatch, mock_register_aumid: MagicMock
) -> None:
    monkeypatch.setattr(
        notifier_module, "WindowsToaster", MagicMock(side_effect=OSError("no toast support"))
    )

    notifier = WindowsNotifier()
    notifier.notify("Title", "Message")  # must not raise


def test_show_toast_failure_is_swallowed(
    monkeypatch: pytest.MonkeyPatch, mock_register_aumid: MagicMock
) -> None:
    mock_toaster_instance = MagicMock()
    mock_toaster_instance.show_toast.side_effect = RuntimeError("boom")
    monkeypatch.setattr(
        notifier_module, "WindowsToaster", MagicMock(return_value=mock_toaster_instance)
    )

    notifier = WindowsNotifier()
    notifier.notify("Title", "Message")  # must not raise


def test_register_aumid_sets_registry_display_name(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_key = MagicMock()
    mock_key.__enter__ = MagicMock(return_value=mock_key)
    mock_key.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(winreg, "CreateKey", MagicMock(return_value=mock_key))
    monkeypatch.setattr(winreg, "SetValueEx", MagicMock())
    mock_shell32 = MagicMock()
    monkeypatch.setattr(notifier_module.ctypes, "windll", MagicMock(shell32=mock_shell32))

    notifier_module._register_aumid()

    winreg.SetValueEx.assert_called_once()  # type: ignore[attr-defined]
    mock_shell32.SetCurrentProcessExplicitAppUserModelID.assert_called_once_with("CodePulse")


def test_register_aumid_swallows_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(winreg, "CreateKey", MagicMock(side_effect=OSError("access denied")))

    notifier_module._register_aumid()  # must not raise

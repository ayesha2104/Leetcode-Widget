"""Sends Windows toast notifications via the ``windows-toasts`` library.

Degrades to a logged no-op if the toaster can't be constructed (e.g. an
unsupported Windows version) or a specific ``show_toast`` call fails --
per the "never crash" requirement, a failed notification is never worth
taking the whole app down over.
"""

from __future__ import annotations

import ctypes
import winreg

from loguru import logger
from windows_toasts import Toast, WindowsToaster

from codepulse.domain.interfaces.notifier import Notifier

_AUMID = "CodePulse"
_AUMID_REGISTRY_PATH = rf"Software\Classes\AppUserModelId\{_AUMID}"


def _register_aumid() -> None:
    """Register CodePulse's Application User Model ID so Windows will render its toasts.

    ``ToastNotificationManager.create_toast_notifier_with_id`` (used
    internally by ``WindowsToaster``) accepts an arbitrary, unregistered ID
    without error, but Windows silently drops any toast sent under an ID it
    can't resolve to a known app -- ``show_toast`` "succeeds" yet nothing
    ever appears. Registering a DisplayName under this registry key plus
    telling the current process to use it as its AUMID is the standard,
    documented workaround for unpackaged Win32/console Python apps (a
    properly installed app with a Start Menu shortcut gets this for free).
    """
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _AUMID_REGISTRY_PATH) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, _AUMID)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_AUMID)
    except OSError as exc:
        logger.warning("Could not register CodePulse's AUMID for toast notifications: {}", exc)


class WindowsNotifier(Notifier):
    """Shows Windows 10/11 toast notifications for CodePulse."""

    def __init__(self, app_name: str = _AUMID) -> None:
        _register_aumid()
        try:
            self._toaster: WindowsToaster | None = WindowsToaster(app_name)
        except Exception as exc:  # third-party toast backend init can fail many ways
            logger.warning("Windows toast notifications unavailable: {}", exc)
            self._toaster = None

    def notify(self, title: str, message: str) -> None:
        if self._toaster is None:
            logger.info("Notification (toasts unavailable): {} - {}", title, message)
            return

        try:
            self._toaster.show_toast(Toast([title, message]))
        except Exception as exc:  # never let a failed toast take the app down
            logger.warning("Failed to show toast notification {!r}: {}", title, exc)

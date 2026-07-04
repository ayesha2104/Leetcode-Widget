"""Registers/unregisters CodePulse in the current user's Windows startup.

Uses the per-user ``Run`` registry key (no admin rights needed) rather than
a scheduled task or service -- the same mechanism most consumer desktop
apps use for "start with Windows".
"""

from __future__ import annotations

import contextlib
import sys
import winreg

from loguru import logger

_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "CodePulse"


def set_start_with_windows(enabled: bool, *, executable_path: str | None = None) -> None:
    """Add or remove CodePulse from the per-user Windows startup registry key."""
    target_path = executable_path or sys.executable
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, target_path)
            else:
                with contextlib.suppress(FileNotFoundError):
                    winreg.DeleteValue(key, _VALUE_NAME)
    except OSError as exc:
        logger.warning("Could not update Windows startup registration: {}", exc)


def is_start_with_windows_enabled() -> bool:
    """Return whether CodePulse is currently registered to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except OSError:
        return False

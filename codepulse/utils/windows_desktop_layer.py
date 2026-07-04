"""Best-effort "pin to the desktop" placement, the same trick Rainmeter and
Wallpaper Engine use to render widgets behind every application window but
above the wallpaper, at the same visual layer as desktop icons.

Undocumented and Explorer-version-dependent: Explorer normally only creates
a "WorkerW" host window (originally meant for the desktop slideshow
feature) after being sent an undocumented message. Once it exists, we can
reparent our own window into it via ``SetParent`` so it inherits that
layer's z-order -- behind normal app windows, above the wallpaper, never
stealing focus or appearing in Alt+Tab.

Every step here can silently fail on some Windows build (Explorer changes
this internal behavior between releases without notice); callers must
treat a ``False`` return as "fall back to a normal window", not an error.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from loguru import logger

_SPAWN_WORKERW_MESSAGE = 0x052C
_SEND_MESSAGE_TIMEOUT_MS = 1000

_user32 = ctypes.WinDLL("user32", use_last_error=True)

_user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_user32.FindWindowW.restype = wintypes.HWND

_user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(wintypes.DWORD),
]
_user32.SendMessageTimeoutW.restype = wintypes.LPARAM

_user32.FindWindowExW.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
]
_user32.FindWindowExW.restype = wintypes.HWND

_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL

_user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
_user32.SetParent.restype = wintypes.HWND


def _find_empty_workerw() -> int:
    """Find the WorkerW sibling that hosts nothing (the one behind icons).

    Explorer's desktop is: Progman -> SHELLDLL_DefView (the icons) inside
    one WorkerW, plus an empty sibling WorkerW created for the slideshow
    feature. That empty one is the layer we want; the icon-hosting one must
    be left alone.
    """
    empty_worker_w = wintypes.HWND(0)

    def _visit(hwnd: int, _lparam: int) -> bool:
        nonlocal empty_worker_w
        has_icons = _user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if has_icons:
            candidate = _user32.FindWindowExW(None, hwnd, "WorkerW", None)
            if candidate:
                empty_worker_w = wintypes.HWND(candidate)
        return True

    _user32.EnumWindows(_WNDENUMPROC(_visit), 0)
    return empty_worker_w.value or 0


def pin_to_desktop(window_handle: int) -> bool:
    """Reparent ``window_handle`` behind every app window, at the desktop-icon layer.

    Returns ``True`` if the reparent succeeded, ``False`` if Explorer didn't
    respond the expected way on this Windows build -- callers should keep
    the window as a normal (non-topmost) window in that case rather than
    treating this as fatal.
    """
    try:
        progman = _user32.FindWindowW("Progman", None)
        if not progman:
            return False

        # Undocumented: asks Explorer to spawn the WorkerW used for the
        # desktop slideshow feature, which is otherwise absent.
        timeout_result = wintypes.DWORD()
        _user32.SendMessageTimeoutW(
            progman,
            _SPAWN_WORKERW_MESSAGE,
            0,
            0,
            0,
            _SEND_MESSAGE_TIMEOUT_MS,
            ctypes.byref(timeout_result),
        )

        worker_w = _find_empty_workerw()
        if not worker_w:
            return False

        return bool(_user32.SetParent(window_handle, worker_w))
    except OSError as exc:
        logger.warning("Could not pin window to the desktop layer: {}", exc)
        return False

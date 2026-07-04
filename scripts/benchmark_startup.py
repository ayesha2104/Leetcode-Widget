"""Measures CodePulse's startup time, memory footprint, and idle CPU usage.

Dev-only diagnostic script, not part of the shipped application. Uses only
stdlib (ctypes into the Win32 psapi/kernel32 APIs) so it carries no extra
dependency just to answer "does this meet the performance targets".

Usage::

    python scripts/benchmark_startup.py
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = (
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    )


_psapi = ctypes.WinDLL("psapi.dll")
_psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(_ProcessMemoryCounters),
    wintypes.DWORD,
]
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


def _working_set_bytes() -> int:
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    _psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    return counters.WorkingSetSize


_kernel32 = ctypes.WinDLL("kernel32.dll")
_kernel32.GetProcessTimes.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
]
_kernel32.GetProcessTimes.restype = wintypes.BOOL


def _cpu_time_seconds() -> float:
    """Total user+kernel CPU time consumed by this process so far, in seconds."""
    creation, exit_, kernel, user = (wintypes.FILETIME() for _ in range(4))
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    _kernel32.GetProcessTimes(
        handle,
        ctypes.byref(creation),
        ctypes.byref(exit_),
        ctypes.byref(kernel),
        ctypes.byref(user),
    )

    def _filetime_to_seconds(ft: wintypes.FILETIME) -> float:
        return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10_000_000

    return _filetime_to_seconds(kernel) + _filetime_to_seconds(user)


def main() -> None:
    process_start = time.perf_counter()

    import tempfile

    from PySide6.QtWidgets import QApplication

    import codepulse.main as main_module
    from codepulse.infrastructure.config.settings import AppSettings

    settings = AppSettings(data_dir=Path(tempfile.mkdtemp()))
    main_module.get_app_settings = lambda: settings
    main_module.WindowsNotifier = MagicMock()

    app = QApplication.instance() or QApplication(sys.argv)
    app.exec = lambda: 0  # never actually block
    main_module.QApplication = MagicMock(return_value=app)

    startup_start = time.perf_counter()
    main_module.main()
    startup_elapsed = time.perf_counter() - startup_start

    total_elapsed = time.perf_counter() - process_start
    working_set_mb = _working_set_bytes() / (1024 * 1024)

    print(f"Import + composition-root time: {startup_start - process_start:.3f}s")
    print(f"main() wiring + window.show() time: {startup_elapsed:.3f}s")
    print(f"Total time to first paint: {total_elapsed:.3f}s (target: < 2s)")
    print(f"Working set memory after startup: {working_set_mb:.1f} MB (target: < 100 MB)")

    # Idle CPU: pump the real event loop for a few seconds with nothing to do
    # (no user interaction) and see how much CPU time that actually consumed.
    idle_duration_s = 3.0
    cpu_before = _cpu_time_seconds()
    wall_before = time.perf_counter()

    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    QTimer.singleShot(int(idle_duration_s * 1000), loop.quit)
    loop.exec()

    cpu_after = _cpu_time_seconds()
    wall_elapsed = time.perf_counter() - wall_before
    idle_cpu_percent = (cpu_after - cpu_before) / wall_elapsed * 100
    print(
        f"Idle CPU over {wall_elapsed:.1f}s with widgets running: {idle_cpu_percent:.2f}% (target: < 1%)"
    )


if __name__ == "__main__":
    main()

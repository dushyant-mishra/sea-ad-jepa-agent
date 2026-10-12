#!/usr/bin/env python3
"""Standard-library resource monitoring and single-heavy-fit custody for V79."""
from __future__ import annotations

import contextlib
import ctypes
import os
import platform
import threading
import time
from pathlib import Path


class ResourceMonitorRefused(RuntimeError):
    pass


def _rss_bytes() -> int:
    if platform.system().lower() == "windows":
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = PMC(); counters.cb = ctypes.sizeof(PMC)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.argtypes = []
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        get_process_memory_info.restype = wintypes.BOOL
        h = get_current_process()
        if not get_process_memory_info(h, ctypes.byref(counters), counters.cb):
            raise ResourceMonitorRefused("GetProcessMemoryInfo failed")
        return int(counters.WorkingSetSize)
    try:
        import resource
        v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return v if platform.system().lower() == "darwin" else v * 1024
    except Exception as exc:
        raise ResourceMonitorRefused(f"RSS unavailable: {exc}") from exc


class ResourceMonitor:
    def __init__(self, poll_seconds: float = 0.25):
        self.poll_seconds = float(poll_seconds); self.peak_rss = 0; self._stop = threading.Event(); self._thread = None
        self.wall_start = self.cpu_start = 0.0
    def _poll(self):
        while not self._stop.is_set():
            self.peak_rss = max(self.peak_rss, _rss_bytes())
            self._stop.wait(self.poll_seconds)
    def __enter__(self):
        self.wall_start = time.perf_counter(); self.cpu_start = time.process_time(); self.peak_rss = _rss_bytes()
        self._thread = threading.Thread(target=self._poll, daemon=True); self._thread.start(); return self
    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        if self._thread is not None: self._thread.join(timeout=max(1.0, self.poll_seconds * 4))
        self.peak_rss = max(self.peak_rss, _rss_bytes())
        self.wall_seconds = time.perf_counter() - self.wall_start
        self.process_cpu_seconds = time.process_time() - self.cpu_start


@contextlib.contextmanager
def single_heavy_fit_lock(lock_path: Path):
    """O_EXCL lock; a stale lock is never auto-deleted or stolen."""
    p = Path(lock_path); p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ResourceMonitorRefused(f"heavy-fit lock already exists: {p}") from exc
    try:
        os.write(fd, f"pid={os.getpid()}\n".encode()); os.close(fd); fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        if p.exists():
            p.unlink()

# SPDX-License-Identifier: Apache-2.0
"""M0 - foreground window snapshot.

Captures the active window only: HWND, owning process, DPI-aware bounds and a
monotonically increasing screen_revision. The Desktop Root is never scanned.
"""
import ctypes
import threading
import time
from ctypes import wintypes

_u32 = ctypes.WinDLL("user32", use_last_error=True)
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)

if not _u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
    _u32.SetProcessDPIAware()

_revision = 0
_rev_lock = threading.Lock()


def bump_revision():
    global _revision
    with _rev_lock:
        _revision += 1
        return _revision


def current_revision():
    with _rev_lock:
        return _revision


def ensure_min_revision(minimum):
    global _revision
    with _rev_lock:
        if int(minimum) > _revision:
            _revision = int(minimum)
        return _revision


def _process_name(pid):
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = _k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return "unknown"
    try:
        size = wintypes.DWORD(512)
        buf = ctypes.create_unicode_buffer(size.value)
        if _k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1]
        return "unknown"
    finally:
        _k32.CloseHandle(h)


def _window_bounds(hwnd):
    """DWM extended frame bounds when available (excludes invisible resize borders)."""
    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                    ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

    r = RECT()
    try:
        dwm = ctypes.WinDLL("dwmapi")
        if dwm.DwmGetWindowAttribute(wintypes.HWND(hwnd), 9, ctypes.byref(r),
                                     ctypes.sizeof(RECT)) == 0 and r.right > r.left:
            return [r.left, r.top, r.right - r.left, r.bottom - r.top]
    except OSError:
        pass
    if _u32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(r)):
        return [r.left, r.top, r.right - r.left, r.bottom - r.top]
    return None


def client_origin(hwnd):
    pt = wintypes.POINT(0, 0)
    _u32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(pt))
    return pt.x, pt.y


def active_window():
    """Snapshot of the current foreground window. No desktop-root enumeration."""
    hwnd = _u32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    n = _u32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    _u32.GetWindowTextW(hwnd, buf, n + 1)
    return {"hwnd": hwnd, "pid": pid.value, "process": _process_name(pid.value),
            "title": buf.value, "bounds": _window_bounds(hwnd),
            "client_origin": list(client_origin(hwnd)),
            "revision": bump_revision(), "captured_at": time.time()}


def window(hwnd, bump=False):
    """Metadata/bounds of a specific window; never bumps revision unless bump=True."""
    pid = wintypes.DWORD()
    _u32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    n = _u32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    _u32.GetWindowTextW(hwnd, buf, n + 1)
    rev = bump_revision() if bump else current_revision()
    return {"hwnd": hwnd, "pid": pid.value, "process": _process_name(pid.value),
            "title": buf.value, "bounds": _window_bounds(hwnd),
            "client_origin": list(client_origin(hwnd)),
            "revision": rev, "captured_at": time.time()}

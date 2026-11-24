# SPDX-License-Identifier: Apache-2.0
"""Win32 probe primitives for H2 (Windows desktop cursor probing).

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 is set as the very first executable
statement, before any window rect, UIA query or cursor move (ctypes line 1 rule).

Real pointer input: SendInput with MOUSEEVENTF_MOVE | ABSOLUTE | VIRTUALDESK.
Cursor classification: GetCursorInfo only (no GetIconInfo bitmap parsing).
Kill switch: if the physical cursor is more than 5 px from the last commanded
position before a probe, the run aborts, restores the cursor and hands control back.
"""
import ctypes
from ctypes import wintypes

_u32 = ctypes.WinDLL("user32", use_last_error=True)
_gdi = ctypes.WinDLL("gdi32", use_last_error=True)

# --- line 1: DPI awareness, before anything else ---------------------------------
_u32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
_u32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
_u32.SetProcessDPIAware.argtypes = []
_u32.SetProcessDPIAware.restype = wintypes.BOOL
if not _u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
    _u32.SetProcessDPIAware()
# -------------------------------------------------------------------------------

VK_ESCAPE = 0x1B
MOUSEEVENTF_MOVE, MOUSEEVENTF_ABSOLUTE, MOUSEEVENTF_VIRTUALDESK = 0x0001, 0x8000, 0x4000
IDC = {"arrow": 32512, "ibeam": 32513, "hand": 32649, "wait": 32514, "cross": 32515}
SW_RESTORE = 9
GA_ROOT = 2

ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class _UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _UNION)]


class CURSORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("hCursor", ctypes.c_void_p), ("ptScreenPos", wintypes.POINT)]


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


# Explicit Win32 ctypes signatures (prevents 64-bit pointer truncation on Windows)
_u32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
_u32.LoadCursorW.restype = ctypes.c_void_p
_u32.GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]
_u32.GetCursorInfo.restype = wintypes.BOOL
_u32.GetSystemMetrics.argtypes = [ctypes.c_int]
_u32.GetSystemMetrics.restype = ctypes.c_int
_u32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_u32.SendInput.restype = wintypes.UINT
_u32.GetForegroundWindow.argtypes = []
_u32.GetForegroundWindow.restype = wintypes.HWND
_u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
_u32.GetWindowRect.restype = wintypes.BOOL
_u32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
_u32.GetClientRect.restype = wintypes.BOOL
_u32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
_u32.ClientToScreen.restype = wintypes.BOOL
_u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_u32.ShowWindow.restype = wintypes.BOOL
_u32.SetForegroundWindow.argtypes = [wintypes.HWND]
_u32.SetForegroundWindow.restype = wintypes.BOOL
_u32.IsWindowVisible.argtypes = [wintypes.HWND]
_u32.IsWindowVisible.restype = wintypes.BOOL
_u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_u32.GetWindowTextLengthW.restype = ctypes.c_int
_u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetWindowTextW.restype = ctypes.c_int
_u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetClassNameW.restype = ctypes.c_int
_u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_u32.PostMessageW.restype = wintypes.BOOL
_u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_u32.GetWindowThreadProcessId.restype = wintypes.DWORD
_u32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
_u32.EnumWindows.restype = wintypes.BOOL
_u32.EnumChildWindows.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.LPARAM]
_u32.EnumChildWindows.restype = wintypes.BOOL
_u32.GetWindowDC.argtypes = [wintypes.HWND]
_u32.GetWindowDC.restype = wintypes.HDC
_u32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
_u32.ReleaseDC.restype = ctypes.c_int
_u32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
_u32.PrintWindow.restype = wintypes.BOOL


def _cursor_handle(name):
    val = _u32.LoadCursorW(None, ctypes.c_void_p(IDC[name]))
    return int(val) if val else None


SYSTEM_CURSORS = {str(_cursor_handle(n)): n for n in ("arrow", "ibeam", "hand")}


def cursor_state():
    """(handle string, (x, y)) - handle via GetCursorInfo, nothing else."""
    ci = CURSORINFO(ctypes.sizeof(CURSORINFO), 0, None, wintypes.POINT(0, 0))
    if not _u32.GetCursorInfo(ctypes.byref(ci)):
        err = ctypes.get_last_error()
        return f"error:{err}", (0, 0)
    hval = ctypes.cast(ci.hCursor, ctypes.c_void_p).value
    return (str(int(hval)) if hval is not None else "None"), (ci.ptScreenPos.x, ci.ptScreenPos.y)


def cursor_class(handle):
    name = SYSTEM_CURSORS.get(handle)
    if name == "hand":
        return "HAND"
    if name == "ibeam":
        return "IBEAM"
    if name == "arrow":
        return "ARROW"
    if handle in (None, "None", "unknown") or str(handle).startswith("error:"):
        return "UNKNOWN"
    return f"CUSTOM:{int(handle):#x}"


def move(x, y):
    """Absolute move in virtual-desktop coordinates via SendInput."""
    vx, vy = _u32.GetSystemMetrics(76), _u32.GetSystemMetrics(77)
    vw, vh = _u32.GetSystemMetrics(78), _u32.GetSystemMetrics(79)
    nx = int(round((x - vx) * 65535 / max(vw - 1, 1)))
    ny = int(round((y - vy) * 65535 / max(vh - 1, 1)))
    inp = INPUT(0, _UNION(mi=MOUSEINPUT(nx, ny, 0,
                                        MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                                        0, 0)))
    sent = _u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if sent != 1:
        raise OSError(f"SendInput failed: {ctypes.get_last_error()}")
    return x, y


def foreground():
    return _u32.GetForegroundWindow()


def window_rect(hwnd):
    r = RECT()
    if _u32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(r)):
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def client_origin(hwnd):
    pt = wintypes.POINT(0, 0)
    _u32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(pt))
    return pt.x, pt.y


def client_rect(hwnd):
    r = RECT()
    if _u32.GetClientRect(wintypes.HWND(hwnd), ctypes.byref(r)):
        return r.left, r.top, r.right - r.left, r.bottom - r.top
    return None


def find_render_child(hwnd):
    """Find the Chrome_RenderWidgetHostHWND child window whose origin equals the web viewport."""
    matches = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(child, _):
        buf = ctypes.create_unicode_buffer(256)
        _u32.GetClassNameW(child, buf, 256)
        if buf.value == "Chrome_RenderWidgetHostHWND":
            rect = window_rect(child)
            area = (rect[2] * rect[3]) if rect else 0
            matches.append((bool(_u32.IsWindowVisible(child)), area, child))
        return True

    _u32.EnumChildWindows(wintypes.HWND(hwnd), cb, 0)
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][2]


def content_origin(hwnd, inner_width_px=None, inner_height_px=None):
    """True web content viewport origin in screen pixels (excludes Chrome tab/omnibox chrome)."""
    render_hwnd = find_render_child(hwnd)
    if render_hwnd:
        return client_origin(render_hwnd)
    cox, coy = client_origin(hwnd)
    crect = client_rect(hwnd)
    if crect and inner_height_px:
        cw, ch = crect[2], crect[3]
        dx = max(0, (cw - int(inner_width_px)) // 2) if inner_width_px else 0
        dy = max(0, ch - int(inner_height_px))
        return cox + dx, coy + dy
    return cox, coy


def focus(hwnd):
    _u32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
    return bool(_u32.SetForegroundWindow(wintypes.HWND(hwnd)))


def find_window(title_part, timeout=15.0):
    """Top-level visible window whose title contains title_part (case-insensitive)."""
    import time
    deadline = time.time() + timeout
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not _u32.IsWindowVisible(hwnd):
            return True
        n = _u32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            _u32.GetWindowTextW(hwnd, buf, n + 1)
            if title_part.lower() in buf.value.lower():
                found.append((hwnd, buf.value))
                return False
        return True

    while time.time() < deadline and not found:
        _u32.EnumWindows(cb, 0)
        if not found:
            time.sleep(0.25)
    return found[0] if found else (None, None)


def windows_by_class(class_name):
    """Set of visible top-level HWNDs matching class_name."""
    out = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if _u32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            _u32.GetClassNameW(hwnd, buf, 256)
            if buf.value == class_name:
                out.add(hwnd)
        return True

    _u32.EnumWindows(cb, 0)
    return out


class KillSwitch:
    """Abort as soon as a human moves the physical cursor away from the command."""

    def __init__(self, enabled=True, tolerance=5):
        self.last = None
        self.enabled = enabled
        self.armed = False
        self.tolerance = tolerance

    def pre_move(self):
        if not self.enabled or not self.armed:
            return
        handle, pos = cursor_state()
        if str(handle).startswith("error:"):
            raise RuntimeError(f"GetCursorInfo failed ({handle}) — non-input desktop?")
        if self.last and (abs(pos[0] - self.last[0]) > self.tolerance
                          or abs(pos[1] - self.last[1]) > self.tolerance):
            raise SystemExit(f"HUMAN TAKEOVER: cursor at {pos}, last commanded {self.last}")

    def moved(self, xy):
        self.armed = True
        self.last = xy


def close_window(hwnd):
    """Ask the window to close (never force-kill a shared process)."""
    _u32.PostMessageW(wintypes.HWND(hwnd), 0x0010, 0, 0)  # WM_CLOSE


def find_window_by_pid(pid, timeout=15.0):
    """Top-level visible window owned by pid - never matches another app's window."""
    import time
    deadline = time.time() + timeout

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not _u32.IsWindowVisible(hwnd):
            return True
        owner = wintypes.DWORD()
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and _u32.GetWindowTextLengthW(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            _u32.GetWindowTextW(hwnd, buf, 256)
            found.append((hwnd, buf.value))
            return False
        return True

    while time.time() < deadline:
        found = []
        _u32.EnumWindows(cb, 0)
        if found:
            return found[0]
        time.sleep(0.3)
    return None, None


def screenshot(box=None, path=None):
    from PIL import ImageGrab
    img = ImageGrab.grab(bbox=box, all_screens=True)
    if path:
        img.save(path)
    return img


def capture_window_region(hwnd, box=None, path=None):
    """Capture a screen bbox via ImageGrab, falling back to PrintWindow if screen DC is blocked."""
    from PIL import Image
    try:
        return screenshot(box=box, path=path), "image_grab"
    except OSError:
        wrect = window_rect(hwnd)
        if not wrect:
            raise
        wx, wy, ww, wh = wrect
        hdc = _u32.GetWindowDC(wintypes.HWND(hwnd))
        mem = _gdi.CreateCompatibleDC(hdc)
        bmp = _gdi.CreateCompatibleBitmap(hdc, max(1, ww), max(1, wh))
        old = _gdi.SelectObject(mem, bmp)
        try:
            ok = _u32.PrintWindow(wintypes.HWND(hwnd), mem, 2)
            if not ok:
                raise OSError(f"PrintWindow failed: {ctypes.get_last_error()}")
            bmi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), ww, -wh, 1, 32, 0, 0, 0, 0, 0, 0)
            buf = ctypes.create_string_buffer(ww * wh * 4)
            _gdi.GetDIBits(mem, bmp, 0, wh, buf, ctypes.byref(bmi), 0)
            img = Image.frombuffer("RGBA", (ww, wh), buf, "raw", "BGRA", 0, 1).convert("RGB")
        finally:
            _gdi.SelectObject(mem, old)
            _gdi.DeleteObject(bmp)
            _gdi.DeleteDC(mem)
            _u32.ReleaseDC(wintypes.HWND(hwnd), hdc)
        if box:
            l, t, r, b = box
            img = img.crop((max(0, l - wx), max(0, t - wy), min(ww, r - wx), min(wh, b - wy)))
        if path:
            img.save(path)
        return img, "print_window"

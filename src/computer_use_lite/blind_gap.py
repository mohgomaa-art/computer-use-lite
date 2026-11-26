# SPDX-License-Identifier: Apache-2.0
"""M2 - Blind-region detection and crop export.

H1b (sync 14.9 s / pipelined 34% agreement) and H2 (blocked in exebox / rejected prior pass)
did not clear the probing gates, so no cursor-probe code ships here. What ships is the
selective visual fallback hook: find the regions that DOM/UIA cannot describe, and
export a small cropped PNG an agent can inspect on demand.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path

from .resolver import INTERACTIVE

MIN_CANVAS_FRACTION = 0.25      # a canvas this big dominates the surface
SMALL_CANVAS_FRACTION = 0.05    # smaller interactive canvas (charts, editors) when sparse
SMALL_CANVAS_MIN_W = 120
SMALL_CANVAS_MIN_H = 80
NEARBY_PAD = 32
MAX_NEARBY_INTERACTIVE = 2
MIN_INTERACTIVE = 6             # fewer interactive controls than this on a big window
MIN_WINDOW_AREA = 200_000


def _area(box):
    return max(box[2], 0) * max(box[3], 0)


def _overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


_DWMWA_CLOAKED = 14
_GW_HWNDPREV = 3


def _virtual_screen():
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    return u32.GetSystemMetrics(76), u32.GetSystemMetrics(77), u32.GetSystemMetrics(78), u32.GetSystemMetrics(79)


def _is_window_cloaked(hwnd):
    """Return True if DWM reports the window is currently cloaked (hidden workspace / virtual desktop)."""
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        dwmapi.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
        cloaked = wintypes.DWORD(0)
        hr = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(_DWMWA_CLOAKED),
            ctypes.byref(cloaked),
            wintypes.DWORD(ctypes.sizeof(cloaked)),
        )
        return hr == 0 and cloaked.value != 0
    except Exception:
        return False


def _is_window_occluded_or_bg(hwnd, bbox):
    """Return True if target HWND is non-foreground, minimized, or overlapped by a higher Z-order window."""
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    u32.IsWindow.argtypes = [wintypes.HWND]
    u32.IsWindow.restype = wintypes.BOOL
    u32.IsIconic.argtypes = [wintypes.HWND]
    u32.IsIconic.restype = wintypes.BOOL
    u32.IsWindowVisible.argtypes = [wintypes.HWND]
    u32.IsWindowVisible.restype = wintypes.BOOL
    u32.GetForegroundWindow.argtypes = []
    u32.GetForegroundWindow.restype = wintypes.HWND
    u32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    u32.GetWindow.restype = wintypes.HWND
    u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u32.GetWindowRect.restype = wintypes.BOOL

    target = wintypes.HWND(hwnd)
    if u32.IsIconic(target):
        return True
    fg = int(u32.GetForegroundWindow() or 0)
    if fg != int(hwnd):
        return True
    if not u32.IsWindow(target):
        return True

    left, top, right, bottom = bbox
    cur = u32.GetWindow(target, _GW_HWNDPREV)
    seen = set()
    steps = 0
    rect = wintypes.RECT()
    while cur and int(cur) not in seen and steps < 256:
        cur_int = int(cur)
        seen.add(cur_int)
        if u32.IsWindowVisible(cur) and not u32.IsIconic(cur) and not _is_window_cloaked(cur_int):
            if u32.GetWindowRect(cur, ctypes.byref(rect)):
                if (
                    rect.right > rect.left
                    and rect.bottom > rect.top
                    and rect.left < right
                    and rect.right > left
                    and rect.top < bottom
                    and rect.bottom > top
                ):
                    return True
        cur = u32.GetWindow(cur, _GW_HWNDPREV)
        steps += 1
    return False


def detect(session, elements, viewport):
    """Return blind regions as [{kind, box, reason, area_fraction}]."""
    regions = []
    vw, vh = viewport[2], viewport[3]
    v_area = max(vw * vh, 1)
    interactive = [e for e in elements if e.get("role") in INTERACTIVE]

    if hasattr(session, "canvas_rects"):
        for box in session.canvas_rects():
            frac = _area(box) / v_area
            if frac >= MIN_CANVAS_FRACTION:
                regions.append({
                    "kind": "opaque_canvas",
                    "box": [round(v, 1) for v in box],
                    "area_fraction": round(frac, 3),
                    "reason": "canvas covers %.0f%% of the viewport; DOM/AX sees one node" % (frac * 100),
                })
            elif frac >= SMALL_CANVAS_FRACTION and box[2] >= SMALL_CANVAS_MIN_W and box[3] >= SMALL_CANVAS_MIN_H:
                expanded = [box[0] - NEARBY_PAD, box[1] - NEARBY_PAD,
                            box[2] + 2 * NEARBY_PAD, box[3] + 2 * NEARBY_PAD]
                nearby = sum(1 for e in interactive if _overlaps(e["box"], expanded))
                if nearby <= MAX_NEARBY_INTERACTIVE:
                    regions.append({
                        "kind": "small_opaque_canvas",
                        "box": [round(v, 1) for v in box],
                        "area_fraction": round(frac, 3),
                        "reason": "canvas covers %.1f%% of the viewport with <=%d interactive DOM nodes nearby"
                                  % (frac * 100, nearby),
                    })

    if not hasattr(session, "canvas_rects") and len(interactive) < MIN_INTERACTIVE \
            and v_area >= MIN_WINDOW_AREA:
        regions.append({
            "kind": "low_uia",
            "box": list(viewport),
            "area_fraction": 1.0,
            "reason": "window exposes only %d interactive UIA controls in %d x %d px"
                      % (len(interactive), vw, vh),
        })
    return regions


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def _capture_hwnd_printwindow(hwnd, crop_bbox):
    """Fallback desktop capture via PrintWindow when ImageGrab is blocked (e.g. non-interactive desktop)."""
    from PIL import Image

    u32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    rect = wintypes.RECT()
    if not u32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        raise OSError(f"GetWindowRect failed for hwnd={hwnd}")
    ww = max(1, rect.right - rect.left)
    wh = max(1, rect.bottom - rect.top)
    hdc = u32.GetWindowDC(wintypes.HWND(hwnd))
    if not hdc:
        raise OSError(f"GetWindowDC failed for hwnd={hwnd}")
    memdc = gdi32.CreateCompatibleDC(hdc)
    hbmp = gdi32.CreateCompatibleBitmap(hdc, ww, wh)
    old = gdi32.SelectObject(memdc, hbmp)
    try:
        u32.PrintWindow(wintypes.HWND(hwnd), memdc, 2)
        bmi = _BITMAPINFOHEADER(ctypes.sizeof(_BITMAPINFOHEADER), ww, -wh, 1, 32, 0, 0, 0, 0, 0, 0)
        raw = ctypes.create_string_buffer(ww * wh * 4)
        gdi32.GetDIBits(memdc, hbmp, 0, wh, raw, ctypes.byref(bmi), 0)
        img = Image.frombuffer("RGBA", (ww, wh), raw, "raw", "BGRA", 0, 1).convert("RGB")
        cl, ct, cr, cb = crop_bbox
        rel_l = max(0, min(ww - 1, cl - rect.left))
        rel_t = max(0, min(wh - 1, ct - rect.top))
        rel_r = max(rel_l + 1, min(ww, cr - rect.left))
        rel_b = max(rel_t + 1, min(wh, cb - rect.top))
        if (rel_l, rel_t, rel_r, rel_b) != (0, 0, ww, wh):
            return img.crop((rel_l, rel_t, rel_r, rel_b))
        return img
    finally:
        gdi32.SelectObject(memdc, old)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(memdc)
        u32.ReleaseDC(wintypes.HWND(hwnd), hdc)


def capture_desktop_region(box, hwnd=None):
    """Capture a virtual-screen desktop box using PrintWindow first for occluded/background/cloaked HWNDs."""
    from PIL import ImageGrab

    x, y, w, h = [int(v) for v in box]
    w, h = max(w, 1), max(h, 1)
    vx, vy, vw, vh = _virtual_screen()
    left = max(x, vx)
    top = max(y, vy)
    right = min(x + w, vx + vw)
    bottom = min(y + h, vy + vh)
    if right <= left:
        right = left + 1
    if bottom <= top:
        bottom = top + 1
    bbox = (left, top, right, bottom)
    if hwnd is not None:
        if _is_window_cloaked(hwnd) or _is_window_occluded_or_bg(hwnd, bbox):
            return _capture_hwnd_printwindow(hwnd, bbox), "printwindow"
    try:
        return ImageGrab.grab(bbox=bbox, all_screens=True), "imagegrab"
    except Exception:
        if hwnd is not None:
            return _capture_hwnd_printwindow(hwnd, bbox), "printwindow"
        raise


def export(session, region, path):
    """Crop the region out of a fresh screenshot and return the file path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x, y, w, h = [int(v) for v in region["box"]]
    w, h = max(w, 1), max(h, 1)
    if hasattr(session, "page"):
        vx, vy, vw, vh = [int(v) for v in session.bounds()]
        x = max(x, vx)
        y = max(y, vy)
        w = min(w, max(1, vx + vw - x))
        h = min(h, max(1, vy + vh - y))
        session.page.screenshot(path=str(path), clip={"x": x, "y": y, "width": w, "height": h})
    else:
        img, _method = capture_desktop_region([x, y, w, h], hwnd=getattr(session, "hwnd", None))
        img.save(path)
    return str(path)

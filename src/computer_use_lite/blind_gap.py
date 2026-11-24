# SPDX-License-Identifier: Apache-2.0
"""M2 - Blind-region detection and crop export.

H1b (sync 14.9 s / pipelined 34% agreement) and H2 (blocked in exebox / rejected prior pass)
did not clear the probing gates, so no cursor-probe code ships here. What ships is the
selective visual fallback hook: find the regions that DOM/UIA cannot describe, and
export a small cropped PNG an agent can inspect on demand.
"""
import ctypes
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


def _virtual_screen():
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    return u32.GetSystemMetrics(76), u32.GetSystemMetrics(77), u32.GetSystemMetrics(78), u32.GetSystemMetrics(79)


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
        from PIL import ImageGrab
        vx, vy, vw, vh = _virtual_screen()
        left = max(x, vx)
        top = max(y, vy)
        right = min(x + w, vx + vw)
        bottom = min(y + h, vy + vh)
        if right <= left:
            right = left + 1
        if bottom <= top:
            bottom = top + 1
        ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True).save(path)
    return str(path)

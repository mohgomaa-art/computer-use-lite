#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""H2 Gate 0 - per-toolkit cursor sensitivity and settle-delay calibration.

Three live desktop targets on this machine:
  win32     : Notepad (real Win32 controls, UIA-rich; control group)
  toolkit   : LibreOffice Writer (VCL custom toolkit, UIA bridge; control group) - skipped if absent
  canvas    : a real Chromium window rendering a <canvas> app, probed through Win32 only
              (no CDP for probing: real WM_SETCURSOR, real UIA blindness)

Re-validated fixes (A2, A3, Phase C):
  - True content origin via Chrome_RenderWidgetHostHWND / innerHeight offset (fixes ~87 px shift).
  - Full settle sweep [2, 5, 10, 15, 30, 50, 80, 120] ms compared against an independent 120 ms pass.
  - Both ordered and randomized point orders measured to detect inter-point lag leakage.
  - Dead points derived algorithmically from fixture geometry and verified to miss every control.
  - Notepad found via PID/new-HWND diff using an isolated scratch file (never touches existing tabs).

Writes results/experiments/h2_gate0.json, h2_gate0_probes.json, h2_gate0_overlay.png.
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import win32_probe as w  # noqa: E402  (import sets DPI awareness first)

DELAYS = [2, 5, 10, 15, 30, 50, 80, 120]
REF_DELAY = 120
UIA_TYPES = {"ButtonControl", "MenuItemControl", "TabItemControl", "SplitButtonControl",
             "HyperlinkControl", "EditControl"}


def uia_scan(hwnd, cap=800):
    """Breadth-first UIA walk scoped to this window only, no CacheRequest."""
    import uiautomation as auto
    auto.SetGlobalSearchTimeout(2.0)
    root = auto.ControlFromHandle(hwnd)
    out, queue = [], [(root, 0)]
    while queue and len(out) < cap:
        ctrl, depth = queue.pop(0)
        try:
            ctype = ctrl.ControlTypeName
            r = ctrl.BoundingRectangle
            rect = (int(r.left), int(r.top), int(r.right) - int(r.left),
                    int(r.bottom) - int(r.top))
        except Exception:
            continue
        try:
            out.append({"type": ctype, "name": (ctrl.Name or "")[:60], "rect": rect,
                        "enabled": bool(ctrl.IsEnabled)})
        except Exception:
            out.append({"type": ctype, "name": "", "rect": rect, "enabled": True})
        if depth < 12:
            try:
                queue.extend((c, depth + 1) for c in ctrl.GetChildren())
            except Exception:
                pass
    return out


def contains(rect, x, y, pad=0):
    l, t, wd, ht = rect
    return l - pad <= x <= l + wd + pad and t - pad <= y <= t + ht + pad


def uia_hit(nodes, x, y):
    for n in nodes:
        if n["type"] in UIA_TYPES and contains(n["rect"], x, y) and n["rect"][2] > 1:
            return n
    return None


def dead_points(rect, avoid, count=10, pad=12):
    """Deterministic scan of an area that verifies every point misses every avoid rect."""
    l, t, wd, ht = rect
    pts = []
    step_x, step_y = 67, 53
    for y in range(t + 20, t + ht - 15, step_y):
        for x in range(l + 20, l + wd - 15, step_x):
            if any(contains(a, x, y, pad=pad) for a in avoid):
                continue
            pts.append((x, y))
            if len(pts) >= count:
                return pts
    return pts


KillSwitch = w.KillSwitch


def _probe_sequence(name, points, delay_ms, order_name, kill):
    rows = []
    for pt in points:
        kill.pre_move()
        t0 = time.perf_counter_ns()
        w.move(pt["x"], pt["y"])
        kill.moved((pt["x"], pt["y"]))
        time.sleep(delay_ms / 1000)
        handle, pos = w.cursor_state()
        if str(handle).startswith("error:"):
            raise RuntimeError(f"GetCursorInfo failed ({handle}) — live cursor probing requires interactive desktop")
        rows.append({
            "target": name, "x": pt["x"], "y": pt["y"], "kind": pt["kind"],
            "label": pt["label"], "delay_ms": delay_ms, "order": order_name,
            "cursor_handle": handle, "cursor_class": w.cursor_class(handle),
            "settle_ms": delay_ms, "elapsed_us": (time.perf_counter_ns() - t0) // 1000,
            "cursor_at": pos,
        })
    return rows


def probe_target(name, hwnd, points, delay_log, kill):
    """Run independent 120 ms reference pass, plus ordered and randomized sweeps across delay_log."""
    rng = random.Random(42)
    ref_pts = list(points)
    rng.shuffle(ref_pts)
    ref_rows = _probe_sequence(name, ref_pts, REF_DELAY, "reference", kill)

    all_rows = list(ref_rows)
    for d in delay_log:
        all_rows.extend(_probe_sequence(name, points, d, "ordered", kill))
        shuf = list(points)
        rng.shuffle(shuf)
        all_rows.extend(_probe_sequence(name, shuf, d, "randomized", kill))
    return all_rows


def _summarize_rows(rows):
    click = [r for r in rows if r["kind"] == "clickable"]
    dead = [r for r in rows if r["kind"] == "dead"]
    hand_click = sum(r["cursor_class"] == "HAND" or r["cursor_class"].startswith("CUSTOM") for r in click)
    custom_click = sum(r["cursor_class"].startswith("CUSTOM") for r in click)
    hand_dead = sum(r["cursor_class"] == "HAND" or r["cursor_class"].startswith("CUSTOM") for r in dead)
    ibeam_dead = sum(r["cursor_class"] == "IBEAM" for r in dead)
    return {
        "p_hand_custom_given_clickable": round(hand_click / max(len(click), 1), 3),
        "p_custom_given_clickable": round(custom_click / max(len(click), 1), 3),
        "p_hand_custom_given_dead": round(hand_dead / max(len(dead), 1), 3),
        "ibeam_on_dead": ibeam_dead,
        "clickable_n": len(click), "dead_n": len(dead),
        "classes_clickable": {c: sum(r["cursor_class"] == c for r in click)
                              for c in sorted({r["cursor_class"] for r in click})},
        "classes_dead": {c: sum(r["cursor_class"] == c for r in dead)
                         for c in sorted({r["cursor_class"] for r in dead})},
    }


def evaluate(results, uia_nodes):
    ref_rows = [r for r in results if r["order"] == "reference"]
    ref_map = {(r["x"], r["y"]): r["cursor_class"] for r in ref_rows}
    ref_summary = _summarize_rows(ref_rows)

    by_delay = {}
    settle_ord, settle_rnd, settle_both = None, None, None
    for d in sorted({r["delay_ms"] for r in results if r["order"] != "reference"}):
        ord_rows = [r for r in results if r["delay_ms"] == d and r["order"] == "ordered"]
        rnd_rows = [r for r in results if r["delay_ms"] == d and r["order"] == "randomized"]
        agree_ord = sum(ref_map.get((r["x"], r["y"])) == r["cursor_class"] for r in ord_rows) / max(len(ord_rows), 1)
        agree_rnd = sum(ref_map.get((r["x"], r["y"])) == r["cursor_class"] for r in rnd_rows) / max(len(rnd_rows), 1)
        entry = _summarize_rows(rnd_rows or ord_rows)
        entry["agreement_ordered_vs_120ms"] = round(agree_ord, 3)
        entry["agreement_randomized_vs_120ms"] = round(agree_rnd, 3)
        by_delay[d] = entry
        if settle_ord is None and agree_ord >= 0.95:
            settle_ord = d
        if settle_rnd is None and agree_rnd >= 0.95:
            settle_rnd = d
        if settle_both is None and agree_ord >= 0.95 and agree_rnd >= 0.95:
            settle_both = d

    uia_recall = None
    if uia_nodes is not None:
        click = [r for r in ref_rows if r["kind"] == "clickable"]
        uia_recall = round(sum(1 for r in click if uia_hit(uia_nodes, r["x"], r["y"]))
                           / max(len(click), 1), 3)
    return {
        "by_delay": by_delay,
        "settle_ms": settle_both,
        "settle_ordered_ms": settle_ord,
        "settle_randomized_ms": settle_rnd,
        "reference_delay_ms": REF_DELAY,
        "uia_recall": uia_recall,
        "p_hand_custom_given_clickable": ref_summary["p_hand_custom_given_clickable"],
        "p_hand_custom_given_dead": ref_summary["p_hand_custom_given_dead"],
    }


def run_canvas_target(out, kill, delay_log):
    from playwright.sync_api import sync_playwright
    fixture = Path(__file__).resolve().parent / "fixtures" / "h2_probe_fixture.html"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-position=20,20",
                                                          "--window-size=1300,820"])
        page = browser.new_page(viewport={"width": 1200, "height": 700})
        page.goto(fixture.as_uri())
        page.wait_for_timeout(800)
        layout = page.evaluate(
            "() => ({c: document.getElementById('c').getBoundingClientRect(),"
            " b: window.__layout.buttons, t: window.__layout.texts,"
            " win: {iw: window.innerWidth, ih: window.innerHeight, dpr: window.devicePixelRatio}})")
        time.sleep(1.0)
        hwnd, title = w.find_window("H2 canvas probe fixture", timeout=10)
        if not hwnd:
            browser.close()
            raise SystemExit("canvas target: chromium window not found")
        w.focus(hwnd)
        time.sleep(0.6)

        # A2 fix: true content origin (Chrome_RenderWidgetHostHWND or innerHeight delta)
        inner_w = int(round(layout["win"]["iw"] * layout["win"]["dpr"]))
        inner_h = int(round(layout["win"]["ih"] * layout["win"]["dpr"]))
        cox, coy = w.content_origin(hwnd, inner_width_px=inner_w, inner_height_px=inner_h)
        cx, cy = int(layout["c"]["left"]), int(layout["c"]["top"])
        cw, ch = int(layout["c"]["width"]), int(layout["c"]["height"])
        origin_x, origin_y = cox + cx, coy + cy

        points = []
        avoid_local = []
        for b in layout["b"]:
            avoid_local.append((b["x"], b["y"], b["w"], b["h"]))
            points.append({"x": origin_x + int(b["x"] + b["w"] / 2),
                           "y": origin_y + int(b["y"] + b["h"] / 2),
                           "kind": "clickable", "label": b["label"]})
        for t in layout["t"]:
            avoid_local.append((t["x"], t["y"], t["w"], t["h"]))

        # Phase C: derive dead points from fixture layout and assert they miss every control
        dead_local = dead_points((0, 0, cw, ch), avoid_local, count=10, pad=16)
        assert len(dead_local) == 10, f"expected 10 dead points, got {len(dead_local)}"
        for dx, dy in dead_local:
            assert not any(contains(a, dx, dy, pad=12) for a in avoid_local), \
                f"dead point {(dx, dy)} overlaps control"
        for i, (x, y) in enumerate(dead_local):
            points.append({"x": origin_x + x, "y": origin_y + y,
                           "kind": "dead", "label": f"dead_{i}"})

        shot_path = out / "_h2_canvas_pre.png"
        box = (origin_x - 10, origin_y - 10, origin_x + cw + 10, origin_y + ch + 10)
        img, cap_method = w.capture_window_region(hwnd, box=box, path=str(shot_path))

        # Visual alignment proof overlay
        ov = img.copy()
        draw = ImageDraw.Draw(ov)
        ox, oy = origin_x - 10, origin_y - 10
        for b in layout["b"]:
            bx, by = origin_x + b["x"] - ox, origin_y + b["y"] - oy
            draw.rectangle([bx, by, bx + b["w"], by + b["h"]], outline=(40, 220, 80), width=2)
        for dx, dy in dead_local:
            px, py = origin_x + dx - ox, origin_y + dy - oy
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 210, 40))
        ov.save(out / "h2_gate0_overlay.png")

        uia = uia_scan(hwnd)
        try:
            res = probe_target("canvas", hwnd, points, delay_log, kill)
            metrics = evaluate(res, uia)
        finally:
            browser.close()
        metrics["uia_nodes"] = len(uia)
        metrics["uia_controls"] = sum(1 for n in uia if n["type"] in UIA_TYPES)
        metrics["gt_source"] = "fixture drawing code (independent of UIA)"
        metrics["control_group"] = False
        metrics["content_origin"] = [origin_x, origin_y]
        metrics["top_client_origin"] = list(w.client_origin(hwnd)) if False else None
        metrics["capture_method"] = cap_method
        metrics["window"] = title
        return metrics, res


def run_native_target(name, hwnd, out, kill, delay_log):
    w.focus(hwnd)
    time.sleep(0.8)
    rect = w.window_rect(hwnd)
    cox, coy = w.client_origin(hwnd)
    shot = out / f"_h2_{name}_pre.png"
    w.capture_window_region(hwnd, box=rect, path=str(shot))
    uia = uia_scan(hwnd)
    ctrl = [n for n in uia if n["type"] in UIA_TYPES and n["rect"][2] > 8 and n["rect"][3] > 8]
    ctrl.sort(key=lambda n: n["rect"][2] * n["rect"][3])
    clickable, seen = [], set()
    for n in ctrl:
        l, t, wd, ht = n["rect"]
        px, py = l + wd // 2, t + ht // 2
        if (px, py) in seen:
            continue
        seen.add((px, py))
        clickable.append({"x": px, "y": py, "kind": "clickable",
                          "label": f"{n['type'].replace('Control', '')}:{n['name']}"})
        if len(clickable) >= 15:
            break
    dead = dead_points(rect, [n["rect"] for n in uia], 10)
    points = clickable + [{"x": x, "y": y, "kind": "dead", "label": f"dead_{i}"}
                          for i, (x, y) in enumerate(dead)]
    res = probe_target(name, hwnd, points, delay_log, kill)
    metrics = evaluate(res, uia)
    metrics["uia_nodes"] = len(uia)
    metrics["uia_controls"] = len(ctrl)
    metrics["control_group"] = True
    metrics["gt_source"] = "UIA control centres (control group: circular, not a blindness test)"
    metrics["content_origin"] = [cox, coy]
    metrics["window"] = name
    return metrics, res


def launch_notepad():
    """Launch an isolated scratch Notepad window without touching user's existing Notepad tabs."""
    tmp = Path(tempfile.gettempdir()) / f"cul_gate0_{int(time.time())}.txt"
    tmp.write_text("", encoding="utf-8")
    before = w.windows_by_class("Notepad")
    proc = subprocess.Popen(["notepad.exe", str(tmp)])
    hwnd, _ = w.find_window_by_pid(proc.pid, timeout=4.0)
    if not hwnd:
        # Win11 Store Notepad spawns a child/broker process with a new HWND
        deadline = time.time() + 10.0
        while time.time() < deadline:
            diff = w.windows_by_class("Notepad") - before
            if diff:
                hwnd = next(iter(diff))
                break
            time.sleep(0.3)
    return hwnd, proc, tmp


def launch_libreoffice():
    exe = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
    if not exe.exists():
        return None, None
    proc = subprocess.Popen([str(exe), "--writer", "--norestore"])
    time.sleep(9.0)
    hwnd, _ = w.find_window_by_pid(proc.pid, timeout=15)
    return hwnd, proc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="canvas,notepad,libreoffice")
    ap.add_argument("--no-kill-switch", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "results" / "experiments"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    kill = KillSwitch(enabled=not args.no_kill_switch)
    orig_h, orig = w.cursor_state()
    if str(orig_h).startswith("error:"):
        raise SystemExit(
            f"ERROR_ACCESS_DENIED / GetCursorInfo failed ({orig_h}): "
            "H2 Gate 0 requires an active interactive desktop (Default), not an isolated exebox desktop."
        )

    print("H2 Gate 0 - the physical mouse will be moved (never clicked).")
    print("Keep your hands off the mouse: any human movement >5 px aborts immediately.")
    for i in (3, 2, 1):
        print(f"  starting in {i}...", flush=True)
        time.sleep(1.0)

    report = {"delays_ms": DELAYS, "reference_delay_ms": REF_DELAY,
              "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "original_cursor": list(orig), "targets": {}}
    all_rows = []
    try:
        for name in [t.strip() for t in args.targets.split(",") if t.strip()]:
            try:
                if name == "canvas":
                    metrics, rows = run_canvas_target(out, kill, DELAYS)
                elif name == "notepad":
                    hwnd, proc, tmp = launch_notepad()
                    try:
                        if not hwnd:
                            report["targets"][name] = {"error": "window not found"}
                            continue
                        metrics, rows = run_native_target("notepad", hwnd, out, kill, DELAYS)
                        w.close_window(hwnd)
                        time.sleep(0.5)
                        proc.poll()
                    finally:
                        tmp.unlink(missing_ok=True)
                elif name == "libreoffice":
                    hwnd, proc = launch_libreoffice()
                    if not hwnd:
                        report["targets"][name] = {"error": "LibreOffice not installed"}
                        continue
                    metrics, rows = run_native_target("libreoffice", hwnd, out, kill, DELAYS)
                    metrics["gt_note"] = "untitled scratch document, closed via WM_CLOSE"
                    w.close_window(hwnd)
                    time.sleep(2.0)
                else:
                    continue
            except SystemExit:
                raise
            except Exception as exc:
                import traceback
                traceback.print_exc()
                report["targets"][name] = {"error": f"{type(exc).__name__}: {exc}",
                                           "traceback": traceback.format_exc()[-1500:]}
                continue
            report["targets"][name] = metrics
            all_rows.extend(rows)
            print(f"[{name}] uia_recall={metrics['uia_recall']} "
                  f"P(HAND/CUSTOM|clickable)={metrics['p_hand_custom_given_clickable']} "
                  f"P(HAND/CUSTOM|dead)={metrics['p_hand_custom_given_dead']} "
                  f"settle={metrics['settle_ms']} ms (ord={metrics['settle_ordered_ms']}, rnd={metrics['settle_randomized_ms']})",
                  flush=True)
    finally:
        try:
            w.move(*orig)
            print(f"cursor restored to {orig}")
        except OSError:
            pass

    gate = {}
    for name, m in report["targets"].items():
        if "error" in m:
            continue
        blind = (not m.get("control_group")) and m["uia_recall"] is not None and m["uia_recall"] < 0.5
        ok = (blind and m["p_hand_custom_given_clickable"] >= 0.5
              and m["p_hand_custom_given_dead"] <= 0.2 and m["settle_ms"] is not None)
        gate[name] = {"blind": blind,
                      "control_group": bool(m.get("control_group")),
                      "hand_rate": m["p_hand_custom_given_clickable"],
                      "dead_fp": m["p_hand_custom_given_dead"],
                      "settle_ms": m["settle_ms"],
                      "passes_gate_2a": ok}
    report["gate2a"] = gate
    report["gate2a_unlock"] = any(v["passes_gate_2a"] for v in gate.values())
    (out / "h2_gate0.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / "h2_gate0_probes.json").write_text(json.dumps(all_rows, indent=2), encoding="utf-8")
    print(json.dumps({"gate2a": gate, "unlock_2b": report["gate2a_unlock"]}, indent=2))


if __name__ == "__main__":
    main()

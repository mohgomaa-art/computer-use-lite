#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""H2 (2B) - progressive desktop grid scan on the UIA-blind canvas window.

Runs only when Gate 2A passes. Uses the calibrated settle delay from results/experiments/h2_gate0.json,
expands 100 -> 250 -> 500 points (stopping after a pass exceeds 5.0 s), and also runs
a randomized point-order pass to verify zero inter-point lag leakage.

All tables, conclusions, and verdicts in results/experiments/h2_report.md are derived strictly
from measured JSON values in h2_gate0.json and the live grid run.
"""
import argparse
import json
import random
import sys
import time
import math
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import win32_probe as w  # noqa: E402  (sets DPI awareness on import)
from h1_canvas_probe import cluster, grid_axes  # noqa: E402

STEPS = [100, 250, 500]
BUDGET_MS = 5000


def grid_points(rect, n):
    step = max(4, int(round(math.sqrt(rect["w"] * rect["h"] / n))))
    xs, ys = grid_axes(rect, step)
    return [(int(x), int(y)) for y in ys for x in xs], step


def inside(b, x, y):
    return b["x"] <= x < b["x"] + b["w"] and b["y"] <= y < b["y"] + b["h"]


def score(hits, ibeam, buttons, texts, step):
    """FP = a cluster of pointer hits that lands on no clickable control at all."""
    tp = [b for b in buttons if any(inside(b, h["x"], h["y"]) for h in hits)]
    stray = [(h["x"], h["y"], h["cursor_class"]) for h in hits
             if not any(inside(b, h["x"], h["y"]) for b in buttons)]
    fp = cluster(stray, 1.5 * step)
    fn = [b for b in buttons if b not in tp]
    text_hit = [t for t in texts if any(inside(t, h["x"], h["y"]) for h in ibeam)]
    recall = len(tp) / max(len(buttons), 1)
    precision = len(tp) / max(len(tp) + len(fp), 1)
    return {"tp": len(tp), "fp_clusters": len(fp), "fn": len(fn),
            "tp_points": len(hits) - len(stray), "stray_points": len(stray),
            "controls_total": len(buttons), "text_fields_total": len(texts),
            "text_fields_hit_by_ibeam": len(text_hit),
            "blind_recall": round(recall, 3), "precision": round(precision, 3)}


def _run_grid_pass(pts, settle_ms, kill):
    hits, started = [], time.perf_counter()
    for (x, y) in pts:
        kill.pre_move()
        t_pt = time.perf_counter_ns()
        w.move(x, y)
        kill.moved((x, y))
        time.sleep(settle_ms / 1000)
        handle, _ = w.cursor_state()
        if str(handle).startswith("error:"):
            raise RuntimeError(f"GetCursorInfo failed ({handle}) — live grid requires interactive desktop")
        cls = w.cursor_class(handle)
        elapsed_us = (time.perf_counter_ns() - t_pt) // 1000
        hits.append({"x": x, "y": y, "cursor_class": cls, "elapsed_us": elapsed_us})
    dur = round((time.perf_counter() - started) * 1000, 1)
    return hits, dur


def _gate0_rows_from_json(gate0):
    rows = []
    for name, m in gate0.get("targets", {}).items():
        if "error" in m:
            rows.append(f"| {name} | error: {m['error']} | - | - | - | - |")
            continue
        is_ctrl = bool(m.get("control_group"))
        recall_str = f"{m['uia_recall'] * 100:.1f}% ({'control group' if is_ctrl else 'blind' if m['uia_recall'] < 0.5 else 'exposed'})"
        settle_str = f"{m['settle_ms']} ms" if m.get("settle_ms") is not None else "n/a"
        rows.append(
            f"| {name} | {recall_str} | {m.get('uia_nodes', '-')} "
            f"| {m['p_hand_custom_given_clickable'] * 100:.1f}% "
            f"| {m['p_hand_custom_given_dead'] * 100:.1f}% | {settle_str} |"
        )
    return "\n".join(rows)


def _gate0_narrative(gate0):
    canvas_gate = gate0.get("gate2a", {}).get("canvas", {})
    unlocked = bool(gate0.get("gate2a_unlock"))
    ctrl_names = [n for n, m in gate0.get("targets", {}).items() if m.get("control_group")]
    ctrl_note = (
        f"Control-group targets ({', '.join(ctrl_names)}) derive ground truth from UIA itself "
        "(circular, not a blindness test) and measure whether native controls change cursor shape."
        if ctrl_names else ""
    )
    if unlocked:
        return (
            f"Gate 2A: canvas UIA recall={gate0['targets']['canvas']['uia_recall'] * 100:.1f}%, "
            f"P(HAND/CUSTOM|clickable)={canvas_gate.get('hand_rate', 0) * 100:.1f}%, "
            f"P(HAND/CUSTOM|dead)={canvas_gate.get('dead_fp', 0) * 100:.1f}% -> **unlocked 2B**. "
            + ctrl_note
        )
    return f"Gate 2A: **did not unlock 2B** (canvas gate={canvas_gate}). " + ctrl_note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", choices=["raster", "randomized", "both"], default="both")
    ap.add_argument("--no-kill-switch", action="store_true")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    out = here.parent / "results" / "experiments"
    out.mkdir(parents=True, exist_ok=True)
    gate0 = json.loads((out / "h2_gate0.json").read_text(encoding="utf-8"))
    if not gate0.get("gate2a_unlock"):
        raise SystemExit("Gate 2A did not unlock 2B in results/experiments/h2_gate0.json")
    settle = gate0["targets"]["canvas"]["settle_ms"]
    if settle is None:
        raise SystemExit("Gate 0 canvas settle_ms is None (no delay reached >= 95% agreement)")

    orig_h, orig = w.cursor_state()
    if str(orig_h).startswith("error:"):
        raise SystemExit(
            f"ERROR_ACCESS_DENIED / GetCursorInfo failed ({orig_h}): "
            "H2 2B grid requires an active interactive desktop (Default), not an isolated exebox desktop."
        )

    print(f"H2 2B - calibrated settle delay: {settle} ms")

    from playwright.sync_api import sync_playwright
    fixture = here / "fixtures" / "h2_probe_fixture.html"
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
            raise SystemExit("canvas window not found")
        w.focus(hwnd)
        time.sleep(0.8)

        # A2 fix: true content origin
        inner_w = int(round(layout["win"]["iw"] * layout["win"]["dpr"]))
        inner_h = int(round(layout["win"]["ih"] * layout["win"]["dpr"]))
        cox, coy = w.content_origin(hwnd, inner_width_px=inner_w, inner_height_px=inner_h)
        cx, cy = int(layout["c"]["left"]), int(layout["c"]["top"])
        canvas = {"x": cox + cx, "y": coy + cy,
                  "w": int(layout["c"]["width"]), "h": int(layout["c"]["height"])}
        buttons = [{**b, "x": canvas["x"] + b["x"], "y": canvas["y"] + b["y"]} for b in layout["b"]]
        texts = [{**t, "x": canvas["x"] + t["x"], "y": canvas["y"] + t["y"]} for t in layout["t"]]

        pre = out / "_h2_grid_pre.png"
        pre_img, cap_method = w.capture_window_region(
            hwnd, (canvas["x"] - 8, canvas["y"] - 8, canvas["x"] + canvas["w"] + 8,
                   canvas["y"] + canvas["h"] + 8), path=str(pre))

        import uiautomation as auto
        auto.SetGlobalSearchTimeout(2.0)
        root = auto.ControlFromHandle(hwnd)
        uia_rects, queue = [], [(root, 0)]
        while queue and len(uia_rects) < 400:
            ctrl, depth = queue.pop(0)
            try:
                r = ctrl.BoundingRectangle
                if int(r.right) - int(r.left) > 2 and int(r.bottom) - int(r.top) > 2:
                    uia_rects.append((int(r.left), int(r.top), int(r.right), int(r.bottom)))
                if depth < 10:
                    queue.extend((c, depth + 1) for c in ctrl.GetChildren())
            except Exception:
                pass

        kill = w.KillSwitch(enabled=not args.no_kill_switch)
        print("moving the mouse again - any human movement >5 px aborts.")
        for i in (3, 2, 1):
            print(f"  starting in {i}...", flush=True)
            time.sleep(1.0)

        passes, stopped_early = [], False
        rng = random.Random(42)
        try:
            for n in STEPS:
                pts, step = grid_points(canvas, n)
                orders = ["raster", "randomized"] if args.order == "both" else [args.order]
                for ord_name in orders:
                    run_pts = list(pts)
                    if ord_name == "randomized":
                        rng.shuffle(run_pts)
                    hits, dur = _run_grid_pass(run_pts, settle, kill)
                    click = [h for h in hits if h["cursor_class"] == "HAND" or
                             h["cursor_class"].startswith("CUSTOM")]
                    ibeam = [h for h in hits if h["cursor_class"] == "IBEAM"]
                    clusters = cluster([(h["x"], h["y"], h["cursor_class"]) for h in click], 1.5 * step)
                    s = score(click, ibeam, buttons, texts, step)
                    passes.append({"requested": n, "order": ord_name, "points": len(run_pts),
                                   "step": step, "duration_ms": dur,
                                   "ms_per_point": round(dur / len(run_pts), 2),
                                   "click_hits": len(click), "ibeam_hits": len(ibeam),
                                   "clusters": len(clusters), "score": s,
                                   "cursor_classes": {c: sum(h["cursor_class"] == c for h in hits)
                                                      for c in sorted({h["cursor_class"] for h in hits})},
                                   "hits": hits})
                    print(f"  {n:>3} pts ({ord_name}) -> {len(run_pts)} probes, {dur} ms "
                          f"({dur / len(run_pts):.1f} ms/pt) recall={s['blind_recall']} "
                          f"precision={s['precision']}", flush=True)
                if passes[-1]["duration_ms"] > BUDGET_MS:
                    stopped_early = True
                    break
        finally:
            try:
                w.move(*orig)
            except OSError:
                pass
            browser.close()

    last = passes[-1]
    step = last["step"]
    hits = last["hits"]
    click = [h for h in hits if h["cursor_class"] == "HAND" or h["cursor_class"].startswith("CUSTOM")]

    img = pre_img.convert("RGB")
    d = ImageDraw.Draw(img)
    off_x, off_y = canvas["x"] - 8, canvas["y"] - 8
    for (l, t, r, b) in uia_rects:
        if r > off_x and l < off_x + img.width and b > off_y and t < off_y + img.height:
            d.rectangle([l - off_x, t - off_y, r - off_x, b - off_y], outline=(0, 220, 120), width=2)
    for h in hits:
        if h["cursor_class"] == "IBEAM":
            d.ellipse([h["x"] - off_x - 3, h["y"] - off_y - 3,
                       h["x"] - off_x + 3, h["y"] - off_y + 3], fill=(60, 140, 255))
    for h in click:
        d.ellipse([h["x"] - off_x - 4, h["y"] - off_y - 4,
                   h["x"] - off_x + 4, h["y"] - off_y + 4], fill=(255, 60, 60))
    img.save(out / "h2_overlay.png")

    s = last["score"]
    recall_ok = s["blind_recall"] >= 0.5
    precision_ok = s["precision"] >= 0.8
    latency_ok = last["duration_ms"] < BUDGET_MS
    passed = recall_ok and precision_ok and latency_ok
    verdict = "PASS" if passed else "REJECTED"

    report = {"target": title, "settle_ms": settle, "canvas": canvas,
              "capture_method": cap_method, "passes": passes,
              "stopped_early_on_budget": stopped_early,
              "final_score": s, "final_pass": {k: v for k, v in last.items() if k != "hits"},
              "overlay": str(out / "h2_overlay.png"),
              "gate2b": {"blind_recall": s["blind_recall"], "precision": s["precision"],
                         "duration_ms": last["duration_ms"], "budget_ms": BUDGET_MS,
                         "recall_ok": recall_ok, "precision_ok": precision_ok,
                         "latency_ok": latency_ok},
              "H2": verdict}
    (out / "h2_probes.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    rows = "\n".join(
        f"| {p['requested']} ({p['order']}) | {p['points']} | {p['step']} | {p['duration_ms']} | "
        f"{p['ms_per_point']} | {p['click_hits']} | {p['clusters']} | "
        f"{p['score']['blind_recall'] * 100:.1f}% | {p['score']['precision'] * 100:.1f}% |"
        for p in passes)
    stop_line = (
        f"Expansion stopped after pass #{len(passes)} ({last['points']} points, "
        f"{last['duration_ms'] / 1000:.2f} s) exceeded the {BUDGET_MS / 1000:.1f} s budget."
        if stopped_early else
        f"All {len(passes)} passes completed within the {BUDGET_MS / 1000:.1f} s budget."
    )
    if passed:
        conclusion = (
            f"**H2 = PASS.** The {last['points']}-point ({last['order']}) pass achieved "
            f"{s['blind_recall'] * 100:.1f}% blind recall (>= 50%), {s['precision'] * 100:.1f}% "
            f"precision (>= 80%), and completed in {last['duration_ms'] / 1000:.2f} s (< 5.0 s) "
            f"at {settle} ms settle."
        )
    else:
        failed_gates = [
            name for ok, name in [
                (recall_ok, f"recall {s['blind_recall'] * 100:.1f}% < 50%"),
                (precision_ok, f"precision {s['precision'] * 100:.1f}% < 80%"),
                (latency_ok, f"duration {last['duration_ms'] / 1000:.2f} s >= 5.0 s"),
            ] if not ok
        ]
        conclusion = (
            f"**H2 = REJECTED.** Failed gate(s) on the {last['points']}-point ({last['order']}) pass: "
            + "; ".join(failed_gates) + "."
        )

    (out / "h2_report.md").write_text(f"""# H2 - Windows Desktop Cursor Probe

- **Target:** {title} (real Chromium window painting a `<canvas>` app, probed through Win32 only)
- **Calibrated settle delay:** {settle} ms (Gate 0: first delay with >= 95% agreement against {gate0.get('reference_delay_ms', 120)} ms)
- **Verdict:** **H2 = {verdict}**

## Gate 0 (per-toolkit calibration)

| target | UIA recall | UIA nodes | P(HAND/CUSTOM abs clickable) | P(HAND/CUSTOM abs dead) | settle |
| --- | --- | --- | --- | --- | --- |
{_gate0_rows_from_json(gate0)}

{_gate0_narrative(gate0)}

## Progressive scan

| budget | points | step | duration | ms/point | click hits | clusters | blind recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{rows}

{stop_line}

## Accuracy on the {last['points']}-point ({last['order']}) pass

| Metric | Value | Gate |
| --- | --- | --- |
| TP controls hit (of {s['controls_total']}) | {s['tp']} |  |
| FP clusters (not inside any control) | {s['fp_clusters']} |  |
| FN controls with no hit | {s['fn']} |  |
| Text fields found by IBEAM (never counted as clickable) | {s['text_fields_hit_by_ibeam']} |  |
| Blind Recall | {s['blind_recall'] * 100:.1f}% | >= 50% {'PASS' if recall_ok else 'FAIL'} |
| Precision | {s['precision'] * 100:.1f}% | >= 80% {'PASS' if precision_ok else 'FAIL'} |
| Scan duration | {last['duration_ms'] / 1000:.2f} s | < 5.0 s {'PASS' if latency_ok else 'FAIL'} |

Overlay: `h2_overlay.png` (green = UIA boxes in the window, red = HAND/CUSTOM hits, blue = IBEAM).

{conclusion}
""", encoding="utf-8")
    print(json.dumps({"H2": verdict, "gate2b": report["gate2b"],
                      "final": report["final_pass"]}, indent=2))


if __name__ == "__main__":
    main()

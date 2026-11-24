#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""H1b spike: latency and clustering reality check for the canvas cursor probe.

Re-validated after fixing two defects in the first H1b pass:
  1. The first pass imported PROBE_JS (which awaits requestAnimationFrame inside JS),
     so 'sync' and 'yield2' still waited 1 rAF (~33 ms) and 'raf' waited 2 rAFs (~50 ms).
  2. It only tested sequential round trips. This version adds async CDP pipelining.

Modes compared against a single-rAF baseline ('raf'):
  - raf      : Input.dispatchMouseEvent + single-rAF PROBE_JS (2 CDP RTs + 1 rAF)
  - sync     : Input.dispatchMouseEvent + synchronous NO_RAF_PROBE_JS (no rAF)
  - yield2   : Input.dispatchMouseEvent + 2 ms sleep + NO_RAF_PROBE_JS (no rAF)
  - pipe_20  : async CDP batch of 20 (mouseMoved + synchronous Runtime.evaluate)
  - pipe_80  : async CDP batch of 80 (mouseMoved + synchronous Runtime.evaluate)

Practical gate passes only if the SAME mode achieves both agreement >= 90% and
full-viewport scan duration < 3.0 s.

Writes results/experiments/h1b_report.md, h1b_report.json, and prints the JSON summary.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h1_canvas_probe import DEFAULT_URL, FIND_CANVAS, PROBE_JS, cluster, grid_axes  # noqa: E402

from playwright.async_api import async_playwright  # noqa: E402

NO_RAF_BODY = """((x, y) => {
  let el = document.elementFromPoint(x, y);
  while (el && el.shadowRoot) {
    const next = el.shadowRoot.elementFromPoint(x, y);
    if (!next || next === el) break;
    el = next;
  }
  const cv = window.__h1canvas;
  return {cursor: el ? getComputedStyle(el).cursor : 'none',
          canvas: cv ? getComputedStyle(cv).cursor : 'none',
          tag: el ? el.tagName : null};
})"""

NO_RAF_PROBE_JS = f"([x, y]) => {NO_RAF_BODY}(x, y)"


def grid(rect, step):
    xs, ys = grid_axes(rect, step)
    return [(x, y) for y in ys for x in xs]


def agreement(a, b):
    """Jaccard over the pointer hit sets of two passes."""
    a2 = {(round(x), round(y)) for x, y, _ in a}
    b2 = {(round(x), round(y)) for x, y, _ in b}
    if not a2 and not b2:
        return 1.0
    return len(a2 & b2) / len(a2 | b2)


async def wait_ready_async(page, budget_ms):
    t0 = time.perf_counter()
    deadline = t0 + budget_ms / 1000
    rect = None
    while time.perf_counter() < deadline and not rect:
        rect = await page.evaluate(FIND_CANVAS)
        if not rect:
            await page.wait_for_timeout(100)
    stable, prev = False, None
    while rect and time.perf_counter() < deadline:
        await page.wait_for_timeout(150)
        shot = await page.screenshot()
        if shot == prev:
            stable = True
            break
        prev = shot
    return rect, round((time.perf_counter() - t0) * 1000), stable


async def run_sequential(cdp, page, points, mode):
    """Sequential per-point round trips; 'raf' waits one rAF only."""
    hits, stats, started = set(), {}, time.perf_counter()
    for x, y in points:
        await cdp.send("Input.dispatchMouseEvent",
                       {"type": "mouseMoved", "x": x, "y": y, "button": "none", "buttons": 0})
        if mode == "raf":
            state = await page.evaluate(PROBE_JS, [x, y])
        elif mode == "sync":
            state = await page.evaluate(NO_RAF_PROBE_JS, [x, y])
        elif mode == "yield2":
            await asyncio.sleep(0.002)
            state = await page.evaluate(NO_RAF_PROBE_JS, [x, y])
        else:
            raise ValueError(f"unknown mode {mode!r}")
        c = state["cursor"]
        stats[c] = stats.get(c, 0) + 1
        if c == "pointer":
            hits.add((x, y, state["tag"] or "none"))
    dur = (time.perf_counter() - started) * 1000
    return {"probes": len(points), "duration_ms": round(dur, 1),
            "ms_per_probe": round(dur / len(points), 2),
            "pointer_hits": len(hits), "stats": dict(sorted(stats.items(), key=lambda kv: -kv[1])),
            "hits": hits}


async def run_pipelined(cdp, points, batch_size):
    """Batched CDP pipelining: send N mouseMoved + Runtime.evaluate calls without blocking per point."""
    hits, stats, started = set(), {}, time.perf_counter()
    for i in range(0, len(points), batch_size):
        chunk = points[i:i + batch_size]
        tasks = []
        for x, y in chunk:
            tasks.append(cdp.send("Input.dispatchMouseEvent",
                                  {"type": "mouseMoved", "x": x, "y": y, "button": "none", "buttons": 0}))
            tasks.append(cdp.send("Runtime.evaluate",
                                  {"expression": f"{NO_RAF_BODY}({x}, {y})", "returnByValue": True}))
        results = await asyncio.gather(*tasks)
        for j, (x, y) in enumerate(chunk):
            state = results[2 * j + 1]["result"]["value"]
            c = state["cursor"]
            stats[c] = stats.get(c, 0) + 1
            if c == "pointer":
                hits.add((x, y, state["tag"] or "none"))
    dur = (time.perf_counter() - started) * 1000
    return {"probes": len(points), "duration_ms": round(dur, 1),
            "ms_per_probe": round(dur / len(points), 2),
            "pointer_hits": len(hits), "stats": dict(sorted(stats.items(), key=lambda kv: -kv[1])),
            "hits": hits}


async def run_async(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": args.width, "height": args.height})
        await page.goto(args.url, wait_until="load", timeout=60000)
        try:
            await page.wait_for_load_state("networkidle", timeout=min(args.wait, 10000))
        except Exception:
            pass
        canvas, ready_ms, stable = await wait_ready_async(page, args.wait)
        if not canvas:
            await browser.close()
            raise SystemExit(f"no <canvas> within --wait {args.wait} ms on {args.url}")
        canvas = {"x": max(canvas["x"], 0), "y": max(canvas["y"], 0),
                  "w": min(canvas["x"] + canvas["w"], args.width) - max(canvas["x"], 0),
                  "h": min(canvas["y"] + canvas["h"], args.height) - max(canvas["y"], 0)}
        cdp = await page.context.new_cdp_session(page)
        points = grid(canvas, args.step)

        passes = {}
        for mode in ("raf", "sync", "yield2"):
            await page.mouse.move(1, args.height - 1)
            passes[mode] = await run_sequential(cdp, page, points, mode)
        for batch in (20, 80):
            await page.mouse.move(1, args.height - 1)
            passes[f"pipe_{batch}"] = await run_pipelined(cdp, points, batch)
        await browser.close()

    base = passes["raf"]
    regions = cluster(sorted(base["hits"]), 1.5 * args.step)
    agree_map = {}
    for m, res in passes.items():
        if m == "raf":
            continue
        agree_map[m] = round(agreement(base["hits"], res["hits"]), 4)

    candidates = [m for m in passes if m != "raf"]
    accurate_modes = [m for m in candidates if agree_map[m] >= 0.90]
    practical_modes = [m for m in accurate_modes if passes[m]["duration_ms"] < 3000]
    fastest_accurate = min(accurate_modes, key=lambda m: passes[m]["duration_ms"]) if accurate_modes else None
    fastest_overall = min(candidates, key=lambda m: passes[m]["duration_ms"])

    shot_tokens = round(args.width * args.height / 750)
    region_tokens = len(regions) * 10
    signal_ok = bool(accurate_modes)
    practical_ok = bool(practical_modes)
    verdict = ("PASS" if practical_ok else ("SIGNAL-ONLY" if signal_ok else "REJECTED"))

    report = {
        "url": args.url, "step": args.step, "grid_points": len(points),
        "canvas": canvas, "readiness": {"ms": ready_ms, "paint_stable": stable},
        "passes": {m: {k: v for k, v in passes[m].items() if k != "hits"} for m in passes},
        "agreement": {f"{m}_vs_raf": agree_map[m] for m in candidates},
        "fastest_accurate_mode": fastest_accurate,
        "fastest_overall_mode": fastest_overall,
        "regions": len(regions),
        "tokens": {"regions_unlabeled": region_tokens, "screenshot": shot_tokens},
        "gate": {"signal_pass_agreement_ge_0.90": signal_ok,
                 "practical_pass_lt_3.0s_with_agreement": practical_ok},
        "H1_PRACTICAL": verdict,
    }
    (out / "h1b_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    mode_order = ["raf", "sync", "yield2", "pipe_20", "pipe_80"]
    rows = "\n".join(
        f"| {m} | {passes[m]['ms_per_probe']:.2f} | {passes[m]['duration_ms'] / 1000:.2f} s "
        f"| {passes[m]['pointer_hits']} | {passes[m]['stats'].get('pointer', 0)} "
        f"| {'baseline' if m == 'raf' else f'{agree_map[m] * 100:.1f}%'} |"
        for m in mode_order)
    agree_rows = "\n".join(
        f"| {m} vs rAF (1 frame) | {agree_map[m] * 100:.1f}% | {'yes' if agree_map[m] >= 0.9 else 'no'} "
        f"| {'yes' if passes[m]['duration_ms'] < 3000 else 'no'} |"
        for m in candidates)
    fastest_summary = (
        f"**{fastest_accurate}** at **{passes[fastest_accurate]['duration_ms'] / 1000:.2f} s** "
        f"({passes[fastest_accurate]['ms_per_probe']:.2f} ms/probe)"
        if fastest_accurate else "none (>= 90% agreement not met)"
    )

    (out / "h1b_report.md").write_text(f"""# H1b — Latency & Clustering Reality Check

- **Target:** `{args.url}`
- **Grid:** {len(points)} points at step {args.step} px over {args.width}x{args.height}
- **H1_PRACTICAL:** **{verdict}**

## Latency

| mode | ms/probe | duration | pointer hits (distinct) | raw pointer probes | agreement vs rAF |
| --- | --- | --- | --- | --- | --- |
{rows}

Agreement against the single-rAF baseline (Jaccard over pointer hit coordinates, rounded to 1 px):

| comparison | agreement | agreement >= 90% | duration < 3.0 s |
| --- | --- | --- | --- |
{agree_rows}

Fastest mode meeting the >= 90% agreement gate: {fastest_summary} (gate: < 3.0 s).
Fastest pipelined mode ({fastest_overall}): **{passes[fastest_overall]['duration_ms'] / 1000:.2f} s**,
agreement **{agree_map[fastest_overall] * 100:.1f}%** (fails agreement gate).

## Clustering

- Distinct pointer regions at radius 1.5 x step: **{len(regions)}** (from {base['pointer_hits']} distinct hits)
- Unlabeled region list: **~{region_tokens} tokens** ({len(regions)} x ~10)
- 1 viewport screenshot: **~{shot_tokens} tokens**

## Gate

| gate | result |
| --- | --- |
| Hit agreement >= 90% | {'PASS' if signal_ok else 'REJECTED'} |
| Full-viewport scan < 3.0 s (with >= 90% agreement) | {'PASS' if practical_ok else 'REJECTED'} |
| **H1_PRACTICAL** | **{verdict}** |
""", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="H1b latency + clustering check")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--step", type=int, default=32)
    ap.add_argument("--wait", type=int, default=12000)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--out", default=str(here.parent / "results" / "experiments"))
    args = ap.parse_args()
    asyncio.run(run_async(args))


if __name__ == "__main__":
    main()

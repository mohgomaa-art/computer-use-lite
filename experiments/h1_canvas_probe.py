#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""H1 spike: canvas virtual cursor probe.

Hypothesis H1: on a real <canvas> app whose DOM/AX exposes no internal controls,
synthetic CDP Input.dispatchMouseEvent(mouseMoved) over a grid plus the deepest
hovered node's getComputedStyle(el).cursor finds clickable controls that DOM/AX
misses.

This script measures and renders only. It never declares a verdict: status stays
PENDING HUMAN REVIEW (SMOKE TEST ONLY on file:// targets) until a human scores
TP/FP/FN, Blind Recall and Precision on results/experiments/h1_overlay.png.
"""
import argparse
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROLES = {"button", "link", "textbox", "checkbox", "menuitem", "tab"}
DEFAULT_URL = "https://www.google.com/maps/@40.7580,-73.9855,17z"

# Largest visible canvas, walking open shadow roots (Flutter/CanvasKit paints inside them).
FIND_CANVAS = """() => {
  const out = [];
  const walk = (root) => {
    for (const c of root.querySelectorAll('canvas')) {
      const r = c.getBoundingClientRect();
      if (r.width > 1 && r.height > 1) out.push({el: c, r: r});
    }
    for (const el of root.querySelectorAll('*')) if (el.shadowRoot) walk(el.shadowRoot);
  };
  walk(document);
  out.sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
  window.__h1canvas = out.length ? out[0].el : null;
  const r = out.length ? out[0].r : null;
  return r ? {x: r.x, y: r.y, w: r.width, h: r.height} : null;
}"""

# One round trip: settle one frame, drill into open shadow roots, read the cursor.
PROBE_JS = """async ([x, y]) => {
  await new Promise(r => requestAnimationFrame(r));
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
}"""


def text(tbl, v):
    """DOMSnapshot strings are indexes; -1 means 'no string' (never index from the end)."""
    if isinstance(v, list):
        return "".join(tbl[i] for i in v if 0 <= i < len(tbl))
    if isinstance(v, int):
        return tbl[v] if 0 <= v < len(tbl) else ""
    return v or ""


def baseline(page, cdp, viewport):
    """Union of DOMSnapshot (isClickable | cursor:pointer) across all documents and AX roles, viewport only."""
    snap = cdp.send("DOMSnapshot.captureSnapshot", {"computedStyles": ["cursor"]})
    tbl, out = snap["strings"], {}
    sx, sy = page.evaluate("() => [scrollX, scrollY]")
    vw, vh = viewport

    def add(nid, source, box, name="", subtract_scroll=True):
        ox = sx if subtract_scroll else 0
        oy = sy if subtract_scroll else 0
        x, y, w, h = box[0] - ox, box[1] - oy, box[2], box[3]
        if w > 0 and h > 0 and x < vw and y < vh and x + w > 0 and y + h > 0:
            out[nid] = {"source": source, "name": name,
                        "box": [round(v, 1) for v in (x, y, w, h)]}

    for doc_idx, doc in enumerate(snap["documents"]):
        nodes, lay = doc["nodes"], doc.get("layout", {})
        boxes, cursor = {}, {}
        for i, ni in enumerate(lay.get("nodeIndex", [])):
            q = lay["bounds"][i]
            if len(q) == 4:
                boxes[ni] = list(q)
            elif len(q) == 8:
                boxes[ni] = [min(q[0::2]), min(q[1::2]),
                             max(q[0::2]) - min(q[0::2]), max(q[1::2]) - min(q[1::2])]
            seg = lay.get("styles", [[]])[i] if i < len(lay.get("styles", [])) else []
            cursor[ni] = text(tbl, seg[0]) if seg else ""

        clicked = set(nodes.get("isClickable", {}).get("index", []))
        for ni in sorted(clicked | {n for n, c in cursor.items() if c == "pointer"}):
            if ni in boxes and ni < len(nodes["backendNodeId"]):
                add(nodes["backendNodeId"][ni],
                    "isClickable" if ni in clicked else "cursor:pointer",
                    boxes[ni], subtract_scroll=(doc_idx == 0))

    for node in cdp.send("Accessibility.getFullAXTree")["nodes"]:
        role, nid = (node.get("role") or {}).get("value"), node.get("backendDOMNodeId")
        if node.get("ignored") or role not in ROLES or nid is None or nid in out:
            continue
        try:
            q = cdp.send("DOM.getBoxModel", {"backendNodeId": nid})["model"]["content"]
        except Exception:
            continue
        # DOM.getBoxModel already returns viewport coordinates
        add(nid, "ax:" + role,
            [min(q[0::2]), min(q[1::2]),
             max(q[0::2]) - min(q[0::2]), max(q[1::2]) - min(q[1::2])],
            (node.get("name") or {}).get("value", ""), subtract_scroll=False)
    return list(out.values())


def wait_ready(page, budget_ms):
    """Within the --wait budget: canvas must exist, then viewport paint must settle."""
    t0 = time.perf_counter()
    deadline = t0 + budget_ms / 1000
    rect = None
    while time.perf_counter() < deadline and not rect:
        rect = page.evaluate(FIND_CANVAS)
        if not rect:
            page.wait_for_timeout(100)
    stable, prev = False, None
    while rect and time.perf_counter() < deadline:
        page.wait_for_timeout(150)
        shot = page.screenshot()
        if shot == prev:
            stable = True
            break
        prev = shot
    return rect, round((time.perf_counter() - t0) * 1000), stable


def grid_axes(rect, step):
    """Axis coordinates covering the canvas without leaving an unprobed trailing edge strip."""
    def axis(start, span):
        if span <= 0:
            return []
        pts = [start + step / 2 + i * step for i in range(int(span / step))]
        end_edge = start + span - min(step / 2, span / 2)
        if not pts or (start + span - pts[-1]) > step / 2:
            if not pts or abs(end_edge - pts[-1]) >= 2:
                pts.append(end_edge)
        return pts

    return axis(rect["x"], rect["w"]), axis(rect["y"], rect["h"])


def probe(cdp, page, rect, step):
    """Grid probe: one mouseMoved + one evaluate (rAF settle + cursor read) per point."""
    clicks, texts, stats, tags, mismatches = [], [], {}, {}, 0
    xs, ys = grid_axes(rect, step)
    started, n = time.perf_counter(), 0
    for y in ys:
        for x in xs:
            cdp.send("Input.dispatchMouseEvent",
                     {"type": "mouseMoved", "x": x, "y": y, "button": "none", "buttons": 0})
            state = page.evaluate(PROBE_JS, [x, y])
            n, cursor = n + 1, state["cursor"]
            stats[cursor] = stats.get(cursor, 0) + 1
            tag = state["tag"] or "none"
            tags[tag] = tags.get(tag, 0) + 1
            mismatches += cursor != state["canvas"]
            if cursor == "pointer":
                clicks.append([x, y, tag])
            elif cursor == "text":  # I-beam: never counted as clickable
                texts.append([x, y, tag])
    return {"probes": n, "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            "clicks": clicks, "texts": texts, "mismatches": mismatches,
            "stats": dict(sorted(stats.items(), key=lambda kv: -kv[1])),
            "tags": dict(sorted(tags.items(), key=lambda kv: -kv[1])[:8])}


def cluster(points, radius):
    """Union adjacent probe hits (Chebyshev distance <= radius) into distinct regions."""
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if abs(points[i][0] - points[j][0]) <= radius and abs(points[i][1] - points[j][1]) <= radius:
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
    groups = {}
    for i, pt in enumerate(points):
        groups.setdefault(find(i), []).append(pt)
    out = []
    for g in groups.values():
        xs, ys = [p[0] for p in g], [p[1] for p in g]
        out.append({"probes": len(g),
                    "box": [round(min(xs), 1), round(min(ys), 1),
                            round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)],
                    "centroid": [round(sum(xs) / len(g), 1), round(sum(ys) / len(g), 1)],
                    "tags": sorted({p[2] for p in g})})
    out.sort(key=lambda c: -c["probes"])
    return out


def overlay(shot, base, res, path):
    img = Image.open(shot).convert("RGB")
    draw = ImageDraw.Draw(img)
    for el in base:
        x, y, w, h = el["box"]
        draw.rectangle([x, y, x + w, y + h], outline=(0, 220, 120), width=2)
    for x, y, _ in res["texts"]:
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(60, 140, 255))
    for x, y, _ in res["clicks"]:
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 60, 60))
    img.save(path)


def report(args, canvas, base, res, viewport, ready, status, out_dir):
    clicks, texts = len(res["clicks"]), len(res["texts"])
    per_probe = res["duration_ms"] / res["probes"] if res["probes"] else 0
    on_canvas = sum(1 for pt in res["clicks"] if pt[2] == "CANVAS")
    regions = cluster(res["clicks"], 1.5 * args.step)
    overlap = [e for e in base
               if e["box"][0] < canvas["x"] + canvas["w"] and e["box"][0] + e["box"][2] > canvas["x"]
               and e["box"][1] < canvas["y"] + canvas["h"] and e["box"][1] + e["box"][3] > canvas["y"]]
    list_tokens = len(base) * 18            # element list: role + name + bbox
    cluster_tokens = len(regions) * 10      # clustered regions only: bbox + centroid, unlabeled
    shot_tokens = round(viewport[0] * viewport[1] / 750)
    rows = "\n".join(f"| `{k}` | {v} | {'yes' if k == 'pointer' else 'no'} |"
                     for k, v in res["stats"].items())
    tag_rows = "\n".join(f"| `{k}` | {v} |" for k, v in res["tags"].items())
    region_rows = "\n".join(
        f"| {i} | {r['probes']} | {r['box'][0]:.0f},{r['box'][1]:.0f},{r['box'][2]:.0f},{r['box'][3]:.0f} "
        f"| {r['centroid'][0]:.0f},{r['centroid'][1]:.0f} | {', '.join(r['tags'])} |"
        for i, r in enumerate(regions, 1))

    Path(out_dir / "h1_report.md").write_text(f"""# H1 — Browser Canvas Virtual Cursor Probe

- **Target:** `{args.url}`
- **Status:** {status}
- **Rule:** no verdict is computed here. `PASS`/`BLOCKED`/`REJECTED` is a human decision from `h1_overlay.png`.

## Metrics

| Metric | Value |
| --- | --- |
| Viewport | {viewport[0]}x{viewport[1]} |
| Grid step | {args.step} px |
| Canvas rect (viewport-clipped) | x={canvas['x']:.0f} y={canvas['y']:.0f} w={canvas['w']:.0f} h={canvas['h']:.0f} |
| Readiness | canvas + paint settled after {ready['ms']} ms, paint stable: {'yes' if ready['stable'] else 'no'} (--wait {args.wait} ms) |
| Total probes | {res['probes']} |
| Total duration | {res['duration_ms'] / 1000:.1f} s ({res['duration_ms']} ms) |
| Average per probe | {per_probe:.1f} ms |
| DOM/AX baseline elements (viewport) | {len(base)} |
| DOM/AX baseline elements overlapping canvas | {len(overlap)} |
| `pointer` hits (clickable) | {clicks} |
| `text` / I-beam hits (not clickable) | {texts} |
| `pointer` hits whose hovered node is the `<canvas>` itself | {on_canvas} |
| Distinct `pointer` regions after clustering (radius 1.5 x step) | {len(regions)} |
| Cursor mismatches (hovered vs canvas) | {res['mismatches']} |

## Cursor distribution

| cursor | count | counted as clickable |
| --- | --- | --- |
{rows}

## Top hovered tags

| tag | probes |
| --- | --- |
{tag_rows}

## Token cost estimate

Probing does not emit the raw grid to a model: adjacent hits are spatially clustered first and
only the regions travel. Each region carries a bounding box and centroid but **no semantic
label** — unlike a DOM/AX row (role + name + bbox) or a screenshot, where the model reads the
label off the pixels itself.

| Representation | Estimated tokens |
| --- | --- |
| DOM/AX element list ({len(base)} elements x ~18 tokens) | ~{list_tokens} |
| Clustered probe regions ({len(regions)} regions x ~10 tokens, unlabeled) | ~{cluster_tokens} |
| Raw grid points ({res['probes']} points x ~4 tokens) — *not emitted, upper bound only* | ~{res['probes'] * 4} |
| 1 viewport screenshot ({viewport[0]}x{viewport[1]}) | ~{shot_tokens} |

## Probe regions (clustered)

| # | probes | box (x,y,w,h) | centroid | tags |
| --- | --- | --- | --- | --- |
{region_rows}

## Review Scorecard (filled by the reviewer after inspecting `h1_overlay.png`)

| Metric | Value | Gate |
| --- | --- | --- |
| TP clickable clusters |  |  |
| FP clickable clusters |  |  |
| FN blind clickables |  |  |
| Blind Recall (distinct blind clickable controls hit / total blind clickables missed by DOM/AX) |  | >= 50% |
| Precision (TP clusters / TP + FP) |  | >= 80% |
| Decision (PASS / BLOCKED / REJECTED) |  | human only |
""", encoding="utf-8")
    return {"list_tokens": list_tokens, "cluster_tokens": cluster_tokens,
            "raw_point_tokens_upper_bound": res["probes"] * 4, "shot_tokens": shot_tokens,
            "regions": len(regions)}


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="H1 canvas cursor probe")
    ap.add_argument("--url", default=DEFAULT_URL, help=f"target page (default: {DEFAULT_URL})")
    ap.add_argument("--step", type=int, default=32, help="grid step in px (default 32)")
    ap.add_argument("--wait", type=int, default=3500, help="ms to wait for canvas paint (default 3500)")
    ap.add_argument("--out", default=str(here.parent / "results" / "experiments"))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--headful", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    viewport = (args.width, args.height)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        try:
            page.goto(args.url, wait_until="load", timeout=60000)
        except Exception as exc:
            browser.close()
            raise SystemExit(f"could not open {args.url}: {type(exc).__name__}")
        try:  # best effort: long-lived connections are common on canvas apps
            page.wait_for_load_state("networkidle", timeout=min(args.wait, 10000))
        except Exception:
            pass
        canvas, ready_ms, stable = wait_ready(page, args.wait)
        if not canvas:
            title = page.title()
            browser.close()
            raise SystemExit(f"no <canvas> within --wait {args.wait} ms on {args.url} "
                             f"(title: {title!r}); the target may be missing or not a canvas app")
        canvas = {"x": max(canvas["x"], 0), "y": max(canvas["y"], 0),
                  "w": min(canvas["x"] + canvas["w"], args.width) - max(canvas["x"], 0),
                  "h": min(canvas["y"] + canvas["h"], args.height) - max(canvas["y"], 0)}
        cdp = page.context.new_cdp_session(page)
        base = baseline(page, cdp, viewport)
        shot = out / "_viewport.png"
        page.screenshot(path=str(shot), full_page=False)  # before probing: no hover state
        page.mouse.move(1, args.height - 1)
        res = probe(cdp, page, canvas, args.step)
        browser.close()

    status = "SMOKE TEST ONLY" if args.url.startswith("file:") else "PENDING HUMAN REVIEW"
    overlay(shot, base, res, out / "h1_overlay.png")
    (out / "h1_baseline.json").write_text(json.dumps(base, indent=2), encoding="utf-8")
    (out / "h1_probes.json").write_text(json.dumps(
        {"canvas": canvas, "step": args.step, "clicks": res["clicks"],
         "texts": res["texts"],
         "regions": cluster(res["clicks"], 1.5 * args.step),
         "canvas_regions": cluster([p for p in res["clicks"] if p[2] == "CANVAS"],
                                  1.5 * args.step)}, indent=2), encoding="utf-8")
    summary = report(args, canvas, base, res, viewport,
                     {"ms": ready_ms, "stable": stable}, status, out)
    print(json.dumps({"url": args.url, "status": status, "step": args.step,
                      "canvas": canvas,
                      "readiness": {"ms": ready_ms, "paint_stable": stable},
                      "probes": res["probes"], "duration_ms": res["duration_ms"],
                      "ms_per_probe": round(res["duration_ms"] / res["probes"], 1),
                      "baseline_elements": len(base), "clickable_hits": len(res["clicks"]),
                      "text_hits": len(res["texts"]),
                      "canvas_pointer_hits": sum(1 for pt in res["clicks"] if pt[2] == "CANVAS"),
                      "pointer_regions": summary["regions"],
                      "cursor_stats": res["stats"], "top_tags": res["tags"],
                      "est_tokens": summary}, indent=2))


if __name__ == "__main__":
    main()

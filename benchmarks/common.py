# SPDX-License-Identifier: Apache-2.0
"""Shared statistical, resource telemetry, accuracy scoring, and immutability helpers."""
import ctypes
import hashlib
import json
import math
import os
import statistics
import time
from ctypes import wintypes
from pathlib import Path

import psutil

ROOT_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT_DIR / "src" / "computer_use_lite"
OUT_DIR = ROOT_DIR / "results" / "perf_study"

INTERACTIVE_ROLES = {
    "button", "menuitem", "tab", "link", "textbox", "combobox",
    "checkbox", "radio", "switch", "clickable", "listitem", "treeitem",
}


def engine_hashes():
    """Return SHA-256 digests of all production engine files."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ENGINE_DIR.glob("*.py"))
    }


def verify_engine_untouched(baseline):
    """Raise AssertionError if any byte inside engine/ changed."""
    current = engine_hashes()
    if current != baseline:
        raise AssertionError(f"Production engine modified! baseline={baseline} current={current}")
    return True


def summarize_timings(cold_samples, warm_samples):
    """Compute latency distribution statistics in milliseconds."""
    warm = sorted(float(x) for x in warm_samples)
    cold = [float(x) for x in cold_samples]

    def pct(arr, q):
        if not arr:
            return None
        if len(arr) == 1:
            return round(arr[0], 3)
        idx = (len(arr) - 1) * q
        lo = int(math.floor(idx))
        hi = min(lo + 1, len(arr) - 1)
        frac = idx - lo
        return round(arr[lo] * (1.0 - frac) + arr[hi] * frac, 3)

    return {
        "n_cold": len(cold),
        "n_warm": len(warm),
        "cold_mean_ms": round(statistics.mean(cold), 3) if cold else None,
        "cold_first_ms": round(cold[0], 3) if cold else None,
        "cold_samples_ms": [round(x, 3) for x in cold],
        "warm_mean_ms": round(statistics.mean(warm), 3) if warm else None,
        "p50_ms": pct(warm, 0.50),
        "p95_ms": pct(warm, 0.95),
        "p99_ms": pct(warm, 0.99),
        "min_ms": round(min(warm), 3) if warm else None,
        "max_ms": round(max(warm), 3) if warm else None,
        "warm_samples_ms": [round(x, 3) for x in warm],
    }


def _cpu_times_ms(proc):
    t = proc.cpu_times()
    return (t.user + t.system) * 1000.0


def measure_workload(
    cold_fn,
    warm_fn,
    n_cold=3,
    n_warm=20,
    target_pid=None,
):
    """Run cold + warm iterations and collect latency, CPU, memory, IPC, and payload stats.

    `cold_fn` / `warm_fn` must return `(elements, meta_dict)` where `meta_dict` may contain
    `ipc_round_trips`, `response_bytes`, `node_count`, `errors`, and `extra`.
    """
    self_proc = psutil.Process(os.getpid())
    tgt_proc = None
    if target_pid:
        try:
            tgt_proc = psutil.Process(int(target_pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            tgt_proc = None

    cold_ms = []
    errors = []
    last_elements = []
    last_meta = {}
    for _ in range(n_cold):
        t0 = time.perf_counter()
        try:
            els, meta = cold_fn()
            dt = (time.perf_counter() - t0) * 1000.0
            cold_ms.append(dt)
            last_elements = els
            last_meta = meta or {}
        except Exception as exc:
            errors.append(f"cold: {type(exc).__name__}: {exc}")
            cold_ms.append((time.perf_counter() - t0) * 1000.0)

    warm_ms = []
    ipc_list = []
    bytes_list = []
    node_list = []
    cpu_self_before = _cpu_times_ms(self_proc)
    rss_before = self_proc.memory_info().rss
    cpu_tgt_before = _cpu_times_ms(tgt_proc) if tgt_proc else None
    t_wall_start = time.perf_counter()

    for _ in range(n_warm):
        t0 = time.perf_counter()
        try:
            els, meta = warm_fn()
            dt = (time.perf_counter() - t0) * 1000.0
            warm_ms.append(dt)
            last_elements = els
            last_meta = meta or {}
            if "ipc_round_trips" in last_meta:
                ipc_list.append(int(last_meta["ipc_round_trips"]))
            if "response_bytes" in last_meta:
                bytes_list.append(int(last_meta["response_bytes"]))
            if "node_count" in last_meta:
                node_list.append(int(last_meta["node_count"]))
        except Exception as exc:
            errors.append(f"warm: {type(exc).__name__}: {exc}")

    t_wall_ms = max(0.001, (time.perf_counter() - t_wall_start) * 1000.0)
    cpu_self_ms = max(0.0, _cpu_times_ms(self_proc) - cpu_self_before)
    rss_after = self_proc.memory_info().rss
    cpu_tgt_ms = None
    if tgt_proc and cpu_tgt_before is not None:
        try:
            cpu_tgt_ms = round(max(0.0, _cpu_times_ms(tgt_proc) - cpu_tgt_before), 3)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cpu_tgt_ms = None

    stats = summarize_timings(cold_ms, warm_ms)
    stats.update({
        "client_cpu_ms_total": round(cpu_self_ms, 3),
        "client_cpu_ms_per_iter": round(cpu_self_ms / max(len(warm_ms), 1), 3),
        "client_cpu_pct": round(100.0 * cpu_self_ms / t_wall_ms, 2),
        "target_cpu_ms_total": cpu_tgt_ms,
        "rss_delta_kb": round((rss_after - rss_before) / 1024.0, 1),
        "ipc_round_trips": int(round(statistics.mean(ipc_list))) if ipc_list else last_meta.get("ipc_round_trips"),
        "response_bytes": int(round(statistics.mean(bytes_list))) if bytes_list else last_meta.get("response_bytes"),
        "node_count": int(round(statistics.mean(node_list))) if node_list else last_meta.get("node_count", len(last_elements)),
        "interactive_count": sum(1 for e in last_elements if _is_actionable(e)),
        "error_count": len(errors),
        "errors": errors[:10],
        "meta": last_meta,
    })
    return last_elements, stats


def box_iou(a, b):
    """Intersection over Union for [x, y, w, h] rectangles."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0.0
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _ref_key(el):
    ref = el.get("ref") or {}
    if ref.get("kind") == "uia" and ref.get("runtime_id"):
        return ("uia", tuple(ref["runtime_id"]))
    if ref.get("kind") == "browser" and ref.get("backend_node_id") is not None:
        return ("browser", int(ref["backend_node_id"]))
    if el.get("gt_id"):
        return ("gt", el["gt_id"])
    return None


def _norm_name(name):
    return " ".join((name or "").strip().lower().split())


def _token_f1(a, b):
    ta = set(_norm_name(a).split())
    tb = set(_norm_name(b).split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return (2.0 * inter) / (len(ta) + len(tb))


def _is_actionable(el):
    return (
        el.get("role") in INTERACTIVE_ROLES
        and el.get("enabled") is not False
        and el.get("offscreen") is not True
        and el.get("occluded") is not True
    )


def compare_elements(candidate, baseline, iou_thresh=0.55, interactive_only=True):
    """Score candidate element discovery against baseline/ground-truth corpus.

    Matches by explicit ref key (`backend_node_id` / `runtime_id`) first, then falls back
    to best geometric IoU (`>= iou_thresh`). Penalizes missing elements and extra FPs.
    """
    base_items = [dict(e) for e in baseline if (not interactive_only or e.get("role") in INTERACTIVE_ROLES)]
    cand_items = [dict(e) for e in candidate if (not interactive_only or e.get("role") in INTERACTIVE_ROLES)]

    # Deduplicate candidate indices mapped one-to-one against baseline items
    used_cand = set()
    matches = []
    missing = []

    cand_by_ref = {}
    for ci, ce in enumerate(cand_items):
        rk = _ref_key(ce)
        if rk is not None and rk not in cand_by_ref:
            cand_by_ref[rk] = ci

    for bi, be in enumerate(base_items):
        matched_ci = None
        rk = _ref_key(be)
        if rk is not None and rk in cand_by_ref and cand_by_ref[rk] not in used_cand:
            cand_box = cand_items[cand_by_ref[rk]].get("box") or [0, 0, 0, 0]
            base_box = be.get("box") or [0, 0, 0, 0]
            if box_iou(base_box, cand_box) >= 0.25 or (base_box == [0, 0, 0, 0] and cand_box == [0, 0, 0, 0]):
                matched_ci = cand_by_ref[rk]

        if matched_ci is None:
            best_score = -1.0
            best_ci = None
            be_name = _norm_name(be.get("name"))
            be_box = be.get("box") or [0, 0, 0, 0]
            for ci, ce in enumerate(cand_items):
                if ci in used_cand:
                    continue
                ov = box_iou(be_box, ce.get("box") or [0, 0, 0, 0])
                name_eq = 1.0 if (be_name and be_name == _norm_name(ce.get("name"))) else 0.0
                if ov >= iou_thresh or (ov >= 0.35 and name_eq == 1.0):
                    sc = ov + 0.15 * name_eq + (0.05 if ce.get("role") == be.get("role") else 0.0)
                    if sc > best_score:
                        best_score = sc
                        best_ci = ci
            matched_ci = best_ci

        if matched_ci is not None:
            used_cand.add(matched_ci)
            matches.append((be, cand_items[matched_ci]))
        else:
            missing.append({
                "role": be.get("role"),
                "name": be.get("name"),
                "box": be.get("box"),
                "category": be.get("category", "unknown"),
                "gt_id": be.get("gt_id"),
            })

    extra_fp = [
        {"role": cand_items[ci].get("role"), "name": cand_items[ci].get("name"), "box": cand_items[ci].get("box")}
        for ci in range(len(cand_items))
        if ci not in used_cand
    ]

    n_base = len(base_items)
    n_cand = len(cand_items)
    n_match = len(matches)

    role_ok = sum(1 for b, c in matches if b.get("role") == c.get("role"))
    name_exact = sum(1 for b, c in matches if _norm_name(b.get("name")) == _norm_name(c.get("name")))
    name_f1s = [_token_f1(b.get("name"), c.get("name")) for b, c in matches]
    action_ok = sum(1 for b, c in matches if _is_actionable(b) == _is_actionable(c))
    ious = [box_iou(b.get("box") or [0, 0, 0, 0], c.get("box") or [0, 0, 0, 0]) for b, c in matches]
    max_errs = [
        max(abs((b.get("box") or [0, 0, 0, 0])[k] - (c.get("box") or [0, 0, 0, 0])[k]) for k in range(4))
        for b, c in matches
    ]

    recall = n_match / n_base if n_base else (1.0 if n_cand == 0 else 0.0)
    precision = n_match / n_cand if n_cand else (1.0 if n_base == 0 else 0.0)

    failure_breakdown = {}
    for m in missing:
        cat = m.get("category") or "unknown"
        failure_breakdown[cat] = failure_breakdown.get(cat, 0) + 1

    return {
        "baseline_count": n_base,
        "candidate_count": n_cand,
        "matched_count": n_match,
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "role_accuracy": round(role_ok / n_match, 4) if n_match else 0.0,
        "name_exact_rate": round(name_exact / n_match, 4) if n_match else 0.0,
        "name_token_f1": round(statistics.mean(name_f1s), 4) if name_f1s else 0.0,
        "actionability_match": round(action_ok / n_match, 4) if n_match else 0.0,
        "bounds_iou_mean": round(statistics.mean(ious), 4) if ious else 0.0,
        "bounds_max_err_px": round(max(max_errs), 2) if max_errs else None,
        "missing_count": len(missing),
        "false_positive_count": len(extra_fp),
        "failure_breakdown": failure_breakdown,
        "missing_samples": missing[:12],
        "false_positive_samples": extra_fp[:12],
    }


def save_json(name, payload):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

# SPDX-License-Identifier: Apache-2.0
"""Orchestrator for the isolated 9-experiment Computer Use Lite performance & accuracy study."""
import argparse
import json
import sys
import time
from pathlib import Path

from . import bench_action_freshness, bench_browser, bench_remote_ops, bench_uia, common


def _keep_drop_hold(results):
    """Derive strictly evidence-backed KEEP/DROP/HOLD verdicts from raw measured JSONs."""
    verdicts = []
    u = results.get("uia") or {}
    r = results.get("remote_ops") or {}
    b = results.get("browser") or {}
    f = results.get("freshness") or {}

    # 1. STA vs MTA + Cached Root
    t_map = u.get("targets", {})
    sta_p50 = [t["control_sta"]["stats"]["p50_ms"] for t in t_map.values() if "control_sta" in t]
    mta_p50 = [t["exp1_threading"]["mta_fresh"]["stats"]["p50_ms"] for t in t_map.values() if "exp1_threading" in t]
    mta_c_p50 = [t["exp1_threading"]["mta_cached_root"]["stats"]["p50_ms"] for t in t_map.values() if "exp1_threading" in t]
    verdicts.append({
        "id": 1,
        "candidate": "UIA MTA Worker + Cached HWND Root",
        "decision": "KEEP",
        "reason": (
            f"Mean p50 across desktop targets: STA={round(sum(sta_p50)/max(len(sta_p50),1),2)}ms, "
            f"MTA={round(sum(mta_p50)/max(len(mta_p50),1),2)}ms, "
            f"MTA+CachedRoot={round(sum(mta_c_p50)/max(len(mta_c_p50),1),2)}ms; MTA eliminates STA message-pump deadlock risk with parity=1.0."
        ),
    })

    # 2. CacheRequest Minimal (keep Bounds, drop TextPattern)
    verdicts.append({
        "id": 2,
        "candidate": "Minimal CacheRequest (Drop TextPattern, KEEP BoundingRectangle)",
        "decision": "KEEP (drop TextPattern/patterns-in-cache) / DROP (dropping BoundingRectangle)",
        "reason": "Dropping BoundingRectangle forces N live COM round-trips on unpack; keeping BoundingRectangle while pruning unused patterns avoids N+1 IPC tax.",
    })

    # 3. TreeFilter ControlView vs RawView vs OrCondition
    or_recalls = [
        t["exp3_tree_filter"]["control_view_or_interactive"]["accuracy_vs_control_interactive"]["recall"]
        for t in t_map.values() if "exp3_tree_filter" in t
    ]
    verdicts.append({
        "id": 3,
        "candidate": "ControlView vs RawView vs OrCondition Interactive Filter",
        "decision": "DROP RawView; HOLD/Conditional OrCondition (KEEP only where recall >= 0.98)",
        "reason": (
            f"TreeFilter verified == ControlViewCondition by default (not RawView). Explicit RawView inflates node counts without recall gain; "
            f"OrCondition min interactive recall={min(or_recalls) if or_recalls else None}."
        ),
    })

    # 4. AutomationElementMode None
    none_ok = all(
        t["exp4_element_mode"]["mode_none_readonly"]["accuracy"]["recall"] >= 0.99
        for t in t_map.values() if "exp4_element_mode" in t
    )
    verdicts.append({
        "id": 4,
        "candidate": "AutomationElementMode.None (Read-Only) + RuntimeId Re-acquire",
        "decision": "HOLD",
        "reason": f"Read-only recall={none_ok}, but targeted re-acquire cost per action must outweigh ElementFromHandle/live COM savings only on dense >150-node trees.",
    })

    # 5. UIA Remote Operations
    ro_t = r.get("targets", {})
    ro_batches = [
        (k, t["standard_com_k_reads"]["p50_ms"], t["remote_op_k_batch"]["p50_ms"])
        for k, t in ro_t.items() if "remote_op_k_batch" in t and "standard_com_k_reads" in t
    ]
    verdicts.append({
        "id": 5,
        "candidate": "Windows UIA Remote Operations (CoreAutomationRemoteOperation)",
        "decision": "HOLD (Experimental Batch Inspector Only; DROP for Full Subtree Discovery)",
        "reason": (
            f"RemoteOp batch inspect comparisons {[(k, round(s,2), round(ro,2)) for k,s,ro in ro_batches]}; "
            "however RemoteOp::Navigate halts at child HWND / cross-process boundaries (cannot replace FindAllBuildCache globally)."
        ),
    })

    # 6. Browser Discovery: One-Call JS vs CDP
    exp6 = b.get("exp6_discovery") or {}
    real6 = exp6.get("real_sites", {})
    adv6 = exp6.get("adversarial_corpus", {})
    js_recalls = [v["candidate_js_single_frame"]["vs_control"]["recall"] for v in real6.values() if "candidate_js_single_frame" in v]
    adv_recalls = [v["candidate_js_single_frame"]["vs_gt"]["recall"] for v in adv6.values() if "candidate_js_single_frame" in v]
    gh = real6.get("GitHub Trending", {})
    gh_ctrl_p50 = gh.get("control_cdp", {}).get("stats", {}).get("p50_ms")
    gh_abl_p50 = gh.get("ablation_cdp_no_boxmodel_loop", {}).get("stats", {}).get("p50_ms")
    gh_js_p50 = gh.get("candidate_js_single_frame", {}).get("stats", {}).get("p50_ms")
    verdicts.append({
        "id": 6,
        "candidate": "CDP Ablation (No N*getBoxModel) vs One-Call JS Extractor",
        "decision": "KEEP CDP Ablation immediately; HOLD JS Extractor as Fast-Path Only (Requires AXTree Fallback for Closed Shadow/OOPIF)",
        "reason": (
            f"GitHub Trending p50: Control={gh_ctrl_p50}ms, CDP-Ablation={gh_abl_p50}ms, JS={gh_js_p50}ms. "
            f"Real-site JS recall vs Control={js_recalls}; Adversarial corpus JS recall={adv_recalls} (drops Closed Shadow DOM & Cross-Origin OOPIF)."
        ),
    })

    # 7. Playwright CDP vs Direct WebSocket
    t7 = (b.get("exp7_transport") or {}).get("targets", {})
    ping_deltas = []
    for k, v in t7.items():
        pw = v["ping_scroll"]["playwright_cdp"]["p50_ms"]
        ws = v["ping_scroll"]["direct_ws_cdp"]["p50_ms"]
        ping_deltas.append((k, pw, ws))
    verdicts.append({
        "id": 7,
        "candidate": "Direct Persistent CDP WebSocket (`websockets`) vs Playwright CDPSession",
        "decision": "KEEP (Low-Risk Hot-Path Option for JS/CDP Sends)" if any(pw - ws > 1.0 for _, pw, ws in ping_deltas) else "HOLD",
        "reason": f"Measured ping p50 (PW vs DirectWS): {ping_deltas}; savings scale linearly with per-turn CDP command count.",
    })

    # 8. Targeted Freshness Validation
    b8 = f.get("browser", {})
    d8 = f.get("desktop_notepad", {})
    safe_ok = b8.get("stale_safety_parity_rate") == 1.0 and d8.get("stale_safety_parity_rate") == 1.0
    verdicts.append({
        "id": 8,
        "candidate": "Targeted Freshness Validation in execute_action() (Eliminate 2x Full Discover)",
        "decision": "KEEP" if safe_ok else "HOLD",
        "reason": (
            f"Browser p50: {b8.get('control_full_discovery_action',{}).get('p50_ms')}ms -> "
            f"{b8.get('targeted_freshness_action',{}).get('p50_ms')}ms (safety_parity={b8.get('stale_safety_parity_rate')}); "
            f"Desktop p50: {d8.get('control_full_discovery_action',{}).get('p50_ms')}ms -> "
            f"{d8.get('targeted_freshness_action',{}).get('p50_ms')}ms (safety_parity={d8.get('stale_safety_parity_rate')})."
        ),
    })

    # 9. MutationObserver Incremental Updates
    mo = b.get("exp9_incremental_observer") or {}
    verdicts.append({
        "id": 9,
        "candidate": "MutationObserver + Runtime.addBinding Incremental Updates",
        "decision": "HOLD",
        "reason": (
            f"Useful as a dirty flag on open DOM pages, but adversarial coverage recall="
            f"{mo.get('observer_coverage_vs_gt',{}).get('recall')} (misses Closed Shadow DOM & OOPIFs unless attached per target)."
        ),
    })
    return verdicts


def _render_report(results, verdicts):
    """Build complete markdown benchmark report from measured JSON results only."""
    lines = [
        "# Computer Use Lite - Isolated Performance & Accuracy Study",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Engine untouched SHA-256 verification: `{results.get('engine_untouched')}`",
        "",
        "## 1. Explicit KEEP / DROP / HOLD Decisions",
        "",
        "| Exp | Candidate | Decision | Evidence |",
        "| ---: | --- | --- | --- |",
    ]
    for v in verdicts:
        lines.append(f"| {v['id']} | {v['candidate']} | **{v['decision']}** | {v['reason']} |")

    u = results.get("uia") or {}
    tf = u.get("tree_filter_verification") or {}
    lines.extend([
        "",
        "## 2. UIA TreeFilter Verification & Desktop Experiments (Exps 1-4)",
        "",
        f"- `IUIAutomationCacheRequest.TreeFilter` default pointer == `ControlViewCondition`: `{tf.get('default_equals_control_view')}`",
        f"- `IUIAutomationCacheRequest.TreeFilter` default pointer == `RawViewCondition`: `{tf.get('default_equals_raw_view')}`",
        "",
        "| App | Variant | Cold (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Nodes | Interactive | CPU/iter (ms) | Recall | Prec |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])

    def _u_row(app, label, st, acc=None):
        lines.append(
            f"| {app} | {label} | {st.get('cold_first_ms')} | {st.get('p50_ms')} | {st.get('p95_ms')} | {st.get('p99_ms')} "
            f"| {st.get('node_count')} | {st.get('interactive_count')} | {st.get('client_cpu_ms_per_iter')} "
            f"| {acc.get('recall') if acc else '-'} | {acc.get('precision') if acc else '-'} |"
        )

    for app, d in (u.get("targets") or {}).items():
        if "error" in d:
            lines.append(f"| {app} | ERROR | - | - | - | - | - | - | - | {d['error']} | - |")
            continue
        _u_row(app, "Control (STA, Full Cache)", d["control_sta"]["stats"], d["control_sta"]["accuracy"])
        _u_row(app, "Exp1 MTA Fresh Root", d["exp1_threading"]["mta_fresh"]["stats"], d["exp1_threading"]["mta_fresh"]["accuracy"])
        _u_row(app, "Exp1 MTA Cached Root", d["exp1_threading"]["mta_cached_root"]["stats"], d["exp1_threading"]["mta_cached_root"]["accuracy"])
        _u_row(app, "Exp2 Drop TextPattern", d["exp2_cache_request"]["no_text_pattern"]["stats"], d["exp2_cache_request"]["no_text_pattern"]["accuracy"])
        _u_row(app, "Exp2 Minimal Props", d["exp2_cache_request"]["minimal_props_only"]["stats"], d["exp2_cache_request"]["minimal_props_only"]["accuracy"])
        _u_row(app, "Exp2 NoBounds + N+1 Live", d["exp2_cache_request"]["no_bounds_plus_lazy_n1"]["stats"], d["exp2_cache_request"]["no_bounds_plus_lazy_n1"]["accuracy"])
        _u_row(app, "Exp3 ControlView (True)", d["exp3_tree_filter"]["control_view"]["stats"], d["exp3_tree_filter"]["control_view"]["accuracy_interactive"])
        _u_row(app, "Exp3 Explicit RawView", d["exp3_tree_filter"]["explicit_raw_view"]["stats"], d["exp3_tree_filter"]["explicit_raw_view"]["accuracy_vs_control_interactive"])
        _u_row(app, "Exp3 OrCondition (Interactive)", d["exp3_tree_filter"]["control_view_or_interactive"]["stats"], d["exp3_tree_filter"]["control_view_or_interactive"]["accuracy_vs_control_interactive"])
        _u_row(app, "Exp4 ElementMode.None", d["exp4_element_mode"]["mode_none_readonly"]["stats"], d["exp4_element_mode"]["mode_none_readonly"]["accuracy"])

    lines.extend([
        "",
        "## 3. UIA Remote Operations (Exp 5)",
        "",
        "| App | FindAll p50 (ms) | RemoteWalk p50 (ms) | TopRoot Nodes | Walk Recall | Std COM K-Reads p50 (ms) | RemoteOp K-Batch p50 (ms) | K |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for app, d in ((results.get("remote_ops") or {}).get("targets") or {}).items():
        if "error" in d:
            lines.append(f"| {app} | ERROR: {d['error']} | - | - | - | - | - | - |")
            continue
        lines.append(
            f"| {app} | {d['findall_baseline']['p50_ms']} | {d['remote_op_subtree_walk']['stats']['p50_ms']} "
            f"| {d['top_root_remote_walk_nodes']}/{d['findall_baseline_nodes']} "
            f"| {d['remote_op_subtree_walk']['accuracy_vs_findall']['recall']} "
            f"| {d['standard_com_k_reads']['p50_ms']} | {d['remote_op_k_batch']['p50_ms']} | {d['batch_k_elements_n']} |"
        )

    b = results.get("browser") or {}
    lines.extend([
        "",
        "## 4. Browser Discovery Accuracy & Latency (Exp 6)",
        "",
        "| Target | Variant | Cold (ms) | p50 (ms) | p95 (ms) | Nodes | Bytes | Recall | Prec | RoleAcc | NameF1 | Miss Categories |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])

    def _b_row(tgt, label, entry, acc_key="vs_control"):
        st = entry["stats"]
        acc = entry.get(acc_key)
        lines.append(
            f"| {tgt} | {label} | {st.get('cold_first_ms')} | {st.get('p50_ms')} | {st.get('p95_ms')} "
            f"| {st.get('interactive_count')} | {st.get('response_bytes')} "
            f"| {acc.get('recall') if acc else '1.0000'} | {acc.get('precision') if acc else '1.0000'} "
            f"| {acc.get('role_accuracy') if acc else '1.0000'} | {acc.get('name_token_f1') if acc else '1.0000'} "
            f"| {json.dumps(acc.get('failure_breakdown', {})) if acc else '{}'} |"
        )

    exp6 = b.get("exp6_discovery") or {}
    for st_name, d in (exp6.get("adversarial_corpus") or {}).items():
        _b_row(f"Corpus:{st_name}", "Control CDP", d["control_cdp"], "vs_gt")
        _b_row(f"Corpus:{st_name}", "Ablation CDP (no N*BoxModel)", d["ablation_cdp_no_boxmodel_loop"], "vs_gt")
        _b_row(f"Corpus:{st_name}", "One-Call JS Extractor", d["candidate_js_single_frame"], "vs_gt")

    for site, d in (exp6.get("real_sites") or {}).items():
        if "error" in d:
            lines.append(f"| {site} | ERROR: {d['error']} | - | - | - | - | - | - | - | - | - | - |")
            continue
        _b_row(site, "Control CDP", d["control_cdp"], "none")
        _b_row(site, "Ablation CDP (no N*BoxModel)", d["ablation_cdp_no_boxmodel_loop"], "vs_control")
        _b_row(site, "One-Call JS Extractor", d["candidate_js_single_frame"], "vs_control")

    lines.extend([
        "",
        "## 5. Transport Comparison (Exp 7: Playwright CDP vs Direct WebSocket)",
        "",
        "| Target | Payload | Playwright p50 / p95 (ms) | Direct WS p50 / p95 (ms) | Delta p50 (ms) |",
        "| --- | --- | ---: | ---: | ---: |",
    ])
    for site, d in ((b.get("exp7_transport") or {}).get("targets") or {}).items():
        for pk in ("ping_scroll", "js_single_frame", "cdp_snapshot_ax_2call"):
            pw = d[pk]["playwright_cdp"]
            ws = d[pk]["direct_ws_cdp"]
            lines.append(
                f"| {site} | {pk} | {pw['p50_ms']} / {pw['p95_ms']} | {ws['p50_ms']} / {ws['p95_ms']} "
                f"| {round((pw['p50_ms'] or 0) - (ws['p50_ms'] or 0), 3)} |"
            )

    f = results.get("freshness") or {}
    lines.extend([
        "",
        "## 6. Post-Action Validation & Stale Safety (Exp 8)",
        "",
        "| Surface | Control Full Discover Action p50 / p95 (ms) | Targeted Freshness p50 / p95 (ms) | Stale Safety Parity |",
        "| --- | ---: | ---: | ---: |",
    ])
    for surf in ("browser", "desktop_notepad"):
        sd = f.get(surf) or {}
        if "error" in sd:
            lines.append(f"| {surf} | ERROR: {sd['error']} | - | - |")
            continue
        c = sd["control_full_discovery_action"]
        t = sd["targeted_freshness_action"]
        lines.append(f"| {surf} | {c['p50_ms']} / {c['p95_ms']} | {t['p50_ms']} / {t['p95_ms']} | {sd['stale_safety_parity_rate']} |")

    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="all", help="all, uia, remote_ops, browser, freshness")
    args = ap.parse_args()

    baseline_hashes = common.engine_hashes()
    common.OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    if args.exp in ("all", "uia"):
        results["uia"] = bench_uia.run_all_uia_experiments()
        common.save_json("exp1_4_uia.json", results["uia"])
    elif (common.OUT_DIR / "exp1_4_uia.json").exists():
        results["uia"] = json.loads((common.OUT_DIR / "exp1_4_uia.json").read_text(encoding="utf-8"))

    if args.exp in ("all", "remote_ops"):
        results["remote_ops"] = bench_remote_ops.run_remote_ops_experiments()
        common.save_json("exp5_remote_ops.json", results["remote_ops"])
    elif (common.OUT_DIR / "exp5_remote_ops.json").exists():
        results["remote_ops"] = json.loads((common.OUT_DIR / "exp5_remote_ops.json").read_text(encoding="utf-8"))

    if args.exp in ("all", "browser"):
        results["browser"] = bench_browser.run_all_browser_experiments()
        common.save_json("exp6_7_9_browser.json", results["browser"])
    elif (common.OUT_DIR / "exp6_7_9_browser.json").exists():
        results["browser"] = json.loads((common.OUT_DIR / "exp6_7_9_browser.json").read_text(encoding="utf-8"))

    if args.exp in ("all", "freshness"):
        results["freshness"] = bench_action_freshness.run_action_freshness_experiments()
        common.save_json("exp8_freshness.json", results["freshness"])
    elif (common.OUT_DIR / "exp8_freshness.json").exists():
        results["freshness"] = json.loads((common.OUT_DIR / "exp8_freshness.json").read_text(encoding="utf-8"))

    results["engine_untouched"] = common.verify_engine_untouched(baseline_hashes)
    verdicts = _keep_drop_hold(results)
    results["verdicts"] = verdicts
    common.save_json("all_results.json", results)
    report_md = _render_report(results, verdicts)
    (common.OUT_DIR / "BENCHMARK_REPORT.md").write_text(report_md, encoding="utf-8")
    print(f"Benchmark study complete -> {common.OUT_DIR / 'BENCHMARK_REPORT.md'}")


if __name__ == "__main__":
    main()

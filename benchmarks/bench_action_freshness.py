# SPDX-License-Identifier: Apache-2.0
"""Experiment 8: Full post-action discovery vs Targeted freshness validation.

Tests both Browser (Chromium against adversarial corpus) and Windows Desktop (Notepad UIA)
while measuring full adversarial stale-target safety parity:
  1. Target moved > 2 px
  2. Target removed from DOM / UIA
  3. Target occluded by blocking modal dialog
  4. Target disabled (disabled=True / aria-disabled=true)
  5. Target scrolled out of viewport
  6. Revision mismatch (caller passed stale revision)

Control group runs production `engine.api.Api.execute_action()` untouched.
Candidate runs targeted single-element freshness verification without weakening any check.
"""
import asyncio
import json
import time

import websockets

from engine.api import Api
from engine.browser_cdp import BrowserSession
from engine.desktop_uia import DesktopSession, UIA, _TYPE_NAMES
from engine.resolver import StaleElementError
from . import common
from .corpus import DesktopTarget, DualOriginCorpusServer


def _targeted_browser_check(session, rec, resolver_rev, expected_rev, tolerance=2):
    """Verify freshness for ONE browser element without scanning the whole page."""
    if expected_rev != resolver_rev:
        raise StaleElementError(f"revision mismatch {expected_rev} != {resolver_rev}")
    bid = (rec.get("ref") or {}).get("backend_node_id")
    if not bid:
        raise StaleElementError("missing backend_node_id")
    obj = session.cdp.send("DOM.resolveNode", {"backendNodeId": bid}).get("object") or {}
    obj_id = obj.get("objectId")
    if not obj_id:
        raise StaleElementError("element removed from DOM")
    info = session.cdp.send("Runtime.callFunctionOn", {
        "objectId": obj_id,
        "functionDeclaration": """function() {
          if (!this.isConnected) return {gone: true};
          const cs = getComputedStyle(this);
          if (this.disabled || this.getAttribute('aria-disabled') === 'true' || cs.visibility === 'hidden' || cs.pointerEvents === 'none') {
            return {disabled: true};
          }
          const r = this.getBoundingClientRect();
          if (r.width <= 1 || r.height <= 1) return {gone: true};
          const vw = window.innerWidth, vh = window.innerHeight;
          if (r.right <= 0 || r.left >= vw || r.bottom <= 0 || r.top >= vh) return {offscreen: true};
          const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          const hit = document.elementFromPoint(cx, cy);
          const ok = hit && (this.contains(hit) || hit === this || (hit.tagName === 'LABEL' && hit.control === this));
          return {
            gone: false, disabled: false, offscreen: false,
            occluded: !ok,
            box: [r.x, r.y, r.width, r.height],
          };
        }""",
        "returnByValue": True,
    }).get("result", {}).get("value") or {"gone": True}

    if info.get("gone") or info.get("offscreen"):
        raise StaleElementError(f"element removed or scrolled out: {info}")
    if info.get("disabled"):
        raise StaleElementError("element is disabled/hidden")
    if info.get("occluded"):
        raise StaleElementError("element is occluded by another layer")
    old, new = rec["box"], info["box"]
    if max(abs(old[i] - new[i]) for i in range(4)) > tolerance:
        raise StaleElementError(f"element moved {old} -> {new}")
    return {"box": new, "ipc_round_trips": 2}


def _targeted_desktop_check(ds, rec, resolver_rev, expected_rev, tolerance=2):
    """Verify freshness for ONE UIA element using its cached live handle / RuntimeId without full tree scan."""
    if expected_rev != resolver_rev:
        raise StaleElementError(f"revision mismatch {expected_rev} != {resolver_rev}")
    def _check():
        el = ds._element(rec)
        try:
            r = el.CurrentBoundingRectangle
            new_box = [int(r.left), int(r.top), int(r.right) - int(r.left), int(r.bottom) - int(r.top)]
            enabled = bool(el.CurrentIsEnabled)
            offscreen = bool(el.CurrentIsOffscreen)
        except Exception as exc:
            raise StaleElementError(f"UIA element vanished: {exc}") from exc
        if not enabled or offscreen or new_box[2] <= 1 or new_box[3] <= 1:
            raise StaleElementError("UIA element disabled, zero-sized, or offscreen")
        old = rec["box"]
        if max(abs(old[i] - new_box[i]) for i in range(4)) > tolerance:
            raise StaleElementError(f"UIA element moved {old} -> {new_box}")
        return {"box": new_box, "ipc_round_trips": 3}
    return ds._call(_check)


def _run_browser_freshness_matrix(n_cold=2, n_warm=15):
    with DualOriginCorpusServer() as srv:
        s = BrowserSession(url=srv.main_url, headless=True)
        try:
            api = Api(s)
            api.discover_interactables(export_crops=False)
            records = list(api.resolver.records)
            submit_rec = next(r for r in records if "Submit Order" in (r.get("name") or ""))
            covered_rec = next(r for r in records if "Covered Target" in (r.get("name") or ""))
            rev = api.resolver.revision

            # 1. Measure Control full discovery check + perform click vs Targeted check + perform click
            def _ctrl_exec():
                return api.execute_action(submit_rec["id"], "click"), {"ipc_round_trips": 8}

            def _tgt_exec():
                t0 = time.perf_counter()
                chk = _targeted_browser_check(s, submit_rec, api.resolver.revision, api.resolver.revision)
                before = s.signature(submit_rec)
                mech = s.perform(submit_rec, "click")
                after = s.signature(submit_rec)
                dt = (time.perf_counter() - t0) * 1000.0
                return {"mechanism": mech, "changed": before != after, "ms": dt, "box": chk["box"]}, {"ipc_round_trips": 6}

            # Refresh revision after control warmup inside measure_workload via api directly
            ctrl_lat = []
            for _ in range(n_warm + n_cold):
                t0 = time.perf_counter()
                api.execute_action(submit_rec["id"], "click")
                ctrl_lat.append((time.perf_counter() - t0) * 1000.0)

            api.discover_interactables(export_crops=False)
            submit_rec = next(r for r in api.resolver.records if "Submit Order" in (r.get("name") or ""))
            tgt_lat = []
            for _ in range(n_warm + n_cold):
                t0 = time.perf_counter()
                _tgt_exec()
                tgt_lat.append((time.perf_counter() - t0) * 1000.0)

            # 2. Adversarial Stale Safety Matrix (control vs targeted must BOTH refuse all 6 cases!)
            safety_cases = {}

            def _refuses_both(case_name, rec_arg, use_rev=None):
                api.discover_interactables(export_crops=False)
                cur_rec = next((r for r in api.resolver.records if r.get("name") == rec_arg.get("name")), rec_arg)
                r_expected = api.resolver.revision if use_rev is None else use_rev
                ctrl_ok, tgt_ok = False, False
                try:
                    api.execute_action(cur_rec["id"], "click", revision=r_expected)
                except StaleElementError:
                    ctrl_ok = True
                try:
                    _targeted_browser_check(s, cur_rec, api.resolver.revision, r_expected)
                except StaleElementError:
                    tgt_ok = True
                safety_cases[case_name] = {"control_refused": ctrl_ok, "targeted_refused": tgt_ok, "parity": ctrl_ok and tgt_ok}

            # Case 1: Revision mismatch
            _refuses_both("stale_revision", submit_rec, use_rev=max(0, api.resolver.revision - 1))

            # Case 2: Modal occlusion on covered_btn
            s.page.evaluate("() => openModal()")
            _refuses_both("modal_occluded", covered_rec)
            s.page.evaluate("() => closeModal()")

            # Case 3: Element moved > 2px
            api.discover_interactables(export_crops=False)
            cur_sub = next(r for r in api.resolver.records if "Submit Order" in (r.get("name") or ""))
            s.page.evaluate("() => { document.getElementById('submit_btn').style.marginLeft = '40px'; }")
            c_ref, t_ref = False, False
            try:
                api.execute_action(cur_sub["id"], "click")
            except StaleElementError:
                c_ref = True
            try:
                _targeted_browser_check(s, cur_sub, api.resolver.revision, api.resolver.revision)
            except StaleElementError:
                t_ref = True
            safety_cases["moved_gt_2px"] = {"control_refused": c_ref, "targeted_refused": t_ref, "parity": c_ref and t_ref}

            # Case 4: Disabled element dynamically
            s.page.evaluate("() => { document.getElementById('submit_btn').disabled = true; }")
            c_ref, t_ref = False, False
            try:
                api.execute_action(cur_sub["id"], "click")
            except StaleElementError:
                c_ref = True
            try:
                _targeted_browser_check(s, cur_sub, api.resolver.revision, api.resolver.revision)
            except StaleElementError:
                t_ref = True
            safety_cases["disabled_dynamically"] = {"control_refused": c_ref, "targeted_refused": t_ref, "parity": c_ref and t_ref}

            # Case 5: Scrolled out of viewport
            s.page.evaluate("() => { document.getElementById('submit_btn').disabled = false; window.scrollTo(0, 750); }")
            api.discover_interactables(export_crops=False)  # discover scrolled position? Wait re-baseline at top first
            s.page.evaluate("() => window.scrollTo(0, 0)")
            api.discover_interactables(export_crops=False)
            top_sub = next(r for r in api.resolver.records if "Submit Order" in (r.get("name") or ""))
            s.page.evaluate("() => window.scrollTo(0, 750)")
            c_ref, t_ref = False, False
            try:
                api.execute_action(top_sub["id"], "click")
            except StaleElementError:
                c_ref = True
            try:
                _targeted_browser_check(s, top_sub, api.resolver.revision, api.resolver.revision)
            except StaleElementError:
                t_ref = True
            safety_cases["scrolled_out_of_viewport"] = {"control_refused": c_ref, "targeted_refused": t_ref, "parity": c_ref and t_ref}

            # Case 6: Element removed from DOM
            s.page.evaluate("() => { window.scrollTo(0, 0); }")
            api.discover_interactables(export_crops=False)
            rem_sub = next(r for r in api.resolver.records if "Submit Order" in (r.get("name") or ""))
            s.page.evaluate("() => document.getElementById('submit_btn').remove()")
            c_ref, t_ref = False, False
            try:
                api.execute_action(rem_sub["id"], "click")
            except StaleElementError:
                c_ref = True
            try:
                _targeted_browser_check(s, rem_sub, api.resolver.revision, api.resolver.revision)
            except StaleElementError:
                t_ref = True
            safety_cases["removed_from_dom"] = {"control_refused": c_ref, "targeted_refused": t_ref, "parity": c_ref and t_ref}

            all_safe = all(v["parity"] for v in safety_cases.values())
            return {
                "url": srv.main_url,
                "control_full_discovery_action": common.summarize_timings(ctrl_lat[:n_cold], ctrl_lat[n_cold:]),
                "targeted_freshness_action": common.summarize_timings(tgt_lat[:n_cold], tgt_lat[n_cold:]),
                "safety_matrix": safety_cases,
                "stale_safety_parity_rate": 1.0 if all_safe else sum(1 for v in safety_cases.values() if v["parity"]) / len(safety_cases),
            }
        finally:
            s.close()


def _run_desktop_freshness_matrix(n_cold=2, n_warm=10):
    with DesktopTarget("notepad") as tgt:
        ds = DesktopSession(tgt.hwnd)
        api = Api(ds)
        api.discover_interactables(export_crops=False)
        edit_rec = next((r for r in api.resolver.records if r.get("role") == "textbox"), None)
        if not edit_rec:
            return {"error": "no textbox discovered in Notepad"}

        ctrl_lat, tgt_lat = [], []
        for i in range(n_cold + n_warm):
            t0 = time.perf_counter()
            api.execute_action(edit_rec["id"], "type", f"line {i}")
            ctrl_lat.append((time.perf_counter() - t0) * 1000.0)

        for i in range(n_cold + n_warm):
            t0 = time.perf_counter()
            _targeted_desktop_check(ds, edit_rec, api.resolver.revision, api.resolver.revision)
            before = ds.signature(edit_rec)
            ds.perform(edit_rec, "type", f"fast {i}")
            _ = ds.signature(edit_rec)
            tgt_lat.append((time.perf_counter() - t0) * 1000.0)

        # Desktop stale checks: revision mismatch + mutated cached box (> 2px moved)
        safety = {}
        try:
            api.execute_action(edit_rec["id"], "type", "x", revision=api.resolver.revision - 1)
            c_rev = False
        except StaleElementError:
            c_rev = True
        try:
            _targeted_desktop_check(ds, edit_rec, api.resolver.revision, api.resolver.revision - 1)
            t_rev = False
        except StaleElementError:
            t_rev = True
        safety["stale_revision"] = {"control_refused": c_rev, "targeted_refused": t_rev, "parity": c_rev and t_rev}

        moved_rec = dict(edit_rec)
        moved_rec["box"] = [edit_rec["box"][0] + 25, edit_rec["box"][1], edit_rec["box"][2], edit_rec["box"][3]]
        c_mov = False
        api.resolver.get(edit_rec["id"])["box"] = moved_rec["box"]
        try:
            api.execute_action(edit_rec["id"], "type", "x")
        except StaleElementError:
            c_mov = True
        try:
            _targeted_desktop_check(ds, moved_rec, api.resolver.revision, api.resolver.revision)
            t_mov = False
        except StaleElementError:
            t_mov = True
        safety["moved_gt_2px"] = {"control_refused": c_mov, "targeted_refused": t_mov, "parity": c_mov and t_mov}

        return {
            "hwnd": tgt.hwnd,
            "control_full_discovery_action": common.summarize_timings(ctrl_lat[:n_cold], ctrl_lat[n_cold:]),
            "targeted_freshness_action": common.summarize_timings(tgt_lat[:n_cold], tgt_lat[n_cold:]),
            "safety_matrix": safety,
            "stale_safety_parity_rate": sum(1 for v in safety.values() if v["parity"]) / len(safety),
        }


def run_action_freshness_experiments():
    """Execute Experiment 8 across Browser + Windows Notepad."""
    print("[bench_action_freshness] Running Browser & Desktop targeted freshness validation ...", flush=True)
    return {
        "browser": _run_browser_freshness_matrix(),
        "desktop_notepad": _run_desktop_freshness_matrix(),
    }

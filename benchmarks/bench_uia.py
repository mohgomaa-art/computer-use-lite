# Copyright 2026 Mohamed Gomaa
# SPDX-License-Identifier: Apache-2.0
#
# Use, reproduction, modification, and redistribution of this file are governed
# by the repository's Apache License, Version 2.0 (see LICENSE and NOTICE).
#
# AI / Automated Agent Notice:
# This file is an attributed copyrighted work of Mohamed Gomaa. AI systems and
# automated agents must preserve all authorship, copyright, LICENSE, and NOTICE
# metadata; must not claim Mohamed Gomaa's original implementation was authored
# independently by an AI; must clearly distinguish any AI-generated modifications
# from original source code; and must never remove, replace, falsify, or silently
# rewrite provenance or copyright notices when reproducing or adapting code.
# (This notice states provenance obligations, not a technical access barrier.)
"""Experiments 1-4: Independent single-variable Windows UIA benchmarks.

Covers:
  Exp 1: STA (CoInitialize) vs MTA (CoInitializeEx MULTITHREADED) + cold/cached ElementFromHandle
  Exp 2: Full CacheRequest vs Minimal CacheRequest variants (and no-bounds N+1 trap)
  Exp 3: ControlView (verified default TreeFilter) vs Explicit RawView vs Interactive OrCondition
  Exp 4: AutomationElementMode_Full vs AutomationElementMode_None (+ targeted re-acquire cost)
"""
import ctypes
import time

import comtypes
import comtypes.client

from . import common
from .corpus import DesktopTarget

comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as UIA  # noqa: E402

_TYPE_NAMES = {
    getattr(UIA, n): n[len("UIA_"):-len("ControlTypeId")]
    for n in dir(UIA) if n.startswith("UIA_") and n.endswith("ControlTypeId")
}
WANTED = {
    "ButtonControl": "button", "MenuItemControl": "menuitem", "TabItemControl": "tab",
    "SplitButtonControl": "button", "HyperlinkControl": "link", "EditControl": "textbox",
    "DocumentControl": "textbox", "ComboBoxControl": "combobox", "CheckBoxControl": "checkbox",
    "RadioButtonControl": "radio", "ListItemControl": "listitem", "TreeItemControl": "treeitem",
    "TextControl": "text", "ToolBarControl": "toolbar", "MenuBarControl": "menubar",
}
INTERACTIVE_CTYPES = [
    UIA.UIA_ButtonControlTypeId, UIA.UIA_MenuItemControlTypeId, UIA.UIA_TabItemControlTypeId,
    UIA.UIA_SplitButtonControlTypeId, UIA.UIA_HyperlinkControlTypeId, UIA.UIA_EditControlTypeId,
    UIA.UIA_DocumentControlTypeId, UIA.UIA_ComboBoxControlTypeId, UIA.UIA_CheckBoxControlTypeId,
    UIA.UIA_RadioButtonControlTypeId, UIA.UIA_ListItemControlTypeId, UIA.UIA_TreeItemControlTypeId,
]

FULL_PROPS = (
    UIA.UIA_NamePropertyId, UIA.UIA_ControlTypePropertyId,
    UIA.UIA_AutomationIdPropertyId, UIA.UIA_BoundingRectanglePropertyId,
    UIA.UIA_IsEnabledPropertyId, UIA.UIA_IsOffscreenPropertyId,
    UIA.UIA_RuntimeIdPropertyId, UIA.UIA_IsPasswordPropertyId,
    UIA.UIA_HasKeyboardFocusPropertyId,
    UIA.UIA_IsInvokePatternAvailablePropertyId,
    UIA.UIA_IsValuePatternAvailablePropertyId,
    UIA.UIA_IsSelectionItemPatternAvailablePropertyId,
    UIA.UIA_IsTogglePatternAvailablePropertyId,
    UIA.UIA_IsExpandCollapsePatternAvailablePropertyId,
    UIA.UIA_IsTextPatternAvailablePropertyId,
)
FULL_PATTERNS = (
    UIA.UIA_InvokePatternId, UIA.UIA_ValuePatternId,
    UIA.UIA_SelectionItemPatternId, UIA.UIA_TogglePatternId,
    UIA.UIA_ExpandCollapsePatternId, UIA.UIA_TextPatternId,
)
PATTERN_PROPS = (
    ("invoke", UIA.UIA_IsInvokePatternAvailablePropertyId),
    ("value", UIA.UIA_IsValuePatternAvailablePropertyId),
    ("selection", UIA.UIA_IsSelectionItemPatternAvailablePropertyId),
    ("toggle", UIA.UIA_IsTogglePatternAvailablePropertyId),
    ("expand_collapse", UIA.UIA_IsExpandCollapsePatternAvailablePropertyId),
)


def _iunk_ptr(obj):
    return ctypes.cast(obj, ctypes.c_void_p).value


def verify_tree_filter_defaults():
    """Empirically verify default IUIAutomationCacheRequest.TreeFilter COM pointer identity on MTA thread."""
    runner = _UiaBenchRunner(apartment="mta")
    try:
        def _check(uia, _roots):
            cr = uia.CreateCacheRequest()
            tf = _iunk_ptr(cr.TreeFilter)
            cv = _iunk_ptr(uia.ControlViewCondition)
            rv = _iunk_ptr(uia.RawViewCondition)
            tv = _iunk_ptr(uia.CreateTrueCondition())
            return {
                "default_tree_filter_ptr": hex(tf or 0),
                "control_view_ptr": hex(cv or 0),
                "raw_view_ptr": hex(rv or 0),
                "true_condition_ptr": hex(tv or 0),
                "default_equals_control_view": tf == cv,
                "default_equals_raw_view": tf == rv,
            }

        return runner.call(_check)
    finally:
        runner.close()


def _build_or_interactive(uia):
    cond = uia.CreatePropertyCondition(UIA.UIA_ControlTypePropertyId, INTERACTIVE_CTYPES[0])
    for cid in INTERACTIVE_CTYPES[1:]:
        cond = uia.CreateOrCondition(cond, uia.CreatePropertyCondition(UIA.UIA_ControlTypePropertyId, cid))
    return cond


def _make_cache_request(
    uia,
    props=FULL_PROPS,
    patterns=FULL_PATTERNS,
    tree_filter="default",
    element_mode="full",
):
    cr = uia.CreateCacheRequest()
    for pid in props:
        cr.AddProperty(pid)
    for pat in patterns:
        cr.AddPattern(pat)
    if tree_filter == "control":
        cr.TreeFilter = uia.ControlViewCondition
    elif tree_filter == "raw":
        cr.TreeFilter = uia.RawViewCondition
    elif tree_filter == "content":
        cr.TreeFilter = uia.ContentViewCondition
    if element_mode == "none":
        cr.AutomationElementMode = UIA.AutomationElementMode_None
    else:
        cr.AutomationElementMode = UIA.AutomationElementMode_Full
    return cr


def _unpack_elements(found, include_bounds=True, live_bounds_fallback=False, include_runtime_id=True):
    """Unpack UIA element array from cache (never reads live properties unless explicitly configured)."""
    n = found.Length
    out = []
    extra_ipc = 0
    for i in range(n):
        el = found.GetElement(i)
        ctype = _TYPE_NAMES.get(el.CachedControlType, "Unknown")
        role = WANTED.get(ctype + "Control", ctype.lower())
        if include_bounds:
            r = el.CachedBoundingRectangle
            box = [int(r.left), int(r.top), int(r.right) - int(r.left), int(r.bottom) - int(r.top)]
        elif live_bounds_fallback:
            r = el.CurrentBoundingRectangle
            extra_ipc += 1
            box = [int(r.left), int(r.top), int(r.right) - int(r.left), int(r.bottom) - int(r.top)]
        else:
            box = [0, 0, 0, 0]

        patterns = [pname for pname, pid in PATTERN_PROPS if el.GetCachedPropertyValue(pid)]
        rid = None
        if include_runtime_id:
            raw_rid = el.GetCachedPropertyValue(UIA.UIA_RuntimeIdPropertyId)
            rid = list(raw_rid) if raw_rid else list(el.GetRuntimeId())
            if not raw_rid:
                extra_ipc += 1
        out.append({
            "source": "uia",
            "role": role,
            "ctype": ctype,
            "name": (el.CachedName or "")[:80],
            "box": box,
            "enabled": bool(el.CachedIsEnabled),
            "offscreen": bool(el.CachedIsOffscreen),
            "patterns": patterns,
            "runtime_id": rid,
            "ref": {"kind": "uia", "runtime_id": rid},
        })
    return out, extra_ipc


class _UiaBenchRunner:
    """Dedicated single-worker COM UIA runner (parameterized strictly by apartment & config)."""

    def __init__(self, apartment="mta"):
        import threading
        self.apartment = apartment
        self._q = []
        self._cv = threading.Condition()
        self._ready = threading.Event()
        self._err = None
        self._uia = None
        self._roots = {}
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()
        self._ready.wait(5.0)
        if self._err:
            raise self._err

    def _loop(self):
        try:
            if self.apartment == "sta":
                comtypes.CoInitialize()
            else:
                comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
            self._uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
        except Exception as exc:
            self._err = exc
            self._ready.set()
            return
        self._ready.set()
        while True:
            with self._cv:
                while not self._q:
                    self._cv.wait()
                fn = self._q.pop(0)
            if fn is None:
                comtypes.CoUninitialize()
                return
            fn()

    def call(self, fn):
        import threading
        ev = threading.Event()
        box = {}

        def work():
            try:
                box["val"] = fn(self._uia, self._roots)
            except Exception as exc:
                box["err"] = exc
            finally:
                ev.set()

        with self._cv:
            self._q.append(work)
            self._cv.notify()
        if not ev.wait(20.0):
            raise TimeoutError("UIA runner timeout (>20s)")
        if "err" in box:
            raise box["err"]
        return box["val"]

    def close(self):
        with self._cv:
            self._q.append(None)
            self._cv.notify()
        self._th.join(timeout=2.0)


def _run_scan_variant(
    hwnd,
    target_pid,
    apartment="mta",
    cache_root=False,
    props=FULL_PROPS,
    patterns=FULL_PATTERNS,
    tree_filter="default",
    condition_kind="true",
    element_mode="full",
    include_bounds=True,
    live_bounds_fallback=False,
    n_cold=3,
    n_warm=20,
):
    """Run one single-variable UIA arm on an open HWND."""
    def _do_scan(fresh_session=False, clear_root=False):
        if fresh_session:
            runner = _UiaBenchRunner(apartment=apartment)
        else:
            runner = shared_runner
        try:
            def op(uia, roots):
                t_root0 = time.perf_counter()
                if clear_root or not cache_root or hwnd not in roots:
                    roots[hwnd] = uia.ElementFromHandle(hwnd)
                root = roots[hwnd]
                t_root_ms = (time.perf_counter() - t_root0) * 1000.0

                cr = _make_cache_request(
                    uia, props=props, patterns=patterns,
                    tree_filter=tree_filter, element_mode=element_mode,
                )
                cond = _build_or_interactive(uia) if condition_kind == "or_interactive" else uia.CreateTrueCondition()
                t_find0 = time.perf_counter()
                found = root.FindAllBuildCache(UIA.TreeScope_Subtree, cond, cr)
                t_find_ms = (time.perf_counter() - t_find0) * 1000.0

                t_unp0 = time.perf_counter()
                els, extra_ipc = _unpack_elements(
                    found,
                    include_bounds=include_bounds,
                    live_bounds_fallback=live_bounds_fallback,
                )
                t_unp_ms = (time.perf_counter() - t_unp0) * 1000.0
                return els, {
                    "node_count": len(els),
                    "ipc_round_trips": 2 + extra_ipc,  # ElementFromHandle(or cached) + FindAllBuildCache + extras
                    "elem_from_hwnd_ms": round(t_root_ms, 3),
                    "find_all_ms": round(t_find_ms, 3),
                    "unpack_ms": round(t_unp_ms, 3),
                }
            return runner.call(op)
        finally:
            if fresh_session:
                runner.close()

    shared_runner = _UiaBenchRunner(apartment=apartment)
    try:
        return common.measure_workload(
            cold_fn=lambda: _do_scan(fresh_session=True, clear_root=True),
            warm_fn=lambda: _do_scan(fresh_session=False, clear_root=not cache_root),
            n_cold=n_cold,
            n_warm=n_warm,
            target_pid=target_pid,
        )
    finally:
        shared_runner.close()


def _bench_elem_from_hwnd_cold_vs_warm(hwnd, n_warm=30):
    """Isolate ElementFromHandle(hwnd) cost cold COM vs warm session vs cached ref."""
    cold_samples = []
    for _ in range(3):
        r = _UiaBenchRunner(apartment="mta")
        try:
            _, meta = r.call(lambda u, _: ([], {"ms": _timed_efh(u, hwnd)}))
            cold_samples.append(meta["ms"])
        finally:
            r.close()

    r = _UiaBenchRunner(apartment="mta")
    try:
        def warm_op(u, _):
            return [], {"ms": _timed_efh(u, hwnd)}
        warm_samples = [r.call(warm_op)[1]["ms"] for _ in range(n_warm)]
    finally:
        r.close()
    return {
        "cold": common.summarize_timings(cold_samples, cold_samples),
        "warm_uncached": common.summarize_timings([], warm_samples),
    }


def _timed_efh(uia, hwnd):
    t0 = time.perf_counter()
    _ = uia.ElementFromHandle(hwnd)
    return (time.perf_counter() - t0) * 1000.0


def _make_i4_array_variant(values):
    """Build a Variant(VT_ARRAY | VT_I4) solely owned by VariantClear (avoids comtypes double-free)."""
    import comtypes.automation
    oleaut = ctypes.WinDLL("oleaut32", use_last_error=True)
    oleaut.SafeArrayCreateVector.argtypes = [ctypes.c_ushort, ctypes.c_long, ctypes.c_ulong]
    oleaut.SafeArrayCreateVector.restype = ctypes.c_void_p
    oleaut.SafeArrayAccessData.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    oleaut.SafeArrayAccessData.restype = ctypes.c_long
    oleaut.SafeArrayUnaccessData.argtypes = [ctypes.c_void_p]
    oleaut.SafeArrayUnaccessData.restype = ctypes.c_long

    psa = oleaut.SafeArrayCreateVector(comtypes.automation.VT_I4, 0, len(values))
    if not psa:
        raise MemoryError("SafeArrayCreateVector failed")
    pdata = ctypes.c_void_p()
    oleaut.SafeArrayAccessData(psa, ctypes.byref(pdata))
    try:
        buf = (ctypes.c_int32 * len(values)).from_address(pdata.value)
        for i, val in enumerate(values):
            buf[i] = int(val)
    finally:
        oleaut.SafeArrayUnaccessData(psa)

    v = comtypes.automation.VARIANT()
    v.vt = comtypes.automation.VT_ARRAY | comtypes.automation.VT_I4
    v._.c_void_p = psa
    return v


def _bench_reacquire_by_rid(hwnd, elements, sample_n=5):
    """Measure targeted UIA element re-acquisition by RuntimeId (needed for ElementMode.None)."""
    candidates = [e for e in elements if e.get("role") in common.INTERACTIVE_ROLES and e.get("runtime_id")][:sample_n]
    if not candidates:
        return {"attempted": 0, "succeeded": 0, "p50_ms": None}
    runner = _UiaBenchRunner(apartment="mta")
    lat = []
    ok = 0
    try:
        def fn(u, _):
            nonlocal ok
            root = u.ElementFromHandle(hwnd)
            for c in candidates:
                rid = [int(x) for x in c["runtime_id"]]
                t0 = time.perf_counter()
                v_i4 = _make_i4_array_variant(rid)
                cond = u.CreatePropertyCondition(UIA.UIA_RuntimeIdPropertyId, v_i4)
                found = root.FindFirst(UIA.TreeScope_Subtree, cond)
                dt = (time.perf_counter() - t0) * 1000.0
                lat.append(dt)
                if found:
                    ok += 1
            return [], {}
        runner.call(fn)
    finally:
        runner.close()
    s = common.summarize_timings([], lat)
    return {"attempted": len(candidates), "succeeded": ok, "p50_ms": s["p50_ms"], "p95_ms": s["p95_ms"]}


def run_all_uia_experiments(targets=("notepad", "explorer", "chromium", "electron"), n_cold=3, n_warm=20):
    """Execute Experiments 1-4 sequentially across desktop targets, one variable at a time."""
    tree_filter_info = verify_tree_filter_defaults()
    results = {
        "tree_filter_verification": tree_filter_info,
        "targets": {},
    }

    minimal_props = (
        UIA.UIA_NamePropertyId, UIA.UIA_ControlTypePropertyId,
        UIA.UIA_BoundingRectanglePropertyId, UIA.UIA_IsEnabledPropertyId,
        UIA.UIA_IsOffscreenPropertyId, UIA.UIA_RuntimeIdPropertyId,
        UIA.UIA_IsInvokePatternAvailablePropertyId,
        UIA.UIA_IsValuePatternAvailablePropertyId,
        UIA.UIA_IsSelectionItemPatternAvailablePropertyId,
        UIA.UIA_IsTogglePatternAvailablePropertyId,
        UIA.UIA_IsExpandCollapsePatternAvailablePropertyId,
    )
    no_textpat_props = tuple(p for p in FULL_PROPS if p != UIA.UIA_IsTextPatternAvailablePropertyId)
    no_textpat_pats = tuple(p for p in FULL_PATTERNS if p != UIA.UIA_TextPatternId)
    no_bounds_props = tuple(p for p in minimal_props if p != UIA.UIA_BoundingRectanglePropertyId)

    for kind in targets:
        print(f"[bench_uia] Launching desktop target: {kind} ...", flush=True)
        try:
            with DesktopTarget(kind) as tgt:
                hwnd, pid = tgt.hwnd, tgt.pid
                # Baseline control group matches production desktop_uia.py configuration (STA, full cache, default filter, Mode_Full)
                ctrl_els, ctrl_stats = _run_scan_variant(
                    hwnd, pid, apartment="sta", cache_root=False,
                    props=FULL_PROPS, patterns=FULL_PATTERNS,
                    tree_filter="default", condition_kind="true", element_mode="full",
                    n_cold=n_cold, n_warm=n_warm,
                )

                efh_probe = _bench_elem_from_hwnd_cold_vs_warm(hwnd)

                # Exp 1: STA vs MTA (variable = apartment) and MTA + cached_root (variable = ElementFromHandle reuse)
                exp1_mta_els, exp1_mta = _run_scan_variant(
                    hwnd, pid, apartment="mta", cache_root=False,
                    props=FULL_PROPS, patterns=FULL_PATTERNS,
                    tree_filter="default", condition_kind="true", element_mode="full",
                    n_cold=n_cold, n_warm=n_warm,
                )
                exp1_cached_els, exp1_cached = _run_scan_variant(
                    hwnd, pid, apartment="mta", cache_root=True,
                    props=FULL_PROPS, patterns=FULL_PATTERNS,
                    tree_filter="default", condition_kind="true", element_mode="full",
                    n_cold=n_cold, n_warm=n_warm,
                )

                # Exp 2: CacheRequest under fixed MTA baseline (variable = CacheRequest properties/patterns)
                exp2_notext_els, exp2_notext = _run_scan_variant(
                    hwnd, pid, apartment="mta", cache_root=False,
                    props=no_textpat_props, patterns=no_textpat_pats,
                    n_cold=n_cold, n_warm=n_warm,
                )
                exp2_min_els, exp2_min = _run_scan_variant(
                    hwnd, pid, apartment="mta", cache_root=False,
                    props=minimal_props, patterns=(),
                    n_cold=n_cold, n_warm=n_warm,
                )
                exp2_nobounds_els, exp2_nobounds = _run_scan_variant(
                    hwnd, pid, apartment="mta", cache_root=False,
                    props=no_bounds_props, patterns=(),
                    include_bounds=False, live_bounds_fallback=True,
                    n_cold=n_cold, n_warm=max(5, n_warm // 2),
                )

                # Exp 3: TreeFilter ControlView vs Explicit RawView vs Interactive OrCondition (fixed MTA, full cache)
                exp3_cv_els, exp3_cv = _run_scan_variant(
                    hwnd, pid, apartment="mta", tree_filter="control", condition_kind="true",
                    n_cold=n_cold, n_warm=n_warm,
                )
                exp3_rv_els, exp3_rv = _run_scan_variant(
                    hwnd, pid, apartment="mta", tree_filter="raw", condition_kind="true",
                    n_cold=n_cold, n_warm=n_warm,
                )
                exp3_or_els, exp3_or = _run_scan_variant(
                    hwnd, pid, apartment="mta", tree_filter="control", condition_kind="or_interactive",
                    n_cold=n_cold, n_warm=n_warm,
                )

                # Exp 4: AutomationElementMode_Full vs None (fixed MTA, ControlView)
                exp4_none_els, exp4_none = _run_scan_variant(
                    hwnd, pid, apartment="mta", element_mode="none",
                    n_cold=n_cold, n_warm=n_warm,
                )
                reacquire_stats = _bench_reacquire_by_rid(hwnd, exp4_none_els)

                results["targets"][kind] = {
                    "hwnd": hwnd,
                    "pid": pid,
                    "elem_from_hwnd_breakdown": efh_probe,
                    "control_sta": {
                        "stats": ctrl_stats,
                        "accuracy": common.compare_elements(ctrl_els, ctrl_els),
                    },
                    "exp1_threading": {
                        "mta_fresh": {
                            "stats": exp1_mta,
                            "accuracy": common.compare_elements(exp1_mta_els, ctrl_els),
                        },
                        "mta_cached_root": {
                            "stats": exp1_cached,
                            "accuracy": common.compare_elements(exp1_cached_els, ctrl_els),
                        },
                    },
                    "exp2_cache_request": {
                        "no_text_pattern": {
                            "stats": exp2_notext,
                            "accuracy": common.compare_elements(exp2_notext_els, exp1_mta_els),
                        },
                        "minimal_props_only": {
                            "stats": exp2_min,
                            "accuracy": common.compare_elements(exp2_min_els, exp1_mta_els),
                        },
                        "no_bounds_plus_lazy_n1": {
                            "stats": exp2_nobounds,
                            "accuracy": common.compare_elements(exp2_nobounds_els, exp1_mta_els),
                        },
                    },
                    "exp3_tree_filter": {
                        "control_view": {
                            "stats": exp3_cv,
                            "accuracy_interactive": common.compare_elements(exp3_cv_els, exp3_cv_els, interactive_only=True),
                            "accuracy_all": common.compare_elements(exp3_cv_els, exp3_cv_els, interactive_only=False),
                        },
                        "explicit_raw_view": {
                            "stats": exp3_rv,
                            "accuracy_vs_control_interactive": common.compare_elements(exp3_rv_els, exp3_cv_els, interactive_only=True),
                        },
                        "control_view_or_interactive": {
                            "stats": exp3_or,
                            "accuracy_vs_control_interactive": common.compare_elements(exp3_or_els, exp3_cv_els, interactive_only=True),
                        },
                    },
                    "exp4_element_mode": {
                        "mode_full": {
                            "stats": exp1_mta,
                            "accuracy": common.compare_elements(exp1_mta_els, exp1_mta_els),
                        },
                        "mode_none_readonly": {
                            "stats": exp4_none,
                            "accuracy": common.compare_elements(exp4_none_els, exp1_mta_els),
                            "reacquire_by_rid": reacquire_stats,
                        },
                    },
                }
        except Exception as exc:
            results["targets"][kind] = {"error": f"{type(exc).__name__}: {exc}"}

    return results

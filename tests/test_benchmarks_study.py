# SPDX-License-Identifier: Apache-2.0
"""Unit and contract tests for the isolated benchmark study harness (zero engine edits)."""
import json
import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.browser_cdp import BrowserSession
from benchmarks import bench_browser, bench_remote_ops, bench_uia, common
from benchmarks.corpus import DualOriginCorpusServer, extract_corpus_ground_truth


def test_accuracy_comparator_penalizes_missing_and_fp():
    gt = [
        {"gt_id": "a", "role": "button", "name": "Submit Order", "box": [10, 10, 100, 30], "category": "main_dom"},
        {"gt_id": "b", "role": "button", "name": "Closed Shadow", "box": [10, 60, 120, 30], "category": "closed_shadow_dom"},
    ]
    cand = [
        {"role": "button", "name": "Submit Order", "box": [10, 10, 100, 30]},
        {"role": "link", "name": "Spurious Extra", "box": [200, 200, 80, 20]},
    ]
    res = common.compare_elements(cand, gt)
    assert res["recall"] == 0.5
    assert res["precision"] == 0.5
    assert res["missing_count"] == 1
    assert res["false_positive_count"] == 1
    assert res["failure_breakdown"] == {"closed_shadow_dom": 1}


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows UIA")
def test_tree_filter_default_is_control_view():
    tf = bench_uia.verify_tree_filter_defaults()
    assert tf["default_equals_control_view"] is True
    assert tf["default_equals_raw_view"] is False


def test_corpus_dual_origin_and_js_vs_control_coverage():
    with DualOriginCorpusServer() as srv:
        assert srv.port_a != srv.port_b
        bs = BrowserSession(url=srv.main_url, headless=True)
        try:
            gt = extract_corpus_ground_truth(bs.page)
            cats = {g["category"] for g in gt}
            assert {"main_dom", "open_shadow_dom", "closed_shadow_dom", "cross_origin_iframe", "aria_labelledby", "custom_div", "role_switch"} <= cats

            ctrl_els = bs.discover()
            ctrl_acc = common.compare_elements(ctrl_els, gt)
            assert ctrl_acc["recall"] >= 0.85, f"control lost gt items: {ctrl_acc}"

            js_els, _ = bench_browser._js_single_frame_extract(bs.cdp.send)
            js_acc = common.compare_elements(js_els, gt)
            # Single-frame JS MUST miss closed Shadow DOM and cross-origin OOPIF
            assert "closed_shadow_dom" in js_acc["failure_breakdown"]
            assert "cross_origin_iframe" in js_acc["failure_breakdown"]
        finally:
            bs.close()


def test_remote_op_bytecode_builder_smoke():
    bc, out_reg = bench_remote_ops._build_safe_subtree_walk_bytecode(max_nodes=10)
    assert bc[:4] == b"\x00\x00\x00\x00"
    assert out_reg > 100
    b_bc, b_reg = bench_remote_ops._build_batch_inspect_bytecode(3)
    assert len(b_bc) > 20 and b_reg > 100

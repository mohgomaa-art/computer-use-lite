#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""TDD audit regression suite covering Phase B (B1-B16) and Phase C."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import os
import socket
import subprocess
import sys
import tempfile
import time
from unittest import mock

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / "src", ROOT / "experiments"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine import Api, BrowserSession, DesktopSession, StaleElementError, blind_gap, hover, snapshot, state
from engine import desktop_uia

_SKIP_DESKTOP = sys.platform != "win32" or os.environ.get("CUL_SKIP_DESKTOP") == "1"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _windows_by_class(class_name):
    out = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if desktop_uia._u32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            desktop_uia._u32.GetClassNameW(hwnd, buf, 256)
            if buf.value == class_name:
                out.add(hwnd)
        return True

    desktop_uia._u32.EnumWindows(cb, 0)
    return out


# B1: Role-less clickables and switch role
def test_b1_roleless_clickable_div_and_switch(tmp_path):
    html = """<!doctype html><html><body>
      <div id="cdiv" onclick="document.getElementById('out').textContent='div_ok'" style="cursor:pointer;width:120px;height:40px">Click Div</div>
      <button id="sw" role="switch" aria-checked="false" onclick="this.setAttribute('aria-checked','true');document.getElementById('out').textContent='sw_ok'">Wifi</button>
      <div id="out">none</div>
    </body></html>"""
    p_html = tmp_path / "b1.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        lm = api.discover_interactables(export_crops=False)
        roles = {r["role"]: r for r in api.resolver.records}
        assert "clickable" in roles, f"role-less div dropped: {lm}"
        assert "switch" in roles, f"switch role dropped: {lm}"
        api.execute_action(roles["clickable"]["id"], "click")
        assert s.page.inner_text("#out") == "div_ok"
        api.discover_interactables(export_crops=False)
        sw = next(r for r in api.resolver.records if r["role"] == "switch")
        api.execute_action(sw["id"], "click")
        assert s.page.inner_text("#out") == "sw_ok"
    finally:
        s.close()


# B2: Browser coordinates subtract scrollX/scrollY
def test_b2_scrolled_page_click(tmp_path):
    html = """<!doctype html><html><body style="margin:0;height:2400px">
      <div style="height:900px">Spacer</div>
      <button id="target" style="width:180px;height:50px" onclick="document.getElementById('out').textContent='scrolled_ok'">ScrollTarget</button>
      <div id="out">none</div>
    </body></html>"""
    p_html = tmp_path / "b2.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True, viewport=(1280, 720))
    try:
        s.page.evaluate("() => window.scrollTo(0, 800)")
        s.page.wait_for_timeout(100)
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)
        btns = [r for r in api.resolver.records if r["role"] == "button"]
        assert btns, "scrolled button not discovered in viewport"
        assert 50 <= btns[0]["box"][1] <= 200, f"expected viewport y ~100, got {btns[0]['box']}"
        api.execute_action(btns[0]["id"], "click")
        assert s.page.inner_text("#out") == "scrolled_ok"
    finally:
        s.close()


# B3: Desktop perform("click") fallback chain (Toggle, SelectionItem, SendInput; never moved_to_center)
@pytest.mark.windows_desktop
@pytest.mark.skipif(_SKIP_DESKTOP, reason="Requires Windows UIA / interactive desktop session")
def test_b3_desktop_toggle_selection_and_sendinput_click():
    html = """<!doctype html><html><body>
      <input id="chk" type="checkbox" aria-label="B3Check">
      <div role="tablist">
        <button id="t1" role="tab" aria-selected="false">TabOne</button>
        <button id="t2" role="tab" aria-selected="true">TabTwo</button>
      </div>
      <script>
        document.getElementById('t1').addEventListener('click', () => {
          document.getElementById('t1').setAttribute('aria-selected', 'true');
          document.getElementById('t2').setAttribute('aria-selected', 'false');
        });
      </script>
    </body></html>"""
    before = _windows_by_class("Chrome_WidgetWin_1")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--window-position=20,20", "--window-size=800,600",
                                                    "--force-renderer-accessibility"])
        page = b.new_page()
        page.set_content(html)
        page.wait_for_timeout(400)
        hwnd = next(iter(_windows_by_class("Chrome_WidgetWin_1") - before))
        s = DesktopSession(hwnd)
        nodes = s.discover()
        chk = next(n for n in nodes if n["name"] == "B3Check")
        tab1 = next(n for n in nodes if n["name"] == "TabOne")
        # Force InvokePattern to fail on a non-Invoke control or verify pattern choice
        res_chk = s.perform(chk, "click")
        assert res_chk["mechanism"] in ("toggle_pattern", "invoke_pattern", "sendinput_click")
        assert res_chk["mechanism"] != "moved_to_center"
        assert page.is_checked("#chk") is True

        res_tab = s.perform(tab1, "click")
        assert res_tab["mechanism"] in ("selection_item_pattern", "invoke_pattern", "sendinput_click")
        assert res_tab["mechanism"] != "moved_to_center"
        b.close()


def test_b3_sendinput_fallback_never_reports_moved_to_center():
    # Unit boundary check when all UIA patterns fail: must verify foreground and call SendInput LEFTDOWN/UP
    s = DesktopSession.__new__(DesktopSession)
    s.hwnd = 12345
    s._last = {}
    s._kill = desktop_uia.KillSwitch()
    fake_el = mock.MagicMock()
    fake_el.GetCurrentPattern.side_effect = RuntimeError("no pattern")
    s._element = lambda el: fake_el
    s._call = lambda fn: fn()
    el = {"box": [100, 100, 40, 20], "ref": {"kind": "uia", "runtime_id": (1,)}}
    with mock.patch.object(desktop_uia, "_ensure_foreground"), \
         mock.patch.object(desktop_uia, "click_at", return_value="sendinput_click") as m_click:
        res = s.perform(el, "click")
        assert res["mechanism"] == "sendinput_click"
        m_click.assert_called_once_with(120, 110, hwnd=12345, kill_switch=s._kill)


# B4: Revision & stale guard (bounds() no bump; removed / covered / rev-changed / moved)
def test_b4_revision_and_stale_guard(tmp_path):
    html = """<!doctype html><html><body>
      <button id="b1" style="position:fixed;left:40px;top:40px;width:120px;height:40px">Btn1</button>
      <button id="b2" style="position:fixed;left:220px;top:40px;width:120px;height:40px">Btn2</button>
    </body></html>"""
    p_html = tmp_path / "b4.html"
    p_html.write_text(html, encoding="utf-8")

    # snapshot.window(hwnd) must NOT bump revision
    r0 = snapshot.current_revision()
    snapshot.window(desktop_uia._u32.GetDesktopWindow())
    assert snapshot.current_revision() == r0, "snapshot.window() bumped global revision!"

    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)
        rev1 = api.resolver.revision
        b1 = next(r for r in api.resolver.records if r["name"] == "Btn1")
        b2 = next(r for r in api.resolver.records if r["name"] == "Btn2")

        # Case 1: bounds unchanged, revision changed
        api.discover_interactables(export_crops=False)
        assert api.resolver.revision > rev1
        with pytest.raises(StaleElementError):
            api.execute_action(b1["id"], "click", revision=rev1)

        # Case 2: element covered by modal
        s.page.evaluate("""() => {
            const m = document.createElement('div');
            m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:999';
            document.body.appendChild(m);
        }""")
        with pytest.raises(StaleElementError):
            api.execute_action(b1["id"], "click")

        # Remove modal, then test Case 3: element removed
        s.page.evaluate("() => document.querySelector('div').remove()")
        api.discover_interactables(export_crops=False)
        b2 = next(r for r in api.resolver.records if r["name"] == "Btn2")
        s.page.evaluate("() => document.getElementById('b2').remove()")
        with pytest.raises(StaleElementError):
            api.execute_action(b2["id"], "click")
    finally:
        s.close()


# B5: Foreground safety & 5 px kill switch
def test_b5_foreground_safety_and_killswitch():
    with mock.patch.object(desktop_uia._u32, "GetForegroundWindow", return_value=999999), \
         mock.patch.object(desktop_uia._u32, "ShowWindow", return_value=True), \
         mock.patch.object(desktop_uia._u32, "SetForegroundWindow", return_value=False):
        with pytest.raises(RuntimeError, match="Foreground"):
            desktop_uia.move_mouse(100, 100, hwnd=12345)

    ks = desktop_uia.KillSwitch(enabled=True, tolerance=5)
    with mock.patch.object(desktop_uia, "cursor_pos", return_value=(100, 100)):
        ks.moved((100, 100))
    with mock.patch.object(desktop_uia, "cursor_pos", return_value=(120, 100)):
        with pytest.raises(RuntimeError, match="HUMAN TAKEOVER"):
            ks.pre_move()


# B6: Privacy redaction (TaskState, state_delta, inspect_element)
def test_b6_privacy_redaction(tmp_path):
    html = """<!doctype html><html><body>
      <input id="pw" type="password" aria-label="Password">
      <input id="txt" type="text" aria-label="User">
    </body></html>"""
    p_html = tmp_path / "b6.html"
    p_html.write_text(html, encoding="utf-8")
    state_file = tmp_path / "state.json"
    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=state_file)
        api.discover_interactables(export_crops=False)
        pw = next(r for r in api.resolver.records if r["name"] == "Password")
        secret = "SuperSecret!987"
        res = api.execute_action(pw["id"], "type", secret)
        raw_state = state_file.read_text(encoding="utf-8")
        assert secret not in raw_state, "plaintext secret stored in TaskState!"
        assert secret not in json.dumps(res["state_delta"]), "plaintext secret leaked in state_delta!"
        data = json.loads(raw_state)
        assert data["actions"][-1]["value_length"] == len(secret)
        assert "value_sha256" in data["actions"][-1]
    finally:
        s.close()


# B7: Browser type clear, scrollIntoView, disabled, occlusion
def test_b7_browser_type_clear_scroll_disabled_occlusion(tmp_path):
    html = """<!doctype html><html><body style="margin:0;height:2000px">
      <input id="inp" value="OLD" aria-label="Field" style="width:200px;height:30px">
      <button id="dis" disabled style="width:120px;height:30px">DisabledBtn</button>
      <div style="height:1200px"></div>
      <button id="far" style="width:140px;height:40px" onclick="document.getElementById('out').textContent='far_ok'">FarBtn</button>
      <div id="out">none</div>
    </body></html>"""
    p_html = tmp_path / "b7.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True, viewport=(1280, 720))
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)
        inp = next(r for r in api.resolver.records if r["name"] == "Field")
        api.execute_action(inp["id"], "type", "NEW")
        assert s.page.input_value("#inp") == "NEW", "type appended instead of clearing!"
        api.discover_interactables(export_crops=False)
        inp = next(r for r in api.resolver.records if r["name"] == "Field")
        api.execute_action(inp["id"], "type", "2", clear=False)
        assert s.page.input_value("#inp") == "NEW2"

        # Disabled button should be filtered from interactive discovery and refused if called directly
        assert not any(r["name"] == "DisabledBtn" for r in api.resolver.records)

        # Direct perform on off-viewport element should scrollIntoView
        far_el = {"box": [0, 1270, 140, 40], "enabled": True, "ref": {"kind": "browser",
                  "backend_node_id": s.cdp.send("DOM.getDocument", {"depth": -1}) and
                  s.page.evaluate("() => 0") or None}}
        # Use DOM.querySelector to get real backendNodeId for #far
        doc = s.cdp.send("DOM.getDocument", {"depth": 1})
        nid = s.cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "#far"})["nodeId"]
        bid = s.cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
        far_el["ref"]["backend_node_id"] = bid
        s.perform(far_el, "click")
        assert s.page.inner_text("#out") == "far_ok"
    finally:
        s.close()


# B8: M3 filtering (disabled + occluded) and hover zombie cleanup + no double 350 ms sleep
def test_b8_filtering_hover_cleanup_and_single_sleep(tmp_path):
    html = """<!doctype html><html><body style="margin:0">
      <button id="under" style="position:fixed;left:20px;top:20px;width:140px;height:40px">Under</button>
      <button id="vis" style="position:fixed;left:220px;top:20px;width:140px;height:40px"
              onmouseenter="document.getElementById('under').remove();const b=document.createElement('button');b.id='pop';b.textContent='Popped';b.style='position:fixed;left:220px;top:80px;width:120px;height:36px';document.body.appendChild(b)">Vis</button>
      <div id="modal" style="position:fixed;left:0;top:0;width:180px;height:120px;background:rgba(0,0,0,0.8);z-index:10">Modal</div>
      <button id="dis" disabled style="position:fixed;left:420px;top:20px;width:120px;height:40px">Dis</button>
    </body></html>"""
    p_html = tmp_path / "b8.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)
        names = {r["name"] for r in api.resolver.records}
        assert "Dis" not in names, "disabled button not filtered"
        assert "Under" not in names, "occluded button not filtered"
        assert "Vis" in names

        # Hover Vis -> removes Under from DOM (or test removing Modal/another element) and adds Popped
        vis = next(r for r in api.resolver.records if r["name"] == "Vis")
        # Add another temporary button before hover and remove it during hover
        s.page.evaluate("""() => {
            const z = document.createElement('button');
            z.id = 'z'; z.textContent = 'TempZ'; z.style = 'position:fixed;left:420px;top:90px;width:100px;height:30px';
            document.body.appendChild(z);
        }""")
        api.discover_interactables(export_crops=False)
        vis = next(r for r in api.resolver.records if r["name"] == "Vis")
        s.page.evaluate("() => document.getElementById('vis').addEventListener('mouseenter', () => { const z=document.getElementById('z'); if(z) z.remove(); })")
        res = hover.hover_and_diff(s, api.resolver, vis["id"], wait_ms=100)
        after_names = {r["name"] for r in api.resolver.records}
        assert "TempZ" not in after_names, "hover_and_diff left zombie disappeared element!"
        assert "Popped" in after_names
    finally:
        s.close()

    # Check DesktopSession.hover does not sleep 350 ms on its own
    ds = DesktopSession.__new__(DesktopSession)
    ds.hwnd = 1
    ds._kill = desktop_uia.KillSwitch()
    with mock.patch.object(desktop_uia, "move_mouse") as mm:
        t0 = time.perf_counter()
        ds.hover({"box": [10, 10, 20, 20]})
        dt = time.perf_counter() - t0
        mm.assert_called_once()
        assert dt < 0.15, f"DesktopSession.hover slept {dt:.2f}s (double sleep bug)"


# B9: Connect mode selects active tab and real innerWidth/innerHeight
def test_b9_connect_mode_active_tab_and_viewport(tmp_path):
    port = _free_port()
    user_data = tmp_path / "profile"
    with sync_playwright() as p:
        chrome_exe = p.chromium.executable_path
    proc = subprocess.Popen([
        chrome_exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--headless=new",
        "--window-size=920,560",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import urllib.request
        for _ in range(40):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = b.contexts[0]
            p1 = ctx.new_page()
            p1.set_content("<button>Tab1Active</button>")
            p1.bring_to_front()
            real_vp = p1.evaluate("() => [window.innerWidth, window.innerHeight]")
            b.close()
        bs = BrowserSession(connect=f"http://127.0.0.1:{port}")
        try:
            assert bs.bounds() == [0, 0, real_vp[0], real_vp[1]], f"wrong viewport: {bs.bounds()}"
            assert bs.bounds() != [0, 0, 1280, 720]
            names = [e["name"] for e in bs.discover()]
            assert "Tab1Active" in names, f"picked wrong tab: {names}"

            # Also verify _select_active_page picks visible+focused tab over hidden tab 0
            hidden_pg = mock.MagicMock()
            hidden_pg.evaluate.return_value = [False, False, "https://example.com/bg"]
            active_pg = mock.MagicMock()
            active_pg.evaluate.return_value = [True, True, "https://example.com/active"]
            fake_ctx = mock.MagicMock()
            fake_ctx.pages = [hidden_pg, active_pg]
            assert bs._select_active_page(fake_ctx) is active_pg
        finally:
            bs.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# B10: line_map cap ~60 + filter_query + UIA role fixes
def test_b10_line_map_cap_filter_and_uia_roles(tmp_path):
    btns = "".join(f"<button style='width:80px;height:22px;margin:2px'>Btn{i}</button>" for i in range(90))
    p_html = tmp_path / "b10.html"
    p_html.write_text(f"<!doctype html><html><body>{btns}</body></html>", encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        lm = api.discover_interactables(export_crops=False)
        elem_lines = [l for l in lm.splitlines() if l.startswith("e")]
        assert len(elem_lines) <= 60, f"line_map not capped: {len(elem_lines)}"
        assert "more" in lm.lower()
        filtered = api.line_map(filter_query="Btn75")
        assert "Btn75" in filtered
    finally:
        s.close()
    assert desktop_uia.WANTED["ListItemControl"] == "listitem"
    assert desktop_uia.WANTED["TreeItemControl"] == "treeitem"


# B11: Desktop perf (lightweight signature, 0 full scans on execute_action, targeted freshness + AutoSetFocus=0)
@pytest.mark.windows_desktop
@pytest.mark.skipif(_SKIP_DESKTOP, reason="Requires Windows UIA / interactive desktop session")
def test_b11_desktop_perf_lightweight_signature():
    before = _windows_by_class("Chrome_WidgetWin_1")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--window-position=20,20", "--window-size=800,600",
                                                    "--force-renderer-accessibility"])
        page = b.new_page()
        page.set_content("<button id='btn'>RealBtn</button><input id='txt' aria-label='RealBox'>")
        page.wait_for_timeout(400)
        hwnd = next(iter(_windows_by_class("Chrome_WidgetWin_1") - before))
        s = DesktopSession(hwnd)
        api = Api(s)
        api.discover_interactables(export_crops=False)
        btn = next(r for r in api.resolver.records if r["name"] == "RealBtn")
        # Button should NOT claim value or toggle pattern!
        assert "value" not in btn["patterns"], f"bogus patterns: {btn['patterns']}"
        t0 = time.perf_counter()
        with mock.patch.object(s, "_scan", wraps=s._scan) as spy_scan:
            api.execute_action(btn["id"], "click")
            assert spy_scan.call_count == 0, f"expected 0 full _scan calls on targeted action, got {spy_scan.call_count}"
        assert time.perf_counter() - t0 < 0.8, "UIA Invoke stalled unexpectedly (>800ms; AutoSetFocus=0 regression?)"

        # Stale moved > 2px & disabled checks must still reject via verify_fresh
        api.discover_interactables(export_crops=False)
        btn = next(r for r in api.resolver.records if r["name"] == "RealBtn")
        moved_btn = dict(btn, box=[btn["box"][0] + 20, btn["box"][1], btn["box"][2], btn["box"][3]])
        with pytest.raises(StaleElementError):
            s.verify_fresh(moved_btn, tolerance=2)
        b.close()


# B12: UIA worker fail-fast (MTA CoInitializeEx) instead of 20 s timeout
def test_b12_uia_worker_fail_fast():
    with mock.patch.object(desktop_uia, "UIA", None):
        t0 = time.perf_counter()
        with pytest.raises(RuntimeError, match="UIAutomationClient"):
            DesktopSession(1234)
        assert time.perf_counter() - t0 < 2.0

    with mock.patch.object(desktop_uia.comtypes, "CoInitializeEx", side_effect=OSError("coinit_boom")):
        t0 = time.perf_counter()
        with pytest.raises(OSError, match="coinit_boom"):
            DesktopSession(1234)
        assert time.perf_counter() - t0 < 2.0


# B13: Accessibility activation on Chromium without --force-renderer-accessibility
@pytest.mark.windows_desktop
@pytest.mark.skipif(_SKIP_DESKTOP, reason="Requires Windows UIA / interactive desktop session")
def test_b13_accessibility_activation():
    before = _windows_by_class("Chrome_WidgetWin_1")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--window-position=20,20", "--window-size=800,600"])
        page = b.new_page()
        page.set_content("<button>AlphaB13</button><input aria-label='BetaB13'>")
        page.wait_for_timeout(400)
        hwnd = next(iter(_windows_by_class("Chrome_WidgetWin_1") - before))
        s = DesktopSession(hwnd)
        nodes = s.discover()
        names = {n["name"] for n in nodes}
        assert "AlphaB13" in names and "BetaB13" in names, f"accessibility not activated: {len(nodes)} nodes"
        b.close()


# B14: blind_gap small canvas rule + no false positives on normal DOM page
def test_b14_blind_gap_small_canvas_and_no_false_positive(tmp_path):
    # Normal page with decorative small canvas next to real DOM buttons -> NO blind region
    html_norm = """<!doctype html><html><body style="margin:20px">
      <button style="width:120px;height:40px">B1</button>
      <button style="width:120px;height:40px">B2</button>
      <button style="width:120px;height:40px">B3</button>
      <canvas id="spark" width="240" height="100" style="display:block;margin-top:8px"></canvas>
    </body></html>"""
    p1 = tmp_path / "norm.html"
    p1.write_text(html_norm, encoding="utf-8")
    s1 = BrowserSession(url=p1.as_uri(), headless=True, viewport=(1280, 720))
    try:
        api1 = Api(s1, state_path=tmp_path / "s1.json")
        api1.discover_interactables(export_crops=False)
        assert api1.regions == [], f"false positive blind region: {api1.regions}"
    finally:
        s1.close()

    # Interactive-sized canvas (>= 5% viewport = >= 46080 px^2) with sparse DOM density nearby -> blind region
    html_chart = """<!doctype html><html><body style="margin:20px">
      <canvas id="chart" width="400" height="200" style="display:block"></canvas>
    </body></html>"""
    p2 = tmp_path / "chart.html"
    p2.write_text(html_chart, encoding="utf-8")
    s2 = BrowserSession(url=p2.as_uri(), headless=True, viewport=(1280, 720))
    try:
        api2 = Api(s2, state_path=tmp_path / "s2.json")
        api2.discover_interactables(export_crops=False)
        assert len(api2.regions) == 1 and api2.regions[0]["kind"] == "small_opaque_canvas", api2.regions
    finally:
        s2.close()


# B15: TaskState atomic write, monotonic revision across runs, failed action logging
def test_b15_task_state_atomic_monotonic_and_failed(tmp_path):
    st_path = tmp_path / "ts.json"
    st_path.write_text(json.dumps({"task": "t", "revision": 50, "actions": []}), encoding="utf-8")
    ts = state.TaskState(st_path)
    assert snapshot.current_revision() >= 50
    assert snapshot.bump_revision() >= 51

    html = "<!doctype html><html><body><button id='b'>B</button></body></html>"
    p_html = tmp_path / "b15.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True)
    try:
        api = Api(s, state_path=st_path)
        api.discover_interactables(export_crops=False)
        b = api.resolver.records[0]
        s.page.evaluate("() => document.getElementById('b').remove()")
        with pytest.raises(StaleElementError):
            api.execute_action(b["id"], "click")
        data = json.loads(st_path.read_text(encoding="utf-8"))
        assert data["actions"][-1]["ok"] is False
        assert "error" in data["actions"][-1]
        assert not list(tmp_path.glob("*.tmp"))
    finally:
        s.close()


# B16: blind_gap.export on scrolled page and negative desktop virtual coordinates
def test_b16_export_scroll_and_negative_desktop(tmp_path):
    html = """<!doctype html><html><body style="margin:0;height:2000px">
      <div style="height:600px;background:rgb(255,0,0)"></div>
      <canvas id="c" width="300" height="120" style="display:block"></canvas>
      <script>const g=document.getElementById('c').getContext('2d');g.fillStyle='rgb(0,255,0)';g.fillRect(0,0,300,120);</script>
    </body></html>"""
    p_html = tmp_path / "b16.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True, viewport=(1280, 720))
    try:
        s.page.evaluate("() => window.scrollTo(0, 500)")
        s.page.wait_for_timeout(100)
        rect = s.canvas_rects()[0]
        out_png = tmp_path / "scroll_crop.png"
        blind_gap.export(s, {"box": rect}, out_png)
        px = Image.open(out_png).convert("RGB").getpixel((20, 20))
        assert px == (0, 255, 0), f"scrolled crop missed canvas: {px}"
    finally:
        s.close()

    # Desktop negative coordinates
    class FakeDesktop:
        pass

    fake_img = Image.new("RGB", (300, 200), (1, 2, 3))
    with mock.patch("PIL.ImageGrab.grab", return_value=fake_img) as m_grab, \
         mock.patch.object(blind_gap, "_virtual_screen", return_value=(-1080, -720, 3000, 1920), create=True):
        out_d = tmp_path / "neg.png"
        blind_gap.export(FakeDesktop(), {"box": [-400, -200, 300, 200]}, out_d)
        m_grab.assert_called_once_with(bbox=(-400, -200, -100, 0), all_screens=True)


# Phase C & B17: Report integrity, win32_probe pointer signatures, and grid edge strip
def test_phase_c_report_integrity_and_win32_types():
    import win32_probe
    import h1_canvas_probe
    import h1b_latency_cluster
    import h2_desktop_gate0
    import h2_desktop_grid

    assert win32_probe._u32.LoadCursorW.restype == ctypes.c_void_p
    avoid = [(40, 40, 180, 56), (40, 460, 420, 44)]
    pts = h2_desktop_gate0.dead_points((0, 0, 960, 600), avoid, count=10)
    assert len(pts) == 10
    for x, y in pts:
        assert not any(h2_desktop_gate0.contains(a, x, y, pad=6) for a in avoid)

    # B17: grid_axes covers trailing strip without leaving > step/2 unprobed
    xs, ys = h1_canvas_probe.grid_axes({"x": 0, "y": 0, "w": 960, "h": 600}, 76)
    assert 960 - xs[-1] <= 38
    assert len(h1b_latency_cluster.grid({"x": 0, "y": 0, "w": 960, "h": 600}, 76)) == len(xs) * len(ys)
    gpts, gstep = h2_desktop_grid.grid_points({"x": 0, "y": 0, "w": 960, "h": 600}, 100)
    assert gstep == 76 and len(gpts) == len(xs) * len(ys)

    # Verify h2_desktop_grid uses dynamic gate0 rows
    sample_gate0 = {
        "targets": {
            "canvas": {"uia_recall": 0.0, "uia_nodes": 50, "p_hand_custom_given_clickable": 0.9,
                       "p_hand_custom_given_dead": 0.0, "settle_ms": 15, "control_group": False},
            "notepad": {"uia_recall": 1.0, "uia_nodes": 120, "p_hand_custom_given_clickable": 0.0,
                        "p_hand_custom_given_dead": 0.0, "settle_ms": 5, "control_group": True},
        },
        "gate2a": {"canvas": {"hand_rate": 0.9, "dead_fp": 0.0, "passes_gate_2a": True}},
        "gate2a_unlock": True,
    }
    rows_md = h2_desktop_grid._gate0_rows_from_json(sample_gate0)
    assert "0.0% (blind)" in rows_md and "90.0%" in rows_md and "control group" in rows_md


# Opt-Merge: Direct CDP WebSocket transport, border-box ablation consistency, zero-discover action, and stale guards
def test_opt_merge_direct_ws_targeted_freshness_and_reconnect(tmp_path):
    from engine import browser_cdp

    html = """<!doctype html><html><body style="margin:20px;height:1800px">
      <button id="b1">NativeBtn</button>
      <button id="b2">MoveMe</button>
      <button id="b3">DisableMe</button>
      <div id="out">0</div>
      <script>
        document.getElementById('b1').onclick = () => {
          const o = document.getElementById('out');
          o.textContent = String(Number(o.textContent) + 1);
        };
      </script>
    </body></html>"""
    p_html = tmp_path / "opt_merge.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True, viewport=(1280, 720))
    try:
        assert isinstance(s.cdp, browser_cdp.DirectCdpClient), f"expected DirectCdpClient, got {type(s.cdp)}"
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)

        b1 = next(r for r in api.resolver.records if r["name"] == "NativeBtn")
        dom_rect = s.page.evaluate("() => { const r=document.getElementById('b1').getBoundingClientRect(); return [r.x,r.y,r.width,r.height]; }")
        assert max(abs(b1["box"][i] - dom_rect[i]) for i in range(4)) <= 1.0, (
            f"border-box mismatch: discover={b1['box']} vs dom={dom_rect}"
        )

        # Simulate transient WS socket drop -> DirectCdpClient must auto-reconnect cleanly
        s.cdp._loop.call_soon_threadsafe(lambda: s.cdp._loop.create_task(s.cdp._ws.close()))
        time.sleep(0.1)

        with mock.patch.object(s, "discover", wraps=s.discover) as spy_disc:
            res = api.execute_action(b1["id"], "click")
            assert res["ok"] is True and s.page.inner_text("#out") == "1"
            assert spy_disc.call_count == 0, f"execute_action unexpectedly ran full discover() {spy_disc.call_count} times"

        # Verify moved > 2px, disabled dynamically, and scrolled out of viewport raise StaleElementError via verify_fresh
        api.discover_interactables(export_crops=False)
        b2 = next(r for r in api.resolver.records if r["name"] == "MoveMe")
        s.page.evaluate("() => { document.getElementById('b2').style.marginLeft = '40px'; }")
        with pytest.raises(StaleElementError):
            api.execute_action(b2["id"], "click")

        api.discover_interactables(export_crops=False)
        b3 = next(r for r in api.resolver.records if r["name"] == "DisableMe")
        s.page.evaluate("() => { document.getElementById('b3').disabled = true; }")
        with pytest.raises(StaleElementError):
            api.execute_action(b3["id"], "click")

        api.discover_interactables(export_crops=False)
        b1 = next(r for r in api.resolver.records if r["name"] == "NativeBtn")
        s.page.evaluate("() => window.scrollTo(0, 700)")
        with pytest.raises(StaleElementError):
            api.execute_action(b1["id"], "click")
    finally:
        s.close()


# Regressions for live stress-test findings ERR-01, ERR-02, ERR-03, ERR-06, ERR-07, ERR-16
def test_err01_err03_err06_err07_wrapper_pruning_css_hover_and_clipped_click(tmp_path):
    html = """<!doctype html><html><body style="margin:0;height:1400px" onclick="void 0">
      <style>.figure:hover .figcaption{display:block}.figcaption{display:none}</style>
      <button id="btn" style="margin-top:40px"><span>InnerBtn</span><svg width="16" height="16"></svg></button>
      <button id="topclip" style="position:fixed;left:220px;top:-12px;width:120px;height:36px"
              onclick="document.getElementById('out').textContent='clipped_ok'">ClippedBtn</button>
      <div class="figure" style="width:160px;height:140px;margin-top:40px">
        <div style="width:160px;height:100px;background:#ccc">Card</div>
        <div class="figcaption"><a id="vp" href="#vp">View profile</a></div>
      </div>
      <div id="out">none</div>
    </body></html>"""
    p_html = tmp_path / "err_regress.html"
    p_html.write_text(html, encoding="utf-8")
    s = BrowserSession(url=p_html.as_uri(), headless=True, viewport=(1280, 720))
    try:
        api = Api(s, state_path=tmp_path / "state.json")
        api.discover_interactables(export_crops=False)
        # ERR-01 / ERR-07: No root 1280x720 body wrapper, and nested span/svg inside button collapsed
        assert all(r["box"][2] * r["box"][3] < 0.85 * 1280 * 720 for r in api.resolver.records)
        btn_matches = [r for r in api.resolver.records if "InnerBtn" in r.get("name", "")]
        assert len(btn_matches) == 1 and btn_matches[0]["role"] == "button"

        # ERR-06: CSS :hover descendant reveal container discovered & hovering reveals child link
        fig = next((r for r in api.resolver.records if r.get("source") == "css:hover"), None)
        assert fig is not None, f"CSS :hover container missed: {api.resolver.records}"
        hres = api.hover_element(fig["id"], wait_ms=80)
        assert any("View profile" in a["name"] for a in hres["added"]), hres

        # ERR-03: Partially top-clipped fixed button clicks inside visible viewport intersection (y >= 0)
        api.discover_interactables(export_crops=False)
        clip_btn = next(r for r in api.resolver.records if r.get("name") == "ClippedBtn")
        cres = api.execute_action(clip_btn["id"], "click")
        assert cres["mechanism"]["y"] >= 0, f"Clicked above viewport: {cres}"
        assert s.page.inner_text("#out") == "clipped_ok"
    finally:
        s.close()


def test_err02_navigation_mid_signature_and_revision_advance(tmp_path):
    p_b = tmp_path / "b.html"
    p_b.write_text("<!doctype html><html><title>Page B</title><body><h1>Arrived B</h1></body></html>", encoding="utf-8")
    p_a = tmp_path / "a.html"
    p_a.write_text(f"<!doctype html><html><title>Page A</title><body><a id='go' href='{p_b.name}'>NextB</a></body></html>", encoding="utf-8")
    s = BrowserSession(url=p_a.as_uri(), headless=True)
    try:
        api = Api(s, state_path=tmp_path / "state_nav.json")
        api.discover_interactables(export_crops=False)
        link = next(r for r in api.resolver.records if r["name"] == "NextB")
        rev_before = api.resolver.revision
        # Simulate Playwright throwing mid-navigation on post-action signature evaluate
        orig_eval = s.page.evaluate
        call_n = {"n": 0}

        def flaky_eval(expr, *args, **kwargs):
            call_n["n"] += 1
            if "activeElement" in expr and call_n["n"] >= 2:
                raise RuntimeError("Page.evaluate: Execution context was destroyed, most likely because of a navigation")
            return orig_eval(expr, *args, **kwargs)

        with mock.patch.object(s.page, "evaluate", side_effect=flaky_eval):
            res = api.execute_action(link["id"], "click")
        assert res["ok"] is True and api.resolver.revision > rev_before
    finally:
        s.close()


@pytest.mark.windows_desktop
@pytest.mark.skipif(_SKIP_DESKTOP, reason="Requires Windows UIA / interactive desktop session")
def test_err16_desktop_toggle_signature_verified(tmp_path):
    html = """<!doctype html><html><body>
      <input id="chk" type="checkbox" aria-label="ToggleVerifyCheck" style="width:28px;height:28px">
    </body></html>"""
    before = _windows_by_class("Chrome_WidgetWin_1")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--window-position=40,40", "--window-size=640,480",
                                                    "--force-renderer-accessibility"])
        pg = b.new_page()
        pg.set_content(html)
        pg.wait_for_timeout(400)
        hwnd = next(iter(_windows_by_class("Chrome_WidgetWin_1") - before))
        ds = DesktopSession(hwnd)
        try:
            api = Api(ds, state_path=tmp_path / "state_uia.json")
            api.discover_interactables(export_crops=False)
            chk = next(r for r in api.resolver.records if r["name"] == "ToggleVerifyCheck")
            res = api.execute_action(chk["id"], "click")
            assert res["verified"] is True, f"ToggleState delta not detected: {res}"
            assert "toggle=" in json.dumps(res["state_delta"]), res
        finally:
            ds.close()
            b.close()

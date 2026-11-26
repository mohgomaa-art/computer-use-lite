# SPDX-License-Identifier: Apache-2.0
"""Integration, security, lifecycle, and overhead verification for computer_use_lite.mcp_server."""
import asyncio
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from unittest import mock

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image
import psutil
import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from computer_use_lite import Api, BrowserSession, blind_gap, desktop_uia  # noqa: E402
from computer_use_lite.mcp_server import build_server  # noqa: E402

_SKIP_DESKTOP = sys.platform != "win32" or os.environ.get("CUL_SKIP_DESKTOP") == "1"

_FORM_HTML = """<!doctype html><html><body style="margin:20px;height:1800px;font-family:sans-serif">
  <h1>MCP Form Fixture</h1>
  <label for="user">Username</label>
  <input id="user" aria-label="Username" type="text" value="">
  <label for="pw">SecretPass</label>
  <input id="pw" aria-label="SecretPass" type="password" value="">
  <button id="submit" onclick="
    const v = document.getElementById('user').value;
    document.getElementById('status_btn').textContent = 'Result:' + v;
    document.getElementById('res_val').value = 'Result:' + v;
  ">Submit</button>
  <button id="status_btn">Result:pending</button>
  <input id="res_val" aria-label="ResultOutput" type="text" value="pending"
         onkeydown="if(event.key==='Enter'){this.value='KeyConfirmed:' + this.value;}">
  <a id="to_p2" href="/page2">Go Page 2</a>
  <div style="height:1000px"></div>
  <button id="bottom_btn" onclick="this.textContent='BottomClicked'">BottomAction</button>
</body></html>"""

_PAGE2_HTML = """<!doctype html><html><body style="margin:20px">
  <h1>Page Two Fixture</h1>
  <button id="p2_btn" onclick="this.textContent='Page2Clicked'">Page2Action</button>
</body></html>"""

_HOVER_HTML = """<!doctype html><html><body style="margin:20px">
  <button id="menu" onmouseenter="document.getElementById('sub').style.display='inline-block'">HoverMenu</button>
  <button id="sub" style="display:none" onclick="this.textContent='SubClicked'">SubReveal</button>
</body></html>"""

_CSS_HOVER_HTML = """<!doctype html><html><body style="margin:20px">
  <style>.figure:hover .figcaption{display:block}.figcaption{display:none}</style>
  <div class="figure" style="width:160px;height:140px">
    <div style="width:160px;height:100px;background:#ccc">AvatarCard</div>
    <div class="figcaption"><a id="vp" href="/page2">ViewProfile</a></div>
  </div>
</body></html>"""

_CANVAS_HTML = """<!doctype html><html><body style="margin:0;padding:12px">
  <canvas id="c" width="900" height="520" style="display:block;border:1px solid #333"></canvas>
  <input id="canvas_out" aria-label="CanvasClickCoord" type="text" value="none">
  <script>
    const c = document.getElementById('c');
    const g = c.getContext('2d');
    g.fillStyle = '#1b4965';
    g.fillRect(0, 0, 900, 520);
    g.fillStyle = '#ffd166';
    g.fillRect(100, 100, 200, 120);
    c.addEventListener('click', (e) => {
      const r = c.getBoundingClientRect();
      document.getElementById('canvas_out').value =
        'clicked:' + Math.round(e.clientX - r.left) + ',' + Math.round(e.clientY - r.top);
    });
  </script>
</body></html>"""


class _FixtureHttpServer:
    """Thread-backed local HTTP test server for http:// MCP E2E runs."""

    def __init__(self):
        routes = {
            "/": _FORM_HTML.encode("utf-8"),
            "/page2": _PAGE2_HTML.encode("utf-8"),
            "/hover": _HOVER_HTML.encode("utf-8"),
            "/css_hover": _CSS_HOVER_HTML.encode("utf-8"),
            "/canvas": _CANVAS_HTML.encode("utf-8"),
        }

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = routes.get(self.path.split("?", 1)[0])
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        self._srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        port = self._srv.server_address[1]
        self.base_url = f"http://127.0.0.1:{port}"
        return self

    def __exit__(self, *exc):
        self._srv.shutdown()
        self._srv.server_close()
        self._thread.join(timeout=2.0)


def _server_params(extra_env: dict[str, str] | None = None) -> StdioServerParameters:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUNBUFFERED"] = "1"
    env.pop("CUL_MCP_ALLOW_FILE_URLS", None)
    if extra_env:
        env.update(extra_env)
    return StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "computer_use_lite.mcp_server"],
        cwd=str(ROOT),
        env=env,
    )


def _parse_session_and_elements(text: str) -> tuple[str, int, dict[str, list[str]]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    sid = None
    rev = 0
    for part in lines[0].split("|"):
        part = part.strip()
        if part.startswith("SESSION:"):
            sid = part.split(":", 1)[1].strip()
    for part in lines[1].split("|"):
        part = part.strip()
        if part.startswith("REV:"):
            rev = int(part.split(":", 1)[1].strip())
    elements: dict[str, list[str]] = {}
    for ln in lines[2:]:
        cols = ln.split("|")
        if len(cols) >= 4:
            elements[cols[0]] = cols
    assert sid is not None, f"Missing SESSION header in:\n{text}"
    return sid, rev, elements


def _find_by_name(elements: dict[str, list[str]], substr: str, role: str | None = None) -> str:
    low = substr.lower()
    for eid, cols in elements.items():
        if role and cols[1] != role:
            continue
        if low in (cols[2] or "").lower():
            return eid
    raise AssertionError(f"Element containing {substr!r} (role={role!r}) not found in {list(elements.values())}")


def _children_named(parent_pid: int, substring: str) -> set[int]:
    try:
        proc = psutil.Process(parent_pid)
        return {
            c.pid
            for c in proc.children(recursive=True)
            if substring in (c.name() or "").lower()
        }
    except psutil.NoSuchProcess:
        return set()


def test_mcp_tool_roster_annotations_and_browser_workflow():
    async def scenario():
        with _FixtureHttpServer() as srv, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    init = await client.initialize()
                    assert init.serverInfo.name == "computer-use-lite"

                    tools_res = await client.list_tools()
                    by_name = {t.name: t for t in tools_res.tools}
                    expected = {
                        "open_browser", "list_desktop_windows", "open_desktop",
                        "close_session", "list_sessions", "discover", "inspect",
                        "act", "hover", "navigate", "scroll", "press_key", "click_at",
                    }
                    assert set(by_name) == expected
                    assert by_name["discover"].annotations.readOnlyHint is True
                    assert by_name["inspect"].annotations.readOnlyHint is True
                    assert by_name["close_session"].annotations.destructiveHint is True
                    assert by_name["act"].annotations.openWorldHint is True

                    # 1. Open browser on local http:// form; confirm zero unsolicited images
                    opened = await client.call_tool("open_browser", {"url": f"{srv.base_url}/", "headless": True})
                    assert not opened.isError
                    assert [c.type for c in opened.content] == ["text"]
                    sid, rev1, els = _parse_session_and_elements(opened.content[0].text)

                    # 2. Password element value is redacted on inspect & omitted on act
                    pw_id = _find_by_name(els, "SecretPass", role="textbox")
                    pw_info = json.loads((await client.call_tool(
                        "inspect", {"session_id": sid, "element_id": pw_id}
                    )).content[0].text)
                    assert pw_info["value"] == "[REDACTED]"
                    pw_act = await client.call_tool("act", {
                        "session_id": sid, "element_id": pw_id,
                        "action": "type", "value": "UltraSecret!42",
                    })
                    assert not pw_act.isError
                    assert "UltraSecret!42" not in pw_act.content[0].text

                    # 3. Type into Username, click Submit, verify DOM update via MCP inspect
                    d2 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els2 = _parse_session_and_elements(d2.content[0].text)
                    assert all(c.type == "text" for c in d2.content)
                    user_id = _find_by_name(els2, "Username", role="textbox")
                    await client.call_tool("act", {"session_id": sid, "element_id": user_id, "action": "type", "value": "NileAgent"})
                    d3 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els3 = _parse_session_and_elements(d3.content[0].text)
                    submit_id = _find_by_name(els3, "Submit", role="button")
                    act_click = await client.call_tool("act", {"session_id": sid, "element_id": submit_id, "action": "click"})
                    assert json.loads(act_click.content[0].text)["ok"] is True

                    d4 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els4 = _parse_session_and_elements(d4.content[0].text)
                    out_id = _find_by_name(els4, "ResultOutput", role="textbox")
                    out_info = json.loads((await client.call_tool(
                        "inspect", {"session_id": sid, "element_id": out_id}
                    )).content[0].text)
                    assert out_info["value"] == "Result:NileAgent"

                    # 4. Focus + Enter key press advances key handler and invalidates revision
                    await client.call_tool("act", {"session_id": sid, "element_id": out_id, "action": "focus"})
                    kp = await client.call_tool("press_key", {"session_id": sid, "key": "Enter"})
                    assert json.loads(kp.content[0].text)["ok"] is True

                    # Stale element from before press_key must be rejected cleanly
                    stale_try = await client.call_tool("act", {"session_id": sid, "element_id": out_id, "action": "click"})
                    assert stale_try.isError is True
                    assert json.loads(stale_try.content[0].text)["error_type"] == "StaleElementError"

                    d5 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els5 = _parse_session_and_elements(d5.content[0].text)
                    out_id2 = _find_by_name(els5, "ResultOutput", role="textbox")
                    out_info2 = json.loads((await client.call_tool(
                        "inspect", {"session_id": sid, "element_id": out_id2}
                    )).content[0].text)
                    assert out_info2["value"] == "KeyConfirmed:Result:NileAgent"

                    # 5. Scroll down reveals bottom button after refresh
                    await client.call_tool("scroll", {"session_id": sid, "dy": 900, "dx": 0})
                    d6 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els6 = _parse_session_and_elements(d6.content[0].text)
                    bottom_id = _find_by_name(els6, "BottomAction")
                    assert not (await client.call_tool("act", {"session_id": sid, "element_id": bottom_id, "action": "click"})).isError

                    # 6. Navigate goto & back
                    nav2 = await client.call_tool("navigate", {
                        "session_id": sid, "action": "goto", "url": f"{srv.base_url}/page2", "auto_discover": True
                    })
                    assert not nav2.isError
                    _, _, els_p2 = _parse_session_and_elements(nav2.content[0].text)
                    _find_by_name(els_p2, "Page2Action")

                    nav_back = await client.call_tool("navigate", {"session_id": sid, "action": "back"})
                    assert srv.base_url in json.loads(nav_back.content[0].text)["url"]

                    # 7. Hover reveal (JS onmouseenter + pure CSS :hover card)
                    nav_h = await client.call_tool("navigate", {
                        "session_id": sid, "action": "goto", "url": f"{srv.base_url}/hover", "auto_discover": True
                    })
                    _, _, els_h = _parse_session_and_elements(nav_h.content[0].text)
                    menu_id = _find_by_name(els_h, "HoverMenu")
                    hov = json.loads((await client.call_tool(
                        "hover", {"session_id": sid, "element_id": menu_id, "wait_ms": 150}
                    )).content[0].text)
                    assert any("SubReveal" in a["name"] for a in hov["added"])

                    # 7b. Pure CSS :hover trigger + act() click updates list_sessions() target URL
                    nav_ch = await client.call_tool("navigate", {
                        "session_id": sid, "action": "goto", "url": f"{srv.base_url}/css_hover", "auto_discover": True
                    })
                    _, _, els_ch = _parse_session_and_elements(nav_ch.content[0].text)
                    fig_id = _find_by_name(els_ch, "figure")
                    chov = json.loads((await client.call_tool(
                        "hover", {"session_id": sid, "element_id": fig_id, "wait_ms": 150}
                    )).content[0].text)
                    assert any("ViewProfile" in a["name"] for a in chov["added"])
                    vp_id = next(a["id"] for a in chov["added"] if "ViewProfile" in a["name"])
                    vp_click = await client.call_tool("act", {"session_id": sid, "element_id": vp_id, "action": "click"})
                    assert not vp_click.isError
                    await client.call_tool("discover", {"session_id": sid})
                    sessions_now = json.loads((await client.call_tool("list_sessions", {})).content[0].text)
                    assert sessions_now["sessions"][0]["target"].endswith("/page2")

                    closed = json.loads((await client.call_tool("close_session", {"session_id": sid})).content[0].text)
                    assert closed["ok"] is True
                    listed = json.loads((await client.call_tool("list_sessions", {})).content[0].text)
                    assert listed["count"] == 0

    anyio.run(scenario)


def test_mcp_blind_canvas_image_content_and_click_at():
    async def scenario():
        with _FixtureHttpServer() as srv, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    opened = await client.call_tool("open_browser", {"url": f"{srv.base_url}/canvas", "headless": True})
                    assert not opened.isError
                    types = [c.type for c in opened.content]
                    assert types == ["text", "image"], f"Expected inline ImageContent for blind canvas, got {types}"
                    assert opened.content[1].mimeType == "image/png"
                    png_raw = base64.b64decode(opened.content[1].data)
                    img = Image.open(io.BytesIO(png_raw))
                    assert img.width >= 300 and img.height >= 200

                    sid, _, els = _parse_session_and_elements(opened.content[0].text)
                    assert "blind0" in els
                    bx, by, _, _ = [int(v) for v in els["blind0"][3].split(",")]

                    # Click inside canvas blind region using bounded click_at
                    clk = await client.call_tool("click_at", {"session_id": sid, "x": bx + 150, "y": by + 160})
                    assert not clk.isError

                    # Off-viewport coordinate must be refused
                    bad_clk = await client.call_tool("click_at", {"session_id": sid, "x": 5000, "y": 5000})
                    assert bad_clk.isError is True

                    d2 = await client.call_tool("discover", {"session_id": sid})
                    _, _, els2 = _parse_session_and_elements(d2.content[0].text)
                    out_id = _find_by_name(els2, "CanvasClickCoord")
                    info = json.loads((await client.call_tool(
                        "inspect", {"session_id": sid, "element_id": out_id}
                    )).content[0].text)
                    assert info["value"].startswith("clicked:"), info
                    await client.call_tool("close_session", {"session_id": sid})

    anyio.run(scenario)


def test_mcp_security_guards_multi_session_and_errors():
    async def scenario():
        with _FixtureHttpServer() as srv, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()

                    # Blocked schemes
                    for bad_url in ("file:///C:/Windows/win.ini", "javascript:alert(1)", "data:text/html,x", "chrome://settings"):
                        res = await client.call_tool("open_browser", {"url": bad_url})
                        assert res.isError is True, f"Should block {bad_url}"
                        assert json.loads(res.content[0].text)["error_type"] == "PermissionDenied"

                    # Multi-session isolation
                    r1 = await client.call_tool("open_browser", {"url": f"{srv.base_url}/", "headless": True})
                    r2 = await client.call_tool("open_browser", {"url": f"{srv.base_url}/page2", "headless": True})
                    s1, _, e1 = _parse_session_and_elements(r1.content[0].text)
                    s2, _, e2 = _parse_session_and_elements(r2.content[0].text)
                    assert s1 != s2

                    listed = json.loads((await client.call_tool("list_sessions", {})).content[0].text)
                    assert listed["count"] == 2

                    # Navigating session 1 to javascript: is also blocked
                    bad_nav = await client.call_tool("navigate", {"session_id": s1, "url": "javascript:void(0)"})
                    assert bad_nav.isError is True
                    assert json.loads(bad_nav.content[0].text)["error_type"] == "PermissionDenied"

                    # Blocked OS modifier key
                    bad_key = await client.call_tool("press_key", {"session_id": s1, "key": "Win+r"})
                    assert bad_key.isError is True

                    # Unknown session / element yield recoverable JSON errors without killing server
                    unk_sess = await client.call_tool("discover", {"session_id": "missing_99"})
                    assert unk_sess.isError is True
                    assert json.loads(unk_sess.content[0].text)["error_type"] == "SessionNotFound"

                    unk_el = await client.call_tool("inspect", {"session_id": s1, "element_id": "does_not_exist"})
                    assert unk_el.isError is True
                    assert json.loads(unk_el.content[0].text)["error_type"] == "ElementNotFound"

                    # Close s1, confirm s2 still healthy
                    await client.call_tool("close_session", {"session_id": s1})
                    p2_btn = _find_by_name(e2, "Page2Action")
                    assert not (await client.call_tool("act", {"session_id": s2, "element_id": p2_btn, "action": "click"})).isError
                    await client.call_tool("close_session", {"session_id": s2})

    anyio.run(scenario)


def test_mcp_abrupt_eof_leaves_zero_orphan_browser_processes():
    async def scenario():
        with _FixtureHttpServer() as srv, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            server_pids: set[int] = set()
            chrome_pids: set[int] = set()
            async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    opened = await client.call_tool("open_browser", {"url": f"{srv.base_url}/", "headless": True})
                    assert not opened.isError
                    # Locate spawned mcp_server python processes and inspect its child chromium PIDs
                    for p in psutil.process_iter(["pid", "cmdline"]):
                        cmd = " ".join(p.info.get("cmdline") or [])
                        if "computer_use_lite.mcp_server" in cmd:
                            children = _children_named(p.pid, "chrome")
                            if children:
                                server_pids.add(p.pid)
                                chrome_pids.update(children)
                    assert chrome_pids, "Expected live Chromium subprocess under MCP server"
                    # Intentionally do NOT call close_session(); exit client context -> closes stdin (EOF).

            # Poll briefly for clean teardown after stdin EOF
            deadline = time.time() + 5.0
            while time.time() < deadline:
                alive = [pid for pid in chrome_pids if psutil.pid_exists(pid)]
                if not alive:
                    break
                time.sleep(0.1)
            alive_after = [pid for pid in chrome_pids if psutil.pid_exists(pid)]
            assert not alive_after, f"Orphaned Chromium PIDs remained after stdin EOF: {alive_after}"

    anyio.run(scenario)


@pytest.mark.windows_desktop
@pytest.mark.skipif(_SKIP_DESKTOP, reason="Requires Windows UIA / interactive desktop session")
def test_mcp_windows_desktop_notepad_flow():
    tmp = Path(tempfile.gettempdir()) / f"cul_mcp_notepad_{int(time.time())}.txt"
    tmp.write_text("", encoding="utf-8")
    before = {w["hwnd"] for w in desktop_uia.list_windows(class_name="Notepad", limit=40)}
    proc = subprocess.Popen(["notepad.exe", str(tmp)])
    hwnd = None
    try:
        for _ in range(30):
            after = {w["hwnd"] for w in desktop_uia.list_windows(class_name="Notepad", limit=40)}
            new = after - before
            if new:
                hwnd = new.pop()
                break
            time.sleep(0.5)
        assert hwnd, "Notepad window failed to appear"

        async def scenario():
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
                async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                    async with ClientSession(read, write) as client:
                        await client.initialize()
                        listed = json.loads((await client.call_tool(
                            "list_desktop_windows", {"class_name": "Notepad", "limit": 20}
                        )).content[0].text)
                        assert any(w["hwnd"] == hwnd for w in listed["windows"])

                        opened = await client.call_tool("open_desktop", {"hwnd": hwnd})
                        assert not opened.isError
                        sid, _, els = _parse_session_and_elements(opened.content[0].text)
                        editor_id = next(eid for eid, cols in els.items() if cols[1] == "textbox")

                        acted = json.loads((await client.call_tool("act", {
                            "session_id": sid, "element_id": editor_id,
                            "action": "type", "value": "mcp desktop verified",
                        })).content[0].text)
                        assert acted["ok"] is True

                        inspected = json.loads((await client.call_tool(
                            "inspect", {"session_id": sid, "element_id": editor_id}
                        )).content[0].text)
                        assert (inspected.get("value") or "").startswith("mcp desktop verified")

                        await client.call_tool("close_session", {"session_id": sid})

        anyio.run(scenario)
    finally:
        if hwnd:
            try:
                desktop_uia._u32.PostMessageW(hwnd, 0x0010, 0, 0)
                time.sleep(0.4)
            except Exception:
                pass
        try:
            proc.terminate()
        except Exception:
            pass
        tmp.unlink(missing_ok=True)


def test_printwindow_fallback_in_blind_gap(tmp_path):
    class FakeDesktopSession:
        hwnd = 12345

    fake_img = Image.new("RGB", (320, 180), (10, 20, 30))
    out_png = tmp_path / "fallback.png"
    with mock.patch("PIL.ImageGrab.grab", side_effect=OSError("screen grab failed")), \
         mock.patch.object(blind_gap, "_virtual_screen", return_value=(0, 0, 1920, 1080)), \
         mock.patch.object(blind_gap, "_capture_hwnd_printwindow", return_value=fake_img) as m_pw:
        result = blind_gap.export(FakeDesktopSession(), {"box": [10, 20, 320, 180]}, out_png)
        assert m_pw.called
        assert Path(result).exists()
        assert Image.open(result).size == (320, 180)


def test_build_server_stdout_untouched_until_run():
    orig = sys.stdout
    server, mgr = build_server()
    assert sys.stdout is orig
    assert server.name == "computer-use-lite"
    mgr.close_all_sync()


def test_mcp_console_script_entrypoint():
    exe = shutil.which("computer-use-lite-mcp")
    if not exe:
        pytest.skip("computer-use-lite-mcp console script not installed on PATH")

    async def scenario():
        params = StdioServerParameters(command=exe, args=[], cwd=str(ROOT))
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    init = await client.initialize()
                    assert init.serverInfo.name == "computer-use-lite"
                    tools = await client.list_tools()
                    assert len(tools.tools) == 13

    anyio.run(scenario)


def test_err12_err13_err14_no_session_leak_untitled_proc_and_fg_error():
    from computer_use_lite import mcp_server, session_manager, snapshot

    async def scenario():
        mgr = session_manager.SessionManager()
        with _FixtureHttpServer() as srv:
            with mock.patch.object(mgr, "_discover_inside_worker", side_effect=RuntimeError("boom discover")):
                with pytest.raises(RuntimeError, match="boom discover"):
                    await mgr.open_browser(url=f"{srv.base_url}/", headless=True, auto_discover=True)
            assert mgr.list_sessions() == [], f"Failed open leaked session: {mgr.list_sessions()}"

        if sys.platform == "win32":
            class FakeDesktop:
                hwnd = 65848
                def bounds(self):
                    return [0, 1032, 1920, 48]
                def close(self):
                    pass

            with mock.patch.object(session_manager, "_list_desktop_windows", return_value=[]), \
                 mock.patch.object(snapshot, "window", return_value={"hwnd": 65848, "process": "explorer.exe", "title": ""}), \
                 mock.patch.object(session_manager, "DesktopSession", return_value=FakeDesktop()), \
                 mock.patch("ctypes.WinDLL") as m_dll:
                u32 = m_dll.return_value
                u32.IsWindow.return_value = 1
                u32.IsWindowVisible.return_value = 1
                res = await mgr.open_desktop(hwnd=65848, auto_discover=False)
                assert res["process_name"] == "explorer.exe"
                await mgr.close_all()

        fg_res = mcp_server._error_result(RuntimeError("Foreground safety abort: expected hwnd=65848, active foreground=197140"))
        fg_payload = json.loads(fg_res.content[0].text)
        assert fg_res.isError is True and fg_payload["error_type"] == "ForegroundMismatch" and fg_payload["recoverable"] is True

    anyio.run(scenario)


def benchmark_mcp_overhead(n_cold: int = 2, n_warm: int = 15) -> dict:
    """Compare live stdio MCP discover/act latency against direct in-process Api."""
    with _FixtureHttpServer() as srv:
        # 1. Direct Api baseline
        s = BrowserSession(url=f"{srv.base_url}/", headless=True, viewport=(1280, 720))
        try:
            with tempfile.TemporaryDirectory() as td:
                api = Api(s, state_path=Path(td) / "s.json")
                api.discover_interactables(export_crops=False)
                btn = next(r for r in api.resolver.records if "Result:" in r.get("name", "") or "Submit" in r.get("name", ""))
                direct_disc, direct_act = [], []
                for i in range(n_cold + n_warm):
                    t0 = time.perf_counter()
                    api.discover_interactables(export_crops=False)
                    dt_d = (time.perf_counter() - t0) * 1000.0
                    btn = next(r for r in api.resolver.records if "Submit" in r.get("name", ""))
                    t1 = time.perf_counter()
                    api.execute_action(btn["id"], "click")
                    dt_a = (time.perf_counter() - t1) * 1000.0
                    if i >= n_cold:
                        direct_disc.append(dt_d)
                        direct_act.append(dt_a)
        finally:
            s.close()

        # 2. Live MCP stdio loop
        async def run_mcp():
            mcp_disc, mcp_act = [], []
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
                async with stdio_client(_server_params(), errlog=errlog) as (read, write):
                    async with ClientSession(read, write) as client:
                        await client.initialize()
                        opened = await client.call_tool("open_browser", {"url": f"{srv.base_url}/", "headless": True})
                        sid, _, _ = _parse_session_and_elements(opened.content[0].text)
                        for i in range(n_cold + n_warm):
                            t0 = time.perf_counter()
                            d_res = await client.call_tool("discover", {"session_id": sid, "export_crops": False})
                            dt_d = (time.perf_counter() - t0) * 1000.0
                            _, _, els = _parse_session_and_elements(d_res.content[0].text)
                            btn_id = _find_by_name(els, "Submit")
                            t1 = time.perf_counter()
                            await client.call_tool("act", {"session_id": sid, "element_id": btn_id, "action": "click"})
                            dt_a = (time.perf_counter() - t1) * 1000.0
                            if i >= n_cold:
                                mcp_disc.append(dt_d)
                                mcp_act.append(dt_a)
                        await client.call_tool("close_session", {"session_id": sid})
            return mcp_disc, mcp_act

        mcp_disc, mcp_act = anyio.run(run_mcp)

    def pct(vals, q):
        svals = sorted(vals)
        idx = (len(svals) - 1) * q
        lo = int(idx)
        hi = min(lo + 1, len(svals) - 1)
        return round(svals[lo] * (1.0 - (idx - lo)) + svals[hi] * (idx - lo), 2)

    return {
        "n_warm": n_warm,
        "direct_discover_p50_ms": pct(direct_disc, 0.50),
        "mcp_discover_p50_ms": pct(mcp_disc, 0.50),
        "discover_overhead_p50_ms": round(pct(mcp_disc, 0.50) - pct(direct_disc, 0.50), 2),
        "direct_act_p50_ms": pct(direct_act, 0.50),
        "mcp_act_p50_ms": pct(mcp_act, 0.50),
        "act_overhead_p50_ms": round(pct(mcp_act, 0.50) - pct(direct_act, 0.50), 2),
        "direct_discover_p95_ms": pct(direct_disc, 0.95),
        "mcp_discover_p95_ms": pct(mcp_disc, 0.95),
        "direct_act_p95_ms": pct(direct_act, 0.95),
        "mcp_act_p95_ms": pct(mcp_act, 0.95),
    }


if __name__ == "__main__":
    summary = benchmark_mcp_overhead()
    print(json.dumps(summary, indent=2))

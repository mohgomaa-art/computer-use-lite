# SPDX-License-Identifier: Apache-2.0
"""Ground-truth corpus server and isolated Windows desktop app lifecycle managers."""
import ctypes
import http.server
import socketserver
import subprocess
import tempfile
import threading
import time
from ctypes import wintypes
from pathlib import Path

import psutil

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_u32 = ctypes.WinDLL("user32", use_last_error=True)

_u32.IsWindowVisible.argtypes = [wintypes.HWND]
_u32.IsWindowVisible.restype = wintypes.BOOL
_u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetClassNameW.restype = ctypes.c_int
_u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_u32.GetWindowTextLengthW.restype = ctypes.c_int
_u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_u32.GetWindowTextW.restype = ctypes.c_int
_u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_u32.GetWindowThreadProcessId.restype = wintypes.DWORD
_u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_u32.PostMessageW.restype = wintypes.BOOL
_u32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
_u32.EnumWindows.restype = wintypes.BOOL


class _QuietHandler(http.server.BaseHTTPRequestHandler):
    routes = {}

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        body = self.routes.get(path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        return


class DualOriginCorpusServer:
    """Serve corpus_main.html on port A and corpus_iframe.html on port B (true OOPIF)."""

    def __init__(self):
        self._srv_a = None
        self._srv_b = None
        self._th_a = None
        self._th_b = None
        self.port_a = None
        self.port_b = None
        self.main_url = None
        self.iframe_url = None

    def __enter__(self):
        iframe_html = (FIXTURES_DIR / "corpus_iframe.html").read_text(encoding="utf-8")

        class HandlerB(_QuietHandler):
            routes = {"/corpus_iframe.html": iframe_html}

        self._srv_b = socketserver.ThreadingTCPServer(("127.0.0.1", 0), HandlerB)
        self.port_b = self._srv_b.server_address[1]
        self.iframe_url = f"http://127.0.0.1:{self.port_b}/corpus_iframe.html"

        main_html = (FIXTURES_DIR / "corpus_main.html").read_text(encoding="utf-8").replace(
            "__OOPIF_URL__", self.iframe_url
        )

        class HandlerA(_QuietHandler):
            routes = {"/corpus_main.html": main_html, "/": main_html}

        self._srv_a = socketserver.ThreadingTCPServer(("127.0.0.1", 0), HandlerA)
        self.port_a = self._srv_a.server_address[1]
        self.main_url = f"http://127.0.0.1:{self.port_a}/corpus_main.html"

        self._th_a = threading.Thread(target=self._srv_a.serve_forever, daemon=True)
        self._th_b = threading.Thread(target=self._srv_b.serve_forever, daemon=True)
        self._th_b.start()
        self._th_a.start()
        return self

    def __exit__(self, *exc):
        for srv in (self._srv_a, self._srv_b):
            if srv is not None:
                try:
                    srv.shutdown()
                    srv.server_close()
                except Exception:
                    pass


def extract_corpus_ground_truth(page):
    """Build exact ground-truth actionable elements from corpus_main + OOPIF iframe."""
    vw, vh = page.evaluate("() => [window.innerWidth, window.innerHeight]")
    main_items = page.evaluate(
        """([vw, vh]) => {
          const out = [];
          const vis = (r) => r.width > 1 && r.height > 1 && (r.right > 0 && r.left < vw && r.bottom > 0 && r.top < vh);
          const roleOf = (el) => {
            const explicit = el.getAttribute('role');
            if (explicit) return explicit;
            const tag = el.tagName.toLowerCase();
            if (tag === 'button') return 'button';
            if (tag === 'a') return 'link';
            if (tag === 'input' || tag === 'textarea') return 'textbox';
            if (tag === 'select') return 'combobox';
            return 'clickable';
          };
          const nameOf = (el) => {
            const al = el.getAttribute('aria-label');
            if (al) return al.trim();
            const lby = el.getAttribute('aria-labelledby');
            if (lby) {
              const ref = document.getElementById(lby);
              if (ref) return ref.textContent.trim();
            }
            if (el.id) {
              const lbl = document.querySelector(`label[for="${el.id}"]`);
              if (lbl) return lbl.textContent.trim();
            }
            return (el.innerText || el.textContent || el.getAttribute('placeholder') || '').trim();
          };
          const occluded = (el, r) => {
            const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
            const root = el.getRootNode();
            const hit = (root.elementFromPoint ? root.elementFromPoint(cx, cy) : document.elementFromPoint(cx, cy));
            if (!hit) return true;
            return !(el.contains(hit) || hit === el || (hit.getRootNode && hit.getRootNode().host === el));
          };
          const add = (el, category, idOverride, roleOverride, nameOverride) => {
            const r = el.getBoundingClientRect();
            const disabled = Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true');
            if (!vis(r) || disabled || occluded(el, r)) return;
            out.push({
              gt_id: idOverride || el.getAttribute('data-gt') || el.id,
              role: roleOverride || roleOf(el),
              name: nameOverride || nameOf(el),
              box: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10,
                    Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
              enabled: true,
              occluded: false,
              category,
            });
          };
          for (const el of document.querySelectorAll('[data-gt]')) {
            const gt = el.getAttribute('data-gt');
            let cat = 'main_dom';
            if (gt === 'aria_lbl_btn') cat = 'aria_labelledby';
            else if (gt === 'custom_div') cat = 'custom_div';
            else if (gt === 'switch_btn') cat = 'role_switch';
            else if (gt === 'svg_icon_btn') cat = 'svg_aria_label';
            else if (gt === 'modal_confirm_btn') cat = 'modal_dialog';
            else if (gt === 'dyn_btn' || gt === 'dyn_input') cat = 'dynamic_drawer';
            else if (gt === 'below_fold_btn' || gt === 'inner_top_btn' || gt === 'inner_bottom_btn') cat = 'scroll';
            add(el, cat);
          }
          const openHost = document.getElementById('open_shadow_host');
          if (openHost && openHost.shadowRoot) {
            const ob = openHost.shadowRoot.getElementById('open_shadow_btn');
            if (ob) add(ob, 'open_shadow_dom', 'open_shadow_btn');
          }
          for (const c of (window.__closedShadowControls || [])) {
            add(c.el, 'closed_shadow_dom', c.id, c.role, c.name);
          }
          return out;
        }""",
        [vw, vh],
    )

    # Append cross-origin OOPIF iframe controls via Playwright frame object + iframe viewport offset
    iframe_rect = page.evaluate(
        "() => { const r = document.getElementById('oopif_frame').getBoundingClientRect();"
        " return [r.x, r.y, r.width, r.height]; }"
    )
    if iframe_rect[2] > 1 and iframe_rect[3] > 1 and iframe_rect[1] < vh and iframe_rect[1] + iframe_rect[3] > 0:
        for fr in page.frames:
            if "corpus_iframe.html" in fr.url:
                sub = fr.evaluate(
                    """() => {
                      const out = [];
                      for (const el of document.querySelectorAll('[data-gt]')) {
                        const r = el.getBoundingClientRect();
                        if (r.width <= 1 || r.height <= 1) continue;
                        const role = el.tagName.toLowerCase() === 'button' ? 'button' : 'textbox';
                        const name = (el.innerText || el.getAttribute('placeholder') || '').trim();
                        out.push({
                          gt_id: el.getAttribute('data-gt'),
                          role, name,
                          local_box: [r.x, r.y, r.width, r.height],
                        });
                      }
                      return out;
                    }"""
                )
                for item in sub:
                    lx, ly, lw, lh = item["local_box"]
                    bx = round(iframe_rect[0] + lx, 1)
                    by = round(iframe_rect[1] + ly, 1)
                    if by + lh > 0 and by < vh:
                        main_items.append({
                            "gt_id": item["gt_id"],
                            "role": item["role"],
                            "name": item["name"],
                            "box": [bx, by, round(lw, 1), round(lh, 1)],
                            "enabled": True,
                            "occluded": False,
                            "category": "cross_origin_iframe",
                        })
    return main_items


def _enum_visible_windows():
    out = {}

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if _u32.IsWindowVisible(hwnd):
            cbuf = ctypes.create_unicode_buffer(128)
            _u32.GetClassNameW(hwnd, cbuf, 128)
            n = _u32.GetWindowTextLengthW(hwnd)
            tbuf = ctypes.create_unicode_buffer(max(n + 1, 1))
            if n > 0:
                _u32.GetWindowTextW(hwnd, tbuf, n + 1)
            pid = wintypes.DWORD()
            _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            out[hwnd] = {"hwnd": hwnd, "pid": pid.value, "class": cbuf.value, "title": tbuf.value}
        return True

    _u32.EnumWindows(cb, 0)
    return out


class DesktopTarget:
    """Context manager launching and safely tearing down an isolated Win11 app window."""

    def __init__(self, kind):
        self.kind = kind
        self.hwnd = None
        self.pid = None
        self.proc = None
        self._tmp_dir = None
        self._pw = None
        self._browser = None
        self._server = None
        self.extra = {}

    def __enter__(self):
        before = set(_enum_visible_windows())
        self._tmp_dir = tempfile.TemporaryDirectory(prefix=f"cul_bench_{self.kind}_")
        td = Path(self._tmp_dir.name)

        if self.kind == "notepad":
            scratch = td / "bench_note.txt"
            scratch.write_text("Computer Use Lite UIA benchmark line.\nSecond line.", encoding="utf-8")
            self.proc = subprocess.Popen(["notepad.exe", str(scratch)])
            self.hwnd, self.pid = self._wait_new_hwnd(before, class_name="Notepad", pid_hint=self.proc.pid)
        elif self.kind == "explorer":
            for i in range(1, 5):
                (td / f"sample_{i}.txt").write_text("x", encoding="utf-8")
            self.proc = subprocess.Popen(["explorer.exe", str(td)])
            self.hwnd, self.pid = self._wait_new_hwnd(before, class_name="CabinetWClass", timeout=15.0)
        elif self.kind == "chromium":
            from playwright.sync_api import sync_playwright
            self._server = DualOriginCorpusServer().__enter__()
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=False,
                args=["--window-position=40,40", "--window-size=1100,720", "--force-renderer-accessibility"],
            )
            page = self._browser.new_page(viewport={"width": 1060, "height": 640})
            page.goto(self._server.main_url, wait_until="load", timeout=30000)
            self.hwnd, self.pid = self._wait_new_hwnd(
                before, class_name="Chrome_WidgetWin_1", title_part="Adversarial Corpus", timeout=15.0
            )
            self.extra["url"] = self._server.main_url
        elif self.kind == "electron":
            obs = Path(r"C:\Program Files\Obsidian\Obsidian.exe")
            if not obs.exists():
                raise FileNotFoundError(f"Electron target missing: {obs}")
            ud = td / "obsidian_ud"
            ud.mkdir()
            self.proc = subprocess.Popen(
                [str(obs), f"--user-data-dir={ud}", "--force-renderer-accessibility", "--no-sandbox"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.hwnd, self.pid = self._wait_new_hwnd(before, class_name="Chrome_WidgetWin_1", timeout=20.0)
            time.sleep(2.0)  # allow Electron Chromium renderer DOM to finish painting
        else:
            raise ValueError(f"Unknown desktop target: {self.kind}")

        if not self.hwnd:
            raise RuntimeError(f"Timed out waiting for desktop target window: {self.kind}")
        return self

    def _wait_new_hwnd(self, before, class_name=None, pid_hint=None, title_part=None, timeout=12.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            cur = _enum_visible_windows()
            for h, info in cur.items():
                if pid_hint and info["pid"] == pid_hint and info["title"]:
                    return h, info["pid"]
                if h in before:
                    continue
                if class_name and info["class"] != class_name:
                    continue
                if title_part and title_part.lower() not in info["title"].lower():
                    continue
                if class_name or title_part:
                    return h, info["pid"]
            time.sleep(0.2)
        return None, None

    def __exit__(self, *exc):
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
        if self._server is not None:
            self._server.__exit__(*exc)
        if self.hwnd:
            try:
                _u32.PostMessageW(wintypes.HWND(self.hwnd), 0x0010, 0, 0)  # WM_CLOSE
                time.sleep(0.4)
            except Exception:
                pass
        if self.kind == "electron":
            if self.pid:
                try:
                    p = psutil.Process(self.pid)
                    for child in p.children(recursive=True):
                        child.terminate()
                    p.terminate()
                except Exception:
                    pass
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                except Exception:
                    pass
        elif self.proc and self.proc.poll() is None and self.kind not in ("explorer",):
            try:
                self.proc.terminate()
            except Exception:
                pass
        if self._tmp_dir is not None:
            try:
                self._tmp_dir.cleanup()
            except Exception:
                pass

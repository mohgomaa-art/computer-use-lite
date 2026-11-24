# SPDX-License-Identifier: Apache-2.0
"""Experiments 6, 7, 9: Isolated Browser CDP, Transport, and Incremental Observer benchmarks.

Exp 6: Current CDP (DOMSnapshot + scroll + getFullAXTree + N*getBoxModel)
       vs Optimized CDP ablation (scroll from DOMSnapshot + zero N*getBoxModel loop)
       vs Single-Frame JS DOM/ARIA Extractor
Exp 7: Playwright CDP Session transport vs Direct Persistent CDP WebSocket (`websockets`)
Exp 9: Repeated Full Discovery vs MutationObserver + IntersectionObserver + Runtime.addBinding
"""
import asyncio
import json
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import websockets
from playwright.sync_api import sync_playwright

from engine.browser_cdp import ROLES, BrowserSession, _attrs_dict, _is_ancestor, _text
from . import common
from .corpus import DualOriginCorpusServer, extract_corpus_ground_truth

REAL_WEB_TARGETS = [
    ("GitHub Trending", "real_web", "https://github.com/trending"),
    ("YouTube", "real_web", "https://www.youtube.com/"),
    ("Gmail sign-in", "real_web", "https://accounts.google.com/v3/signin/identifier?service=mail"),
    ("Google Maps", "real_canvas", "https://www.google.com/maps/@40.7580,-73.9855,17z"),
]

# Single-frame JS DOM/ARIA extractor (walks main DOM + open ShadowRoots; cannot see closed Shadow or OOPIF)
JS_SINGLE_FRAME_EXTRACTOR = r"""() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const ROLE_TAGS = { A: 'link', BUTTON: 'button', SELECT: 'combobox', TEXTAREA: 'textbox' };
  const INTERACTIVE_ROLES = new Set([
    'button','menuitem','tab','link','textbox','combobox','checkbox','radio','switch','clickable','listitem','treeitem'
  ]);
  const out = [];
  const seen = new Set();

  const accName = (el) => {
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim().slice(0, 80);
    const lby = el.getAttribute('aria-labelledby');
    if (lby) {
      const parts = lby.split(/\s+/).map(id => document.getElementById(id)?.textContent?.trim() || '').filter(Boolean);
      if (parts.length) return parts.join(' ').slice(0, 80);
    }
    if (el.id) {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl && lbl.textContent.trim()) return lbl.textContent.trim().slice(0, 80);
    }
    const parLbl = el.closest('label');
    if (parLbl && parLbl.textContent.trim()) return parLbl.textContent.trim().slice(0, 80);
    return (el.getAttribute('title') || el.getAttribute('placeholder') || el.getAttribute('alt') || el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
  };

  const roleOf = (el) => {
    const ar = (el.getAttribute('role') || '').toLowerCase().trim();
    if (ar && INTERACTIVE_ROLES.has(ar)) return ar;
    const tag = el.tagName;
    if (tag === 'A' && el.hasAttribute('href')) return 'link';
    if (tag in ROLE_TAGS && tag !== 'A') return ROLE_TAGS[tag];
    if (tag === 'INPUT') {
      const t = (el.getAttribute('type') || 'text').toLowerCase();
      if (t === 'hidden') return '';
      if (t === 'checkbox') return 'checkbox';
      if (t === 'radio') return 'radio';
      if (['button', 'submit', 'reset', 'image'].includes(t)) return 'button';
      return 'textbox';
    }
    if (el.hasAttribute('onclick')) return 'clickable';
    if (el.hasAttribute('tabindex') && el.getAttribute('tabindex') !== '-1') return 'clickable';
    return '';
  };

  const visit = (root) => {
    const all = root.querySelectorAll('*');
    for (const el of all) {
      let role = roleOf(el);
      let cs = null;
      if (!role) {
        if (el.tagName === 'DIV' || el.tagName === 'SPAN' || el.tagName === 'LI' || el.tagName === 'SECTION') {
          cs = getComputedStyle(el);
          if (cs.cursor === 'pointer') role = 'clickable';
        }
      }
      if (!role) {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      if (!cs) cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.pointerEvents === 'none') {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      const r = el.getBoundingClientRect();
      if (r.width <= 1 || r.height <= 1) {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      if (r.right <= 0 || r.left >= vw || r.bottom <= 0 || r.top >= vh) {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      const cx = Math.min(vw - 1, Math.max(0, r.left + r.width / 2));
      const cy = Math.min(vh - 1, Math.max(0, r.top + r.height / 2));
      const hit = (root.elementFromPoint ? root.elementFromPoint(cx, cy) : document.elementFromPoint(cx, cy));
      if (hit && !(el.contains(hit) || hit === el || (hit.getRootNode && hit.getRootNode().host === el) || (hit.tagName === 'LABEL' && hit.control === el))) {
        if (el.shadowRoot) visit(el.shadowRoot);
        continue;
      }
      if (!seen.has(el)) {
        seen.add(el);
        const tag = el.tagName;
        const isPw = tag === 'INPUT' && (el.getAttribute('type') || '').toLowerCase() === 'password';
        out.push({
          source: 'js_single_frame',
          role,
          name: accName(el),
          box: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
          enabled: true,
          occluded: false,
          is_password: isPw,
        });
      }
      if (el.shadowRoot) visit(el.shadowRoot);
    }
  };
  visit(document);
  return { elements: out, scanned_dom_nodes: document.querySelectorAll('*').length };
}"""


def _control_cdp_discover_with_meta(bs):
    """Run exact production `BrowserSession.discover()` while capturing raw IPC + byte count."""
    orig_send = bs.cdp.send
    ipc_calls = 0
    resp_bytes = 0

    def wrapped_send(method, params=None):
        nonlocal ipc_calls, resp_bytes
        ipc_calls += 1
        res = orig_send(method, params or {})
        resp_bytes += len(json.dumps(res))
        return res

    bs.cdp.send = wrapped_send
    try:
        els = bs.discover()
        return els, {"ipc_round_trips": ipc_calls + 1, "response_bytes": resp_bytes, "node_count": len(els)}
    finally:
        bs.cdp.send = orig_send


def _optimized_cdp_ablation(send_fn):
    """Same DOMSnapshot + AXTree signals WITHOUT N*getBoxModel loop, scroll eval, or O(N^2) occlusion."""
    snap = send_fn("DOMSnapshot.captureSnapshot", {
        "computedStyles": ["cursor", "visibility", "pointer-events"],
        "includePaintOrder": True,
    })
    ax = send_fn("Accessibility.getFullAXTree", {})
    resp_bytes = len(json.dumps(snap)) + len(json.dumps(ax))
    tbl = snap["strings"]
    docs = snap["documents"]

    # Read scroll offsets straight from doc[0].scrollOffsetX/Y instead of separate page.evaluate
    sx = float(docs[0].get("scrollOffsetX", 0.0)) if docs else 0.0
    sy = float(docs[0].get("scrollOffsetY", 0.0)) if docs else 0.0
    doc_offsets = {0: (-sx, -sy)}

    all_boxes = {}
    elements = {}
    for d_idx, doc in enumerate(docs):
        ox, oy = doc_offsets.get(d_idx, (0.0, 0.0))
        nodes, lay = doc["nodes"], doc.get("layout", {})
        parents = nodes.get("parentIndex", [])
        node_names = nodes.get("nodeName", [])
        node_vals = nodes.get("nodeValue", [])
        attrs_list = nodes.get("attributes", [])
        backend_ids = nodes.get("backendNodeId", [])

        boxes = {}
        for i, ni in enumerate(lay.get("nodeIndex", [])):
            q = lay["bounds"][i]
            if len(q) == 4:
                boxes[ni] = [q[0] + ox, q[1] + oy, q[2], q[3]]
            elif len(q) == 8:
                xs, ys = q[0::2], q[1::2]
                boxes[ni] = [min(xs) + ox, min(ys) + oy, max(xs) - min(xs), max(ys) - min(ys)]
            if ni < len(backend_ids):
                all_boxes[backend_ids[ni]] = boxes[ni]

        cd_map = nodes.get("contentDocumentIndex", {})
        for idx_pos, ni in enumerate(cd_map.get("index", [])):
            child_doc = cd_map.get("value", [])[idx_pos]
            if ni in boxes and 0 <= child_doc < len(docs):
                doc_offsets[child_doc] = (boxes[ni][0], boxes[ni][1])

        child_text = {}
        for ni, p_idx in enumerate(parents):
            if p_idx >= 0 and ni < len(node_vals):
                val = _text(tbl, node_vals[ni]).strip()
                if val and len(child_text.get(p_idx, "")) < 80:
                    child_text[p_idx] = (child_text.get(p_idx, "") + " " + val).strip()[:80]

        cursor, vis_map, pe_map = {}, {}, {}
        for i, ni in enumerate(lay.get("nodeIndex", [])):
            seg = lay.get("styles", [[]])[i] if i < len(lay.get("styles", [])) else []
            cursor[ni] = _text(tbl, seg[0]) if len(seg) > 0 else ""
            vis_map[ni] = _text(tbl, seg[1]) if len(seg) > 1 else "visible"
            pe_map[ni] = _text(tbl, seg[2]) if len(seg) > 2 else "auto"

        clicked = set(nodes.get("isClickable", {}).get("index", []))
        for ni in clicked | {n for n, c in cursor.items() if c == "pointer"}:
            if ni not in boxes or ni >= len(backend_ids):
                continue
            b = boxes[ni]
            if b[2] <= 0 or b[3] <= 0 or vis_map.get(ni) == "hidden" or pe_map.get(ni) == "none":
                continue
            attrs = _attrs_dict(tbl, attrs_list[ni] if ni < len(attrs_list) else [])
            if "disabled" in attrs or attrs.get("aria-disabled", "").lower() == "true":
                continue
            bid = backend_ids[ni]
            fallback_name = (attrs.get("aria-label") or attrs.get("title") or attrs.get("placeholder") or child_text.get(ni, ""))[:80]
            elements[bid] = {
                "source": "isClickable" if ni in clicked else "cursor:pointer",
                "role": "clickable",
                "name": fallback_name,
                "box": [round(v, 1) for v in b],
                "enabled": True,
                "occluded": False,
                "ref": {"kind": "browser", "backend_node_id": bid},
            }

    for node in ax["nodes"]:
        role = (node.get("role") or {}).get("value")
        bid = node.get("backendDOMNodeId")
        if bid is None:
            continue
        props = {pr.get("name"): (pr.get("value") or {}).get("value") for pr in node.get("properties", [])}
        disabled = bool(props.get("disabled"))
        ax_name = ((node.get("name") or {}).get("value") or "")[:80]
        if bid in elements:
            if node.get("ignored") or disabled:
                elements[bid]["enabled"] = False
            if role in ROLES:
                elements[bid]["role"] = role
            if ax_name:
                elements[bid]["name"] = ax_name
            continue
        if node.get("ignored") or role not in ROLES or disabled:
            continue
        box = all_boxes.get(bid)
        if not box or box[2] <= 0 or box[3] <= 0:
            continue
        elements[bid] = {
            "source": f"ax:{role}",
            "role": role,
            "name": ax_name,
            "box": [round(v, 1) for v in box],
            "enabled": True,
            "occluded": False,
            "ref": {"kind": "browser", "backend_node_id": bid},
        }
    out = [e for e in elements.values() if e.get("enabled") is not False]
    return out, {"ipc_round_trips": 2, "response_bytes": resp_bytes, "node_count": len(out)}


def _js_single_frame_extract(send_fn):
    res = send_fn("Runtime.evaluate", {"expression": f"({JS_SINGLE_FRAME_EXTRACTOR})()", "returnByValue": True})
    val = res.get("result", {}).get("value") or {}
    els = val.get("elements", [])
    return els, {
        "ipc_round_trips": 1,
        "response_bytes": len(json.dumps(res)),
        "node_count": val.get("scanned_dom_nodes", len(els)),
    }


class _DirectCdpWs:
    """Minimal persistent direct CDP WebSocket transport (`websockets`) for Exp 7 & Exp 9."""

    def __init__(self, ws_url):
        self.ws_url = ws_url
        self._loop = asyncio.new_event_loop()
        self._ws = None
        self._id = 0
        self.events = []
        self._loop.run_until_complete(self._connect())

    async def _connect(self):
        self._ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024)

    def send(self, method, params=None):
        return self._loop.run_until_complete(self._send_async(method, params or {}))

    async def _send_async(self, method, params):
        self._id += 1
        cid = self._id
        await self._ws.send(json.dumps({"id": cid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self._ws.recv())
            if msg.get("id") == cid:
                if "error" in msg:
                    raise RuntimeError(f"CDP error {msg['error']}")
                return msg.get("result", {})
            self.events.append(msg)

    def drain_events(self, wait_ms=50):
        async def _drain():
            t_end = time.perf_counter() + (wait_ms / 1000.0)
            while time.perf_counter() < t_end:
                rem = max(0.001, t_end - time.perf_counter())
                try:
                    raw = await asyncio.wait_for(self._ws.recv(), timeout=rem)
                    self.events.append(json.loads(raw))
                except asyncio.TimeoutError:
                    break
        self._loop.run_until_complete(_drain())
        ev = list(self.events)
        self.events.clear()
        return ev

    def close(self):
        if self._ws is not None:
            try:
                self._loop.run_until_complete(self._ws.close())
            except Exception:
                pass
        self._loop.close()


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _page_ws_url(port, substr):
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5).read().decode())
    for t in tabs:
        if t.get("type") == "page" and substr in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    pages = [t for t in tabs if t.get("type") == "page" and "webSocketDebuggerUrl" in t]
    return pages[0]["webSocketDebuggerUrl"] if pages else None


def _run_exp6_discovery_compare(n_cold=2, n_warm=10):
    out = {"adversarial_corpus": {}, "real_sites": {}}
    # 1. Adversarial ground-truth corpus across 4 dynamic states
    with DualOriginCorpusServer() as srv:
        bs = BrowserSession(url=srv.main_url, headless=True)
        try:
            def _eval_state(state_name, setup_js=None):
                if setup_js:
                    bs.page.evaluate(setup_js)
                    bs.page.wait_for_timeout(120)
                gt = extract_corpus_ground_truth(bs.page)
                ctrl_els, ctrl_stats = common.measure_workload(
                    cold_fn=lambda: _control_cdp_discover_with_meta(bs),
                    warm_fn=lambda: _control_cdp_discover_with_meta(bs),
                    n_cold=1, n_warm=n_warm,
                )
                abl_els, abl_stats = common.measure_workload(
                    cold_fn=lambda: _optimized_cdp_ablation(bs.cdp.send),
                    warm_fn=lambda: _optimized_cdp_ablation(bs.cdp.send),
                    n_cold=1, n_warm=n_warm,
                )
                js_els, js_stats = common.measure_workload(
                    cold_fn=lambda: _js_single_frame_extract(bs.cdp.send),
                    warm_fn=lambda: _js_single_frame_extract(bs.cdp.send),
                    n_cold=1, n_warm=n_warm,
                )
                out["adversarial_corpus"][state_name] = {
                    "ground_truth_count": len(gt),
                    "control_cdp": {"stats": ctrl_stats, "vs_gt": common.compare_elements(ctrl_els, gt)},
                    "ablation_cdp_no_boxmodel_loop": {"stats": abl_stats, "vs_gt": common.compare_elements(abl_els, gt)},
                    "candidate_js_single_frame": {"stats": js_stats, "vs_gt": common.compare_elements(js_els, gt)},
                }

            _eval_state("initial_viewport")
            _eval_state("drawer_open", "() => { toggleDrawer(); }")
            _eval_state("modal_occluded", "() => { openModal(); }")
            _eval_state("scrolled_view", "() => { closeModal(); window.scrollTo(0, 620); }")
        finally:
            bs.close()

    # 2. Real public websites (Control = AXTree+DOMSnapshot ground baseline, JS Extractor = candidate)
    for label, kind, url in REAL_WEB_TARGETS:
        print(f"[bench_browser:exp6] Real site {label} ...", flush=True)
        try:
            bs = BrowserSession(url=url, headless=True)
            try:
                bs.page.wait_for_timeout(1200)
                ctrl_els, ctrl_stats = common.measure_workload(
                    cold_fn=lambda: _control_cdp_discover_with_meta(bs),
                    warm_fn=lambda: _control_cdp_discover_with_meta(bs),
                    n_cold=n_cold, n_warm=n_warm,
                )
                abl_els, abl_stats = common.measure_workload(
                    cold_fn=lambda: _optimized_cdp_ablation(bs.cdp.send),
                    warm_fn=lambda: _optimized_cdp_ablation(bs.cdp.send),
                    n_cold=n_cold, n_warm=n_warm,
                )
                js_els, js_stats = common.measure_workload(
                    cold_fn=lambda: _js_single_frame_extract(bs.cdp.send),
                    warm_fn=lambda: _js_single_frame_extract(bs.cdp.send),
                    n_cold=n_cold, n_warm=n_warm,
                )
                out["real_sites"][label] = {
                    "kind": kind,
                    "url": url,
                    "control_cdp": {"stats": ctrl_stats},
                    "ablation_cdp_no_boxmodel_loop": {
                        "stats": abl_stats,
                        "vs_control": common.compare_elements(abl_els, ctrl_els),
                    },
                    "candidate_js_single_frame": {
                        "stats": js_stats,
                        "vs_control": common.compare_elements(js_els, ctrl_els),
                    },
                }
            finally:
                bs.close()
        except Exception as exc:
            out["real_sites"][label] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


def _run_exp7_transport_compare(n_warm=15):
    """Isolate ONLY Playwright CDP transport vs Direct WebSocket (`websockets`)."""
    out = {"targets": {}}
    with DualOriginCorpusServer() as srv:
        bench_urls = [
            ("corpus_main", srv.main_url, "corpus_main"),
            ("GitHub Trending", "https://github.com/trending", "github.com"),
            ("Google Maps", "https://www.google.com/maps/@40.7580,-73.9855,17z", "google.com/maps"),
        ]
        for label, url, substr in bench_urls:
            print(f"[bench_browser:exp7] Transport compare on {label} ...", flush=True)
            port = _free_port()
            with sync_playwright() as p:
                exe = p.chromium.executable_path
            import tempfile
            with tempfile.TemporaryDirectory(prefix="cul_ws_") as td:
                proc = subprocess.Popen([
                    exe, f"--remote-debugging-port={port}", f"--user-data-dir={td}",
                    "--headless=new", "--window-size=1280,720",
                    "--no-first-run", "--no-default-browser-check", url,
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    for _ in range(50):
                        try:
                            ws_url = _page_ws_url(port, substr)
                            if ws_url:
                                break
                        except Exception:
                            pass
                        time.sleep(0.2)
                    time.sleep(2.5)
                    ws_url = _page_ws_url(port, substr)
                    direct_ws = _DirectCdpWs(ws_url)
                    try:
                        with sync_playwright() as p:
                            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                            ctx = browser.contexts[0]
                            pg = next((pg for pg in ctx.pages if substr in pg.url), ctx.pages[0])
                            pw_cdp = pg.context.new_cdp_session(pg)

                            def _measure_transport(send_fn, fn_name):
                                if fn_name == "ping_scroll":
                                    call = lambda: (send_fn("Runtime.evaluate", {"expression": "[scrollX, scrollY]", "returnByValue": True}), {"ipc_round_trips": 1})
                                elif fn_name == "js_extract":
                                    call = lambda: _js_single_frame_extract(send_fn)
                                else:
                                    call = lambda: _optimized_cdp_ablation(send_fn)
                                _, st = common.measure_workload(cold_fn=call, warm_fn=call, n_cold=2, n_warm=n_warm)
                                return st

                            out["targets"][label] = {
                                "ping_scroll": {
                                    "playwright_cdp": _measure_transport(lambda m, pr=None: pw_cdp.send(m, pr or {}), "ping_scroll"),
                                    "direct_ws_cdp": _measure_transport(direct_ws.send, "ping_scroll"),
                                },
                                "js_single_frame": {
                                    "playwright_cdp": _measure_transport(lambda m, pr=None: pw_cdp.send(m, pr or {}), "js_extract"),
                                    "direct_ws_cdp": _measure_transport(direct_ws.send, "js_extract"),
                                },
                                "cdp_snapshot_ax_2call": {
                                    "playwright_cdp": _measure_transport(lambda m, pr=None: pw_cdp.send(m, pr or {}), "snapshot_ax"),
                                    "direct_ws_cdp": _measure_transport(direct_ws.send, "snapshot_ax"),
                                },
                            }
                            browser.close()
                    finally:
                        direct_ws.close()
                finally:
                    proc.terminate()
                    proc.wait(timeout=5)
    return out


def _run_exp9_mutation_observer():
    """Compare repeated full discovery vs MutationObserver + Runtime.addBinding on dynamic changes."""
    with DualOriginCorpusServer() as srv:
        port = _free_port()
        with sync_playwright() as p:
            exe = p.chromium.executable_path
        import tempfile
        with tempfile.TemporaryDirectory(prefix="cul_mo_") as td:
            proc = subprocess.Popen([
                exe, f"--remote-debugging-port={port}", f"--user-data-dir={td}",
                "--headless=new", "--window-size=1280,720",
                "--no-first-run", "--no-default-browser-check", srv.main_url,
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                ws_url = None
                for _ in range(50):
                    try:
                        ws_url = _page_ws_url(port, "corpus_main")
                        if ws_url:
                            break
                    except Exception:
                        pass
                    time.sleep(0.2)
                time.sleep(1.2)
                ws = _DirectCdpWs(ws_url)
                try:
                    ws.send("Runtime.enable", {})
                    ws.send("Runtime.addBinding", {"name": "__culDelta"})
                    # Install debounced semantic MutationObserver (ignores text-only ticks when tag/attr not interactive)
                    ws.send("Runtime.evaluate", {"expression": r"""(() => {
                      window.__moStats = { rawRecords: 0, pushes: 0 };
                      let pending = false;
                      const flush = () => {
                        pending = false;
                        const drawer = document.getElementById('dynamic_drawer');
                        const modal = document.getElementById('blocking_modal');
                        const payload = {
                          t: performance.now(),
                          drawer_open: drawer && getComputedStyle(drawer).display !== 'none',
                          modal_open: modal && getComputedStyle(modal).display !== 'none',
                          scrollY: window.scrollY
                        };
                        window.__moStats.pushes += 1;
                        window.__culDelta(JSON.stringify(payload));
                      };
                      const mo = new MutationObserver((recs) => {
                        window.__moStats.rawRecords += recs.length;
                        let semantic = false;
                        for (const r of recs) {
                          if (r.type === 'childList') semantic = true;
                          else if (r.type === 'attributes' && ['style','class','disabled','aria-disabled','hidden'].includes(r.attributeName)) semantic = true;
                        }
                        if (semantic && !pending) {
                          pending = true;
                          queueMicrotask(flush);
                        }
                      });
                      mo.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: false });
                      window.addEventListener('scroll', () => { if (!pending) { pending = true; queueMicrotask(flush); } }, { passive: true });
                    })()"""})
                    ws.drain_events(20)

                    # Measure incremental push latency across 4 dynamic transitions
                    transitions = []
                    for label, expr in [
                        ("open_drawer", "toggleDrawer()"),
                        ("open_modal", "openModal()"),
                        ("scroll_down", "window.scrollTo(0, 620)"),
                        ("close_modal", "closeModal()"),
                    ]:
                        t0 = time.perf_counter()
                        ws.send("Runtime.evaluate", {"expression": expr})
                        evs = ws.drain_events(40)
                        bindings = [e for e in evs if e.get("method") == "Runtime.bindingCalled"]
                        dt_ms = (time.perf_counter() - t0) * 1000.0
                        transitions.append({
                            "transition": label,
                            "binding_received": len(bindings) > 0,
                            "binding_count": len(bindings),
                            "push_latency_ms_incl_drain": round(dt_ms, 2),
                            "payload_bytes": sum(len(json.dumps(b)) for b in bindings),
                        })

                    # Burst test: start 25ms DOM text churn (40/sec) for 500ms and count raw vs false pushes
                    ws.send("Runtime.evaluate", {"expression": "startChurn()"})
                    time.sleep(0.5)
                    churn_evs = ws.drain_events(30)
                    ws.send("Runtime.evaluate", {"expression": "stopChurn()"})
                    mo_stats = ws.send("Runtime.evaluate", {"expression": "window.__moStats", "returnByValue": True}).get("result", {}).get("value", {})

                    # Compare full vs incremental coverage on same page via Playwright
                    with sync_playwright() as p:
                        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                        pg = br.contexts[0].pages[0]
                        gt = extract_corpus_ground_truth(pg)
                        js_res, _ = _js_single_frame_extract(ws.send)
                        cov = common.compare_elements(js_res, gt)
                        br.close()

                    return {
                        "transitions": transitions,
                        "churn_500ms_stats": {
                            "raw_mutation_records": mo_stats.get("rawRecords"),
                            "filtered_pushes": mo_stats.get("pushes"),
                            "binding_events_during_churn": sum(1 for e in churn_evs if e.get("method") == "Runtime.bindingCalled"),
                        },
                        "observer_coverage_vs_gt": {
                            "recall": cov["recall"],
                            "precision": cov["precision"],
                            "failure_breakdown": cov["failure_breakdown"],
                            "note": "Top-frame MutationObserver cannot observe closed Shadow DOM or cross-origin OOPIF mutations without per-frame attach.",
                        },
                    }
                finally:
                    ws.close()
            finally:
                proc.terminate()
                proc.wait(timeout=5)


def run_all_browser_experiments():
    """Run Experiments 6, 7, and 9 sequentially."""
    print("[bench_browser] Starting Exp 6 (Discovery + Extractor) ...", flush=True)
    exp6 = _run_exp6_discovery_compare()
    print("[bench_browser] Starting Exp 7 (Transport Playwright vs Direct WS) ...", flush=True)
    exp7 = _run_exp7_transport_compare()
    print("[bench_browser] Starting Exp 9 (MutationObserver vs Full Discovery) ...", flush=True)
    exp9 = _run_exp9_mutation_observer()
    return {"exp6_discovery": exp6, "exp7_transport": exp7, "exp9_incremental_observer": exp9}

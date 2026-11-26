# SPDX-License-Identifier: Apache-2.0
"""M1-Browser - CDP DOMSnapshot + Accessibility tree, viewport & occlusion filtered.

Union of DOMSnapshot (isClickable or cursor:pointer) and AX roles over a persistent
direct CDP WebSocket (with Playwright managing browser lifecycle and automatic fallback).
"""
import asyncio
import collections
import hashlib
import json
import socket
import threading
import urllib.parse

try:
    import websockets
except ImportError:  # pragma: no cover - optional runtime fallback keeps PW session working
    websockets = None

from .resolver import StaleElementError, visible as _box_visible

ROLES = {"button", "link", "textbox", "checkbox", "menuitem", "tab",
         "combobox", "switch", "radio", "listitem", "treeitem"}

_HOVER_TRIGGER_JS = r"""(() => {
  const triggers = new Set();
  const vw = window.innerWidth || 1280, vh = window.innerHeight || 720;
  const vpArea = vw * vh;
  for (const sheet of document.styleSheets) {
    let rules;
    try { rules = sheet.cssRules; } catch (_) { continue; }
    if (!rules) continue;
    const scan = (list) => {
      for (const r of list) {
        if (r.cssRules && r.cssRules.length && !r.selectorText) { scan(r.cssRules); continue; }
        const sel = r.selectorText;
        if (!sel || !sel.includes(':hover')) {
          if (r.cssRules && r.cssRules.length) scan(r.cssRules);
          continue;
        }
        for (const part of sel.split(',')) {
          const m = part.trim().match(/^(.+?):hover(?::[a-z-]+)?(?:\s*[>+~]\s*|\s+)(.+)$/i);
          if (!m) continue;
          const hostSel = m[1].trim(), childSel = m[2].trim();
          if (!hostSel || !childSel) continue;
          let hosts;
          try { hosts = document.querySelectorAll(hostSel); } catch (_) { continue; }
          for (const h of hosts) {
            const rect = h.getBoundingClientRect();
            if (rect.width <= 1 || rect.height <= 1 || rect.width * rect.height >= 0.85 * vpArea) continue;
            if (rect.bottom <= 0 || rect.top >= vh || rect.right <= 0 || rect.left >= vw) continue;
            let children;
            try { children = h.querySelectorAll(childSel); } catch (_) { continue; }
            for (const c of children) {
              const cs = getComputedStyle(c);
              if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') {
                triggers.add(h);
                break;
              }
            }
          }
        }
        if (r.cssRules && r.cssRules.length) scan(r.cssRules);
      }
    };
    scan(rules);
  }
  return triggers.size ? [...triggers] : null;
})()"""

_NODE_PROBE_JS = """function(doScroll) {
  if (!this.isConnected) return {gone: true};
  const elem = this.nodeType === 1 ? this : this.parentElement;
  if (!elem) return {gone: true};
  const doc = elem.ownerDocument || document;
  const win = doc.defaultView || window;
  const cs = win.getComputedStyle(elem);
  if (elem.disabled || elem.getAttribute('aria-disabled') === 'true' ||
      cs.display === 'none' || cs.visibility === 'hidden' || cs.pointerEvents === 'none') {
    return {disabled: true};
  }
  if (doScroll && elem.scrollIntoView) {
    elem.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'});
  }
  let r;
  if (this.nodeType === 1) {
    r = this.getBoundingClientRect();
  } else {
    const rng = doc.createRange();
    rng.selectNodeContents(this);
    r = rng.getBoundingClientRect();
  }
  if (r.width <= 1 || r.height <= 1) return {gone: true};
  let ax = r.x, ay = r.y;
  let curWin = win;
  let crossOrigin = false;
  try {
    while (curWin && curWin.parent && curWin.parent !== curWin) {
      if (!curWin.frameElement) { crossOrigin = true; break; }
      const fr = curWin.frameElement.getBoundingClientRect();
      ax += fr.x;
      ay += fr.y;
      curWin = curWin.parent;
    }
  } catch (_) { crossOrigin = true; }
  const vw = curWin.innerWidth, vh = curWin.innerHeight;
  if (!doScroll && !crossOrigin && (ax + r.width <= 0 || ax >= vw || ay + r.height <= 0 || ay >= vh)) {
    return {offscreen: true};
  }
  const cx = Math.min(win.innerWidth - 1, Math.max(0, r.left + r.width / 2));
  const cy = Math.min(win.innerHeight - 1, Math.max(0, r.top + r.height / 2));
  const hit = doc.elementFromPoint(cx, cy);
  let ok = false;
  if (hit) {
    if (hit === elem || elem.contains(hit) || (hit.tagName === 'LABEL' && hit.control === elem)) {
      ok = true;
    } else {
      let cur = elem;
      while (cur && cur.getRootNode) {
        const root = cur.getRootNode();
        if (!root || !root.host) break;
        if (root.host === hit || hit.contains(root.host)) { ok = true; break; }
        cur = root.host;
      }
    }
  }
  return {
    gone: false, disabled: false, offscreen: false, occluded: !ok, cross_origin: crossOrigin,
    box: [Math.round(ax * 10) / 10, Math.round(ay * 10) / 10,
          Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]
  };
}"""


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _page_ws_url_from_target(pw_cdp, connect_url, debug_port):
    """Derive exact page-level CDP WebSocket URL for the active tab."""
    if websockets is None:
        return None
    netloc = f"127.0.0.1:{debug_port}" if debug_port else None
    if connect_url:
        parsed = urllib.parse.urlsplit(connect_url)
        if parsed.netloc:
            netloc = parsed.netloc
    if not netloc:
        return None
    info = pw_cdp.send("Target.getTargetInfo")
    tid = (info.get("targetInfo") or {}).get("targetId")
    if not tid:
        return None
    return f"ws://{netloc}/devtools/page/{tid}"


class DirectCdpClient:
    """Thread-isolated persistent CDP WebSocket client with monotonic IDs & reconnect."""

    def __init__(self, ws_url, connect_timeout=10.0, call_timeout=30.0):
        self.ws_url = ws_url
        self._call_timeout = call_timeout
        self._loop = asyncio.new_event_loop()
        self._ws = None
        self._io_lock = None
        self._id = 0
        self._closed = False
        self.events = collections.deque(maxlen=256)
        self._ready = threading.Event()
        self._err = None
        self._th = threading.Thread(target=self._run_loop, name="cul-cdp-ws", daemon=True)
        self._th.start()
        if not self._ready.wait(connect_timeout):
            self.close()
            raise TimeoutError(f"Direct CDP WebSocket connect timeout: {ws_url}")
        if self._err is not None:
            self.close()
            raise self._err

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)

        async def _boot():
            self._io_lock = asyncio.Lock()
            self._ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024)

        try:
            self._loop.run_until_complete(_boot())
        except Exception as exc:
            self._err = exc
            self._ready.set()
            return
        self._ready.set()
        self._loop.run_forever()
        if self._ws is not None:
            try:
                self._loop.run_until_complete(self._ws.close())
            except Exception:
                pass
        self._loop.close()

    async def _send_once(self, method, params):
        if self._ws is None:
            self._ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024)
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

    async def _send_with_reconnect(self, method, params):
        if self._closed:
            raise RuntimeError("DirectCdpClient is closed")
        async with self._io_lock:
            for attempt in range(2):
                try:
                    return await self._send_once(method, params)
                except RuntimeError:
                    raise
                except Exception:
                    if attempt == 1 or self._closed:
                        raise
                    try:
                        if self._ws is not None:
                            await self._ws.close()
                    except Exception:
                        pass
                    self._ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024)

    def send(self, method, params=None):
        if self._closed:
            raise RuntimeError("DirectCdpClient is closed")
        fut = asyncio.run_coroutine_threadsafe(
            self._send_with_reconnect(method, params or {}), self._loop
        )
        return fut.result(timeout=self._call_timeout)

    def detach(self):
        self.close()

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass
        if self._th.is_alive():
            self._th.join(timeout=2.0)


def _text(tbl, v):
    if isinstance(v, list):
        return "".join(tbl[i] for i in v if 0 <= i < len(tbl))
    if isinstance(v, int):
        return tbl[v] if 0 <= v < len(tbl) else ""
    return v or ""


def _attrs_dict(tbl, raw_attrs):
    out = {}
    if not raw_attrs:
        return out
    for i in range(0, len(raw_attrs) - 1, 2):
        k = _text(tbl, raw_attrs[i]).lower()
        v = _text(tbl, raw_attrs[i + 1])
        if k:
            out[k] = v
    return out


def _quad_to_box(q, ox=0.0, oy=0.0):
    if len(q) == 4:
        return [q[0] + ox, q[1] + oy, q[2], q[3]]
    if len(q) == 8:
        xs, ys = q[0::2], q[1::2]
        return [min(xs) + ox, min(ys) + oy, max(xs) - min(xs), max(ys) - min(ys)]
    return None


def _is_ancestor(parents, anc, node):
    cur = node
    seen = 0
    while 0 <= cur < len(parents) and seen < 128:
        p = parents[cur]
        if p == anc:
            return True
        if p < 0 or p == cur:
            break
        cur = p
        seen += 1
    return False


class BrowserSession:
    name = "browser"

    def __init__(self, url=None, connect=None, headless=True, viewport=(1280, 720), direct_ws=True):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = None
        self._debug_port = None
        try:
            if connect:
                self.browser = self._pw.chromium.connect_over_cdp(connect)
                ctx = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
                self.page = self._select_active_page(ctx)
            else:
                launch_args = []
                if direct_ws and websockets is not None:
                    self._debug_port = _free_port()
                    launch_args.append(f"--remote-debugging-port={self._debug_port}")
                self.browser = self._pw.chromium.launch(headless=headless, args=launch_args)
                self.page = self.browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
                if url:
                    self.page.goto(url, wait_until="load", timeout=60000)
            self.viewport = self._query_viewport() or tuple(viewport)
            self.cdp = self._attach_cdp(connect, direct_ws)
        except Exception:
            try:
                if self.browser is not None:
                    self.browser.close()
            finally:
                self._pw.stop()
            raise

    def _attach_cdp(self, connect, direct_ws):
        pw_cdp = self.page.context.new_cdp_session(self.page)
        if not direct_ws or websockets is None:
            return pw_cdp
        try:
            ws_url = _page_ws_url_from_target(pw_cdp, connect, self._debug_port)
            if ws_url:
                pw_cdp.detach()
                return DirectCdpClient(ws_url)
        except Exception:
            try:
                pw_cdp.send("Runtime.evaluate", {"expression": "1", "returnByValue": True})
                return pw_cdp
            except Exception:
                return self.page.context.new_cdp_session(self.page)
        return pw_cdp

    def _select_active_page(self, ctx):
        if not ctx.pages:
            return ctx.new_page()

        def _score(pg):
            try:
                res = pg.evaluate(
                    "() => [document.visibilityState === 'visible', document.hasFocus(), location.href, Boolean(document.body && document.body.childElementCount > 0)]"
                )
                vis = bool(res[0])
                foc = bool(res[1])
                url = str(res[2] or "")
                has_dom = bool(res[3]) if len(res) > 3 else False
                real_url = url not in ("", "about:blank") and not url.startswith("chrome://")
                return (vis and foc, vis, real_url, has_dom)
            except Exception:
                return (False, False, False, False)

        best = ctx.pages[0]
        best_score = _score(best)
        for pg in ctx.pages[1:]:
            sc = _score(pg)
            if sc > best_score:
                best, best_score = pg, sc
        return best

    def _query_viewport(self):
        try:
            vw, vh = self.page.evaluate("() => [window.innerWidth, window.innerHeight]")
            if vw and vh:
                return (int(vw), int(vh))
        except Exception:
            pass
        return None

    # -- geometry ---------------------------------------------------------------
    def bounds(self):
        vp = self._query_viewport()
        if vp:
            self.viewport = vp
        return [0, 0, self.viewport[0], self.viewport[1]]

    def canvas_rects(self):
        js = """() => {
          const out = [];
          const walk = (root) => {
            for (const c of root.querySelectorAll('canvas')) {
              const r = c.getBoundingClientRect();
              if (r.width > 1 && r.height > 1) out.push([r.x, r.y, r.width, r.height]);
            }
            for (const el of root.querySelectorAll('*')) if (el.shadowRoot) walk(el.shadowRoot);
          };
          walk(document);
          return out;
        }"""
        return self.page.evaluate(js)

    # -- discovery --------------------------------------------------------------
    def discover(self):
        snap = self.cdp.send("DOMSnapshot.captureSnapshot", {
            "computedStyles": ["cursor", "visibility", "pointer-events"],
            "includePaintOrder": True,
        })
        tbl = snap["strings"]
        docs = snap["documents"]
        sx = float(docs[0].get("scrollOffsetX", 0.0)) if docs else 0.0
        sy = float(docs[0].get("scrollOffsetY", 0.0)) if docs else 0.0

        # Map child iframe document index -> frame origin offset in viewport coordinates
        doc_offsets = {0: (-sx, -sy)}
        for d_idx, doc in enumerate(docs):
            ox, oy = doc_offsets.get(d_idx, (0.0, 0.0))
            nodes, lay = doc["nodes"], doc.get("layout", {})
            boxes = {}
            for i, ni in enumerate(lay.get("nodeIndex", [])):
                b = _quad_to_box(lay["bounds"][i], ox, oy)
                if b is not None:
                    boxes[ni] = b
            cd_map = nodes.get("contentDocumentIndex", {})
            for idx_pos, ni in enumerate(cd_map.get("index", [])):
                child_doc = cd_map.get("value", [])[idx_pos]
                if ni in boxes and 0 <= child_doc < len(docs):
                    doc_offsets[child_doc] = (boxes[ni][0], boxes[ni][1])

        all_boxes = {}
        elements = {}
        occluded_bids = set()
        vp_w, vp_h = self.bounds()[2:]
        vp_area = max(1.0, float(vp_w * vp_h))
        bid_loc = {}
        doc_parents = {}
        doc_bids = {}
        aria_labels = {}
        tag_by_bid = {}
        for d_idx, doc in enumerate(docs):
            ox, oy = doc_offsets.get(d_idx, (0.0, 0.0))
            nodes, lay = doc["nodes"], doc.get("layout", {})
            parents = nodes.get("parentIndex", [])
            node_names = nodes.get("nodeName", [])
            node_vals = nodes.get("nodeValue", [])
            attrs_list = nodes.get("attributes", [])
            backend_ids = nodes.get("backendNodeId", [])
            doc_parents[d_idx] = parents
            doc_bids[d_idx] = backend_ids
            for ni, bid in enumerate(backend_ids):
                bid_loc[bid] = (d_idx, ni)

            # Collect simple text fallback per parent node
            child_text = {}
            for ni, p_idx in enumerate(parents):
                if p_idx >= 0 and ni < len(node_vals):
                    val = _text(tbl, node_vals[ni]).strip()
                    if val and len(child_text.get(p_idx, "")) < 80:
                        child_text[p_idx] = (child_text.get(p_idx, "") + " " + val).strip()[:80]

            boxes, cursor, vis_map, pe_map, po_map = {}, {}, {}, {}, {}
            paint_orders = lay.get("paintOrders", [])
            lay_nodes = lay.get("nodeIndex", [])
            lay_items = []
            for i, ni in enumerate(lay_nodes):
                b = _quad_to_box(lay["bounds"][i], ox, oy)
                if b is None:
                    continue
                boxes[ni] = b
                if ni < len(backend_ids):
                    all_boxes[backend_ids[ni]] = b
                seg = lay.get("styles", [[]])[i] if i < len(lay.get("styles", [])) else []
                cursor[ni] = _text(tbl, seg[0]) if len(seg) > 0 else ""
                vis_map[ni] = _text(tbl, seg[1]) if len(seg) > 1 else "visible"
                pe_map[ni] = _text(tbl, seg[2]) if len(seg) > 2 else "auto"
                po = paint_orders[i] if i < len(paint_orders) else i
                po_map[ni] = po
                tag = _text(tbl, node_names[ni]) if ni < len(node_names) else ""
                if tag != "#text" and b[2] > 0 and b[3] > 0 and vis_map[ni] != "hidden" and pe_map[ni] != "none":
                    lay_items.append((po, ni, b))

            def is_occluded_in_snap(ni, b):
                if vis_map.get(ni) == "hidden" or pe_map.get(ni) == "none":
                    return True
                el_po = po_map.get(ni, 0)
                cx, cy = b[0] + b[2] / 2, b[1] + b[3] / 2
                for other_po, other_ni, ob in lay_items:
                    if other_po <= el_po or other_ni == ni:
                        continue
                    if ob[0] <= cx <= ob[0] + ob[2] and ob[1] <= cy <= ob[1] + ob[3]:
                        if not _is_ancestor(parents, ni, other_ni) and not _is_ancestor(parents, other_ni, ni):
                            return True
                return False

            for ni, b in boxes.items():
                if ni < len(backend_ids) and b[2] > 0 and b[3] > 0 and is_occluded_in_snap(ni, b):
                    occluded_bids.add(backend_ids[ni])

            clicked = set(nodes.get("isClickable", {}).get("index", []))
            for ni in clicked | {n for n, c in cursor.items() if c == "pointer"}:
                if ni not in boxes or ni >= len(backend_ids):
                    continue
                b = boxes[ni]
                if b[2] <= 0 or b[3] <= 0:
                    continue
                attrs = _attrs_dict(tbl, attrs_list[ni] if ni < len(attrs_list) else [])
                if "disabled" in attrs or attrs.get("aria-disabled", "").lower() == "true":
                    continue
                bid = backend_ids[ni]
                if bid in occluded_bids:
                    continue
                tag = (_text(tbl, node_names[ni]) if ni < len(node_names) else "").lower()
                if tag in ("#document", "html", "body"):
                    continue
                if b[2] * b[3] >= 0.85 * vp_area and tag not in ("button", "a", "input", "select", "textarea"):
                    continue
                is_pw = tag == "input" and attrs.get("type", "").lower() == "password"
                aria_lbl = (attrs.get("aria-label") or "").strip()
                fallback_name = (aria_lbl or attrs.get("title")
                                 or attrs.get("placeholder") or child_text.get(ni, ""))[:80]
                if aria_lbl:
                    aria_labels[bid] = aria_lbl
                tag_by_bid[bid] = tag
                elements[bid] = {
                    "source": "isClickable" if ni in clicked else "cursor:pointer",
                    "role": "clickable",
                    "name": fallback_name,
                    "box": [round(v, 1) for v in b],
                    "enabled": True,
                    "occluded": False,
                    "is_password": is_pw,
                    "ref": {"kind": "browser", "backend_node_id": bid},
                }

        for node in self.cdp.send("Accessibility.getFullAXTree")["nodes"]:
            role = (node.get("role") or {}).get("value")
            bid = node.get("backendDOMNodeId")
            if bid is None:
                continue
            props = {pr.get("name"): (pr.get("value") or {}).get("value")
                     for pr in node.get("properties", [])}
            disabled = bool(props.get("disabled"))
            ax_name = ((node.get("name") or {}).get("value") or "")[:80]

            if bid in elements:
                if node.get("ignored") or disabled:
                    elements[bid]["enabled"] = False
                if role in ROLES:
                    elements[bid]["role"] = role
                    elements[bid]["source"] = f"ax:{role}"
                if ax_name:
                    elements[bid]["name"] = ax_name
                if props.get("protected"):
                    elements[bid]["is_password"] = True
                continue

            if node.get("ignored") or role not in ROLES or disabled or bid in occluded_bids:
                continue
            box = all_boxes.get(bid)
            if not box:
                try:
                    box = self._box_from_cdp_border(bid)
                except Exception:
                    continue
            if box[2] <= 0 or box[3] <= 0:
                continue
            elements[bid] = {
                "source": f"ax:{role}",
                "role": role,
                "name": ax_name,
                "box": [round(v, 1) for v in box],
                "enabled": not disabled,
                "occluded": False,
                "is_password": bool(props.get("protected")),
                "ref": {"kind": "browser", "backend_node_id": bid},
            }

        self._prune_nested_clickables(elements, bid_loc, doc_parents, doc_bids, aria_labels, tag_by_bid)
        self._collect_css_hover_triggers(elements, all_boxes, occluded_bids)
        return [e for e in elements.values() if e.get("enabled") is not False and not e.get("occluded")]

    def _prune_nested_clickables(self, elements, bid_loc, doc_parents, doc_bids, aria_labels, tag_by_bid):
        ax_parent_roles = {"button", "link", "menuitem", "tab", "checkbox", "radio", "switch"}
        native_tags = {"input", "select", "textarea", "button", "a"}
        to_drop = []
        for bid, el in elements.items():
            if el.get("role") != "clickable" or bid not in bid_loc:
                continue
            if tag_by_bid.get(bid) in native_tags:
                continue
            d_idx, ni = bid_loc[bid]
            parents = doc_parents.get(d_idx, ())
            bids = doc_bids.get(d_idx, ())
            cur = parents[ni] if 0 <= ni < len(parents) else -1
            steps = 0
            while 0 <= cur < len(parents) and steps < 32:
                if cur < len(bids):
                    anc = elements.get(bids[cur])
                    if anc is not None and anc.get("role") in ax_parent_roles:
                        child_aria = aria_labels.get(bid, "")
                        anc_name = (anc.get("name") or "").lower()
                        if not child_aria or child_aria.lower() in anc_name:
                            to_drop.append(bid)
                        break
                nxt = parents[cur]
                if nxt < 0 or nxt == cur:
                    break
                cur = nxt
                steps += 1
        for bid in to_drop:
            elements.pop(bid, None)

    def _collect_css_hover_triggers(self, elements, all_boxes, occluded_bids):
        """Surface CSS :hover ancestor triggers whose hidden child (e.g. figcaption/menu) is revealed."""
        try:
            eval_res = self.cdp.send("Runtime.evaluate", {"expression": _HOVER_TRIGGER_JS, "returnByValue": False})
        except Exception:
            return
        arr_oid = (eval_res.get("result") or {}).get("objectId")
        if not arr_oid:
            return
        try:
            props = self.cdp.send("Runtime.getProperties", {"objectId": arr_oid, "ownProperties": True})
            for prop in props.get("result", []):
                if not prop.get("name", "").isdigit():
                    continue
                item_oid = (prop.get("value") or {}).get("objectId")
                if not item_oid:
                    continue
                try:
                    node = self.cdp.send("DOM.describeNode", {"objectId": item_oid}).get("node") or {}
                    bid = node.get("backendNodeId")
                    if not bid or bid in elements or bid in occluded_bids:
                        continue
                    box = all_boxes.get(bid)
                    if not box:
                        box = self._box_from_cdp_border(bid)
                    if not box or box[2] <= 1 or box[3] <= 1:
                        continue
                    raw_attrs = node.get("attributes") or []
                    attrs = {raw_attrs[i]: raw_attrs[i + 1] for i in range(0, len(raw_attrs) - 1, 2)}
                    label = (attrs.get("aria-label") or attrs.get("title") or attrs.get("class")
                             or node.get("localName") or "hover").strip()[:80]
                    elements[bid] = {
                        "source": "css:hover",
                        "role": "clickable",
                        "name": label,
                        "box": [round(v, 1) for v in box],
                        "enabled": True,
                        "occluded": False,
                        "is_password": False,
                        "ref": {"kind": "browser", "backend_node_id": bid},
                    }
                except Exception:
                    continue
                finally:
                    try:
                        self.cdp.send("Runtime.releaseObject", {"objectId": item_oid})
                    except Exception:
                        pass
        finally:
            try:
                self.cdp.send("Runtime.releaseObject", {"objectId": arr_oid})
            except Exception:
                pass

    # -- safety & inspection ----------------------------------------------------
    def _box_from_cdp_border(self, bid):
        q = self.cdp.send("DOM.getBoxModel", {"backendNodeId": bid})["model"]["border"]
        xs, ys = q[0::2], q[1::2]
        return [round(min(xs), 1), round(min(ys), 1), round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)]

    def verify_fresh(self, el, tolerance=2):
        """Verify live DOM presence, enabled/offscreen state, occlusion, and bounds for one element."""
        bid = (el.get("ref") or {}).get("backend_node_id")
        if not bid:
            raise StaleElementError(f"{el.get('id') or 'element'} missing backend_node_id")
        try:
            obj = self.cdp.send("DOM.resolveNode", {"backendNodeId": bid}).get("object") or {}
        except Exception as exc:
            raise StaleElementError(f"{el.get('id') or 'element'} removed from DOM: {exc}") from exc
        obj_id = obj.get("objectId")
        if not obj_id:
            raise StaleElementError(f"{el.get('id') or 'element'} removed from DOM")
        info = self._call_on_node(obj_id, _NODE_PROBE_JS, False) or {"gone": True}
        if info.get("gone") or info.get("offscreen"):
            raise StaleElementError(f"{el.get('id') or 'element'} removed or scrolled out of viewport")
        if info.get("disabled"):
            raise StaleElementError(f"{el.get('id') or 'element'} is disabled or hidden")
        if info.get("occluded"):
            raise StaleElementError(f"{el.get('id') or 'element'} is occluded by another element")
        new = info["box"]
        if info.get("cross_origin"):
            try:
                new = self._box_from_cdp_border(bid)
            except Exception as exc:
                raise StaleElementError(f"{el.get('id') or 'element'} cross-origin box vanished: {exc}") from exc
            if not _box_visible(new, self.bounds()):
                raise StaleElementError(f"{el.get('id') or 'element'} scrolled out of viewport")
        old = el["box"]
        if max(abs(old[i] - new[i]) for i in range(4)) > tolerance:
            raise StaleElementError(
                f"{el.get('id') or 'element'} moved {old} -> {new} since revision {el.get('revision')}"
            )
        updated = dict(el)
        updated.update({"box": new, "enabled": True, "offscreen": False, "occluded": False})
        return updated

    def _resolve_node_id(self, el):
        bid = (el.get("ref") or {}).get("backend_node_id")
        if not bid:
            return None
        try:
            obj = self.cdp.send("DOM.resolveNode", {"backendNodeId": bid})["object"]
            return obj.get("objectId")
        except Exception:
            return None

    def _call_on_node(self, obj_id, fn_js, *args):
        res = self.cdp.send("Runtime.callFunctionOn", {
            "objectId": obj_id,
            "functionDeclaration": fn_js,
            "arguments": [{"value": a} for a in args],
            "returnByValue": True,
        })
        return res.get("result", {}).get("value")

    def is_occluded(self, el):
        obj_id = self._resolve_node_id(el)
        if not obj_id:
            return False
        info = self._call_on_node(obj_id, """function() {
          const r = this.getBoundingClientRect();
          if (r.width <= 0 || r.height <= 0) return {occluded: true};
          const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          const hit = document.elementFromPoint(cx, cy);
          if (!hit) return {occluded: true};
          const ok = this.contains(hit) || (hit.tagName === 'LABEL' && hit.control === this);
          return {occluded: !ok};
        }""")
        return bool((info or {}).get("occluded"))

    def read_value(self, el):
        if el.get("is_password"):
            return "[REDACTED]"
        obj_id = self._resolve_node_id(el)
        if not obj_id:
            return None
        val = self._call_on_node(obj_id, """function() {
          if ((this.type || '').toLowerCase() === 'password') return '[REDACTED]';
          const lbl = ((this.name || '') + ' ' + (this.id || '') + ' ' + (this.autocomplete || '')).toLowerCase();
          if (/(pass|secret|token|cvv|pin|pwd)/.test(lbl)) return '[REDACTED]';
          return (this.value !== undefined ? String(this.value) : (this.textContent || '')).slice(0, 400);
        }""")
        return val

    # -- actions ---------------------------------------------------------------
    def _center(self, el):
        bx = el["box"]
        vx, vy, vw, vh = self.bounds()
        x0, y0 = max(vx, bx[0]), max(vy, bx[1])
        x1, y1 = min(vx + vw, bx[0] + bx[2]), min(vy + vh, bx[1] + bx[3])
        if x1 > x0 and y1 > y0:
            return (x0 + x1) / 2.0, (y0 + y1) / 2.0
        return bx[0] + bx[2] / 2.0, bx[1] + bx[3] / 2.0

    def perform(self, el, action, value=None, clear=True):
        if el.get("enabled") is False:
            raise RuntimeError(f"element {el.get('id') or el.get('name')} is disabled")

        x, y = self._center(el)
        obj_id = self._resolve_node_id(el)
        if obj_id:
            state = self._call_on_node(obj_id, _NODE_PROBE_JS, True)
            if state:
                if state.get("disabled"):
                    raise RuntimeError("element is disabled")
                bx = state.get("box") or el["box"]
                if state.get("cross_origin"):
                    try:
                        bx = self._box_from_cdp_border((el.get("ref") or {}).get("backend_node_id"))
                    except Exception:
                        pass
                x, y = self._center({"box": bx})
                if state.get("occluded"):
                    raise StaleElementError(f"element occluded at ({x:.1f}, {y:.1f})")

        if action in ("click", "type", "focus"):
            self.page.mouse.click(x, y)
        if action == "type":
            if clear:
                self.page.keyboard.press("Control+a")
                self.page.keyboard.press("Backspace")
            if value is not None and str(value) != "":
                self.page.keyboard.type(str(value))
        return {"x": round(x, 1), "y": round(y, 1)}

    def hover(self, el):
        x, y = self._center(el)
        self.page.mouse.move(x, y)
        return {"x": x, "y": y}

    def navigate(self, url):
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": self.page.url, "title": self.page.title()}

    def back(self):
        resp = self.page.go_back(wait_until="domcontentloaded", timeout=15000)
        return {"url": self.page.url, "title": self.page.title(), "navigated": resp is not None}

    def scroll(self, dx=0, dy=0):
        vx, vy, vw, vh = self.bounds()
        self.page.mouse.move(vx + vw / 2, vy + vh / 2)
        self.page.mouse.wheel(dx, dy)
        pos = self.page.evaluate(
            "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => "
            "r([Math.round(window.scrollX), Math.round(window.scrollY)]))))"
        )
        return {"dx": dx, "dy": dy, "scroll_x": pos[0], "scroll_y": pos[1]}

    def press_key(self, key):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Key must be a non-empty string")
        aliases = {
            "ctrl": "Control", "esc": "Escape", "return": "Enter",
            "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight",
            "del": "Delete",
        }
        parts = [p.strip() for p in key.split("+") if p.strip()]
        if any(p.lower() in {"win", "lwin", "rwin", "meta", "super", "command", "cmd"} for p in parts):
            raise ValueError(f"Blocked OS modifier key in {key!r}")
        normalized = "+".join(aliases.get(p.lower(), p) for p in parts)
        self.page.keyboard.press(normalized)
        return {"key": normalized}

    def click_coordinate(self, x, y, button="left", clicks=1):
        if button not in ("left", "right", "middle"):
            raise ValueError(f"Unsupported mouse button: {button!r}")
        if clicks < 1 or clicks > 3:
            raise ValueError(f"Unsupported click count: {clicks}")
        vx, vy, vw, vh = self.bounds()
        if not (vx <= x < vx + vw and vy <= y < vy + vh):
            raise ValueError(f"Coordinate ({x}, {y}) is outside viewport {[vx, vy, vw, vh]}")
        self.page.mouse.click(x, y, button=button, click_count=clicks)
        return {"x": x, "y": y, "button": button, "clicks": clicks}

    def _safe_url(self):
        try:
            return self.page.url
        except Exception:
            return ""

    def signature(self, target=None):
        """Cheap privacy-safe state fingerprint for post-action diffing (hashes active value)."""
        url = self._safe_url()
        try:
            raw = self.page.evaluate("""() => {
              const els = document.querySelectorAll('input,button,a,select,textarea,[role]');
              const ae = document.activeElement;
              let aeTag = '', aeVal = '', aeSecret = false;
              if (ae) {
                aeTag = ae.tagName || '';
                const t = (ae.type || '').toLowerCase();
                const meta = ((ae.name || '') + ' ' + (ae.id || '') + ' ' + (ae.autocomplete || '')).toLowerCase();
                aeSecret = t === 'password' || /(pass|secret|token|cvv|pin|pwd)/.test(meta);
                aeVal = ae.value !== undefined ? String(ae.value) : (ae.textContent || '').slice(0, 80);
              }
              return {
                title: document.title,
                ae_tag: aeTag,
                ae_val: aeVal,
                ae_secret: aeSecret,
                text: (document.body.innerText || '').slice(0, 400),
                n: els.length,
              };
            }""")
        except Exception as exc:
            msg = str(exc).lower()
            if "execution context" in msg or "navigat" in msg:
                return {"url": self._safe_url() or url, "title": "", "focus": "", "text": "", "n": 0}
            raise
        ae_val = raw.get("ae_val") or ""
        val_hash = hashlib.sha256(ae_val.encode("utf-8")).hexdigest()[:12] if ae_val else ""
        focus_fp = f"{raw.get('ae_tag', '')}:len={len(ae_val)}:h={val_hash}"
        if raw.get("ae_secret"):
            focus_fp = f"{raw.get('ae_tag', '')}:[REDACTED]:len={len(ae_val)}:h={val_hash}"
        return {
            "url": self._safe_url() or url,
            "title": raw.get("title", ""),
            "focus": focus_fp,
            "text": raw.get("text", ""),
            "n": raw.get("n", 0),
        }

    def close(self):
        try:
            if getattr(self, "cdp", None) is not None and hasattr(self.cdp, "close"):
                self.cdp.close()
        except Exception:
            pass
        try:
            self.browser.close()
        finally:
            self._pw.stop()

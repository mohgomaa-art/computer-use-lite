# SPDX-License-Identifier: Apache-2.0
"""M1-Browser - CDP DOMSnapshot + Accessibility tree, viewport & occlusion filtered.

Union of DOMSnapshot (isClickable or cursor:pointer) and AX roles. Open shadow roots
are included; DOMSnapshot layout bounds (document coords) are converted to viewport coords
by subtracting (scrollX, scrollY). DOM.getBoxModel already returns viewport coordinates.
"""
import hashlib

from .resolver import StaleElementError

ROLES = {"button", "link", "textbox", "checkbox", "menuitem", "tab",
         "combobox", "switch", "radio", "listitem", "treeitem"}


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

    def __init__(self, url=None, connect=None, headless=True, viewport=(1280, 720)):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        if connect:
            self.browser = self._pw.chromium.connect_over_cdp(connect)
            ctx = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
            self.page = self._select_active_page(ctx)
        else:
            self.browser = self._pw.chromium.launch(headless=headless)
            self.page = self.browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
            if url:
                self.page.goto(url, wait_until="load", timeout=60000)
        self.viewport = self._query_viewport() or tuple(viewport)
        self.cdp = self.page.context.new_cdp_session(self.page)

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
        sx, sy = self.page.evaluate("() => [scrollX, scrollY]")
        docs = snap["documents"]

        # Map child iframe document index -> frame origin offset in viewport coordinates
        doc_offsets = {0: (-sx, -sy)}
        for d_idx, doc in enumerate(docs):
            ox, oy = doc_offsets.get(d_idx, (0.0, 0.0))
            nodes, lay = doc["nodes"], doc.get("layout", {})
            boxes = {}
            for i, ni in enumerate(lay.get("nodeIndex", [])):
                q = lay["bounds"][i]
                if len(q) == 4:
                    boxes[ni] = [q[0] + ox, q[1] + oy, q[2], q[3]]
                elif len(q) == 8:
                    xs, ys = q[0::2], q[1::2]
                    boxes[ni] = [min(xs) + ox, min(ys) + oy, max(xs) - min(xs), max(ys) - min(ys)]
            cd_map = nodes.get("contentDocumentIndex", {})
            for idx_pos, ni in enumerate(cd_map.get("index", [])):
                child_doc = cd_map.get("value", [])[idx_pos]
                if ni in boxes and 0 <= child_doc < len(docs):
                    doc_offsets[child_doc] = (boxes[ni][0], boxes[ni][1])

        elements = {}
        occluded_bids = set()
        for d_idx, doc in enumerate(docs):
            ox, oy = doc_offsets.get(d_idx, (0.0, 0.0))
            nodes, lay = doc["nodes"], doc.get("layout", {})
            parents = nodes.get("parentIndex", [])
            node_names = nodes.get("nodeName", [])
            node_vals = nodes.get("nodeValue", [])
            attrs_list = nodes.get("attributes", [])
            backend_ids = nodes.get("backendNodeId", [])

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
                q = lay["bounds"][i]
                if len(q) == 4:
                    b = [q[0] + ox, q[1] + oy, q[2], q[3]]
                elif len(q) == 8:
                    xs, ys = q[0::2], q[1::2]
                    b = [min(xs) + ox, min(ys) + oy, max(xs) - min(xs), max(ys) - min(ys)]
                else:
                    continue
                boxes[ni] = b
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
                is_pw = tag == "input" and attrs.get("type", "").lower() == "password"
                fallback_name = (attrs.get("aria-label") or attrs.get("title")
                                 or attrs.get("placeholder") or child_text.get(ni, ""))[:80]
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
            try:
                q = self.cdp.send("DOM.getBoxModel", {"backendNodeId": bid})["model"]["content"]
            except Exception:
                continue
            xs, ys = q[0::2], q[1::2]
            box = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
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

        return [e for e in elements.values() if e.get("enabled") is not False and not e.get("occluded")]

    # -- safety & inspection ----------------------------------------------------
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
        x, y, w, h = el["box"]
        return x + w / 2, y + h / 2

    def perform(self, el, action, value=None, clear=True):
        if el.get("enabled") is False:
            raise RuntimeError(f"element {el.get('id') or el.get('name')} is disabled")

        x, y = self._center(el)
        obj_id = self._resolve_node_id(el)
        if obj_id:
            state = self._call_on_node(obj_id, """function() {
              if (this.disabled || this.getAttribute('aria-disabled') === 'true') {
                return {disabled: true};
              }
              this.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'});
              const r = this.getBoundingClientRect();
              const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
              const hit = document.elementFromPoint(cx, cy);
              const ok = hit && (this.contains(hit) || (hit.tagName === 'LABEL' && hit.control === this));
              return {disabled: false, occluded: !ok, x: cx, y: cy};
            }""")
            if state:
                if state.get("disabled"):
                    raise RuntimeError("element is disabled")
                if state.get("occluded"):
                    raise StaleElementError(f"element occluded at ({state.get('x'):.1f}, {state.get('y'):.1f})")
                x, y = state["x"], state["y"]

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

    def signature(self, target=None):
        """Cheap privacy-safe state fingerprint for post-action diffing (hashes active value)."""
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
        ae_val = raw.get("ae_val") or ""
        val_hash = hashlib.sha256(ae_val.encode("utf-8")).hexdigest()[:12] if ae_val else ""
        focus_fp = f"{raw.get('ae_tag', '')}:len={len(ae_val)}:h={val_hash}"
        if raw.get("ae_secret"):
            focus_fp = f"{raw.get('ae_tag', '')}:[REDACTED]:len={len(ae_val)}:h={val_hash}"
        return {
            "title": raw.get("title", ""),
            "focus": focus_fp,
            "text": raw.get("text", ""),
            "n": raw.get("n", 0),
        }

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

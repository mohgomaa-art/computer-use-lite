# SPDX-License-Identifier: Apache-2.0
"""M3 - merge, deduplicate, filter and guard elements against stale bounds."""
INTERACTIVE = {
    "button", "menuitem", "tab", "link", "textbox", "combobox",
    "checkbox", "radio", "switch", "clickable", "listitem", "treeitem",
}
IOU_DEDUPE = 0.75


class StaleElementError(RuntimeError):
    """Raised when an element moved, disappeared, is occluded, or belongs to an older revision."""


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def visible(box, viewport, pad=0):
    x, y, w, h = box
    vx, vy, vw, vh = viewport
    if w <= 1 or h <= 1:
        return False
    return (x + w > vx - pad and x < vx + vw + pad
            and y + h > vy - pad and y < vy + vh + pad)


def _keepable(el, viewport):
    if el.get("enabled") is False or el.get("offscreen") is True or el.get("occluded") is True:
        return False
    return visible(el["box"], viewport)


class Resolver:
    def __init__(self):
        self.records = []
        self.revision = 0
        self._next_id = 1

    def merge(self, elements, viewport, revision):
        """Filter offscreen/disabled/occluded, dedupe overlapping, assign eN ids."""
        kept = [el for el in elements if _keepable(el, viewport)]
        kept.sort(key=lambda e: -(e["box"][2] * e["box"][3]))
        deduped = []
        for el in kept:
            clash = None
            for other in deduped:
                if iou(el["box"], other["box"]) >= IOU_DEDUPE:
                    clash = other
                    break
            if clash is None:
                deduped.append(dict(el))
                continue
            score = lambda r: (bool(r.get("name")), r.get("role") in INTERACTIVE,
                               r["box"][2] * r["box"][3])
            if score(el) > score(clash):
                deduped[deduped.index(clash)] = dict(el)

        deduped.sort(key=lambda e: (e.get("role") not in INTERACTIVE, e["box"][1], e["box"][0]))
        for i, el in enumerate(deduped, 1):
            el["id"] = f"e{i}"
            el["revision"] = revision
        self._next_id = len(deduped) + 1
        self.records = deduped
        self.revision = revision
        return deduped

    def get(self, element_id):
        for r in self.records:
            if r["id"] == element_id:
                return r
        raise KeyError(f"unknown element {element_id!r}")

    def add(self, elements, viewport, revision):
        """Add newly discovered elements without renumbering existing ones."""
        known = {_ref_key(r) for r in self.records}
        fresh = [dict(e) for e in elements
                 if _ref_key(e) not in known and _keepable(e, viewport)]
        added = []
        for el in fresh:
            el["id"] = f"e{self._next_id}"
            self._next_id += 1
            el["revision"] = revision
            self.records.append(el)
            added.append(el)
        self.revision = revision
        return added

    def reconcile_hover(self, elements, viewport, revision):
        """Update surviving elements, drop disappeared ones (no zombies), append newly revealed ones."""
        valid = [dict(e) for e in elements if _keepable(e, viewport)]
        by_key = {_ref_key(e): e for e in valid}
        surviving = []
        known_keys = set()
        for r in self.records:
            k = _ref_key(r)
            cur = by_key.get(k)
            if cur is None:
                continue
            updated = dict(cur)
            updated["id"] = r["id"]
            updated["revision"] = revision
            surviving.append(updated)
            known_keys.add(k)

        added = []
        for e in valid:
            k = _ref_key(e)
            if k in known_keys:
                continue
            e["id"] = f"e{self._next_id}"
            self._next_id += 1
            e["revision"] = revision
            surviving.append(e)
            added.append(e)
            known_keys.add(k)

        self.records = surviving
        self.revision = revision
        return added

    def assert_fresh(self, element_id, current_elements, revision, tolerance=2, occluded=False):
        """Reject an action when the element moved, vanished, is occluded, or revision rolled."""
        rec = self.get(element_id)
        if revision != self.revision:
            raise StaleElementError(
                f"{element_id} belongs to revision {revision}, current {self.revision}")
        match = next((e for e in current_elements if _ref_key(e) == _ref_key(rec)), None)
        if match is None:
            raise StaleElementError(f"{element_id} is gone or disabled/occluded in the current UI")
        if occluded or match.get("occluded") is True:
            raise StaleElementError(f"{element_id} is occluded by another element")
        old, new = rec["box"], match["box"]
        if max(abs(old[i] - new[i]) for i in range(4)) > tolerance:
            raise StaleElementError(
                f"{element_id} moved {old} -> {new} since revision {rec['revision']}")
        return match


def _ref_key(el):
    ref = el.get("ref") or {}
    return (ref.get("kind"), tuple(ref.get("runtime_id") or [ref.get("backend_node_id")]))

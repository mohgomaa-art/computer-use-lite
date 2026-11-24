# SPDX-License-Identifier: Apache-2.0
"""M5 - the three-tool interface and its compact line map."""
import time

from . import blind_gap, snapshot, state
from .resolver import INTERACTIVE, Resolver, StaleElementError

ACTIONS = {
    "button": "click", "menuitem": "click", "tab": "click", "link": "click",
    "checkbox": "click", "radio": "click", "switch": "click", "clickable": "click",
    "listitem": "click", "treeitem": "click",
    "textbox": "click,type", "combobox": "click,type",
}
DEFAULT_LINE_MAP_CAP = 60


class Api:
    """discover_interactables / inspect_element / execute_action over one session."""

    def __init__(self, session, state_path=None, crops_dir=None):
        self.session = session
        self.resolver = Resolver()
        self.task_state = state.TaskState(state_path)
        self.crops_dir = crops_dir
        self.regions = []
        self.last_stats = {}

    # -- 1. discovery -----------------------------------------------------------
    def discover_interactables(self, target="auto", export_crops=True,
                               max_elements=DEFAULT_LINE_MAP_CAP, filter_query=None):
        t0 = time.perf_counter()
        elements = [e for e in self.session.discover() if e.get("role") in INTERACTIVE]
        revision = snapshot.bump_revision()
        viewport = self.session.bounds()
        records = self.resolver.merge(elements, viewport, revision)
        self.regions = blind_gap.detect(self.session, records, viewport)
        for i, region in enumerate(self.regions):
            if export_crops and self.crops_dir:
                region["crop"] = blind_gap.export(
                    self.session, region, f"{self.crops_dir}/blind_{i}.png")
        text = self.line_map(max_elements=max_elements, filter_query=filter_query)
        self.last_stats = {
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "elements": len(records),
            "blind_regions": len(self.regions),
            "chars": len(text),
            "tokens": round(len(text) / 4, 1),
            "revision": revision,
            "viewport": viewport,
        }
        return text

    def line_map(self, max_elements=DEFAULT_LINE_MAP_CAP, filter_query=None):
        records = self.resolver.records
        if filter_query:
            q = filter_query.lower()
            records = [
                r for r in records
                if q in (r.get("name") or "").lower()
                or q in (r.get("role") or "").lower()
                or q in (r.get("id") or "").lower()
            ]
        total = len(records)
        shown = records[:max_elements] if max_elements is not None else records
        head = (f"REV:{self.resolver.revision} | WIN:{_window_name(self.session)} | "
                f"ELEMENTS:{len(self.resolver.records)} | "
                f"BLIND_REGIONS:{len(self.regions)}")
        lines = [head]
        for r in shown:
            x, y, w, h = [int(v) for v in r["box"]]
            name = (r.get("name") or "").replace("|", "/").replace("\n", " ")[:40]
            acts = ACTIONS.get(r.get("role"), "click" if r.get("role") in INTERACTIVE else "")
            extra = f"|children={r['children_count']}" if r.get("children_count") else ""
            lines.append(f"{r['id']}|{r.get('role') or '?'}|{name}|{x},{y},{w},{h}|{acts}{extra}")
        if len(shown) < total:
            lines.append(f"... +{total - len(shown)} more elements (use filter_query= or inspect_element)")
        for i, region in enumerate(self.regions):
            lines.append(f"blind{i}|{region['kind']}||"
                         f"{','.join(str(int(v)) for v in region['box'])}|crop"
                         + (f" -> {region['crop']}" if region.get("crop") else ""))
        return "\n".join(lines)

    # -- 2. inspect -------------------------------------------------------------
    def inspect_element(self, element_id):
        rec = self.resolver.get(element_id)
        info = {k: v for k, v in rec.items() if k not in ("ref", "_element")}
        if hasattr(self.session, "read_value") and rec.get("role") == "textbox":
            info["value"] = "[REDACTED]" if rec.get("is_password") else self.session.read_value(rec)
        return info

    # -- 3. execute -------------------------------------------------------------
    def execute_action(self, element_id, action, value=None, revision=None, clear=True):
        rec = self.resolver.get(element_id)
        expected_rev = rec["revision"] if revision is None else revision
        try:
            fresh = [e for e in self.session.discover() if e.get("role") in INTERACTIVE]
            occluded = self.session.is_occluded(rec) if hasattr(self.session, "is_occluded") else False
            match = self.resolver.assert_fresh(element_id, fresh, expected_rev, occluded=occluded)
            before = _call_sig(self.session, match)
            if action == "type" and hasattr(self.session, "page"):
                mechanism = self.session.perform(match, action, value, clear=clear)
            else:
                mechanism = self.session.perform(match, action, value)
            after = _call_sig(self.session, match)
            result = state.verify(before, after)
            new_rev = snapshot.bump_revision()
            self.resolver.revision = new_rev
            rec["revision"] = new_rev
            rec["box"] = match["box"]
            self.task_state.record_action({
                "element": element_id, "action": action, "value": value,
                "ok": True, "revision": new_rev,
                "verified": result["changed"], "mechanism": mechanism,
            })
            return {
                "ok": True, "element": element_id, "action": action,
                "mechanism": mechanism, "verified": result["changed"],
                "state_delta": result["delta"], "revision": new_rev,
            }
        except Exception as exc:
            self.task_state.record_action({
                "element": element_id, "action": action, "value": value,
                "ok": False, "error": f"{type(exc).__name__}: {exc}",
                "revision": self.resolver.revision,
            })
            raise


def _call_sig(session, match):
    try:
        return session.signature(match)
    except TypeError:
        return session.signature()


def _window_name(session):
    try:
        return session.process_name
    except AttributeError:
        return getattr(session, "name", "unknown")


__all__ = ["Api", "StaleElementError"]

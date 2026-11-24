# SPDX-License-Identifier: Apache-2.0
"""M4 - explicit single-element hover that reconciles disappeared and newly revealed items."""
import time

from . import snapshot
from .resolver import INTERACTIVE


def hover_and_diff(session, resolver, element_id, wait_ms=350):
    """Hover one element, settle once, re-discover, remove disappeared items, and add new ones."""
    rec = resolver.get(element_id)
    before = {r["id"] for r in resolver.records}
    point = session.hover(rec)
    if wait_ms and wait_ms > 0:
        time.sleep(wait_ms / 1000)
    elements = [e for e in session.discover() if e.get("role") in INTERACTIVE]
    revision = snapshot.bump_revision()
    added = resolver.reconcile_hover(elements, session.bounds(), revision)
    return {
        "hovered": element_id,
        "point": point,
        "revision": revision,
        "added": [{k: r[k] for k in ("id", "role", "name", "box")} for r in added],
        "known_before": len(before),
        "known_after": len(resolver.records),
    }

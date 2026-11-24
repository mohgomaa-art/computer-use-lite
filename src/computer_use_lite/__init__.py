# SPDX-License-Identifier: Apache-2.0
"""Computer Use Lite engine - local-first UI discovery (Windows + Chromium CDP).

Layers: M0 snapshot, M1-Browser CDP, M1-Windows UIA (Windows-only), M2 blind-region crops,
M3 resolver/stale guard, M4 hover, M5 api. Cursor probing is deliberately absent:
see docs/ARCHITECTURE_DECISION.md (H1b and H2 both failed or are unshipped).
"""
from .api import Api
from .blind_gap import detect, export
from .browser_cdp import BrowserSession
from .desktop_uia import DesktopSession
from .resolver import Resolver, StaleElementError

__all__ = ["Api", "BrowserSession", "DesktopSession", "Resolver", "StaleElementError",
           "detect", "export"]

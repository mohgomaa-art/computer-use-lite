# Computer Use Lite Python API, Architecture & Testing Reference

Use this reference when importing `computer_use_lite` directly in Python scripts, custom orchestrators, tests, or benchmarks.

---

## Canonical Imports & Legacy Compatibility

Prefer `computer_use_lite` (`src/computer_use_lite/`). Legacy `src/engine/` re-exports the same symbols for backwards compatibility:

```python
from computer_use_lite import (
    Api,
    BrowserSession,
    DesktopSession,
    Resolver,
    StaleElementError,
    detect,   # blind_gap.detect
    export,   # blind_gap.export
)
from computer_use_lite.session_manager import SessionManager
from computer_use_lite.desktop_uia import list_windows
```

- **Thread-affinity requirement**: `BrowserSession` wraps Playwright `sync_api` (strict greenlet thread affinity — cannot move across OS threads or run inside an active `asyncio` event loop without worker isolation) paired with `DirectCdpClient`. `DesktopSession` pins UIA COM MTA calls to one worker thread. Use `SessionManager` (or a dedicated single-thread worker per session) for async or parallel execution.
- **Per-session storage isolation**: pass distinct `state_path` and `crops_dir` per concurrent `Api(session, ...)` so sessions do not collide on `state.DEFAULT_PATH` (`COMPUTER_USE_LITE_STATE_PATH` env override or repo runtime file). Pass `state_fsync=False` for disposable sessions when crash durability is not needed.

---

## Core `Api` Workflow

```python
api = Api(session, state_path="session_state.json", crops_dir="session_crops")

# 1. Discover interactables (uses Api defaults unless overridden)
line_map = api.discover_interactables(export_crops=True, filter_query=None)
# Telemetry in api.last_stats; blind region boxes/paths in api.regions

# 2. Inspect one element (live "value" read on textbox/searchbox; "[REDACTED]" for passwords)
info = api.inspect_element(element_id)

# 3. Execute with targeted freshness validation (throws StaleElementError on drift/occlusion/rev mismatch)
res = api.execute_action(element_id, "type", value="...", revision=api.resolver.revision, clear=True)

# 4. Hover to capture newly revealed items without renumbering surviving IDs
hover_res = api.hover_element(target_id)

# 5. Bump revision explicitly after direct session scroll/navigate/press_key/click_coordinate calls
session.scroll(dx=0, dy=400)
new_rev = api.invalidate_revision("scroll")
```

---

## Engine Architecture & Observed Boundaries

1. **Browser Perception (`BrowserSession`)**:
   - Combines Playwright browser lifecycle with `DirectCdpClient` WebSocket (`websockets`) for two-call `DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree` discovery.
   - Walks multi-document snapshot frames and prunes scroll-clipped nodes and `<label>` wrappers for core input roles (`textbox`, `searchbox`, `combobox`, `checkbox`, `radio`, `switch`). In headless local-origin fixtures this achieves cross-origin frame extraction, **however live testing on real websites showed site-isolated third-party embeds (video/ad frames) can still return zero internal controls with `BLIND_REGIONS:0`**, and duplicate `<label>` entries persist beside `button` and `clickable` inputs.
   - Additional boundaries: omits closed Shadow DOM and static text; cross-origin occlusion checks cannot inspect parent-frame DOM; `navigate()` waits only for `"domcontentloaded"`; `perform()` calls `scrollIntoView` only after `verify_fresh(doScroll=False)` passes viewport visibility; `signature()` hashes `.value` rather than `.checked`, creating identical signatures for default checkbox/radio groups (`verified: false` false negative) and focus-shift false positives on read-only inputs.
   - Public methods on `BrowserSession`: `discover`, `bounds`, `verify_fresh`, `is_occluded`, `perform`, `hover`, `navigate`, `back`, `scroll`, `press_key`, `click_coordinate`, `canvas_rects`, `read_value`, `signature`, `close`.
2. **Desktop Perception & Safety (`DesktopSession`)**:
   - Scopes UIA `FindAllBuildCache` queries strictly to one target `hwnd` on a `COINIT_MULTITHREADED` COM worker using `CUIAutomation8` (`IUIAutomation2`) with `AutoSetFocus = 0`. Never executes desktop-root enumeration.
   - Enforces foreground safety checks (`Foreground safety abort` -> MCP `ForegroundMismatch`) before physical input, and preserves physical-cursor `KillSwitch` (`HUMAN TAKEOVER` abort).
   - `DesktopSession.verify_fresh()` inspects UIA bounds/enabled/offscreen state and assigns `"occluded": False` without Z-order checks.
   - In `DesktopSession.perform()`, `action="type"` calls `ValuePattern.SetValue` before `SendInput` fallback: on native Win32 file-save modal `Edit` controls, `ValuePattern` updates UIA text visible to `inspect()` **without committing the typed buffer to the underlying file dialog**, causing silent writes to the prior filename or validation errors on Save (`invoke_pattern`).
   - **Desktop capture (`blind_gap.capture_desktop_region`)**: prioritizes Win32 `PrintWindow` before `PIL.ImageGrab.grab` when `hwnd` is cloaked, minimized, non-foreground, or overlapped by a higher Z-order window. Live verification on covered windows confirmed clean un-occluded content capture without foreground bleed-through (noting dark WinUI Mica backdrops and RTL mirroring asymmetry where `WS_EX_LAYOUTRTL` windows mirror horizontally while UWP apps can stay un-mirrored).
3. **Blind Region Detection (`blind_gap.py`)**:
   - Flags opaque canvases (`opaque_canvas`, `small_opaque_canvas`) in browsers and sparse control windows (`low_uia`) on desktop; heuristic pixel-cursor probing failed reliability/safety gates and is removed by design.
   - Stacked canvases can emit duplicate blind regions; third-party site-isolated embeds and UIA-attached Chromium windows (`RootWebArea`) can emit zero blind regions.
4. **Full Action Redaction (`TaskState`)**:
   - `TaskState.record_action()` strips plaintext `value` whenever `value is not None`, persisting length, truncated SHA-256 hash, and `"value_redacted": true`.

---

## Environment Variables & CLI Test Commands

- `CUL_MCP_ALLOW_FILE_URLS=1`: permit `file://` URLs in `SessionManager`.
- `CUL_MCP_ALLOW_PRIVATE_URLS=1`: permit localhost, loopback, private/link-local IPs, and `.local` hosts in `SessionManager`.
- `CUL_SKIP_DESKTOP=1`: skip Windows UIA desktop tests in `tests/` (intended for headless non-interactive **Windows** CI; `snapshot.py` and `desktop_uia.py` load `ctypes.WinDLL("user32")` on module import, so full package imports require Windows hosts).
- `COMPUTER_USE_LITE_STATE_PATH`: override default `TaskState` JSON file path (`results/runtime/task_state.json`).

Run from the repository root (`computer-use-lite/`):

```powershell
# Full pytest suite (run on an interactive Windows desktop to include UIA tests)
pytest tests -v --tb=short

# Headless Windows CI mode (skips Windows desktop UIA tests)
$env:CUL_SKIP_DESKTOP = "1"
pytest tests -v --tb=short

# Standalone live E2E runner (writes summary to temp by default unless --write-results is passed)
python tests/test_e2e.py

# Standalone stdio MCP vs direct Api latency overhead benchmark
python tests/test_mcp_server.py

# Launch MCP stdio server directly
python -u -m computer_use_lite.mcp_server
# Or via entry point:
computer-use-lite-mcp
```

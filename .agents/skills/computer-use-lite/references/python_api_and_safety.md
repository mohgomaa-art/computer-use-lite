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

- **Thread-affinity requirement**: `BrowserSession` wraps Playwright `sync_api` (strict greenlet thread affinity — cannot cross OS threads or run directly inside an active `asyncio` loop without worker isolation) alongside `DirectCdpClient` (persistent WebSocket I/O thread). `DesktopSession` pins UIA COM MTA calls to one worker thread. Use `SessionManager` (or one worker thread per session) for async or concurrent execution.
- **Per-session storage isolation**: Pass distinct `state_path` and `crops_dir` per concurrent `Api(session, ...)` instance so callers do not collide on `state.DEFAULT_PATH` (`COMPUTER_USE_LITE_STATE_PATH` env override or repo runtime state file). Pass `state_fsync=False` for disposable temp state when durability across crashes is not required.

---

## Core `Api` Workflow

```python
api = Api(session, state_path="session_state.json", crops_dir="session_crops")

# 1. Discover interactables (uses Api defaults for max_elements unless specified)
line_map = api.discover_interactables(export_crops=True, filter_query=None)
# Telemetry in api.last_stats; blind region boxes/paths in api.regions

# 2. Inspect one element (live "value" read on textbox/searchbox; "[REDACTED]" for passwords)
info = api.inspect_element(element_id)

# 3. Execute with targeted freshness validation (throws StaleElementError on drift/occlusion/rev change)
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
   - On current `HEAD`, `BrowserSession.discover()` iterates multi-document snapshot frames to surface interactive elements inside cross-origin OOPIFs and prunes scroll-clipped nodes and redundant `<label>` wrappers (verified in headless localhost corpus tests; unverified live on a restarted MCP server against public sites).
   - Known boundaries: omits closed Shadow DOM; omits non-interactive static text; cross-origin frame occlusion checks cannot walk parent-frame DOM; `navigate()` waits only for `"domcontentloaded"`; `perform()` runs `scrollIntoView` only after `verify_fresh(doScroll=False)` has passed viewport visibility.
   - Public methods on `BrowserSession`: `discover`, `bounds`, `verify_fresh`, `is_occluded`, `perform`, `hover`, `navigate`, `back`, `scroll`, `press_key`, `click_coordinate`, `canvas_rects`, `read_value`, `signature`, `close`.
2. **Desktop Perception & Safety (`DesktopSession`)**:
   - Scopes UIA `FindAllBuildCache` queries strictly to one target `hwnd` on a `COINIT_MULTITHREADED` COM worker using `CUIAutomation8` (`IUIAutomation2`) with `AutoSetFocus = 0`. Never calls desktop-root enumeration.
   - Enforces active foreground match (`Foreground safety abort` -> MCP `ForegroundMismatch`) before physical input.
   - Maintains physical-cursor `KillSwitch` (`HUMAN TAKEOVER` abort when physical cursor movement occurs); never disable `KillSwitch` during live runs.
   - `DesktopSession.verify_fresh()` checks UIA bounds/enabled/offscreen state and sets `"occluded": False` without checking Z-order overlap.
   - **Desktop capture (`blind_gap.capture_desktop_region`)**: on current `HEAD`, checks whether `hwnd` is DWM-cloaked, non-foreground, minimized, or overlapped by a higher visible Z-order window and tries Win32 `PrintWindow` first for those windows before falling back to/using `PIL.ImageGrab.grab` (verified via mocked `CreateWindowExW` test and `exebox` capture; live multi-window `Default` desktop pixel comparison remains unverified due to `exebox` isolation; RTL OS locales can render `PrintWindow` horizontally mirrored).
3. **Blind Region Detection (`blind_gap.py`)**:
   - Detects large/sparse canvases (`opaque_canvas`, `small_opaque_canvas`) in browsers and sparse control counts (`low_uia`) on desktop windows; pixel-cursor grid probing failed reliability/safety gates and is absent by design.
   - Overlapping canvases can emit duplicate blind regions; browser-mode embedded cross-origin frames and desktop-mode collapsed browser windows (`RootWebArea`) can emit zero blind regions.
4. **Full Action Redaction (`TaskState`)**:
   - `TaskState.record_action()` strips plaintext `value` for **all** recorded actions where `value is not None`, replacing it with length, truncated SHA-256 hash, and `"value_redacted": true`.

---

## Environment Variables & CLI Test Commands

- `CUL_MCP_ALLOW_FILE_URLS=1`: allow `file://` navigation targets in `SessionManager`.
- `CUL_MCP_ALLOW_PRIVATE_URLS=1`: allow localhost, loopback, private/link-local IPs, and `.local` hosts in `SessionManager`.
- `CUL_SKIP_DESKTOP=1`: skip Windows UIA desktop tests in `tests/` (intended for headless non-interactive **Windows** CI; note `snapshot.py` and `desktop_uia.py` load `ctypes.WinDLL('user32')` at import time, so full module imports require Windows hosts).
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

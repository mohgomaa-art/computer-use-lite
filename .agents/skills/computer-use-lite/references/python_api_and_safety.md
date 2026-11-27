# Computer Use Lite Python API, Architecture & Testing Reference

Use this reference when importing `computer_use_lite` directly in Python scripts, orchestrators, tests, or benchmarks (`v0.2.0a0+`).

---

## Canonical Imports & Cross-Platform Behavior

Prefer `computer_use_lite` (`src/computer_use_lite/`). Legacy `src/engine/` re-exports the same symbols for backwards compatibility:

```python
from computer_use_lite import (
    Api,
    BrowserSession,
    DesktopSession,
    Resolver,
    StaleElementError,
    __version__,
    detect,   # blind_gap.detect
    export,   # blind_gap.export
)
from computer_use_lite.session_manager import SessionManager
from computer_use_lite.desktop_uia import list_windows
```

- **Cross-platform package imports**: `snapshot.py`, `desktop_uia.py`, and `desktop_cursor_overlay.py` guard Win32 `ctypes`/`comtypes` imports (`sys.platform != "win32"`), allowing browser automation and MCP tests to import and run on Linux (verified on WSL2 `kali-linux` Python `3.14.7`). Native desktop UIA (`DesktopSession`, `list_windows`) requires Windows 10/11.
- **Thread-affinity requirement**: `BrowserSession` wraps Playwright `sync_api` (strict greenlet thread affinity — cannot migrate OS threads or run inside an active `asyncio` event loop without worker isolation). `DesktopSession` pins UIA COM MTA calls to one worker thread. Use `SessionManager` (or a dedicated single-thread worker per session) for async or concurrent execution.
- **Per-session storage isolation**: pass distinct `state_path` and `crops_dir` per concurrent `Api(session, ...)` so sessions do not collide on `state.DEFAULT_PATH` (`COMPUTER_USE_LITE_STATE_PATH` or `<repo>/results/runtime/task_state.json`). Pass `state_fsync=False` for disposable sessions.

---

## Core `Api` Workflow

```python
api = Api(session, state_path="session_state.json", crops_dir="session_crops")

# 1. Discover interactables (max_elements default 60, optional include_static_text=True excerpt)
line_map = api.discover_interactables(export_crops=True, filter_query=None, include_static_text=False)
# Optional static text summary (sanitized [UNTRUSTED_UI_TEXT] helper):
page_text = api.read_page(max_chars=2000)

# 2. Inspect element metadata & value ("[REDACTED]" for passwords/sensitive names)
info = api.inspect_element(element_id)

# 3. Execute with targeted freshness validation (throws StaleElementError on drift/occlusion/rev mismatch)
res = api.execute_action(element_id, "type", value="...", revision=api.resolver.revision, clear=True)
# Continuous drag (browser CDP or desktop SendInput):
drag_res = api.drag(element_id, target_element_id=other_id)  # or to_x=..., to_y=...

# 4. Hover to capture newly revealed items while preserving surviving sibling IDs at the new revision
hover_res = api.hover_element(target_id, wait_ms=350)

# 5. Bump revision explicitly after direct session scroll/navigate/press_key/click_coordinate calls
session.scroll(dx=0, dy=400)
new_rev = api.invalidate_revision("scroll")
```

Note on `clear=False`: `Api.execute_action(..., "type", clear=False)` forwards `clear=clear` only to `BrowserSession.perform()` (`api.py:195-198`). `DesktopSession.perform(el, action, value=None)` takes no `clear` parameter.

---

## Engine Architecture & Observed Boundaries

1. **Browser Perception & Safety (`BrowserSession`, `browser_cdp.py`)**:
   - Combines Playwright browser lifecycle with CDP Pipe IPC by default; optional fast-path `DirectCdpClient` WebSocket (`websockets`) is opt-in via `CUL_MCP_DIRECT_WS=1`.
   - Two-call `DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree` discovery across `15` interactive roles (`resolver.INTERACTIVE`), top-frame compositor hit-testing (`DOM.getNodeForLocation` rejecting parent/cross-frame overlays, marking unprovable cross-origin targets `verification_scope="cross_origin_unprovable"`, `verified=False`), sticky-header scroll offsets, CDP `Fetch` redirect/IP-drift URL validation, full-body FNV-1a digesting in `signature()`, lossless `<input type=date>` prototype filling, multi-tab helpers (`tabs()`, `switch_tab()`, `close_tab()`, `consume_new_tabs()`), and rich `inspect_metadata()` (checked, selected, readonly, disabled, expanded, pressed, range bounds, `<select>` options).
   - Remaining boundaries: closed Shadow DOM and un-focused cross-origin site-isolated third-party embeds can omit internal controls; `navigate()` waits only for `"domcontentloaded"`; `perform()` scrolls after viewport visibility validation; `_target_signature()` (`browser_cdp.py:2483-2534`) captures `ro`, `chk`, `exp`, `prs`, `sel`, `open`, and hashed/redacted values on the target node (while `signature()` without a target falls back to page counts/URL/title/body hash), and unchanged states, `focus_only_noop`, `readonly_target_noop`, or custom un-attributed widgets still benefit from `inspect()` or crop verification.
2. **Desktop Perception & Safety (`DesktopSession`, `desktop_uia.py`)**:
   - Scopes UIA `FindAllBuildCache` strictly to one `hwnd` on `COINIT_MULTITHREADED` (`CUIAutomation8` / `IUIAutomation2` with `AutoSetFocus=0`), excluding inactive lower-Z Explorer `ShellTabWindowClass` containers. Never runs desktop-root UIA enumeration.
   - `DesktopSession.verify_fresh()` checks UIA bounds/enabled/offscreen **plus Win32 Z-order & DWM cloaking** (`blind_gap._is_window_occluded_or_bg(self.hwnd, rect_bbox, require_foreground=False)`), raising `StaleElementError` when occluded.
   - `DesktopSession.perform()` enforces `TakeoverGuard` (`CUL_TAKEOVER_GLOW=1` + physical `Esc` abort -> `UserInterruptedError` / MCP `user_interrupted`), physical-cursor `KillSwitch` (`HUMAN TAKEOVER`), foreground safety (`ForegroundMismatch`), `validate_desktop_target`, and `validate_key_spec`. Uses `_commit_dialog_text` for `#32770` dialogs and `ValuePattern.SetValue` / `SendInput` elsewhere (always verify saved files on disk outside MCP).
   - `blind_gap.capture_desktop_region` uses `PrintWindow` (with horizontal mirroring for `WS_EX_LAYOUTRTL` windows) before screen fallback when occluded/non-foreground (dark WinUI Mica backdrops / un-mirrored UWP frames remain documented caveats).
3. **Overlay & Cursor Physics (`cursor_overlay.py`, `desktop_cursor_overlay.py`, `takeover_guard.py`)**:
   - Controlled via `CUL_AGENT_CURSOR` and `CUL_AGENT_CURSOR_GLIDE_MS` (`0` when headless, `140` default headful), plus `CUL_TAKEOVER_GLOW=1` for desktop interruption glow + `Esc` hotkey guard.
4. **Full Action Redaction (`TaskState`, `state.py`)**:
   - Word/camelCase-boundary `is_sensitive_name` detection plus `sanitize_ui_text` protocol delimiting; `TaskState.record_action()` strips plaintext `value` and stores `hmac:<16hex>` via per-process ephemeral HMAC-SHA256 for secrets.

---

## Environment Variables & CLI Commands

| Variable | Effect |
| :--- | :--- |
| `CUL_MCP_HEADFUL=1` | Makes omitted `headless` default to headful in `open_browser` (explicit `headless=True/False` still wins) |
| `CUL_MCP_ALLOW_FILE_URLS=1` | Allow `file://` URLs in `SessionManager` / SSRF validator |
| `CUL_MCP_ALLOW_PRIVATE_URLS=1` | Allow localhost, private/link-local IPs, `.local`, and unresolved DNS hosts |
| `CUL_MCP_DIRECT_WS=1` | Opt-in to `DirectCdpClient` loopback WebSocket instead of default Playwright Pipe IPC |
| `CUL_AGENT_CURSOR` / `CUL_AGENT_CURSOR_GLIDE_MS` | Force cursor overlay on/off (`1`/`0`) and glide animation duration (ms) |
| `CUL_TAKEOVER_GLOW=1` | Enable desktop takeover glow + physical `Esc` interruption (`UserInterruptedError`) |
| `CUL_SESSION_IDLE_TTL_S` | Idle session reaping threshold when `MAX_SESSIONS` (`16`) is reached (default `1800`s) |
| `CUL_ALLOW_SYSTEM_SHORTCUTS=1` | Allow blocked OS keys/hotkeys (`Win`, `Meta`, `Alt+Tab`, `Alt+F4`, `Ctrl+Esc`, `Ctrl+Alt+Del`, etc.) |
| `CUL_DESKTOP_ALLOW_SENSITIVE=1` / `CUL_DESKTOP_ALLOW_PROCESSES` | Override sensitive desktop app blocklist globally or per comma-separated process list |
| `CUL_SKIP_DESKTOP=1` | Skip `@pytest.mark.windows_desktop` tests (for CI or non-interactive desktops) |
| `COMPUTER_USE_LITE_STATE_PATH` | Override default `TaskState` JSON output path |

Run from the repository root (`computer-use-lite/`):

```powershell
# Full Windows pytest suite (interactive desktop)
pytest -v -rs --strict-markers -W error::pytest.PytestReturnNotNoneWarning

# Headless CI / browser + supervisor suite (skips interactive desktop UIA tests)
$env:CUL_SKIP_DESKTOP = "1"
pytest -q -m "not windows_desktop" --strict-markers -W error::pytest.PytestReturnNotNoneWarning

# Launch supervised reloadable stdio MCP server (16 tools: 15 core + cul_reload)
python -u -m computer_use_lite.supervisor
# or:
computer-use-lite-mcp-supervised

# Launch direct unsupervised stdio MCP server (15 tools)
python -u -m computer_use_lite.mcp_server
# or:
computer-use-lite-mcp

# Standalone E2E runner / MCP overhead benchmark
python tests/test_e2e.py
python tests/test_mcp_server.py
```

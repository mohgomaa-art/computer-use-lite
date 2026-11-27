# Computer Use Lite MCP Tool Reference

Reference schema and runtime guardrails for `computer_use_lite.supervisor` (`computer-use-lite-mcp-supervised`, `16` tools, default Windows MCP installer mode) and `computer_use_lite.mcp_server` (`computer-use-lite-mcp`, `15` core tools). All defaults, clamps, and behaviors trace directly to inspected server code (`v0.2.0a0+`).

---

## Tool Inventory (`15` Core Tools + Supervisor `cul_reload`)

### Session, Lifecycle & Reload

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `open_browser` | `url: str`, `headless: bool \| None = None`, `width: int = 1280`, `height: int = 720`, `auto_discover: bool = True` | No / No / No | Validates URL SSRF/scheme rules (`PermissionDenied`/`ValueError`) and viewport (`200..3840` x `200..2160`). Omitted `headless` uses `CUL_MCP_HEADFUL` (`1`/`true`/`yes`/`on` => headful). Re-run `discover()` if client SPA hydration shifts right after `auto_discover=True`. |
| `list_desktop_windows` | `title_contains: str \| None = None`, `class_name: str \| None = None`, `process_name: str \| None = None`, `limit: int = 40` | Yes / No / Yes | Windows only; clamps `limit` `[1, 200]`. Returns `{windows: [{hwnd, pid, process_name, class, title, box}], count}`. Supports `process_name` substring filtering when window titles mutate dynamically. |
| `open_desktop` | `hwnd: int \| None = None`, `title_contains: str \| None = None`, `process_name: str \| None = None`, `auto_discover: bool = True` | No / No / No | Windows only; requires at least one selector (`hwnd` recommended). Enforces `validate_desktop_target` sensitive-app blocklist (`PermissionDenied`), attaches scoped UIA (`IUIAutomation2` MTA, `AutoSetFocus=0`), and returns `foreground_matched`, `active_foreground_hwnd`, and `active_foreground_process` (`FG_MATCH:true/false` + `ACTIVE_FG:<proc>` in `discover` header). |
| `list_sessions` | *(none)* | Yes / No / Yes | Returns `{sessions: [{session_id, kind, target, revision, elements, blind_regions, idle_s, tab_count?, active_tab_index?}], count, server_pid, headful_default}`. Browser `tab_count`/`active_tab_index` are included when `kind == "browser"`. |
| `close_session` | `session_id: str` | No / Yes / Yes | Closes worker thread, browser/desktop handle, overlay, and temporary session folder (`cul_mcp_<id>_*`). Resets `CursorCoordinator` baseline when closing the last active session. Returns `{ok: true, closed: session_id}`. |
| `cul_reload` | `reason: str \| None = None` | No / Yes / No | **Supervisor-only (`computer_use_lite.supervisor`)**. Pre-spawns and initializes a fresh child server, refreshes the non-destructive temp LKG snapshot on success, closes the old child cleanly (resetting all open sessions/`eN`/`REV:N`/Chrome/overlays), replies with `{ok: true, reloaded: true, generation, old_pid, new_pid, rolled_back, state_reset_warning}` (or rollback fields `{ok: false, reloaded: false, rolled_back: true, active_mode, generation, broken_edit_error, consecutive_failures}`), and emits `notifications/tools/list_changed`. Flushes multi-MB payloads atomically without pipe truncation; edits to `supervisor.py` itself require client restart. |

### Perception & Inspection

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `discover` | `session_id: str`, `max_elements: int = 60`, `filter_query: str \| None = None`, `export_crops: bool = True`, `include_blind_images: bool = True`, `include_static_text: bool = False`, `skip_unchanged_images: bool = False` | Yes / No / No (bumps `REV`) | Captures `15` interactive roles (`button`, `menuitem`, `tab`, `link`, `textbox`, `searchbox`, `combobox`, `checkbox`, `radio`, `switch`, `clickable`, `listitem`, `treeitem`, `slider`, `spinbutton`), clamps `max_elements` `[1, 300]`, filters on `name`/`role`/`id`, excludes inactive Explorer tabs, retries transient `COMError` scans (`4` attempts, backoff `0.15`/`0.35`/`0.70`s), sanitizes text (`sanitize_ui_text`), optionally appends bounded (`<=1200` chars) `PAGE_TEXT:[UNTRUSTED_UI_TEXT]`, attaches up to `MAX_INLINE_BLIND_IMAGES = 4` PNG crops, and omits unchanged inline PNG bytes when `skip_unchanged_images=True` (`IMAGES_UNCHANGED:true`). |
| `inspect` | `session_id: str`, `element_id: str` | Yes / No / Yes | Returns stored metadata (excluding `ref`/`_element`) plus rich live metadata (`input_type`, `checked`, `selected`, `readonly`, `disabled`, `expanded`, `pressed`, `valuemin`, `valuemax`, `valuenow`, `<select>` `options` up to `40`, and `value` up to `400` chars when applicable). Redacts `value`/`valuenow` as `"[REDACTED]"` when password-flagged or `is_sensitive_name` matches. |

### Actions & Navigation

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `act` | `session_id: str`, `element_id: str`, `action: "click" \| "type" \| "focus" \| "drag"`, `value: str \| None = None`, `revision: int \| None = None`, `clear: bool = True`, `target_element_id: str \| None = None`, `to_x: float \| None = None`, `to_y: float \| None = None` | No / No / No | Validates targeted freshness (`moved >2 px`, top-frame/Z-order occluded, disabled/offscreen, removed, or stale revision -> `StaleElementError`). `clear=False` appends **only** in `BrowserSession`; `DesktopSession.perform()` has no `clear` arg (`ValuePattern.SetValue` replaces; `#32770` uses `_commit_dialog_text`); non-focusable UIA `"focus"` raises `ValueError`. Attaches `tab_count`/`opened_tab` on new tabs, bumps `resolver.revision`, and invalidates all prior `eN` IDs. |
| `hover` | `session_id: str`, `element_id: str`, `wait_ms: int = 350` | No / No / No | Clamps `wait_ms` `[0, 5000]`, validates freshness, hovers, waits adaptively (`<= wait_ms`), re-discovers, calls `reconcile_hover` (updating surviving sibling IDs in place **without** invalidating them at the new revision), and returns `{hovered, point, wait_ms_elapsed, revision, added, known_before, known_after}`. |
| `navigate` | `session_id: str`, `url: str \| None = None`, `action: "goto" \| "back" \| "list_tabs" \| "switch_tab" \| "close_tab" = "goto"`, `auto_discover: bool = False`, `tab_index: int \| None = None` | No / No / No | Browser sessions only. `list_tabs` returns `{ok, action, tabs, tab_count, active_tab_index, url, title, revision}` without bumping revision. `switch_tab`/`close_tab` accept `tab_index` or `url`. `goto`/`back`/`switch_tab`/`close_tab` bump revision; call `discover()` after SPA settle. |
| `scroll` | `session_id: str`, `dy: int = 400`, `dx: int = 0`, `x: int \| None = None`, `y: int \| None = None` | No / No / No | Scrolls viewport/window (`dy > 0` down) at optional bounded `(x, y)` (both must be supplied or both omitted for center), emits `verification_scope` (`"unverified_sendinput"` or `"dom_scroll"`), and bumps `resolver.revision`; re-run `discover()` afterward. |
| `press_key` | `session_id: str`, `key: str \| None = None`, `keys: list[str] \| None = None`, `delay_ms: int = 15` | No / No / No | Sends one key/combo or an atomic ordered `keys` sequence (`delay_ms` `0..500` ms) including `Numpad0..9` and `NumpadAdd`/`NumpadPlus`/`NumpadSubtract`/`NumpadMinus`/`NumpadMultiply`/`NumpadDivide`/`NumpadPeriod` with Win32 scan codes and `KEYEVENTF_EXTENDEDKEY`. Validates every key via `validate_key_spec` before sending any key, reports `verification_scope`, attaches `tab_count`/`opened_tab`, and bumps revision. |
| `click_at` | `session_id: str`, `x: int`, `y: int`, `button: "left" \| "right" \| "middle" = "left"`, `clicks: int = 1` | No / No / No | Bounded coordinate click for `blind<k>` crops; rejects out-of-bounds coords or invalid `button`/`clicks` with `ValueError`, emits `verification_scope`, attaches `tab_count`/`opened_tab`, and bumps revision. |
| `drag_at` | `session_id: str`, `x1: int`, `y1: int`, `x2: int`, `y2: int`, `button: "left" \| "right" \| "middle" = "left"`, `duration_ms: int = 250` | No / No / No | Bounded coordinate drag (`left`/`middle`/`right`) strictly inside window/viewport bounds with guaranteed button-up cleanup in `finally`, emits `verification_scope`, attaches `tab_count`/`opened_tab`, and bumps revision. |
| `type_text` | `session_id: str`, `text: str`, `press_enter: bool = False`, `input_mode: "unicode" \| "vk_scan" = "unicode"` | No / No / No | Types text (up to `1000` chars) into the focused control of the active foreground session (or same-process owned modal on desktop) without needing a UIA `element_id`. Desktop mode enforces `kill_switch` guards; `input_mode="vk_scan"` synthesizes real VK/Shift scan codes for ASCII on desktop widgets that ignore `KEYEVENTF_UNICODE` (falling back to Unicode for non-ASCII) and reports `verified` + `verification_scope` (`"uia_readback"` vs `"unverified_sendinput"`/`"unverified_cdp_input"`). |

---

## Error JSON Contract

Failed tool calls return `CallToolResult(isError=True)` with JSON:

```json
{
  "ok": false,
  "error_type": "StaleElementError",
  "error": "...",
  "recoverable": true,
  "next_step": "Call discover(session_id) to refresh elements and revision before retrying."
}
```

- **`recoverable: true` with `next_step`**: `StaleElementError`, `ElementNotFound` (`KeyError`), `ForegroundMismatch`, `HumanTakeover` (emitted on `"HUMAN TAKEOVER"` physical cursor drift), `COMError` (includes `-2146233083` timeout narrowing hint), `WindowNotFound` (`LookupError`), `SessionNotFound`, `SessionLimitReached`, and `user_interrupted` (includes `"user_interrupted": true`, emitted when physical `Esc` triggers takeover abort).
- **`recoverable: true` without `next_step`**: `ValueError` (also emitted for strict `extra="forbid"` / `additionalProperties: false` parameter rejections, naming unknown keys and valid parameter names), `TimeoutError`, and `asyncio.TimeoutError` (normalized with explicit timeout fallback message across Python 3.10+).
- **`recoverable: false` without `next_step`**: `PermissionDenied` (`PermissionError`) and unhandled runtime `Error`.
- **Supervisor JSON-RPC errors (`-32603`)**: emitted when an active child dies mid-request (`"server reloaded, retry"` or crash) or while no healthy child is active during crash backoff.

---

## Runtime Guardrails, Env Flags & Redaction

1. **URL & SSRF Policy (`validate_navigation_url` + browser Fetch guard)**:
   - Allows `http://` and `https://` URLs (`<= 4096` chars, no ASCII control chars).
   - Refuses `file://` unless `CUL_MCP_ALLOW_FILE_URLS=1` (`PermissionDenied`), and always refuses `javascript:` / `data:`.
   - Refuses localhost, loopback, private/link-local/reserved/non-global IPs, `.localhost`/`.local`, `metadata.google.internal`, and unresolved/`socket.gaierror`/empty DNS lookups (**fail-closed**) unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` (`PermissionDenied`). Browser navigation also runs a CDP `Fetch` redirect/IP-drift check; Chromium internal socket DNS-rebinding TOCTOU remains a documented browser boundary.
2. **Blocked OS Keys & Sensitive Desktop Processes (`state.py`)**:
   - `validate_key_spec`: blocks `win`, `lwin`, `rwin`, `meta`, `super`, `command`, `cmd` AND `Alt+Tab`, `Alt+F4`, `Alt+Escape`, `Ctrl+Escape`, `Ctrl+Shift+Escape`, `Ctrl+Alt+Delete` with `ValueError` unless `CUL_ALLOW_SYSTEM_SHORTCUTS=1`.
   - `validate_desktop_target`: blocks shells (`powershell.exe`, `pwsh.exe`, `cmd.exe`, `windowsterminal.exe`, `conhost.exe`, `consolewindowclass`, `cascadia_hosting_window_class`), password managers (`1password.exe`, `bitwarden.exe`, `keepass.exe`, `keepassxc.exe`), credential UIs (`credentialuibroker.exe`, `consent.exe`, `credential dialog xaml host`), and admin tools (`mmc.exe`, `regedit.exe`, `taskmgr.exe`, `regedit_regedit`, `mmcmainframe`) with `PermissionDenied` unless `CUL_DESKTOP_ALLOW_SENSITIVE=1` or listed in comma-separated `CUL_DESKTOP_ALLOW_PROCESSES`.
3. **Session Caps & Ephemeral Storage**:
   - `MAX_SESSIONS = 16`, idle session reaping via `CUL_SESSION_IDLE_TTL_S` (default `1800`s when at capacity), and `MAX_INLINE_BLIND_IMAGES = 4`.
4. **Full Privacy Redaction**:
   - `inspect()` emits `"[REDACTED]"` on password fields or `is_sensitive_name(...)` matches (`pass`, `password`, `pwd`, `secret`, `token`, `cvv`, `cvc`, `pin`, `card`, `ccnum`, `ssn`, `iban`, `otp`, `apikey`, `auth`, `current-password`, `cc-number`, etc., matched on word/camelCase boundaries).
   - `TaskState.record_action()` strips plaintext `value` on all logged actions and hashes secret values with a per-process ephemeral HMAC-SHA256 (`hmac:<16hex>`).

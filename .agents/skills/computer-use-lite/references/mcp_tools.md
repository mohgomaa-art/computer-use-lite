# Computer Use Lite MCP Tool Reference

Reference schema and runtime guardrails for `computer_use_lite.mcp_server` (`computer-use-lite-mcp` or `python -u -m computer_use_lite.mcp_server`). All parameter defaults and descriptions below trace strictly to MCP tool schemas and inspected `HEAD` server code.

---

## Tool Inventory (`13` Tools)

### Session & Window Lifecycle

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `open_browser` | `url: str`, `headless: bool = True`, `width: int = 1280`, `height: int = 720`, `auto_discover: bool = True` | No / No / No | Launches Chromium at a permitted URL (enforces scheme/network allowlist and server viewport bounds, returning `PermissionDenied` or `ValueError` if invalid). Waits for initial page load; client-rendered SPAs can shift right after `auto_discover=True`, so re-run `discover()` if counts look sparse or drift immediately. Returns `SESSION:...` + `REV:N` map when `auto_discover=True`, else `{session_id, kind, url, title, viewport}`. |
| `list_desktop_windows` | `title_contains: str \| None = None`, `class_name: str \| None = None`, `limit: int = 40` | Yes / No / Yes | Windows only; clamps `limit` internally. Returns `{windows: [{hwnd, pid, process_name, class, title, box}], count}`. Excludes untitled windows unless `class_name` is specified and retains minimized/cloaked far-negative boxes alongside valid multi-monitor virtual-screen coordinates. |
| `open_desktop` | `hwnd: int \| None = None`, `title_contains: str \| None = None`, `process_name: str \| None = None`, `auto_discover: bool = True` | No / No / No | Windows only; requires at least one selector (`hwnd` preferred to disambiguate shared processes and mixed/localized titles). Attaches scoped Windows UIA (`IUIAutomation2` MTA with `AutoSetFocus=0`) to one visible window. |
| `list_sessions` | *(none)* | Yes / No / Yes | Returns `{sessions: [{session_id, kind, target, created_at, revision}], count}`. Browser `target` can briefly lag click-triggered navigation until the next `discover()` refreshes it. |
| `close_session` | `session_id: str` | No / Yes / Yes | Closes worker thread, browser/desktop handle, and per-session temporary crop/state directory. Returns `{ok: true, closed: session_id}`. |

### Perception & Inspection

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `discover` | `session_id: str`, `max_elements: int = 60`, `filter_query: str \| None = None`, `export_crops: bool = True`, `include_blind_images: bool = True` | Yes / No / No (bumps `REV`) | Captures interactive roles (`button`, `menuitem`, `tab`, `link`, `textbox`, `searchbox`, `combobox`, `checkbox`, `radio`, `switch`, `clickable`, `listitem`, `treeitem`) into a `REV:N` `line_map` (clamps `max_elements` internally). `filter_query` matches case-insensitively on `name`, `role`, or `id`. Omits static text, native `<select>` dropdown popups, unassociated `<label>` names (`name=""`), closed Shadow DOM, and (observed live) site-isolated third-party cross-origin embeds. File lists/dialogs often emit a `listitem` row plus column `textbox` cells; `<label>` wrappers beside `button`/`clickable` can stay unpruned. Appends bounded inline PNG crops for opaque canvases and sparse UIA surfaces when `include_blind_images=True`. |
| `inspect` | `session_id: str`, `element_id: str` | Yes / No / Yes | Returns stored metadata (excluding internal refs) plus live `"value"` **only** on `textbox` and `searchbox` roles (`"[REDACTED]"` if password-flagged). Omits `"value"` and checked state on `combobox`, `checkbox`, `radio`, `switch`, and `clickable` widgets. Note: read-only inputs expose `textbox` semantics (use `inspect` after typing to verify mutation), while native Win32 file-save `Edit` boxes updated via `ValuePattern` can show the typed string in `inspect` without committing it to the OS file dialog buffer. |

### Actions & Navigation

| Tool | Schema Parameters & Defaults | Hints (`ReadOnly` / `Destructive` / `Idempotent`) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `act` | `session_id: str`, `element_id: str`, `action: "click" \| "type" \| "focus"`, `value: str \| None = None`, `revision: int \| None = None`, `clear: bool = True` | No / No / No | Validates targeted freshness (`moved >2 px`, occluded, disabled, removed, or stale revision -> `StaleElementError`) before executing. Bumps `revision` and invalidates sibling `eN` IDs. Treat `verified` and synchronous `state_delta` strictly as telemetry: adjacent `<input>` elements without distinct values share active-element hashes (`verified: false` false negatives), focus moves on read-only inputs/overlays or Win32 `ValuePattern` return `verified: true` false positives, and debounced typeaheads or navigations capture transient intermediate text. Pass `clear=False` to append text. |
| `hover` | `session_id: str`, `element_id: str`, `wait_ms: int = 350` | No / No / No | Clamps `wait_ms` internally, validates freshness, hovers, waits, re-discovers, reconciles disappeared nodes, and returns `{hovered, point, revision, added, known_before, known_after}` where `added` contains new `{"id", "role", "name", "box"}` entries. Bumps `revision`. |
| `navigate` | `session_id: str`, `url: str \| None = None`, `action: "goto" \| "back" = "goto"`, `auto_discover: bool = False` | No / No / No | Browser sessions only. Waits for `domcontentloaded` (not SPA hydration or lazy scripts) and bumps `revision`. Keep `auto_discover=False` and call `discover()` after rendered UI settles. |
| `scroll` | `session_id: str`, `dy: int = 400`, `dx: int = 0` | No / No / No | Scrolls at the center of the attached viewport/window (`dy > 0` scrolls down) and bumps `revision`. Re-run `discover()` afterward for refreshed coordinates and IDs. |
| `press_key` | `session_id: str`, `key: str` | No / No / No | Sends named keys or combos (`Enter`, `Tab`, `Escape`/`Esc`, `Backspace`, `Delete`/`Del`, `Home`, `End`, `PageUp`, `PageDown`, `Up`/`Down`/`Left`/`Right`, function keys, `Ctrl+a`, `Ctrl+Shift+s`, `Alt+F4`). Rejects blocked OS keys; single-character desktop mapping uses `VkKeyScanW` (untested live on non-US input locales). Bumps `revision`. |
| `click_at` | `session_id: str`, `x: int`, `y: int`, `button: "left" \| "right" \| "middle" = "left"`, `clicks: int = 1` | No / No / No | Bounded coordinate click for `blind<k>` crops; rejects out-of-bounds coordinates or invalid `button`/`clicks` with `ValueError`. No drag-and-drop primitive exists. Bumps `revision`. |

---

## Error JSON Contract

Failed MCP calls return `isError=True` with JSON:

```json
{
  "ok": false,
  "error_type": "StaleElementError",
  "error": "...",
  "recoverable": true,
  "next_step": "Call discover(session_id) to refresh elements and revision before retrying."
}
```

- **Actionable `recoverable: true` errors (include `next_step`)**: `StaleElementError`, `ElementNotFound`, `ForegroundMismatch`, `COMError`, `WindowNotFound`, `SessionNotFound`, `SessionLimitReached`.
- **Argument/timeout `recoverable: true` errors (omit `next_step`)**: `ValueError`, `TimeoutError`.
- **Policy/runtime `recoverable: false` errors (omit `next_step`)**: `PermissionDenied` and unhandled exceptions (such as Playwright `Error` on network navigation failures).

---

## Runtime Guardrails, Env Flags & Redaction

1. **URL & SSRF Policy (`validate_navigation_url`)**:
   - Allows `http://` and `https://` URLs with valid host/netloc, bounded length, and no ASCII control characters.
   - Refuses `file://` unless `CUL_MCP_ALLOW_FILE_URLS=1` is set (`PermissionDenied`), and always refuses `javascript:` or `data:`.
   - Refuses localhost, loopback, private/link-local/reserved/non-global IPs, local domains, and cloud metadata hosts by default unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` is set. Always observe actual runtime error messages rather than assuming server env configuration.
2. **Blocked OS Keys (`press_key`)**:
   - Rejects `win`, `lwin`, `rwin`, `meta`, `super`, `command`, and `cmd` (case-insensitive, standalone or modifier) with `ValueError`.
3. **Session Caps & Ephemeral Storage**:
   - Server enforces active-session limits (`SessionLimitReached` via `MAX_SESSIONS`) and bounded inline crop attachment per `discover` response (`MAX_INLINE_BLIND_IMAGES` in `session_manager.py`).
   - Each session binds a dedicated FIFO worker thread with an ephemeral `task_state.json` (`fsync` disabled) and temporary `crops/` folder removed on `close_session` or server shutdown.
4. **Full Privacy Redaction**:
   - `inspect()` emits `"value": "[REDACTED]"` for password-flagged text/search controls.
   - `signature()` redacts password-like active fields and hashes focused values.
   - `TaskState.record_action()` removes plaintext `value` across **all** logged actions, retaining value length, SHA-256 hash prefix, and `"value_redacted": true`.

# Computer Use Lite MCP Tool Reference

Reference schema and runtime guardrails for `computer_use_lite.mcp_server` (`computer-use-lite-mcp` or `python -u -m computer_use_lite.mcp_server`). All parameter defaults and descriptions below come directly from the MCP tool schemas and server source.

---

## Tool Inventory (13 Tools)

### Session & Window Lifecycle

| Tool | Schema Parameters & Defaults | Hints (ReadOnly / Destructive / Idempotent) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `open_browser` | `url: str`, `headless: bool = True`, `width: int = 1280`, `height: int = 720`, `auto_discover: bool = True` | No / No / No | Launches Chromium at an allowed URL (enforces scheme/network allowlist and server viewport bounds, returning `PermissionDenied` or `ValueError` if invalid). Returns `SESSION:... \| KIND:browser \| URL:... \| TITLE:... \| LATENCY_MS:... \| TOKENS_EST:...` + `REV:N` map when `auto_discover=True`, else `{session_id, kind, url, title, viewport}`. |
| `list_desktop_windows` | `title_contains: str \| None = None`, `class_name: str \| None = None`, `limit: int = 40` | Yes / No / Yes | Windows only. Clamps `limit` internally. Returns `{windows: [{hwnd, pid, process_name, class, title, box}], count}`. Excludes untitled windows unless `class_name` is specified; does not strip minimized/cloaked offscreen coordinates from the list, so skip far-negative boxes before attaching. |
| `open_desktop` | `hwnd: int \| None = None`, `title_contains: str \| None = None`, `process_name: str \| None = None`, `auto_discover: bool = True` | No / No / No | Windows only. Requires at least one selector (`hwnd` preferred to disambiguate multi-window/localized apps). Attaches scoped Windows UIA (`IUIAutomation2` MTA with `AutoSetFocus=0`) to one visible window. |
| `list_sessions` | *(none)* | Yes / No / Yes | Returns `{sessions: [{session_id, kind, target, created_at, revision}], count}`. Browser `target` can briefly lag click-triggered navigation until `discover()` refreshes it. |
| `close_session` | `session_id: str` | No / Yes / Yes | Closes worker thread, browser/desktop handle, and per-session temporary crop/state directory. Returns `{ok: true, closed: session_id}`. |

### Perception & Inspection

| Tool | Schema Parameters & Defaults | Hints (ReadOnly / Destructive / Idempotent) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `discover` | `session_id: str`, `max_elements: int = 60`, `filter_query: str \| None = None`, `export_crops: bool = True`, `include_blind_images: bool = True` | Yes / No / No (bumps `REV`) | Captures interactive roles (`button`, `menuitem`, `tab`, `link`, `textbox`, `searchbox`, `combobox`, `checkbox`, `radio`, `switch`, `clickable`, `listitem`, `treeitem`) into a `REV:N` `line_map` (clamps `max_elements` internally). `filter_query` matches case-insensitively on `name`, `role`, or `id`. Appends server-bounded inline `image/png` crops only when `blind_gap` detects opaque canvas or sparse-UIA regions and `include_blind_images=True`. Omits read-only static text. |
| `inspect` | `session_id: str`, `element_id: str` | Yes / No / Yes | Returns stored metadata (excluding internal DOM/UIA refs) plus live `"value"` **only** on `textbox` and `searchbox` roles (`"[REDACTED]"` if password-flagged). Does not return live `"value"` or checked state for `combobox`, `checkbox`, or range inputs. |

### Actions & Navigation

| Tool | Schema Parameters & Defaults | Hints (ReadOnly / Destructive / Idempotent) | Return Format & Operational Notes |
| :--- | :--- | :--- | :--- |
| `act` | `session_id: str`, `element_id: str`, `action: "click" \| "type" \| "focus"`, `value: str \| None = None`, `revision: int \| None = None`, `clear: bool = True` | No / No / No | Checks targeted freshness (`moved >2 px`, occluded, disabled, removed, or stale revision -> `StaleElementError`) before running action. Returns `{ok, element, action, mechanism, verified, state_delta, revision}` (`state_delta` fields map to `{"before": str, "after": str}`). Bumps revision and invalidates sibling `eN` IDs; treat `verified` as telemetry rather than proof. Pass `clear=False` to append text. |
| `hover` | `session_id: str`, `element_id: str`, `wait_ms: int = 350` | No / No / No | Clamps `wait_ms` internally, verifies freshness, hovers, waits, re-discovers, reconciles disappeared elements, and returns `{hovered, point, revision, added, known_before, known_after}` where `added` holds newly revealed `{"id", "role", "name", "box"}` entries. Bumps `revision`. |
| `navigate` | `session_id: str`, `url: str \| None = None`, `action: "goto" \| "back" = "goto"`, `auto_discover: bool = False` | No / No / No | Browser sessions only. Waits for DOM content load (not full SPA/lazy hydration) and bumps `revision`. Leave `auto_discover=False` on dynamic pages and call `discover()` once rendered content settles. |
| `scroll` | `session_id: str`, `dy: int = 400`, `dx: int = 0` | No / No / No | Scrolls at the center of the attached viewport/window (`dy > 0` scrolls down) and bumps `revision`. Run `discover()` afterward for refreshed viewport coordinates and IDs. |
| `press_key` | `session_id: str`, `key: str` | No / No / No | Sends single keys or combos (`Enter`, `Tab`, `Escape`/`Esc`, `Backspace`, `Delete`/`Del`, `Home`, `End`, `PageUp`, `PageDown`, `Up`/`Down`/`Left`/`Right`, function keys, `Ctrl+a`, `Ctrl+Shift+s`, `Alt+F4`). Rejects blocked OS keys; single printable char layout lookup on desktop relies on active thread layout (untested on non-US layouts). Bumps `revision`. |
| `click_at` | `session_id: str`, `x: int`, `y: int`, `button: "left" \| "right" \| "middle" = "left"`, `clicks: int = 1` | No / No / No | Bounded coordinate click intended for `blind<k>` crops; fails with `ValueError` if `(x, y)` lies outside attached viewport/window bounds or if `button`/`clicks` fails validation. No drag-and-drop primitive exists. Bumps `revision`. |

---

## Error JSON Contract

Failed MCP calls set `isError=True` and emit compact JSON:

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
- **Policy/runtime `recoverable: false` errors (omit `next_step`)**: `PermissionDenied` and unhandled exceptions (such as Playwright `Error` on `net::ERR_*` navigation failures).

---

## Runtime Guardrails & Environment Flags

1. **URL & SSRF Navigation Policy (`validate_navigation_url`)**:
   - Permits `http://` and `https://` URLs with a valid host/netloc, bounded length, and no ASCII control characters.
   - Blocks `file://` unless `CUL_MCP_ALLOW_FILE_URLS=1` is set in the MCP server environment (`PermissionDenied` otherwise); always blocks unsupported schemes such as `javascript:` or `data:`.
   - On current `HEAD` source code, blocks loopback, private/link-local/reserved/non-global IPs, local domains, and cloud metadata hosts by default unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` is set (note: older un-restarted server processes may predate this private-host block; observe actual tool responses at runtime).
2. **Blocked OS Keys (`press_key`)**:
   - Rejects `win`, `lwin`, `rwin`, `meta`, `super`, `command`, and `cmd` (case-insensitive, standalone or modifier) with `ValueError`.
3. **Session Isolation & Resource Caps**:
   - Server enforces an upper active-session cap (`SessionLimitReached` when exceeded) and an inline blind-image cap per `discover` response (`MAX_SESSIONS` and `MAX_INLINE_BLIND_IMAGES` in `session_manager.py`).
   - Each session binds a single FIFO worker thread (`cul-mcp-<session_id>`) plus an isolated temporary `task_state.json` (with `fsync` disabled for ephemeral session speed) and temporary `crops/` folder cleaned up on `close_session` or server shutdown.
4. **Privacy & Secret Redaction**:
   - `inspect()` returns `"value": "[REDACTED]"` on password-flagged `textbox`/`searchbox` elements.
   - `signature()` redacts password-like focused fields and hashes active values.
   - `TaskState.record_action()` strips plaintext `value` across **all** recorded actions and stores length + SHA-256 prefix + `"value_redacted": true`.

---
name: computer-use-lite
description: Local Chromium CDP browser and Windows UIA desktop perception, interaction, and MCP automation via compact element maps. Use whenever automating, inspecting, or debugging web pages or Windows desktop windows with computer-use-lite MCP tools (open_browser, list_desktop_windows, open_desktop, list_sessions, close_session, discover, inspect, act, hover, navigate, scroll, press_key, click_at) or the computer_use_lite Python API (Api, BrowserSession, DesktopSession, SessionManager, Resolver, StaleElementError), recovering from StaleElementError, ForegroundMismatch, or PermissionDenied, using blind-region crops, or running computer-use-lite tests and benchmarks.
license: Apache-2.0
compatibility: Python 3.10+, Playwright Chromium, websockets>=14.0, mcp>=1.25.0; Windows 10/11 required for Desktop UIA tools and Win32 snapshot imports.
---

# Computer Use Lite

Local-first browser (Chromium CDP `DOMSnapshot` + `AXTree`) and Windows desktop (scoped UIA MTA) perception and execution via compact `REV:N` element maps and selective inline crops for unmapped visual gaps.

Load details on demand:
- **13 MCP tool schemas, env gates, error payloads, and redaction semantics**: read `references/mcp_tools.md`
- **Python API (`Api`, `SessionManager`, `BrowserSession`, `DesktopSession`), architecture boundaries, and test/benchmark commands**: read `references/python_api_and_safety.md`

---

## Mode Selection & Runtime Probing

| Context | Entry Point | When to Use |
| :--- | :--- | :--- |
| Drive a live browser or Windows app from an MCP client | `computer-use-lite` MCP server (`13` tools) | Isolated per-session worker threads, automatic cleanup on close/EOF, inline PNG crops on demand. |
| Embed perception/execution in Python scripts or test suites | `computer_use_lite` (`Api`, `SessionManager`, `BrowserSession`, `DesktopSession`) | Programmatic discovery, state diffing, or benchmarks (legacy `engine` re-exports compatible). |

Never assume unexposed caps, fixed server builds, or non-text `inspect` support before observing runtime output:
1. **Verify active tool schemas first**: rely strictly on exposed parameter defaults (`width`, `height`, `limit`, `max_elements`, `wait_ms`, `dy`, `dx`, `clicks`) and adapt when `discover` truncates or tools raise `SessionLimitReached` / `ValueError`.
2. **Treat `PermissionDenied` env hints as authoritative server gates**: if URL navigation refuses a scheme or host and names an environment variable (`CUL_MCP_ALLOW_FILE_URLS` or `CUL_MCP_ALLOW_PRIVATE_URLS`), report that requirement instead of retrying workarounds.
3. **Probe `inspect` once before relying on non-text roles**: `inspect(session_id, element_id)` populates live `"value"` only on `textbox` and `searchbox`; switch immediately to independent verification when `"value"` is omitted.

---

## Core Execution Workflow

### 1. Open or Attach a Target
- **Browser (`open_browser`)**: pass `headless=False` whenever a user is watching or visible window checks matter; otherwise use schema defaults (`headless=True`, `width=1280`, `height=720`, `auto_discover=True`). Note `open_browser` waits for initial load rather than late client-side SPA hydration — if initial elements shift immediately or return sparse/empty counts, run one follow-up `discover(session_id)` once layout settles.
- **Windows desktop (`list_desktop_windows` -> `open_desktop`)**:
  - Enumerate first via `list_desktop_windows(title_contains=..., class_name=..., limit=40)`.
  - Skip minimized/cloaked placeholder coordinates far outside screen bounds, while noting that multi-monitor setups legitimately span beyond primary display width/height.
  - Because OS locales mix localized and English strings and multi-tab apps share processes, match targets by `process_name`, `class`, and visible `title` together, then attach explicitly via `open_desktop(hwnd=..., auto_discover=True)`.
  - Never drive web DOM through `open_desktop`: attaching a browser window via UIA collapses page content into an unmapped container with `BLIND_REGIONS:0`. Use `open_browser`.

### 2. Read the Compact `REV:N` Map
Illustrative format syntax (placeholders only — parse live output tokens, never copy example values):

```text
SESSION:<id> | KIND:<browser|desktop> | ... | LATENCY_MS:<ms> | TOKENS_EST:<n>
REV:<n> | WIN:<surface> | ELEMENTS:<count> | BLIND_REGIONS:<count>
<id>|<role>|<name>|<x>,<y>,<w>,<h>|<actions>
... +<m> more elements (use filter_query= or inspect_element)
blind<k>|<kind>||<x>,<y>,<w>,<h>|crop[ -> <path>]
```

- **Handling truncation (`... +<m> more elements`)**: filter first by schema `role` (`textbox`, `searchbox`, `combobox`, `button`, `link`, `checkbox`, `radio`, `switch`, `tab`, `menuitem`, `listitem`, `treeitem`) or by exact strings copied verbatim from visible UI/titles (not assumed English labels). If raising `max_elements` (`60` default) still omits visible controls on dense UIs, stop looping filters and report discovery omission.
- **Discovery scope & structural quirks**: `discover` omits read-only static text and modal error text; desktop file lists/dialogs often emit a `listitem` plus multiple per-column `textbox` cells per row; `<label>` wrappers beside `button` and `clickable` inputs can stay unpruned alongside their inner control.

### 3. Navigate, Act & Handle Control Hazards
- **Navigation settle (`navigate`)**: keep schema default `navigate(session_id, url=..., action="goto"|"back", auto_discover=False)` because `navigate` waits only for DOM content load; run `discover(session_id)` after dynamic scripts settle.
- **Revision invalidation**: every mutating call (`act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`) advances `REV:N` inside that session and invalidates all sibling `eN` IDs (`>2 px` move, occlusion, or stale revision raises `StaleElementError`). Re-run `discover(session_id)` before acting on another control (or consume new IDs from `hover`'s `added` list). Separate `session_id` instances remain isolated.
- **Native `<select>` (`combobox`) popups**: clicking a native `combobox` opens a platform dropdown that adds zero option controls to `discover()` and omits `"value"` in `inspect()`. Focus or open the control and select options via `press_key` navigation (`Down`/`Enter`) or `act(..., "type")` (plus commit key if dropdown remains open), then verify visually or on submit.
- **Unassociated labels & ambiguous rows**: when checkboxes or list controls sit beside unassociated `<label>` siblings (`name=""` in both `discover` and `inspect`), match targets using row vertical geometry (`box`) plus visual inspection.
- **Read-only, formatted & edge-straddling controls**: call `inspect` immediately after `act(..., "type")` on `textbox`/`searchbox` to catch read-only fields where focus shift returns `verified: true` without mutating value; verify `clickable` date/range/masked widgets visually right after typing because keystrokes can corrupt formatting despite `ok: true`; scroll clear or close overlays before clicking boxes clipped at `x < 0` or `y < 0` under sticky bars or behind open drawers (`occluded: false` is unverified across UIA Z-order or boundary straddlers).
- **Hover menus (`hover`)**: call `hover(session_id, element_id, wait_ms=350)` and act on returned `added` `[{"id", "role", "name", "box"}]` entries directly.

### 4. Blind-Region Visual Fallback (`click_at`) & Cleanup
- Inline PNG crops attach on `opaque_canvas`, `small_opaque_canvas`, or sparse `low_uia` surfaces (layered canvases can emit duplicate `blind<k>` crops with identical bounds). Choose `(x, y)` inside the returned crop and strictly inside session bounds before calling `click_at(session_id, x, y, button="left", clicks=1)`. Pass `include_blind_images=False` or `export_crops=False` when driving known non-canvas DOM/UIA controls.
- Always call `close_session(session_id)` on every session and confirm with `list_sessions()`.

---

## Independent Verification Discipline (Mandatory)

Treat `act` `"ok": true` and `"verified"` strictly as telemetry hints. `verified: true` false positives happen on accidental overlay focus, read-only input focus shifts, corrupted date inputs, and native file-save dialogs; `verified: false` false negatives happen when adjacent checkboxes/radios share default active value fingerprints (`type` omitted / `"on"`), on UIA buttons, and on shadow toggles. Synchronous `state_delta` can also snapshot transient empty navigation frames or mid-debounce typeahead text.

| Effect / Target Type | Independent Verification Channel |
| :--- | :--- |
| File save, export, or download | Read path and bytes from disk outside MCP (native Win32 file-save dialogs can reflect typed paths in `inspect()` while still writing the prior name or failing silently). |
| Text or search input (`textbox`, `searchbox`) | Call `inspect(session_id, element_id)` after typing (`"[REDACTED]"` confirms password-flagged redaction). |
| Navigation or form submission | Re-run `discover(session_id)` after settle (do not rely on `list_sessions()` `target` until `discover()` refreshes it), or inspect rendered output. |
| Combobox, checkbox/radio, slider, canvas | Inspect updated rendered UI/crop or OS capture. On RTL locales, check for horizontal mirroring on WinUI/Win32 `PrintWindow` crops (some UWP frames remain un-mirrored; translucent Mica backdrops render dark) and confirm against un-mirrored capture if ambiguous. |
| Desktop modal or window switch | Call `list_desktop_windows()` to verify the active dialog/window HWND or dismissal. |

---

## Structured Error Handling & Hard Stops

Tool failures set `isError=True` with JSON `{"ok":false,"error_type":...,"error":...,"recoverable":...}` plus optional `"next_step"` (omitted on `ValueError`, `TimeoutError`, `PermissionDenied`, and unhandled `Error`):

| `error_type` | Condition -> Action |
| :--- | :--- |
| `StaleElementError` / `ElementNotFound` | Element moved `>2 px`, occluded, disappeared, or revision advanced -> call `discover(session_id)` before retrying. |
| `ForegroundMismatch` | OS foreground shifted (flyout, menu, dialog) -> call `list_desktop_windows()`, attach dialog `hwnd` with `open_desktop(hwnd=...)` or dismiss it, then re-discover. |
| `COMError` / `WindowNotFound` | Window closed or UIA provider invalidated -> re-check `list_desktop_windows()`. |
| `SessionNotFound` / `SessionLimitReached` | Unknown/closed session or capacity limit reached -> call `list_sessions()`, close idle sessions or re-open. |
| `PermissionDenied` / `ValueError` | Blocked URL/network env gate, blocked OS modifier key, or invalid args/coordinates -> fix args cleanly or report env gate; never probe bypasses. |
| `TimeoutError` / `Error` | Load error (`recoverable: false`) or timeout -> stop retry loops once clear and report exact `error_type` and `error`. |

### When This Fails, Report It Like This
Stop retrying and report the exact blocker whenever a task hits a structural boundary:
- **New tab/popup spawned by click**: `list_desktop_windows()` reveals a new tab title while `discover()`/`list_sessions()` remain pinned on the opener -> report **`BLOCKED / Unsupported`** (no tab-listing or tab-switching tool exists).
- **Drag-and-drop or continuous pointer gesture**: report **`Unsupported`** (schema offers click, type, hover, scroll, key press, and bounded `click_at` only).
- **Site-isolated embed, closed Shadow DOM, or collapsed desktop Chromium target missing controls**: although local multi-frame snapshots work in fixtures, site-isolated third-party cross-origin embeds can still emit zero internal controls and `BLIND_REGIONS:0` live (as do closed Shadow DOM and UIA-attached browsers) -> report the **discovery omission** explicitly instead of guessing coordinates.
- **Native Win32 Save As filename UIA desync**: if a Save dialog accepts `act(..., "type")` (and even reflects it in `inspect()`) yet disk verification shows the target file was not created -> report **`PARTIAL / FAIL (Native Dialog UIA Desync)`** with disk evidence.
- **Isolated shell (`exebox`) desktop invisibility**: processes spawned inside non-interactive shells do not appear in `list_desktop_windows()` -> ask the user to launch the window on the interactive desktop and report **`BLOCKED`**.

---

## Non-Negotiable Safety & Honest Language

- Preserve physical-cursor `KillSwitch` (`HUMAN TAKEOVER` aborts) and active-foreground safety checks; never invoke desktop-root UIA enumeration or pass blocked OS keys (`Win`, `LWin`, `RWin`, `Meta`, `Super`, `Command`, `Cmd`).
- `inspect()` redacts password inputs as `"[REDACTED]"` and `TaskState.record_action()` strips plaintext `value` across all logged actions; server stdio reserves `sys.stdout` strictly for MCP JSON-RPC.
- Qualify behaviors observed once as observed once and fixture/mock checks as unverified live on interactive targets; avoid overstated completion or reliability claims.

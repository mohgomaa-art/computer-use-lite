---
name: computer-use-lite
description: Local Chromium CDP browser and Windows UIA desktop perception, interaction, and MCP automation via compact element maps. Use whenever automating, inspecting, or debugging web pages or Windows desktop windows with computer-use-lite MCP tools (open_browser, list_desktop_windows, open_desktop, list_sessions, close_session, discover, inspect, act, hover, navigate, scroll, press_key, click_at) or the computer_use_lite Python API (Api, BrowserSession, DesktopSession, SessionManager, Resolver, StaleElementError), recovering from StaleElementError or ForegroundMismatch, using blind-region crops, or running computer-use-lite tests and benchmarks.
license: Apache-2.0
compatibility: Python 3.10+, Playwright Chromium, websockets>=14.0, mcp>=1.25.0; Windows 10/11 required for Desktop UIA tools and Win32 snapshot imports.
---

# Computer Use Lite

Local-first browser (Chromium CDP `DOMSnapshot` + `AXTree`) and Windows desktop (scoped UIA MTA) perception and execution using compact `REV:N` element maps and selective inline crops for unmapped visual gaps.

Load details on demand:
- **13 MCP tool signatures, env gates, and error payloads**: read `references/mcp_tools.md`
- **Python API (`Api`, `SessionManager`, `BrowserSession`, `DesktopSession`), internal guarantees, and test/benchmark commands**: read `references/python_api_and_safety.md`

---

## Mode Selection

| Context | Entry Point | When to Use |
| :--- | :--- | :--- |
| Drive a live browser or Windows app from an MCP client | `computer-use-lite` MCP server (`13` tools) | Per-session isolated workers, automatic cleanup on close/EOF, blind PNG crops on demand. |
| Embed perception/execution in Python scripts or test suites | `computer_use_lite` (`Api`, `SessionManager`, `BrowserSession`, `DesktopSession`) | Direct programmatic discovery, action diffing, or running benchmarks (with legacy `engine` re-exports). |

---

## Runtime Capability Detection (Never Assume Server Version)

Tool behavior and security checks depend on the active server process and environment flags:
1. **Check active tool schemas before acting**: verify tool parameter defaults (`headless`, `auto_discover`, `max_elements`, `wait_ms`, `clicks`) and schema descriptions rather than assuming unexposed limits.
2. **Treat `PermissionDenied` messages as authoritative policy state**: if `open_browser` or `navigate` refuses a local file or private/loopback URL and names an environment variable (`CUL_MCP_ALLOW_FILE_URLS` or `CUL_MCP_ALLOW_PRIVATE_URLS`), stop and report that exact configuration requirement instead of probing workarounds.
3. **Probe `inspect` capability on non-text roles before relying on it**: call `inspect(session_id, element_id)` once when checking a control; if the returned JSON omits `"value"` or checked state (expected on non-textbox/non-searchbox roles), switch immediately to an independent verification channel for that control.
4. **Never hardcode undocumented limits**: adapt cleanly when `discover` reports truncated elements or when the server returns `SessionLimitReached` or `ValueError` for out-of-range arguments.

---

## Core Execution Loop

### 1. Open or Attach a Target
- **Visibility rule (`open_browser`)**: if a user is watching or visible window checks are needed, pass `headless=False`; otherwise use schema default (`headless=True`, `width=1280`, `height=720`, `auto_discover=True`). Only permitted URL schemes (`http://` and `https://` by default) open unless server env gates override them.
- **Windows desktop target (`list_desktop_windows` -> `open_desktop`)**:
  - Always enumerate first via `list_desktop_windows(title_contains=..., class_name=..., limit=40)`.
  - Ignore entries whose `box` shows minimized/offscreen placeholder coordinates far outside the desktop bounds.
  - Because multi-tab or multi-window apps share process names and OS locales localize window titles, prefer matching by `process_name`, window `class`, and visible `title` together, then attach explicitly via `open_desktop(hwnd=..., auto_discover=True)`.
  - Never drive web page DOM content through `open_desktop`: attaching Chromium via UIA can collapse the web area into a single `textbox` with `BLIND_REGIONS:0`. Use `open_browser` for web targets.

### 2. Read the Compact `REV:N` Map
Illustrative format syntax (placeholders only — parse live output values, never copy example fields):

```text
SESSION:<id> | KIND:<browser|desktop> | ... | LATENCY_MS:<ms> | TOKENS_EST:<n>
REV:<n> | WIN:<surface> | ELEMENTS:<count> | BLIND_REGIONS:<count>
<id>|<role>|<name>|<x>,<y>,<w>,<h>|<actions>
... +<m> more elements (use filter_query= or inspect_element)
blind<k>|<kind>||<x>,<y>,<w>,<h>|crop[ -> <path>]
```

- **When output is truncated (`... +<m> more elements`)**: first filter by schema `role` (`textbox`, `searchbox`, `combobox`, `button`, `link`, `checkbox`, `radio`, `switch`, `tab`, `menuitem`, `listitem`, `treeitem`) or by exact strings copied verbatim from visible UI/window titles rather than assuming English keywords; if needed, raise `max_elements` or use `filter_query`. If visible controls remain missing even when raising `max_elements` on dense pages, stop retrying filters and report the discovery omission.
- **Interactive-only scope**: `discover` omits read-only static text (such as scrolled paragraphs, computed status readouts, or modal body messages). Use `inspect` on editable text controls or inspect visual/DOM evidence when read-only text matters.
- **Inspecting values (`inspect`)**: `inspect(session_id, element_id)` populates `"value"` on `textbox` and `searchbox` roles (`"[REDACTED]"` for password-flagged fields) and omits live values/checked state on `combobox`, `checkbox`, and range controls.

### 3. Act, Navigate, and Chain Revisions Safely
- **Revision invalidation**: every mutating call (`act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`) advances session `REV:N` and invalidates all other `eN` IDs from the previous `discover` call within that same session. Re-run `discover(session_id)` before acting on another sibling control (or use newly revealed `id` values from `hover`'s `added` list). Multiple independent `session_id` instances keep isolated revisions and do not invalidate one another.
- **Navigation settle (`navigate`)**: keep the schema default `navigate(session_id, url=..., action="goto"|"back", auto_discover=False)`, because `navigate` waits only for DOM content load and `auto_discover=True` can return zero or incomplete elements before dynamic scripts hydrate. Call `discover(session_id)` after navigation; if an active dynamic page returns zero elements immediately after load, run one follow-up `discover(session_id)` after layout settles before treating the page as empty or unmapped.
- **Control-specific hazards before acting**:
  - If an input widget (date picker, range control, custom div) reports `role=clickable` without `textbox`/`searchbox` semantics, verify the rendered value immediately after `act(..., action="type")` because formatted widgets can misparse raw keystrokes even when `ok: true` is returned.
  - If an element sits behind an open overlay/drawer or its bounding box partially straddles a negative viewport boundary (`x < 0` or `y < 0`) under a sticky bar, scroll it clear or dismiss the overlay before clicking; do not assume `occluded=false` guarantees an unobstructed target on boundary-straddling web links or desktop UIA windows.
- **Hover menus (`hover`)**: call `hover(session_id, element_id, wait_ms=350)` to reveal hover-only items and inspect its `added` list (`[{"id", "role", "name", "box"}]`). Use `added` directly rather than trusting unchanged summary counters.

### 4. Blind-Region Visual Fallback (`click_at`)
- Inline PNG crops attach automatically when `discover` finds unmapped canvas regions (`opaque_canvas`, `small_opaque_canvas`) or sparse desktop surfaces (`low_uia`). Layered overlapping canvases can occasionally emit duplicate `blind<k>` rows/crops with identical bounds.
- Inspect the crop image, choose `(x, y)` inside that `blind<k>` box, and call `click_at(session_id, x, y, button="left", clicks=1)`. Keep coordinates strictly inside session viewport/window bounds (`ValueError` outside).
- When automating standard DOM/UIA controls near a known persistent canvas where crops are unnecessary, pass `include_blind_images=False` (or `export_crops=False`) to `discover`.

### 5. Close Sessions Cleanly
- Call `close_session(session_id)` on every opened session once finished, then call `list_sessions()` to confirm no open sessions remain.

---

## Independent Verification Discipline (Mandatory)

Never declare an action or task successful solely because `act` returned `"ok": true` or `"verified": true` (false positives happen on accidental focus shifts and unresponsive native dialogs; false negatives happen on valid submissions, UIA buttons, and shadow checkboxes). Verify the end state through an independent channel matched to the effect:

| Effect / Target Type | Independent Verification Channel |
| :--- | :--- |
| File save, export, or download | Read path/bytes from disk outside MCP (never trust a Save dialog's `verified: true`). |
| Text or search input (`textbox`, `searchbox`) | Call `inspect(session_id, element_id)` after typing (password fields verify redaction via `"[REDACTED]"`). |
| Browser form submit or link navigation | Re-run `discover(session_id)` to verify new URL/controls (do not inspect `list_sessions()` `target` immediately after a click until `discover()` syncs it), or check rendered page output. |
| Combobox, checkbox, slider, custom widget, canvas stroke | Inspect updated rendered UI/crop or OS capture. When inspecting desktop `PrintWindow` crops on right-to-left (RTL) OS locales, account for potential horizontal mirroring and confirm with un-mirrored desktop screen inspection if ambiguous. |
| Native desktop modal or cross-window switch | Re-run `list_desktop_windows()` to verify the new window/dialog HWND or closure. |

---

## Structured Error Handling

Tool failures set `isError=True` with JSON `{"ok":false,"error_type":...,"error":...,"recoverable":...,"next_step":...}` (`next_step` is included on actionable recovery types and omitted on `ValueError`, `TimeoutError`, `PermissionDenied`, and unhandled `Error`):

| `error_type` | Condition -> Action |
| :--- | :--- |
| `StaleElementError` / `ElementNotFound` | Element moved `>2 px`, disappeared, occluded, or revision advanced -> call `discover(session_id)` to bind fresh IDs and `REV:N` before retrying. |
| `ForegroundMismatch` | Windows foreground shifted (flyout, menu, file dialog) -> call `list_desktop_windows()`, attach the active dialog HWND with `open_desktop(hwnd=...)` or dismiss it, then re-discover. |
| `COMError` / `WindowNotFound` | Window closed or UIA provider reset -> call `list_desktop_windows()` to confirm active windows before re-attaching. |
| `SessionNotFound` / `SessionLimitReached` | Unknown/closed session or active session limit reached -> call `list_sessions()`; close idle sessions or open a new session. |
| `PermissionDenied` / `ValueError` | Blocked URL/network policy, blocked OS modifier key, or out-of-bounds `click_at`/argument -> fix arguments cleanly or report the exact env gate; do not probe around security refusals. |
| `TimeoutError` / `Error` | Navigation failure (`recoverable: false` on network/load error) or operation timeout -> stop retry loops once cause is clear and report exact `error_type` and `error`. |

---

## When This Fails, Report It Like This

Stop retrying and report the exact blocker plainly whenever a task hits a structural tool limit:
- **New browser tab or popup spawned by click**: if a click opens another foreground tab (`list_desktop_windows()` shows the new tab title while `discover()`/`list_sessions()` stay pinned on the opener tab), report **`BLOCKED / Unsupported`**: MCP currently tracks one page per `open_browser` session and exposes no tab-listing or tab-switching tool.
- **Pointer drag-and-drop or continuous gesture required**: report **`Unsupported`**: the `13`-tool MCP schema provides click, type, hover, scroll, key press, and bounded `click_at`, with no mouse drag (`down`/`move`/`up`) primitive.
- **Embedded frame, closed Shadow DOM, or collapsed desktop Chromium target missing controls**: if visible UI inside an embedded frame or browser-attached desktop window is omitted from `discover` and `BLIND_REGIONS:0` is returned, report the **discovery omission** explicitly instead of guessing coordinates. Note that cross-origin frame extraction in current code is unverified live on restarted MCP against real sites and closed Shadow DOM is unpierced.
- **Native Win32 file-save dialog pre-filled filename desync**: if a native Save As dialog accepts `act(..., "type")` visually yet fails disk verification with a silent invalid-filename modal whose message is omitted by `discover`, report **`PARTIAL / FAIL (Native Dialog UIA Desync)`** with the disk absence proof instead of looping endlessly.
- **Isolated desktop shell (`exebox`) invisibility**: GUI processes launched from an isolated shell desktop are invisible on the interactive `Default` desktop and fail screen grab without desktop attachment; if a required desktop target is not in `list_desktop_windows()`, ask the user to open or focus it on the interactive desktop and report **`BLOCKED`**.

---

## Non-Negotiable Safety & Reporting Rules

- **Human cursor safety**: never disable `KillSwitch` or background-click another window while physical cursor movement is occurring (`HUMAN TAKEOVER` aborts protect human control).
- **Zero unprompted global probes & blocked OS keys**: never run desktop-root UIA enumeration or pass blocked OS modifier keys (`Win`, `LWin`, `RWin`, `Meta`, `Super`, `Command`, `Cmd`).
- **Privacy & redaction**: `inspect()` redacts password fields as `"[REDACTED]"`, `signature()` hashes/redacts values, and `TaskState.record_action()` strips plaintext `value` across all logged actions (not just passwords).
- **Stdio isolation**: server code reserves `sys.stdout` for MCP JSON-RPC (`run_stdio_server` redirects `sys.stdout` to `sys.stderr`); never write logs to `stdout`.
- **Honest status language**: avoid overstated completion or perfection claims; qualify behaviors seen once as observed once and fixture-only checks as unverified live on interactive targets.

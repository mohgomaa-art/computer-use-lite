---
name: computer-use-lite
description: Drive Chromium CDP browsers and Windows UIA desktop apps via computer-use-lite's 16 MCP tools (open_browser, list_desktop_windows, open_desktop, close_session, list_sessions, discover, inspect, act, hover, navigate, drag_at, type_text, scroll, press_key, click_at, cul_reload) or Python API (Api, BrowserSession, DesktopSession, SessionManager). Use for REV:N element maps, multi-tab or drag flows, mid-session MCP supervisor reloads, blind-region crops, pytest/benchmark workflows, and recovering from StaleElementError, ForegroundMismatch, PermissionDenied, or user_interrupted.
license: Apache-2.0
compatibility: Python 3.10+, Playwright Chromium. Desktop UIA needs Windows 10/11; Browser MCP runs cross-platform (verified Linux/WSL2).
---

# Computer Use Lite

Read a compact `REV:N` element map, act on short `eN` IDs, verify outcomes independently.

Load details on demand:
- **16 MCP tools (`15` core + `cul_reload`), schemas, env gates, error JSON, LKG rollback**: `references/mcp_tools.md`
- **Python API (`Api`, `BrowserSession`, `DesktopSession`, `SessionManager`), boundaries, pytest/benchmarks**: `references/python_api_and_safety.md`

## Loop

1. **Open**
   - Browser: `open_browser(url, width=1280, height=720)`. `headless=None` reads `CUL_MCP_HEADFUL=1`; pass `headless=False` if watched. Run follow-up `discover` if SPA hydration shifts.
   - Desktop: `list_desktop_windows(process_name=...)` (skip minimized/offscreen placeholders; handles dynamic titles like `Blender Render -> Image Editor`), then `open_desktop(hwnd=...)` (check `FG_MATCH` / `foreground_matched` before clicking).
   - Match process, class, and title together. Never attach a browser window via UIA; use `open_browser`.

2. **Read the map.** Lines use `eN|role|name|x,y,w,h|actions` under `REV:N`.
   - On `... +N more`, filter via `filter_query` (role or visible text) or raise `max_elements` (`1..300`).
   - Pass `include_static_text=True` for bounded (`<=1200`-char) `PAGE_TEXT`; pass `skip_unchanged_images=True` on repeat polls to skip duplicate blind PNGs.
   - If controls remain missing on dense UIs, stop and report the omission; never guess unseen IDs.

3. **Act, navigate & reload.** `act(session_id, element_id, action, revision=...)`.
   - **Mutations** (`act`, `navigate` except `list_tabs`, `scroll`, `press_key`, `click_at`, `drag_at`, `type_text`) bump `REV` and invalidate all prior `eN` IDs (`StaleElementError` until `discover` runs).
   - **`hover(session_id, element_id, wait_ms=350)`** updates surviving elements in place and **preserves surviving sibling `eN` IDs at the new revision** — act on its `added` list or surviving IDs.
   - `navigate(action="goto"|"back")` waits only for DOM load; call `discover()` after SPA scripts settle.
   - `DesktopSession.perform()` has **no `clear` parameter** (`clear=False` append is `BrowserSession`-only; Win32 uses `ValuePattern.SetValue` / `#32770` `_commit_dialog_text`).
   - `type_text(session_id, text, input_mode="unicode"|"vk_scan")`: focused typing (`vk_scan` sends VK scan codes for custom desktop widgets).
   - `press_key(session_id, key=..., keys=[...], delay_ms=15)`: single shortcut or atomic batch (`NumpadSubtract`..`NumpadDivide` included); validates every key upfront.
   - `scroll(session_id, dy, dx, x, y)`: targeted scroll at bounded window/viewport coords (both supplied, or omitted for center). Unknown kwargs fail strictly (`ValueError`).
   - `cul_reload`: supervisor-only (`computer_use_lite.supervisor`, not `mcp_server`); resets ALL open `SESSION:*`/browser handles; edits to `supervisor.py` require client restart (see `references/mcp_tools.md` for LKG rollback).

4. **Verify independently.** `ok` and `verified` are hints, not proof:

   | Effect | Independent Check |
   |---|---|
   | Typed text / `<select>` | `inspect()` (`readonly`, `checked`, up to `40` `options`; secrets show `"[REDACTED]"`). Choose native `<select>` via `press_key` (`Down`/`Enter`) + inspect |
   | Save, export, download | Read path & bytes from disk outside MCP |
   | Navigation / submit | Re-run `discover()` or `navigate(..., action="list_tabs")` after settle |
   | Canvas / visual state | `PrintWindow`/crop check (`WS_EX_LAYOUTRTL` bitmaps mirror horizontally; dark WinUI Mica caveat) |
   | Dialog / window switch | `list_desktop_windows(process_name=...)` |

5. **Blind regions** (`opaque_canvas`, `low_uia`): `click_at(x, y)` strictly inside the crop and session bounds. Set `include_blind_images=False` for pure DOM/UIA pages.

6. **Clean up.** Call `close_session` on all sessions (last close resets `CursorCoordinator`), then verify empty via `list_sessions`.

## Errors

On `isError`, read `error_type`, `recoverable`, and `next_step`:
- `StaleElementError`, `ElementNotFound`: moved `>2 px`, occluded (compositor or Win32 Z-order/cloaking in `verify_fresh`), or stale revision -> run `discover`, then retry.
- `ForegroundMismatch`: flyout/modal took focus -> `list_desktop_windows(process_name=...)`, attach dialog `hwnd` or dismiss, then `discover`.
- `HumanTakeover`: physical cursor drifted -> yield to user handoff, then close/re-open or re-sync after user confirmation.
- `user_interrupted`: physical `Esc` aborted takeover -> **hard stop** until user instructs otherwise.
- `PermissionDenied`: report exact env gate (`CUL_MCP_ALLOW_FILE_URLS`, `CUL_MCP_ALLOW_PRIVATE_URLS`, `CUL_DESKTOP_ALLOW_SENSITIVE`, `CUL_DESKTOP_ALLOW_PROCESSES`); never bypass.
- `SessionNotFound`, `SessionLimitReached` (`MAX_SESSIONS=16`): `list_sessions`; close idle sessions.
- `TimeoutError` / non-recoverable `Error`: stop retrying and report exact `error_type` and `error`.

## Report, don't improvise

- **New tab / popup (`opened_tab`, `tab_count`)**: call `navigate(session_id, action="list_tabs"|"switch_tab"|"close_tab", tab_index=...)`.
- **Drag and drop**: use `act(..., action="drag", target_element_id=...|to_x/to_y)` or `drag_at(x1, y1, x2, y2, button=...)`.
- Zero controls from a cross-origin embed, closed Shadow DOM, or a browser attached via UIA: stop and report the **discovery omission** (never guess coordinates).
- Win32 `#32770` Save As where `inspect` shows the name but the file is missing: **PARTIAL (UIA desync)**, with disk evidence.
- App launched in a non-interactive shell (invisible on interactive desktop): ask the user to start it on their desktop.

## Safety

- Preserve physical-cursor `KillSwitch` (`HUMAN TAKEOVER`), `Esc` `TakeoverGuard`, and foreground checks.
- Respect `validate_desktop_target` sensitive-app refusals (terminals, password managers, credential UIs, admin tools); never enumerate the desktop root.
- Blocked keys (`ValueError` unless `CUL_ALLOW_SYSTEM_SHORTCUTS=1`): `Win`, `LWin`, `RWin`, `Meta`, `Super`, `Command`, `Cmd`, `Alt+Tab`, `Alt+F4`, `Alt+Escape`, `Ctrl+Escape`, `Ctrl+Shift+Escape`, `Ctrl+Alt+Delete`.
- Say "observed once" for single runs and "unverified live" for fixture-only results.

# Repair Master Plan (`v0.2.0a0` Engineering Program)

Execution Branches:
1. `cursor-audit-fix` off `de27b49` (`CUL-CUR-001..010` + `CUL-CUR-007` + Section 3 `GetCursorInfo` + Section 4 Animation + Section 5 `CUL_TAKEOVER_GLOW=1`)
2. `fixes/security-reliability-research-release` stacked on `cursor-audit-fix` (`P0` -> `P1` -> `P2` -> `P3`)

Every entry specifies the 15 required engineering contract fields.

---

## Track C / Cursor Subsystem (`branch: cursor-audit-fix`)

### `CUL-CUR-007` (Cursor Fix G) — Exclude Agent Overlay from `canvas_rects`
1. **Finding ID:** `CUL-CUR-007`
2. **Original severity:** Critical / High (`P0` — triggers false `1280x720` `opaque_canvas` blind screenshot!)
3. **Original defect:** Enabling `show_cursor=True` caused `discover()` to emit a `1280x720` `opaque_canvas` blind region & full-screen PNG crop.
4. **Actual root cause:** `BrowserSession.canvas_rects()` (`src/computer_use_lite/browser_cdp.py:1008-1021`) recursively walks `el.shadowRoot` including the `[data-cul-overlay]` host holding the overlay wake `<canvas>`.
5. **Affected files and functions:** `src/computer_use_lite/browser_cdp.py` (`BrowserSession.canvas_rects`), `src/computer_use_lite/cursor_overlay.py` (`OVERLAY_HOST_ATTR` / `data-cul-overlay`).
6. **Reproduction test:** Headless Chrome page with single `<button>` + `show_cursor=True`; assert `discover()` reports `blind_regions == 0` (baseline FAILS with `opaque_canvas 1280x720`).
7. **Expected corrected behavior:** Skip elements matching `[data-cul-overlay]` (do not descend into their `shadowRoot` or record their `<canvas>`).
8. **Regression tests:** `tests/test_cursor_overlay_regressions.py::test_canvas_rects_excludes_cul_overlay`
9. **Compatibility implications:** None (`show_cursor=False` unaffected; `show_cursor=True` stops breaking zero-image guarantee).
10. **Acceptance criteria:** `blind_regions == 0` with `show_cursor=True` on pure DOM page; real `<canvas>` in page DOM still detected.
11. **Required platform:** Cross-platform Chromium.
12. **Verification evidence:** Before FAIL + After PASS pytest output + empirical check.
13. **Dependencies:** None (land cleanly with Cursor Fixes A–G).
14. **Risk of introducing regressions:** Very low.
15. **Priority & Complexity:** P0 / Trivial (S).

### `CUL-CUR-001` (Cursor Fix A) — Deferred `progress` Shape & No Redundant Glyph Rebuilds
1. **Finding ID:** `CUL-CUR-001`
2. **Original severity:** High (`P0/Cur`)
3. **Original defect:** Every `<350 ms` action flashed `progress` then `pointer/text`, causing 3 full DOM glyph rebuilds over 3 rapid actions.
4. **Actual root cause:** `session_manager.py:382-393` wraps every call in `set_cursor_busy(True/False)`; `cursor_overlay.py:786-794` switched immediately to `'progress'`; `desktop_cursor_overlay.py:996-1012` set `self._state["cursor_id"] = "progress"` synchronously; `cursor-audit-fix.patch.txt` failed to remove that eager assignment on desktop.
5. **Affected files and functions:** `cursor_overlay.py` (`setBusy`, `applyShape`), `desktop_cursor_overlay.py` (`set_busy`, `_render_state`), `session_manager.py` (`_with_busy_cursor`).
6. **Reproduction test:** Execute 3 rapid `<200ms` actions (`button` clicks) in Chrome CDP and count `#cul-shape` SVG DOM rebuilds; probe `DesktopCursorOverlay.set_busy(True)` -> `<200ms` `set_busy(False)`.
7. **Expected corrected behavior:** Defer `progress` shape switch until `350 ms` elapsed (`busyTimer` in JS, `busy_since + 0.35` in desktop); skip glyph DOM replacement if target shape `=== activeId` and `shapeLayer.childNodes.length > 0`.
8. **Regression tests:** `test_no_progress_flash_under_350ms_browser_and_desktop`, `test_three_consecutive_actions_single_rebuild`.
9. **Compatibility implications:** None. Long `>350 ms` waits still display `progress`.
10. **Acceptance criteria:** Rebuilds / 3 pointer actions drops from `3` to `1` (`<=1`); `<350 ms` actions never render `'progress'`.
11. **Required platform:** Chrome + Win32 desktop overlay unit/integration.
12. **Verification evidence:** Chrome CDP rebuild counter before/after + pytest output.
13. **Dependencies:** None.
14. **Risk of introducing regressions:** Low; verify `preBusyId` restores properly after genuine `>350ms` busy intervals.
15. **Priority & Complexity:** P0/Cur / Medium (M).

### `CUL-CUR-002` (Cursor Fix B) — Error Glyph Auto-Revert (`900 ms`)
1. **Finding ID:** `CUL-CUR-002`
2. **Original severity:** Medium-High (`P0/Cur`)
3. **Original defect:** `outcome('error')` switched cursor to `not-allowed` and left it stuck until the next action.
4. **Actual root cause:** Neither `cursor_overlay.py:765-777` nor `desktop_cursor_overlay.py:992-994` scheduled a revert timer back to `lastActionId`/`pointer`.
5. **Affected files and functions:** `cursor_overlay.py` (`outcome`, `applyShape`, `moveTo`), `desktop_cursor_overlay.py` (`outcome`, `_tick`).
6. **Reproduction test:** Trigger error outcome -> sleep `1050 ms` -> assert shape is still `'not-allowed'` before fix, reverted after fix; new action cancels pending revert timer cleanly.
7. **Expected corrected behavior:** Auto-revert `not-allowed` to `lastActionId` after `900 ms`; any subsequent `moveTo`/`click`/`setBusy` cancels the revert timer.
8. **Regression tests:** `test_error_glyph_auto_reverts_and_new_action_cancels_timer`.
9. **Compatibility implications:** None.
10. **Acceptance criteria:** Both browser and desktop overlays auto-revert within `900–1100 ms` and never flicker back after a rapid follow-up move.
11. **Required platform:** Chrome + Win32 desktop.
12. **Verification evidence:** Before/After pytest output.
13. **Dependencies:** Builds on clean shape state from `CUL-CUR-001`.
14. **Risk of introducing regressions:** Low.
15. **Priority & Complexity:** P0/Cur / Small (S).

### `CUL-CUR-003` (Cursor Fix C) — Double-Click & Stable Blind Coordinate Shape
1. **Finding ID:** `CUL-CUR-003`
2. **Original severity:** High (`P0/Cur`)
3. **Original defect:** `click(x, y, id, {clicks: 2})` only triggered 1 press animation / 1 ripple / `clickCount += 1`; desktop `click()` lacked `clicks`; blind coordinate clicks could flash shapes.
4. **Actual root cause:** `cursor_overlay.py:725-755` ignored `opts.clicks`; `desktop_cursor_overlay.py:937-959` & `desktop_uia.py:1006` omitted `clicks`.
5. **Affected files and functions:** `cursor_overlay.py` (`click`), `desktop_cursor_overlay.py` (`click`), `desktop_uia.py` (`click_coordinate`, `_overlay_click`), `browser_cdp.py` (`click_coordinate`).
6. **Reproduction test:** Dispatch `clicks=2` in browser & desktop -> assert 2 press pulses, 2 ripples, `click_count == 2`; blind `click_coordinate` keeps `crosshair` shape cleanly.
7. **Expected corrected behavior:** Clamp `n = max(1, min(3, clicks))`, run `n` staggered pulses (`120 ms` gap), increment count by `n`, spawn `n` ripples; keep single stable shape during blind coordinate clicks.
8. **Regression tests:** `test_double_click_pulses_ripples_and_blind_shape_stability`.
9. **Compatibility implications:** Backward-compatible default `clicks=1`.
10. **Acceptance criteria:** `clickCount += 2`, `2` ripples, `2` pulse timestamps measured before (`1`) vs after (`2`).
11. **Required platform:** Chrome + Win32 desktop.
12. **Verification evidence:** Chrome CDP + Windows desktop test output.
13. **Dependencies:** None.
14. **Risk of introducing regressions:** Low.
15. **Priority & Complexity:** P0/Cur / Small (S).

### `CUL-CUR-004` (Cursor Fix D) — Post-Spring Hard Tilt Clamp (`<= 5 deg`)
1. **Finding ID:** `CUL-CUR-004`
2. **Original severity:** Medium (`P0/Cur`)
3. **Original defect:** Fast glide overshoots spring tilt past `12 deg` (`~14.4 deg`), warping glyph.
4. **Actual root cause:** `cursor_overlay.py:604-614` clamps target velocity `tx/ty` to `[-12, 12]` BEFORE spring integration, NOT after `tiltX += tvx * dt`.
5. **Affected files and functions:** `cursor_overlay.py` (`tick` / spring integration + top `MAX_TILT_DEG = 5`).
6. **Reproduction test:** Rapidly sweep cursor across `0..1200 px` and record max `Math.abs(tiltX/tiltY)` per `rAF` frame (baseline `>5 deg`, target `<=5.0 deg`).
7. **Expected corrected behavior:** Clamp rendered `tiltX`/`tiltY` after integration strictly to `[-MAX_TILT_DEG, +MAX_TILT_DEG]` (`5.0 deg`).
8. **Regression tests:** `test_tilt_never_exceeds_max_deg`.
9. **Compatibility implications:** Subtle visual change (cleaner, zero warp).
10. **Acceptance criteria:** Measured max rendered angle `<= 5.0 deg` across high-velocity jumps.
11. **Required platform:** Chromium.
12. **Verification evidence:** Before/After measured max angle in Chrome CDP.
13. **Dependencies:** Integrated into Section 4 single `rAF` loop as well.
14. **Risk of introducing regressions:** Negligible.
15. **Priority & Complexity:** P0/Cur / Trivial (S).

### `CUL-CUR-005` (Cursor Fix E) — Hidden-Tab `rAF` Hang & Stale Glide Cancel
1. **Finding ID:** `CUL-CUR-005`
2. **Original severity:** High (`P0/Cur`)
3. **Original defect:** Calling `moveTo` in background/hidden tab waits forever on paused `requestAnimationFrame`.
4. **Actual root cause:** `cursor_overlay.py:701-724` resolves `moveTo` only inside `window.requestAnimationFrame`, and overlapping `moveTo` calls aren't cancelled cleanly.
5. **Affected files and functions:** `cursor_overlay.py` (`moveTo`), `browser_cdp.py` (`_move_cursor`).
6. **Reproduction test:** Hide tab visibility (`document.visibilityState === 'hidden'` / background tab switch) and invoke `_move_cursor` -> baseline hangs until CDP timeout; fixed returns `< 1.0 s`.
7. **Expected corrected behavior:** Cancel prior in-flight glide (`glideSeq` / resolve prior promise cleanly), jump cleanly when `document.hidden`, and arm `setTimeout` watchdog (`glideMs + 250 ms` capped `< 800 ms`) so promise ALWAYS resolves in `< 1 s`.
8. **Regression tests:** `test_hidden_tab_move_completes_under_1s`.
9. **Compatibility implications:** None (fixes hang).
10. **Acceptance criteria:** Hidden/background tab `moveTo` resolves cleanly under `1.0 s` (`~50–700 ms` vs timeout before).
11. **Required platform:** Chromium.
12. **Verification evidence:** Measured hidden-tab latency before vs after in Chrome CDP.
13. **Dependencies:** Coordinated with Section 4 single `rAF` loop.
14. **Risk of introducing regressions:** Low.
15. **Priority & Complexity:** P0/Cur / Medium (M).

### `CUL-CUR-006` (Cursor Fix F) — Single Per-Session `Page.addScriptToEvaluateOnNewDocument` Registration
1. **Finding ID:** `CUL-CUR-006`
2. **Original severity:** Medium (`P0/Cur`)
3. **Original defect:** `~60 KB` init script re-evaluated via `Runtime.evaluate` across navigations/tabs.
4. **Actual root cause:** `browser_cdp.py:1881-1903` calls `Runtime.evaluate(expression=build_overlay_init_script())` inside `_ensure_cursor_mounted` without registering `Page.addScriptToEvaluateOnNewDocument` IDs or `lru_cache`.
5. **Affected files and functions:** `cursor_overlay.py` (`@lru_cache` on `build_overlay_init_script`), `browser_cdp.py` (`_ensure_cursor_mounted`, `_register_cursor_doc_script`, page cleanup).
6. **Reproduction test:** Spy on `build_overlay_init_script` / CDP `Runtime.evaluate` script length across 3 tab switches/navigations -> drops from repeated ~60KB evals to 1 registration per page/document + tiny `Runtime.evaluate` fallback only if pre-existing doc lacks mount.
7. **Expected corrected behavior:** Cache built init JS via `lru_cache`; register once per `Page`/target with `Page.addScriptToEvaluateOnNewDocument` storing `identifier`; check lightweight `!!window[Symbol.for('cul.agent.cursor')]` on actions and only inject full script once if target pre-dated registration.
8. **Regression tests:** `test_init_script_registered_once_across_navigations_and_tabs`.
9. **Compatibility implications:** Works under strict CSP & Trusted Types.
10. **Acceptance criteria:** Init script bytes pushed over `Runtime.evaluate` during normal multi-tab action sequence `<= 1` full upload per page creation (0 on navigation!).
11. **Required platform:** Chromium.
12. **Verification evidence:** Chrome CDP call count & byte telemetry before/after.
13. **Dependencies:** After Cursor Fix G/E context clean.
14. **Risk of introducing regressions:** Low; ensure OOPIF or `about:blank` fallback still works cleanly.
15. **Priority & Complexity:** P0/Cur / Medium (M).

### `CUL-CUR-008` (Section 3 Theory) — Empirical `GetCursorInfo` Double-Click Probe
1. **Finding ID:** `CUL-CUR-008`
2. **Original severity:** Diagnostic / Open Theory (`P1/Cur`)
3. **Original defect / Question:** Does the physical OS Windows cursor stay visible and flicker/change shapes over `DesktopCursorOverlay` during `SendInput`?
4. **Actual root cause:** To be empirically proven (`NOT ASSUMED`) using Win32 `GetCursorInfo` (`CURSORINFO.flags`, `hCursor`) sampled before, during, and after scripted `SendInput` double-click in `WinSta0\Default`.
5. **Affected files and functions:** `scripts/probe_win32_cursor_info.py` (or diagnostic helper), and ONLY if proven leaking: `desktop_cursor_overlay.py` / `desktop_uia.py` (`ShowCursor` / scoped cursor blanking + `finally`/`atexit` restore).
6. **Experiment & Acceptance:** Log exact `GetCursorInfo` structs (`cbSize`, `flags`, `hCursor`, `ptScreenPos`). If `CURSOR_SHOWING` (`0x1`) & varying `hCursor` (`arrow`/`ibeam`/`hand`) are observed during active `SendInput`, implement minimal scoped cursor hiding with guaranteed `finally` + `atexit` restoration; if not, report exact finding honestly without inventing a broken hack!
7. **Required platform:** Unlocked Windows 11 desktop (`WinSta0\Default`).

### `CUL-CUR-009` (Section 4 Animation Upgrade) — Critically Damped Spring, Morph & Budget
1. **Finding ID:** `CUL-CUR-009`
2. **Original severity:** UX / Performance (`P1/Cur`)
3. **Requirements:** Single `OVERLAY_CONFIG` constants block at top of `cursor_overlay.py` & `desktop_cursor_overlay.py`; distance-scaled duration (`120 ms` short .. `450 ms` long cap) with critically damped spring (`omega`, `zeta=1.0`, zero target overshoot); single `dt`-clamped `<=50 ms` `requestAnimationFrame` loop; `120 ms` cross-fade morph (skipped when shape unchanged); `60 ms` `0.9` click press spring + 1 ripple per click; full `prefers-reduced-motion`; transforms & opacity ONLY (zero layout reads in tick loop). Measure Chrome `rAF` p50/p95 before vs after.
4. **Regression tests:** `test_animation_spring_no_overshoot`, `test_prefers_reduced_motion_disables_tilt_and_ripple_scale`, Chrome CDP p50/p95 probe.

### `CUL-CUR-010` (Section 5 Optional) — `CUL_TAKEOVER_GLOW=1` & `Esc` Handback Guard
1. **Finding ID:** `CUL-CUR-010`
2. **Original severity:** Safety / UX (`P2/Cur`, default OFF)
3. **Requirements:** Flag `CUL_TAKEOVER_GLOW=1` (default OFF). `CUL_GREEN = "#0E9F6E"`.
   - Browser: 3–4 stacked `inset` `box-shadow` layers in `#0E9F6E`, `2.4 s` pulse `0.55..0.9`, `pointer-events: none`.
   - Desktop: Multi-monitor DPI-aware layered topmost click-through HWND (`WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE`), `200 ms` fade-in / `250 ms` fade-out.
   - Input guard + `Esc` handback: Filter `LLMHF_INJECTED` (`0x1`) / `LLKHF_INJECTED` (`0x10`) so `SendInput` never trips guard; physical `Esc` transitions state machine `active -> interrupted`, uninstalls hooks (`finally` + `atexit`), clears glow, releases held keys/buttons, restores cursor, returns explicit `user_interrupted` result; >2 s hook watchdog auto-releases control.
   - Tests: Full unit tests of state machine (`idle`, `armed`, `active`, `interrupted`) with injectable fake input source + real Windows 11 check (or explicit `NOT VERIFIED` if sandbox blocks `WH_KEYBOARD_LL`).

---

## Track A: P0 — Correctness, Security, Privacy, Trust (`fixes/security-reliability-research-release`)

### `CUL-ACC-001` — Cross-Frame Overlay / Wrong-Target Click Prevention
- **Severity / Defect:** `P0` — Click inside same-origin or OOPIF `<iframe>` overlapped by transparent parent `<div>` executes on the covering overlay while reporting `ok=True, verified=True`.
- **Root Cause:** `_NODE_PROBE_JS` (`browser_cdp.py:129-134`) only runs `doc.elementFromPoint(cx, cy)` inside the iframe's own `document`, blind to covering elements in ancestor frames or root document.
- **Files/Functions:** `browser_cdp.py` (`_NODE_PROBE_JS`, `_verify_ancestor_frame_hit`, `perform`).
- **Fix:** (a) Inside `_NODE_PROBE_JS`, walk `win.frameElement` up accessible same-origin ancestors accumulating client coordinates `(ax, ay)` and running `parentDoc.elementFromPoint(ax, ay)` asserting the hit node is the current `frameEl`; (b) For cross-origin / OOPIF (`sid` or cross-origin error), map box center to top viewport coordinates `(gx, gy)` via `_current_frame_offset` and invoke CDP `DOM.getNodeForLocation(x=int(gx), y=int(gy), includeUserAgentShadowDOM=False)` on the main page CDP session to verify the topmost rendered node belongs to the target frame/backendNodeId (NOT an obscuring root overlay!), raising `StaleElementError("element occluded by parent overlay ...")` on mismatch and marking `verification_status="cross_origin_unprovable"` / `verified=False` if browser hit-test cannot resolve ownership!
- **Acceptance & Tests:** Test (1) same-origin iframe under transparent overlay -> rejected `StaleElementError`; (2) cross-origin OOPIF under overlay -> rejected `StaleElementError`; (3) nested 2-level iframe -> works exposed, rejects covered; (4) legitimate exposed iframe button -> succeeds `verified=True`.

### `CUL-PRIV-001` & `CUL-PRIV-002` — Sensitive Field Redaction & Zero Hash Leak on Secrets
- **Severity / Defect:** `P0` / `P2` — Regex `/(pass|secret|token|cvv|pin|pwd)/` misses `card`, `ccnum`, `ssn`, `iban`, `otp`, `autocomplete=cc-number`, while false-positiving `address_shipping`, `opinion`, `spinner`; `TaskState` & `signature()` expose partial SHA-256 hashes of redacted secrets.
- **Root Cause:** Unanchored substring regex duplicated at `browser_cdp.py:1863` and `browser_cdp.py:2150`; `state.py:41-48` & `browser_cdp.py:2168-2171` always emit hash prefix even when redacted.
- **Files/Functions:** Shared JS snippet `_SENSITIVE_FIELD_JS` in `browser_cdp.py` (used by both inspect JS & `signature()` JS — zero duplication!), `state.py` (`redact_value`), `api.py`.
- **Fix:** Token-boundary matcher over normalized identifier tokens + `autocomplete` attribute (`current-password`, `new-password`, `one-time-code`, `cc-number`, `cc-csc`, `cc-exp`, `cc-name`) + `type="password"` / `inputmode="numeric"` combined with card/OTP hints; verify zero match on `address_shipping`, `opinion`, `spinner`, `mapping`, `pine`; suppress `value_sha256` / `h=...` whenever a field/value is redacted (`value_redacted=True`, length only).
- **Acceptance & Tests:** Unit + Playwright + MCP workflow verifying redaction across `discover`, `inspect`, `state.signature()`, `state.record_action()`, persisted JSON, logs, and MCP outputs, plus non-redaction of benign names.

### `CUL-SEC-001` — SSRF DNS Fail-Closed & Rebinding Defenses
- **Severity / Defect:** `P0` — `validate_navigation_url` catches `socket.gaierror` and sets `infos = []` (allowing unresolved / rebinding domains).
- **Root Cause:** `session_manager.py:141-145` treats DNS lookup failure as safe instead of blocking; `_install_browser_fetch_guard` checks `_is_blocked_host` dynamically but does not resolve/pin IPs at navigation start.
- **Files/Functions:** `session_manager.py` (`validate_navigation_url`, `_resolve_public_ips`), `browser_cdp.py` (`_install_browser_fetch_guard`).
- **Fix:** Raise `PermissionError` on `socket.gaierror` (and empty addrinfo) when `CUL_MCP_ALLOW_PRIVATE_URLS != 1`; validate every resolved IPv4/IPv6 record against `_is_disallowed_ip` (plus mapped/Teredo/6to4/NAT64); detect multi-resolution/private answers and block redirects/subrequests in `_install_browser_fetch_guard` across initial goto, `back`, links, and fetches (reusing shared validator); add controlled DNS rebinding simulation fixture (`getaddrinfo` returns public IP on call 1 and `127.0.0.1` on call 2) proving Fetch/re-validation blocks rebinding while honestly documenting Chromium OS socket-level TOCTOU caveat where no `--host-resolver-rules` pin is set.
- **Acceptance & Tests:** `.invalid`, `127.0.0.1`, `[::1]`, `169.254.169.254`, `::ffff:127.0.0.1`, `302` redirect to loopback, and simulated DNS rebinding all raise `PermissionError`.

### `CUL-SEC-002` — Disable `DirectCdpClient` Loopback Exposure by Default
- **Severity / Defect:** `P0` — `CUL_MCP_DIRECT_WS` defaults `True`, opening `--remote-debugging-port` on `127.0.0.1`.
- **Root Cause:** `browser_cdp.py:550-555`.
- **Files/Functions:** `browser_cdp.py` (`_resolve_direct_ws`).
- **Fix:** Return `False` unless `CUL_MCP_DIRECT_WS` is explicitly `"1"` / `"true"` / `"yes"` / `"on"` (or `direct_ws=True` explicitly passed in code for controlled perf harness); verify normal Playwright `CDPSession` path passes all MCP/browser tests cleanly.
- **Acceptance & Tests:** Default `BrowserSession` & `open_browser` MCP have `_use_direct_ws == False` and no `--remote-debugging-port` arg; opt-in still works for Track C perf comparison.

### `CUL-ACC-002` — Truthful `verified` Semantics (No False `verified=True` on No-Op / `readonly`)
- **Severity / Defect:** `P0` — Typing into `readonly` element or no-op click that moves focus reports `verified: true`.
- **Root Cause:** `api.py:143-159` + `state.py:55-98` check only `signature()` string changes (`focus` or unrelated DOM counters) rather than verifying whether the requested mutation (`readonly` block, element value/checked/expanded/url/dom change) genuinely succeeded.
- **Files/Functions:** `api.py` (`execute_action`), `state.py` (`verify`), `browser_cdp.py` (`perform`, `signature`), `desktop_uia.py` (`perform`).
- **Fix:** Inspect target `readonly` / `disabled` before typing (reject or mark no-op cleanly), compare target-specific value/checked/state before vs after (`state_changed`, `target_value_changed`, `focus_only`), and guarantee `verified=False` whenever typing leaves `readonly` unchanged or click produces only a focus ring without state/action delta, emitting explicit `verification_scope` alongside backward-compatible `verified` boolean.
- **Acceptance & Tests:** Typing into `input[readonly]` -> `verified is False`; genuine submit/input/toggle -> `verified is True`; dead/unresponsive button -> `verified is False`.

---

## Track B: P1 — Windows Desktop Safety & Reliability

- **`CUL-SEC-003` (`open_desktop` policy):** Add default sensitive process/class blocklist (`powershell.exe`, `pwsh.exe`, `cmd.exe`, `windowsterminal.exe`, `conhost.exe`, `1password.exe`, `bitwarden.exe`, `keepass.exe`, `mmc.exe`, `regedit.exe`, `CredentialUIBroker.exe`, `Taskmgr.exe`) + `CUL_DESKTOP_ALLOW_SENSITIVE=1` / `CUL_DESKTOP_ALLOW_PROCESSES` explicit policy override in `session_manager.py` & `desktop_uia.py` (raises `PermissionError`).
- **`CUL-DESK-001` (`DesktopSession.verify_fresh` real occlusion):** Reuse `blind_gap._is_window_occluded_or_bg(self.hwnd, bbox)` inside `desktop_uia.py:verify_fresh` to detect foreground mismatch, minimized/cloaked state, and higher Z-order covering windows over target element box -> sets `occluded=True` -> raises `StaleElementError`.
- **`CUL-SEC-004` (`_BLOCKED_KEY_TOKENS` dangerous shortcuts):** Extract shared hotkey guard helper blocking `win/meta/super/command`, `Alt+Tab`, `Alt+F4`, `Alt+Escape`, `Ctrl+Escape`, `Ctrl+Shift+Escape`, `Ctrl+Alt+Delete` across BOTH `desktop_uia.py` and `browser_cdp.py` unless `CUL_ALLOW_SYSTEM_SHORTCUTS=1`.
- **`CUL-DESK-002` (`KillSwitch` fail-closed):** When initial `GetCursorPos()` inside `KillSwitch` fails on Windows (`OSError` / permission denied), do NOT silently arm fail-open; record `_sample_failed` and fail closed (`RuntimeError("KillSwitch unable to read cursor position ...")`) when real desktop input is attempted unless test harness explicitly disables kill switch.
- **`CUL-DESK-003` (Explorer inactive tabs):** In `desktop_uia.py` scan for `CabinetWClass`, filter children belonging to inactive/hidden `ShellTabWindowClass` / `TabBandClass` subtrees (`IsOffscreen` OR bounding box outside active `ShellTabWindowClass` bounds OR ancestor invisible `ShellTabWindowClass`). Verify on real 2-tab Explorer `C:\audit_scratch`.
- **`CUL-DESK-004` (RTL `PrintWindow` mirroring):** In `blind_gap.py:_capture_hwnd_printwindow`, read `GWL_EXSTYLE`; if `WS_EX_LAYOUTRTL` (`0x00400000`) is set, flip captured image horizontally (`ImageOps.mirror`) and map crop coordinates in un-mirrored screen space! Verify visually/pixel-hash on synthetic RTL Win32 HWND vs LTR HWND.
- **`CUL-DESK-005` (`_pulse_screenreader` cleanup & Explorer tab transition):** Track original `SPI_GETSCREENREADER` boolean prior to pulsing, register `atexit` / crash recovery restoration back to original state, and stabilize Explorer post-tab title poll (`WIN:` / `title` refresh).

---

## Track C2: P2 — Runtime, Portability, DX & Security Framing

- **`CUL-DX-001` (Cross-platform imports):** Guard top-level `ctypes.WinDLL`, `ctypes.WINFUNCTYPE`, `SetProcessDpiAwarenessContext`, and `comtypes` across `snapshot.py`, `desktop_cursor_overlay.py`, `desktop_uia.py`, `blind_gap.py`, and `__init__.py` behind lazy Win32 loaders / `sys.platform == "win32"`. Add explicit mock-platform unit test verifying `import computer_use_lite` & `mcp_server` + pytest collection work cleanly when `sys.platform == "linux"`!
- **`CUL-DX-002` (Dependencies & locking):** Add `psutil>=6.0` to `[project.optional-dependencies].dev` in `pyproject.toml`; generate verified `requirements-lock.txt` (`pip freeze` from clean venv matching `0.2.0a0`).
- **`CUL-SEC-005` (`[UNTRUSTED_UI_TEXT]` boundaries):** Wrap `DIALOG_ALERT:` messages and page titles/element snippets cleanly with explicit untrusted markers / sanitization (`[UNTRUSTED_DIALOG_ALERT] ...`) and document prompt-injection boundary in `SECURITY.md` & `_SERVER_INSTRUCTIONS`.

---

## Track D: P3 — Scoped Performance & Capabilities

- **`CUL-ACC-003` (Rich AX metadata & `input[type=date]`):** Pull `checked`, `selected`, `readonly`, `disabled`, `valuemin`, `valuemax`, `valuenow`, `<select>` option list into `inspect_element`; handle `input[type=date]` via clean DOM value/event setter without mangling digits.
- **`CUL-PERF-001` (Scoped ergonomic & resource fixes):**
  - Sticky-header / viewport-safe click center calculation in `browser_cdp.py` (`_safe_click_point` shifting off covering `position: fixed/sticky` header if center occluded while bottom half of target is exposed).
  - Configurable / adaptive `hover(wait_ms=...)` (`hover.py` & `mcp_server.py` default `350`, early return if DOM mutation settles or `wait_ms=0` honored).
  - Continuous `drag` primitive (`Api.drag` / `BrowserSession.drag` / `DesktopSession.drag` + `act(action="drag", target_element_id=..., to_x=..., to_y=...)` keeping exact 13-tool MCP roster intact!).
  - Compact static text excerpt `Api.read_page` + optional `discover(include_static_text=True)` (additive param, zero breaking schema change).
  - `SessionManager` idle TTL / LRU eviction tracking (`last_used_at`, configurable `CUL_SESSION_IDLE_TTL_S` + safe reaper before raising `SessionLimitError` when expired sessions exist).
  - Accurate `TOKENS_EST` disclaimer (`len(text)/4` ASCII approximation, explicit multi-script caveat in Arabic/CJK in docs/metadata).
  - Deterministic `Resolver` IoU `>=0.75` tie-breaking preferring explicit interactive semantic roles over generic `clickable` wrappers (`resolver.py`).

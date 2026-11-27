# Computer Use Lite (`v0.2.0a0`) — Engineering Change History & Research Release Dossier

- **Release Version:** `0.2.0a0` (Experimental Research Preview — Security, Reliability, Portability & Cursor Hardening Edition)
- **Historical Preserved Tags:** [`v0.1.0a0`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a0) (`0d19a9e`, runtime baseline), [`v0.1.0a1`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a1) (`566f08d`), [`v0.1.0a2`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a2) (`de27b49`)
- **Fixed Engine Reference Commit:** `a33a8f261fe4e7b9ef761e1763ac5ad2f2907faf`
- **Comparative Benchmark Suite (`post-fix-v1`):** [`research/benchmarks/post-fix-v1/REPORT.md`](../../../research/benchmarks/post-fix-v1/REPORT.md)
- **Independent Post-Fix Audit:** [`research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md`](../../../research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md)

---

## 1. Per-Defect Engineering Lifecycle (`0d19a9e -> v0.2.0a0`)

Every major issue discovered during the Windows 11 & Linux independent audits is documented below across all seven lifecycle stages.

### `F-01` (`CUL-ACC-001`) — Cross-Frame Overlay Click-Through (`Critical`)
- **What was wrong:** An interactive button inside a same-origin or cross-origin `<iframe>` covered by a top-document `position: fixed; z-index: 999` transparent `<div>` passed `verify_fresh()` and reported `ok: true, verified: true` while clicks landed silently on the covering overlay (`coverClicks=1, btnClicks=0`).
- **How discovered:** Live Windows 11 audit browser probe (`W B5`: `b5_cross_origin_iframe_under_fixed_overlay.png`) + Linux code audit (`L A8`).
- **Why it happened:** `_NODE_PROBE_JS` evaluated `document.elementFromPoint()` inside the *child iframe's* isolated DOM context, which cannot see elements in ancestor frame documents.
- **What code changed:** Added `_verify_top_frame_hit(ref, box)` (`src/computer_use_lite/browser_cdp.py:1860`) using top-level CDP `DOM.getNodeForLocation` to verify the compositor hit lands on the target node or its owning `<iframe>`, returning explicit `StaleElementError` on parent occlusion or `cross_origin_unprovable` when unresolvable.
- **How tested:** `tests/test_repair_p0_security.py::test_cul_acc_001_cross_frame_and_oopif_overlay_occlusion` + Track A (`A01`, `A02`, `A03`) + Track B2 (`s03`).
- **Benchmark improvement:** Baseline `0d19a9e` failed `A01`, `A03`, and `s03` (`1` leaked click, `unprovable_verified_false=False`); `0.2.0a0` blocked every overlay leak (`0` hits) across same-origin and cross-origin frames.
- **Unresolved boundary:** If an embedded third-party iframe cannot be mapped by `DOM.getNodeForLocation` or `DOM.getFrameOwner`, `ok` remains bounded by `verification_scope: "cross_origin_unprovable"` with `verified: false`.

### `F-02` (`CUL-PRIV-001` / `-002`) — Sensitive Field Regex & Deterministic Hash Leak (`High`)
- **What was wrong:** Substring matching `/(pass|secret|token|cvv|pin|pwd)/` missed `card`, `ccnum`, `ssn`, `iban`, `otp`, and `autocomplete="cc-number"`, yet over-redacted innocent fields (`address_shipping`, `opinion`, `spinner`). Meanwhile `TaskState` (`state.py`) and `signature()` emitted deterministic `sha256[:16]` prefixes even on sensitive passwords.
- **How discovered:** Windows 11 audit probe (`W B6`: `browser_probes_results.json`) and Linux code inspection (`L A9`).
- **Why it happened:** Raw unanchored regex alternation lacked camelCase/delimiter word splitting, and `redact_value()` lacked a keyed secret path.
- **What code changed:** Implemented word-boundary tokenization + `autocomplete` checking consistently in Python (`state.py:44` `is_sensitive_name`) and JS (`browser_cdp.py:51` `_IS_SENSITIVE_ELEM_JS`), plus process-ephemeral keyed `hmac` redaction (`state.py:72` `redact_value`, `browser_cdp.py:2513`).
- **How tested:** `tests/test_repair_p0_security.py::test_cul_priv_001_and_002_sensitive_redaction_and_no_secret_hash` + Track A (`A04`–`A06`).
- **Benchmark improvement:** Baseline `0d19a9e` leaked `"4111222233334444"` and deterministic SHA-256 prefixes while redacting `"Cairo St"`, `"good"`, `"fast"`; `0.2.0a0` passes `A04`–`A06` (`3/3`).
- **Unresolved boundary:** Non-standard visually rendered `<canvas>` secrets without accessible names/labels/autocomplete attributes remain opaque text surfaces.

### `CUL-ACC-002` — Dishonest `verified` Flag & >400-Char DOM Signature Blind Spot (`P0`)
- **What was wrong:** `execute_action()` marked `verified: true` whenever `focus` shifted—even on `<input readonly>` edits, dead no-op buttons, or unprovable cross-origin targets. Additionally, Track B2 replay exposed that `signature()` sliced `document.body.innerText` to 400 characters, missing genuine DOM updates at the bottom of dense pages (`b11`).
- **How discovered:** Windows `W B7` probe (`readonly` `verified=True`) and `Track B2` replay diagnostics on `b11_dense_90_grid_clean`.
- **Why it happened:** `state.verify()` lacked action/readonly semantics (`set(d.keys()) == {"focus"}`) and `browser_cdp.py` lacked target control state probing and full-text digesting.
- **What code changed:** Added `_target_signature()` (`browser_cdp.py:2465`), `_DIGEST_TEXT_JS` full-body FNV-1a digest beyond 400 chars (`browser_cdp.py:63`), and semantic `state.verify(before, after, action=...)` (`state.py:150`).
- **How tested:** `tests/test_repair_p0_security.py::test_cul_acc_002_verified_false_on_readonly_and_noop` + `tests/test_repair_p3_capabilities.py::test_signature_detects_dom_text_change_beyond_400_chars` + Track A (`A10`–`A11`) + Track B2 (`s01`, `s02`, `b11`).
- **Benchmark improvement:** Baseline reported false `verified: true` on `s01` (`readonly`) and `s02` (no-op); `0.2.0a0` returns honest `verified: false` (`readonly_target_noop` / `focus_only_noop`) while accurately verifying `b11`.
- **Unresolved boundary:** `verified` confirms DOM/focus/target-state delta locally; asynchronous background network requests settling long after click return require subsequent `discover` / `read_page`.

### `F-04` (`CUL-SEC-001`) — SSRF `gaierror` Fail-Open & DNS Rebinding (`Medium`)
- **What was wrong:** `validate_navigation_url()` caught `socket.gaierror` into an empty `infos` list, allowing unresolvable/synthetic domains (`nonexistent.invalid`) to slip through SSRF validation.
- **How discovered:** Windows `W B8` offline `.invalid` reproduction and Linux static audit (`L A10`).
- **Why it happened:** Over-broad `except socket.gaierror: infos = []` intended for offline test resilience disabled resolution checks whenever `CUL_MCP_ALLOW_PRIVATE_URLS != "1"`.
- **What code changed:** Updated `validate_navigation_url()` (`src/computer_use_lite/session_manager.py:82`) to fail closed (`raise PermissionError`) on `socket.gaierror` or empty address results and block resolved-IP drift across repeated resolves.
- **How tested:** `tests/test_repair_p0_security.py::test_cul_sec_001_ssrf_dns_fail_closed_and_rebinding` + Track A (`A07`, `A08`).
- **Benchmark improvement:** `A07` moved from fail (`False`) to pass (`PermissionError` raised).
- **Unresolved boundary:** True OS/Chromium internal socket-level DNS rebinding TOCTOU between Python pre-check and Chromium's C++ network stack remains open without an OS/proxy resolver firewall (`SECURITY.md`).

### `F-05` (`CUL-SEC-002`) — Default Loopback CDP WebSocket Exposure (`Medium`)
- **What was wrong:** `CUL_MCP_DIRECT_WS` defaulted to enabled (`True`), spawning Chromium with an unauthenticated loopback `--remote-debugging-port` reachable by local processes on the workstation.
- **How discovered:** Linux code audit (`L A11`) & `SECURITY.md` threat review.
- **Why it happened:** `DirectCdpClient` speed optimization (`-98 ms` on 1.1 MB DOMs in `Exp 7`) was prioritized as the default over loopback isolation.
- **What code changed:** Changed `_resolve_direct_ws` (`browser_cdp.py:613`) to default `False` (routing through Playwright's internal Pipe IPC), while preserving `CUL_MCP_DIRECT_WS=1` opt-in.
- **How tested:** `tests/test_repair_p0_security.py::test_cul_sec_002_direct_cdp_disabled_by_default` + Track A (`A09`) + Track C (`baseline` vs `pipe` vs `directws`).
- **Benchmark improvement & tradeoff:** Zero loopback TCP debug port open by default. Measured tradeoff in Track C (`N=10`): `dense_2500` discovery `p50` moved from `163.45 ms` (`0d19a9e`) to `367.09 ms` (`Pipe`), while standard forms stay `9.46 ms` and `CUL_MCP_DIRECT_WS=1` restores `152.43 ms`.

### `F-03` & `CUL-CUR-001`..`010` — Cursor Overlay Canvas Blindness & Motion Bugs (`High`/`P0`)
- **What was wrong:** (`F-03`) Injecting `[data-cul-overlay]` Shadow DOM with a full-viewport `<canvas>` triggered false `1280x720` `opaque_canvas` blind crops on every `discover`; plus (`CUL-CUR-001`–`006`) immediate `<350 ms` `progress` shape flashes caused extra DOM rebuilds, `not-allowed` error cursor stayed stuck permanently, double clicks (`clicks=2`) triggered 1 pulse/ripple, velocity tilt overshot `14.69 deg` (>5°), background tabs stalled `rAF` promises (`1218.8 ms` timeout), and navigation re-evaluated `48 KB` JS inline.
- **How discovered:** Windows `W B14-1` (`b14_cursor_blind_check.txt`) and Cursor Strict Audit sections 2A–2G.
- **What code changed:** Excluded cursor overlay hosts from `canvas_rects` (`browser_cdp.py`), added `busyDelayMs=350`, `errorResetMs=900`, multi-click pulse scheduling, `±5.0 deg` post-spring clamp, `document.hidden` short-circuit (`cursor_overlay.py`), single `Page.addScriptToEvaluateOnNewDocument` cache (`browser_cdp.py:2068`), desktop sprite/thread upgrades + opt-in `CUL_TAKEOVER_GLOW` (`desktop_cursor_overlay.py`, `takeover_guard.py`).
- **How tested:** `tests/test_cursor_overlay.py` + Track A (`A21`–`A26`) + Track C `cursor_raf`.
- **Benchmark improvement:** Baseline `0d19a9e` failed `A21, A23–A26` (`max_tilt_deg=14.69`, hidden tab hung `>1200 ms`, `6` busy rebuilds, `48,234 B` nav eval); `0.2.0a0` passes all (`6/6`) with `1` rebuild, `0 B` per-nav eval, `2.3 ms` hidden return, `5.0 deg` max tilt, and `16.7 ms` `rAF` p50.
- **Unresolved boundary:** Live Win32 `GetCursorInfo()` pointer flicker (`CUL-CUR-008`) and hardware `WH_KEYBOARD_LL` physical `Esc` interrupt (`CUL-CUR-010`) cannot execute inside isolated `exebox` (`ERROR_ACCESS_DENIED`) and remain **`NOT VERIFIED`**.

### `F-06`, `F-07`, `F-08`, `CUL-SEC-003/004`, `CUL-DESK-002/005` — Windows Desktop UIA & Policy Fixes (`P1`)
- **What was wrong:** `open_desktop` attached freely to shells/credential UIs; dangerous OS hotkeys (`Alt+Tab`, `Alt+F4`, `Ctrl+Esc`, `Ctrl+Shift+Esc`) weren't blocked; `DesktopSession.verify_fresh()` hardcoded `occluded: False`; `KillSwitch` swallowed initial `GetCursorPos()` errors fail-open; File Explorer (`CabinetWClass`) leaked inactive background tab items with `IsOffscreen=False`; Win32 `PrintWindow` horizontally mirrored `WS_EX_LAYOUTRTL` windows; `_pulse_screenreader` lacked `atexit` restore; and Arabic Win11 keyboard layout returned `0xFF` from `VkKeyScanW` on `'c'`.
- **How discovered:** Windows 11 isolated `exebox` + live Explorer/Win32 probes (`W B9`, `W B12`, `W chk#9`, `exebox_gui_probe.json`) and live repair probing.
- **What code changed:** Added `validate_desktop_target` (`state.py:228`), `validate_key_spec` (`state.py:202`) + ASCII fallback, `blind_gap._is_window_occluded_or_bg` + DWM cloaking check wired into `DesktopSession.verify_fresh` (`desktop_uia.py:885`), `KillSwitch.ensure_armed` (`desktop_uia.py:239`), `_inactive_explorer_tab_hwnds` lower-Z `ShellTabWindowClass` exclusion (`desktop_uia.py:572`), `WS_EX_LAYOUTRTL` `ImageOps.mirror` (`blind_gap.py:187`), and `_restore_screenreader_state` `atexit` + `RLock` (`desktop_uia.py:538`).
- **How tested:** `tests/test_repair_p1_desktop.py` (5/5 interactive Windows tests) + Track A (`A12`–`A18`).
- **Benchmark improvement:** Baseline `0/7` (`A12`–`A18`); `0.2.0a0` `7/7` (`100%`) while preserving `desktop_uia_explorer` `p50` speed (`126.6 ms` vs `125.63 ms`).
- **Unresolved boundary:** Desktop `T2` (`Calculator` + `7006652.txt`) and UAC/lock-screen external races remain untested.

### `CUL-DX-001/002`, `CUL-SEC-005`, `CUL-ACC-003`, `CUL-PERF-001` — Portability, Metadata & Capabilities (`P2`/`P3`)
- **What was wrong:** Module-level Win32 `ctypes.WinDLL`/`WINFUNCTYPE` crashed Linux imports; `psutil` was omitted from `[dev]`; external UI alerts lacked `[UNTRUSTED_UI_TEXT]` markers; `<input type=date>`, checkbox/slider/select AX states, sticky-header edge-offset clicks, continuous `drag`, and `read_page` were missing or unreliable; `hover` slept a flat `350 ms`; and `SessionManager` lacked idle TTL reaping.
- **What code changed:** Guarded Win32 bindings in `snapshot.py:26`, `desktop_uia.py`, `desktop_cursor_overlay.py`; added `psutil>=6.0` (`pyproject.toml:56`), `requirements-lock.txt`, and CI `test-linux-portability`; added `sanitize_ui_text` (`state.py:254`) & `[UNTRUSTED_UI_TEXT]` framing (`mcp_server.py`); added `inspect_metadata` (`browser_cdp.py:1998`), JS value prototype setter, semantic role tie-breaker (`resolver.py:71`), sticky-header `_is_occluded_node` click point shifting, `Api.drag`/`Api.read_page` & `act(action="drag")` (preserving 13 MCP tools), adaptive `hover_and_diff` (`hover.py:22`), and `SessionManager._reap_expired_idle` (`session_manager.py:329`).
- **How tested:** `tests/test_repair_p2_portability.py`, `tests/test_repair_p3_capabilities.py`, Track A (`A19`, `A20`, `A27`–`A32`), Track C `hover_adaptive`, Track D WSL2 `kali-linux` (`Python 3.14.7`).
- **Benchmark improvement:** `hover_adaptive` dropped **4.3x (`387.39 ms -> 90.83 ms` p50)**; Track B2 climbed from `12/18` (`66.67%`) to **`18/18` (`100.0%`)**; real Linux (`WSL2 Python 3.14.7`) import succeeds cleanly (`WSL_LINUX_OK`).
- **Unresolved boundary:** `Track B1` live LLM reasoning runs stay strictly **`NOT_RUN`** (Codex usage limit exhausted Dec 26, 2026); `P1` Polymer `<style>` filter heuristic & `max_elements` heuristics stay as lightweight structural limits.

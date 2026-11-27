# Repair Acceptance Criteria

1. **Cursor Subsystem (`cursor-audit-fix`):**
   - `CUL-CUR-007`: `show_cursor=True` on clean DOM page -> `blind_regions == 0`.
   - `CUL-CUR-001` (Fix A): Actions `<350 ms` never trigger `progress`; 3 consecutive pointer clicks produce `<= 1` `#cul-shape` SVG DOM rebuilds (measured via CDP).
   - `CUL-CUR-002` (Fix B): Error state auto-reverts within `~900–1100 ms`; follow-up `moveTo` cancels timer cleanly.
   - `CUL-CUR-003` (Fix C): `clicks=2` increments click count by `+2`, triggers `2` press pulses & `2` ripples in browser and Win32 desktop; blind `click_coordinate` keeps stable `crosshair` shape.
   - `CUL-CUR-004` (Fix D): Maximum rendered tilt angle `<= 5.0 deg` across full-viewport fast sweeps.
   - `CUL-CUR-005` (Fix E): Hidden/background tab `moveTo` returns in `< 1.0 s`; overlapping moves cancel prior glide.
   - `CUL-CUR-006` (Fix F): Init script registered once per page via `Page.addScriptToEvaluateOnNewDocument` (`0` full-script re-sends on navigation).
   - `CUL-CUR-008`: Real Win11 `GetCursorInfo` telemetry captured and analyzed during `SendInput` double-click.
   - `CUL-CUR-009`: Spring motion + min-jerk glide + `120 ms` morph + `60 ms` `0.9` press + `prefers-reduced-motion` + `p50`/`p95` Chrome frame time measured before vs after.
   - `CUL-CUR-010`: `CUL_TAKEOVER_GLOW=1` (`#0E9F6E`, default OFF) state machine `idle/armed/active/interrupted` + `LLMHF_INJECTED` guard + >2s watchdog + `user_interrupted` unit-tested (and Win11 hook check marked `FIXED+VERIFIED` only if executed on interactive `WinSta0\Default`, else `NOT VERIFIED`).

2. **`P0` Security & Correctness:**
   - Cross-origin OOPIF, same-origin iframe, nested iframe under transparent overlay -> rejected `StaleElementError`; exposed inner controls -> succeed `verified=True`.
   - Secret fields (`password`, `cc-number`, `ssn`, `iban`, `otp`, `cvv`, `secret`, `token`) redacted across `discover`, `inspect`, `signature`, `TaskState`, JSON logs, and MCP output WITHOUT hashing secrets; `address_shipping`, `opinion`, `spinner` NOT redacted.
   - `validate_navigation_url` raises `PermissionError` on DNS failure, private/loopback/IPv6 ranges, `302` redirects, and simulated DNS rebinding.
   - Default `CUL_MCP_DIRECT_WS` is `False`; normal 13-tool MCP suite passes on `CDPSession`.
   - `readonly` typing & non-mutating no-op clicks report `verified=False`.

3. **`P1` Windows Desktop:**
   - Sensitive process/class targets blocked by default in `open_desktop`; dangerous OS shortcuts (`Alt+Tab`, `Alt+F4`, `Ctrl+Esc`, `Ctrl+Shift+Esc`) blocked by default.
   - `DesktopSession.verify_fresh()` fails closed (`StaleElementError`) when target window/region is occluded.
   - `KillSwitch` fails closed on Win32 `GetCursorPos` failure.
   - File Explorer 2-tab inactive elements excluded; `WS_EX_LAYOUTRTL` `PrintWindow` capture un-mirrored; `_pulse_screenreader` registers restoration hook.

4. **`P2` & `P3`:**
   - Non-Windows platform import simulation succeeds with `0` top-level Win32 `WinDLL` calls; `psutil` present in `[dev]`; `[UNTRUSTED_UI_TEXT]` boundary framing present; `AXTree` state (`checked`/`readonly`/`range`/`select`), `date` input fill, sticky-header clamp, `drag`, `read_page`, and session idle expiry all covered by regression tests; `python scripts/verify_copyright_headers.py` exits `0`.

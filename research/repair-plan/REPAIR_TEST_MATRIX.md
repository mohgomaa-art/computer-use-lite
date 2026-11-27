# Repair Verification & Test Matrix

| Finding ID | Before-Fix Repro Test / Script | After-Fix Regression Test | Platform Required | Execution Mode |
| :--- | :--- | :--- | :--- | :--- |
| `CUL-CUR-001..007` | Baseline `0d19a9e` Chrome CDP + `cursor_overlay` probes | `tests/test_cursor_overlay_regressions.py` + `tests/test_cursor_overlay.py` | Win11 + Chromium | Automated pytest + CDP script |
| `CUL-CUR-008` | `scripts/probe_win32_cursor_info.py` | Recorded Win11 `GetCursorInfo` log (+ scoped restore test if triggered) | Win11 `WinSta0\Default` | Empirical Win32 probe |
| `CUL-CUR-009` | Baseline `rAF` frame latency probe on `0d19a9e` | `test_cursor_animation_upgrade_*` + Chrome `rAF` p50/p95 probe | Win11 + Chromium | Automated + CDP benchmark |
| `CUL-CUR-010` | `CUL_TAKEOVER_GLOW` state unit checks | `tests/test_takeover_glow.py` (`idle/armed/active/interrupted`, watchdog, overlay, live hook check if WinSta0 allows) | Cross-platform + Win11 | Unit mock + conditional Win11 |
| `CUL-ACC-001` | Same-origin & OOPIF overlay click fixture | `tests/test_repair_p0_security.py::test_cross_frame_and_oopif_overlay_occlusion` | Chromium | Automated pytest |
| `CUL-PRIV-001/002` | `b6` field redaction matrix + hash leak check | `tests/test_repair_p0_security.py::test_sensitive_redaction_precision_and_no_secret_hash` | Chromium + Unit | Automated pytest |
| `CUL-SEC-001` | `.invalid` + loopback + simulated rebind fixture | `tests/test_repair_p0_security.py::test_ssrf_dns_fail_closed_and_rebinding` | Cross-platform + Chromium | Automated pytest |
| `CUL-SEC-002` | Check `_resolve_direct_ws()` default | `tests/test_repair_p0_security.py::test_direct_ws_disabled_by_default_and_mcp_works` | Cross-platform | Automated pytest |
| `CUL-ACC-002` | `b7` `readonly` input + no-op button click | `tests/test_repair_p0_security.py::test_verified_false_on_readonly_and_noop` | Chromium | Automated pytest |
| `CUL-SEC-003/004` | Sensitive process attach + `Alt+Tab`/`Alt+F4` test | `tests/test_repair_p1_desktop.py::test_desktop_policy_and_shortcut_blocking` | Cross-platform + Win11 | Automated pytest |
| `CUL-DESK-001/002` | Covering Win32 HWND + `KillSwitch` `OSError` mock | `tests/test_repair_p1_desktop.py::test_desktop_occlusion_and_killswitch_fail_closed` | Win11 (`windows_desktop`/`windows_only`) + Unit | Automated pytest |
| `CUL-DESK-003/004/005` | Explorer 2-tab (`C:\audit_scratch`), `WS_EX_LAYOUTRTL` HWND `PrintWindow`, screenreader restore | `tests/test_repair_p1_desktop.py::test_explorer_tabs_rtl_capture_and_screenreader_restore` | Win11 `WinSta0\Default` | Automated pytest + interactive probe |
| `CUL-DX-001/002`, `CUL-SEC-005` | Mocked `sys.platform='linux'` clean subprocess import | `tests/test_repair_p2_portability.py` | Cross-platform (+ WSL check if runnable) | Automated subprocess pytest |
| `CUL-ACC-003`, `CUL-PERF-001` | `date`, slider, sticky-header, drag, `read_page`, idle TTL fixtures | `tests/test_repair_p3_capabilities.py` | Chromium + Unit | Automated pytest |

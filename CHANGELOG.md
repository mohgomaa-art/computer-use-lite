# Changelog

All notable changes to **Computer Use Lite** are documented in this file.  
Release classification: **Public Research Preview — Experimental — Not Production Ready**.

---

## [Unreleased — Post `0.1.0-alpha` through `d47b4e9`]

> Note: Source and regression test commits below landed on `main` after the `698861d` (`0.1.0-alpha`) documentation baseline (`7c7b9b4..d47b4e9`). No aggregate full-suite `pytest` count for `d47b4e9` was executed during the documentation consolidation pass.

### Added — Workstream A: Cursor Overlay (`7c7b9b4`, `5c0a01e`, `e3d0bd5`, `4f9bcef`, `d47b4e9`)
- **Obsidian-Chrome 3D Cursor System ([`cursor_overlay.py`](src/computer_use_lite/cursor_overlay.py)):** Added a unified `64x64` vector cursor registry (`DESIGN_TOKENS`, `26+` pointer/resize/text/progress variants) and a CSP / Trusted-Types-safe DOM+SVG overlay bridge for Chromium (`CUL_AGENT_CURSOR`, `CUL_AGENT_CURSOR_GLIDE_MS`).
- **Windows Desktop Layered Overlay ([`desktop_cursor_overlay.py`](src/computer_use_lite/desktop_cursor_overlay.py)):** Added a dedicated `60.0 Hz` Win32 GUI-thread click-through overlay (`WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE`) excluded from screen capture (`_WDA_EXCLUDEFROMCAPTURE`) without invoking `SendInput` for visual glides (preserving `KillSwitch`), plus `bring_window_to_front` z-order helper in `desktop_uia.py`.
- **MCP Metadata & Env Toggle ([`mcp_server.py`](src/computer_use_lite/mcp_server.py), [`api.py`](src/computer_use_lite/api.py)):** Added `CUL_MCP_HEADFUL` default resolution on omitted `headless` in `open_browser`, `HEADLESS:`/`CURSOR:` fields in discovery headers, `server_pid` + `headful_default` in `list_sessions()`, and distinct visual outcome cues separating dispatch `ok` from `verified`.
- **Overlay Test Suite (`tests/test_cursor_overlay.py`):** Added unit and desktop overlay tests (note: `tests/test_cursor_overlay.py` carries uncommitted local edits on working tree).

### Changed & Fixed — Phase 1 `P0` Correctness & Security (`77cd171`..`a3291b3`, `d47b4e9`)
- **`P0-1` Site-Isolated OOPIF Verification (`77cd171`):** Added deterministic `--site-per-process` OOPIF ground-truth discovery and action verification test (`tests/test_audit_fixes.py::test_p0_1_site_per_process_oopif_discovery_gt_and_actions`). Live third-party embeds remain unverified on restarted MCP.
- **`P0-2` Multi-Tab Browser Tracking (`bee026e`):** Added Playwright context page tracking (`BrowserSession.tabs`, `switch_tab`, `close_tab`) and extended MCP `navigate` with `list_tabs`, `switch_tab`, and `close_tab` plus `tab_index`, preserving cursor overlay continuity across tab changes.
- **`P0-3` Win32 `#32770` Save As Commit & Dialog Alerts (`16465bf`):** Added `_resolve_dialog_edit_hwnd` and `_commit_dialog_text` (`SendInput` / `EM_SETSEL`+`WM_CHAR` fallback) in `desktop_uia.py`, plus `DIALOG_ALERT:` static text surfacing in `api.py`.
- **`P0-4` CDP `Fetch` Redirect & Sub-Request SSRF Guard (`965eb66`):** Added browser-wide CDP `Fetch` request/response interception (`_install_browser_fetch_guard`) rejecting `3xx` redirects and sub-requests to blocked hosts, and extended `_is_disallowed_ip()` with IPv4-mapped IPv6, 6to4, Teredo, and NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) checks. DNS-rebinding TOCTOU remains open.
- **`P0-5` CDP Origin Restriction & `DirectWS` Gate (`a3291b3`):** Added `--remote-debugging-address=127.0.0.1` + exact-port `--remote-allow-origins=http://127.0.0.1:<port>` on Chromium launches, plus `CUL_MCP_DIRECT_WS=0` opt-out (`_resolve_direct_ws`).
- **UIA Initialization Resilience (`d47b4e9`):** Guarded uninitialized `show_cursor` attribute cleanup on `DesktopSession` and added retry handling for transient Windows 11 UIA initialization `COMError`.

### Documentation Reorganization
- Consolidated canonical documentation under `docs/` (`docs/INDEX.md`, `docs/RESEARCH_FINDINGS.md`, `docs/OPTIMIZATION_ROADMAP.md`, and updated architecture/benchmarks/limitations/security docs) and moved root/release-prep working reports into [`research_archive/`](research_archive/INDEX.md). See [`DOCUMENTATION_REORGANIZATION_REPORT.md`](DOCUMENTATION_REORGANIZATION_REPORT.md).

---

## [0.1.0-alpha] — 2026-11-26

### Implemented Architecture
- **Core Semantic Perception & Execution (`src/computer_use_lite/`):**
  - Compact `REV:N` element line map (`Api.line_map()`, default 60-element cap, `filter_query=` drill-down).
  - Browser perception via direct persistent CDP WebSocket (`DirectCdpClient`) querying `DOMSnapshot.captureSnapshot` and `Accessibility.getFullAXTree`, normalized bounds (`border`-box), paint-order occlusion checks, hover trigger detection (`hover.py`), and `elementFromPoint` pre-action verification.
  - Windows UIA desktop engine (`desktop_uia.py`, Windows-only) on a dedicated COM MTA worker thread using `CUIAutomation8` (`AutoSetFocus=0`), `FindAllBuildCache`, UIA pattern fallbacks -> `SendInput`, foreground enforcement, and a 5 px pointer `KillSwitch`.
  - Targeted visual fallback (`blind_gap.py`) emitting cropped PNG regions only when large/sparse `<canvas>` or low-UIA areas are encountered.
  - Revision-checked `Resolver` (`> 2` px drift, modal occlusion, disappearance checks) and SHA-256 + length value redaction in `TaskState` (`state.py`).
  - Backwards-compatibility module aliases preserved under `src/engine/`.
- **MCP Server (`mcp_server.py` / `session_manager.py`):**
  - `stdio` MCP server exposing 13 tools (`open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`) with per-session thread isolation, `ToolAnnotations`, and `fsync=False` option on disposable temp session state.

### Audited Fixes & Safeguards Applied Prior to Preview
- Resolved `P-01` dense-DOM `$O(N^2)` occlusion bottleneck (`824.40 ms -> 19.32 ms` Python CPU `p50` on `2,500`-cell fixture).
- Resolved `P-03` `<input type="search">` -> `searchbox` role mapping and `inspect_element()` read-back.
- Added default private/loopback/link-local SSRF host refusal on initial URL entry in `validate_navigation_url()` (`CUL_MCP_ALLOW_PRIVATE_URLS=1` opt-in).
- Improved `DOMSnapshot` multi-document tag/role extraction (`P-02` localhost fixture) and pruned redundant `<label>`/nested fragments/overflow-clipped nodes (`P-04`).
- Updated `blind_gap.capture_desktop_region()` to prioritize `PrintWindow` before `ImageGrab` when target desktop HWNDs are covered, non-foreground, minimized, or cloaked (`P-09`).
- Fixed Windows Store Notepad tab/PID test reliability, removed pytest return warnings, and prevented default overwrite of `results/e2e/e2e_results.json` (`P-10`).

### Historical Snapshot Notes at `0.1.0-alpha` (`698861d`)
- Cross-origin embeds still dropped inner controls under strict `--site-per-process` and live video embeds prior to `P0-1`.
- HTTP `302` SSRF redirects, missing `#32770` Save As physical commit, multi-tab browser switching, and exact-port `--remote-allow-origins` remained open until post-`0.1.0-alpha` commits (`77cd171..a3291b3`).
- Archived / rejected paths preserved in `experiments/` & `archive/`: browser/desktop grid cursor probing (`H1`, `H1b`, `H2`, `H3`), UIA `CoreAutomationRemoteOperation` (`Exp 5`), single-frame JS extraction (`Exp 6`), and top-frame `MutationObserver` (`Exp 9`).
- The 20-task VLM paired agent benchmark (`benchmarks/bench_agent_20tasks.py`) has deterministic oracle validation only (`0` live VLM API calls executed).

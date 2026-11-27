# Changelog

All notable changes to **Computer Use Lite** are documented in this file.  
Release classification: **Public Research Preview — Experimental — Not Production Ready**.

---

## [0.2.0a0] — 2026-11-27 (Security, Reliability, Portability & Cursor Hardening Release)

> **Scope & Verification Summary:** Implements and empirically verifies remediation across all **`P0`–`P3`**, **Linux portability**, and **Cursor Overlay A–G & Sections 4–5** findings audited against preserved immutable baseline [`v0.1.0a0`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a0) (`0d19a9e`). See [`docs/releases/v0.2.0a0/ENGINEERING_CHANGE_HISTORY.md`](docs/releases/v0.2.0a0/ENGINEERING_CHANGE_HISTORY.md) and [`research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md`](research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md).
> **Honest Limitations:** Live LLM agent evaluation (`Track B1`) is **`NOT_RUN`** (Codex CLI usage quota reached until Dec 26, 2026; `@oai/sky`/API keys absent), interactive hardware hooks inside isolated `exebox` desktops remain **`NOT VERIFIED`**, and Chromium internal socket-level DNS rebinding TOCTOU remains a documented browser-network boundary.

### Security & Privacy (`P0` / `P1` / `P2`)
- **Cross-Frame Compositor Hit-Testing (`CUL-ACC-001` / `F-01`):** Added top-frame `DOM.getNodeForLocation` verification (`_verify_top_frame_hit`, [`browser_cdp.py`](src/computer_use_lite/browser_cdp.py)) rejecting same-origin/cross-origin fixed parent overlays (`0` leak hits in `A01`, `A03`, `s03`) and setting `verification_scope="cross_origin_unprovable"` with `verified=False` when unprovable.
- **Word-Boundary Secret Redaction & Keyed HMAC (`CUL-PRIV-001/002` / `F-02`):** Replaced substring regex with delimited camelCase/token matching (`is_sensitive_name` in [`state.py`](src/computer_use_lite/state.py), `_IS_SENSITIVE_ELEM_JS` in [`browser_cdp.py`](src/computer_use_lite/browser_cdp.py)) covering `card`/`ccnum`/`ssn`/`iban`/`otp`/`autocomplete`, eliminating `address_shipping`/`opinion`/`spinner` false positives, and replacing deterministic secret SHA-256 prefixes with per-process ephemeral keyed HMAC (`hmac:<16hex>`).
- **SSRF Fail-Closed DNS (`CUL-SEC-001` / `F-04`):** Failed closed (`PermissionError`) on `socket.gaierror` or empty `getaddrinfo` results when `CUL_MCP_ALLOW_PRIVATE_URLS != "1"`, plus drift detection across resolved IP caches in `validate_navigation_url()` ([`session_manager.py`](src/computer_use_lite/session_manager.py)). Chromium socket-level DNS TOCTOU remains documented.
- **Disable Unauthenticated Loopback DirectWS by Default (`CUL-SEC-002` / `F-05`):** Changed `_resolve_direct_ws` ([`browser_cdp.py`](src/computer_use_lite/browser_cdp.py)) to default `False` (Playwright Pipe IPC) while keeping `CUL_MCP_DIRECT_WS=1` opt-in (`152.43 ms` vs `367.09 ms` `dense_2500` `p50` tradeoff measured).
- **Desktop Process Blocklist, Dangerous Hotkeys & Untrusted UI Framing (`CUL-SEC-003/004/005`):** Added default refusal for terminals, password managers, credential brokers, and elevated admin tools (`validate_desktop_target`), blocked `Win`/`Alt+Tab`/`Alt+F4`/`Ctrl+Esc`/`Ctrl+Shift+Esc`/`Ctrl+Alt+Del` (`validate_key_spec`, with Arabic layout ASCII VK fallback), and enforced `[UNTRUSTED_UI_TEXT]` delimiting + control-char/pipe stripping (`sanitize_ui_text` in [`state.py`](src/computer_use_lite/state.py), [`mcp_server.py`](src/computer_use_lite/mcp_server.py)).

### Truthful Verification, Cursor System & Windows Desktop (`P0` / `P1` / `P3`)
- **Truthful Target-Bound Verification + Full-Body Text Hashing (`CUL-ACC-002`):** Added `_target_signature()` (`DOM.resolveNode` + `Runtime.callFunctionOn`), `state.verify(before, after, action=...)` rejecting focus-only no-ops (`focus_only_noop`) and `<input readonly>` edits (`readonly_target_noop`), and `_DIGEST_TEXT_JS` full `innerText` FNV-1a digesting past 400 chars (`b11`).
- **Cursor Overlay Hardening & Physics Upgrade (`CUL-CUR-001..010` / `F-03`):** Excluded Shadow DOM cursor wake canvases from `opaque_canvas` detection (`0` blind crops), added `busyDelayMs=350`, `errorResetMs=900` auto-revert, multi-click pulse/ripple scheduling, `±5.0 deg` post-spring tilt clamp, `document.hidden` `rAF` short-circuit (`2.3 ms`), single-per-document `Page.addScriptToEvaluateOnNewDocument` caching (`48,234 B -> 0 B` nav eval), plus opt-in `CUL_TAKEOVER_GLOW` & interrupt guard ([`cursor_overlay.py`](src/computer_use_lite/cursor_overlay.py), [`desktop_cursor_overlay.py`](src/computer_use_lite/desktop_cursor_overlay.py), [`takeover_guard.py`](src/computer_use_lite/takeover_guard.py)).
- **Desktop UIA Occlusion, Fail-Closed `KillSwitch`, Explorer Tabs & RTL `PrintWindow` (`CUL-DESK-001..005` / `F-06..F-08`):** Wired Win32 Z-order & DWM cloaking check into `DesktopSession.verify_fresh`, enforced fail-closed `KillSwitch.ensure_armed`, excluded inactive File Explorer lower-Z `ShellTabWindowClass` subtrees (`_inactive_explorer_tab_hwnds`), mirrored `WS_EX_LAYOUTRTL` `PrintWindow` bitmaps before cropping (`_capture_hwnd_printwindow`), and added `RLock` + `atexit` `_restore_screenreader_state`.

### Portability, Capabilities & Benchmark Publication (`P2` / `P3`)
- **Cross-Platform Linux Import & Locked Dependencies (`CUL-DX-001/002`):** Guarded top-level Win32 `ctypes`/`comtypes` imports ([`snapshot.py`](src/computer_use_lite/snapshot.py), [`desktop_uia.py`](src/computer_use_lite/desktop_uia.py), [`desktop_cursor_overlay.py`](src/computer_use_lite/desktop_cursor_overlay.py)), added `psutil>=6.0` to `[dev]`, generated `requirements-lock.txt`, and verified real **WSL2 `kali-linux` (`Python 3.14.7`)** import alongside GitHub Actions `test-linux-portability`.
- **Capabilities & Adaptive Latency (`CUL-ACC-003` / `CUL-PERF-001`):** Added rich AX metadata in `inspect`, lossless `<input type=date>` prototype fill, sticky-header safe click offset shifting, continuous `drag` & `read_page` (preserving 13 MCP tools), semantic role tie-breaking in `Resolver`, `SessionManager` idle TTL reaping, and adaptive `hover_and_diff` (`387.39 ms -> 90.83 ms` p50, **4.3x faster**).
- **Comparative Benchmarks & Updated TSX Visuals (`FIG-06`, `FIG-08`–`FIG-11`):** Track A `2/32 -> 32/32`, Track B2 MCP replay `12/18 -> 18/18`, Windows 11 full `pytest` `95 passed, 0 failed` (`79 passed, 16 deselected` with `CUL_SKIP_DESKTOP=1`), plus original white TSX/SVG research figures `FIG-10` & `FIG-11`.

---

## [0.1.0a2] — 2026-11-27 (Benchmark Research Edition + Windows MCP Setup)

> **Scope Notice:** Updates the `v0.1.0a1` research-publication state cleanly while keeping previously pushed tags `v0.1.0a0` (`0d19a9e`) and `v0.1.0a1` (`566f08d`) immutable. **Core runtime engine behavior matches `0d19a9e`** (only `src/computer_use_lite/__init__.py` `__version__` fallback updated to `"0.1.0a2"`). Audited runtime security/reliability issues (`F-01`–`F-08` in [docs/SECURITY_AND_LIMITATIONS.md](docs/SECURITY_AND_LIMITATIONS.md)) remain **open and NOT FIXED**.

### Added & Fixed
- **FIG-01 Visual Clarity Fix (`Fig01BrowserSuccess.tsx`, `SvgPrimitives.tsx`, `FigureFrame.tsx`):** Separated the `95% Wilson CI` whisker cleanly below each bar (eliminating collision between the `100%` rounded emerald corner and right CI cap), updated the `95% Wilson CI` legend icon from a square box to a crisp `|—●—|` whisker glyph, replaced `"Arm A"` shorthand with `"Playwright MCP"` / `"Playwright"` across `FIG-01`/`FIG-03`/`FIG-04`, wired SVG/cover version labels dynamically to `benchmark_data.json#release_version`, and re-exported all 9 SVGs + 2x PNGs (`v0.1.0a2`).
- **Windows MCP Guided Installer & Docs:** Added [`docs/WINDOWS_MCP_SETUP.md`](docs/WINDOWS_MCP_SETUP.md) (indexed in [`docs/INDEX.md`](docs/INDEX.md) and [`README.md`](README.md)), [`scripts/setup_mcp_windows.bat`](scripts/setup_mcp_windows.bat), [`scripts/merge_mcp_configs.ps1`](scripts/merge_mcp_configs.ps1), [`scripts/configure_mcp.py`](scripts/configure_mcp.py), and [`tests/test_mcp_setup_config.py`](tests/test_mcp_setup_config.py) to install `.venv` with `.[setup]` (`tomlkit>=0.12` documented in [`pyproject.toml`](pyproject.toml) and [`NOTICE`](NOTICE)) and atomically merge/back up `computer_use_lite` MCP config entries for Codex, Antigravity, and Claude Code.
- **License Header Audit Coverage (`scripts/verify_copyright_headers.py`):** Refactored `#`-comment header checks into a shared helper covering `.ps1`/`.psm1`/`.sh` alongside `.py`, excluded `.bat` installer wrappers cleanly under `LICENSE`/`NOTICE`, and added `tomlkit` verification in `NOTICE`.

---

## [0.1.0a1] — 2026-11-27 (Benchmark Research Edition)

> **Scope Notice:** `0.1.0a1` is a research-publication, visualization, branding, and documentation release branching cleanly from historical baseline `v0.1.0a0` (`0d19a9e`). **Core runtime engine behavior is unchanged** (aside from read-only `__version__` metadata in `src/computer_use_lite/__init__.py`). Previously audited runtime security/reliability issues (`F-01`–`F-08` in [docs/SECURITY_AND_LIMITATIONS.md](docs/SECURITY_AND_LIMITATIONS.md)) remain **open and NOT FIXED** in this release.

### Added — Research Data, Original TSX Visuals, Brand Identity & Documentation
- **Canonical Benchmark Dataset ([`research_archive/benchmark_publication/`](research_archive/benchmark_publication/)):** Published single-source JSON datasets (`benchmark_data.json`, `benchmark_sources.json`) plus methodology, comparison, and limitation specs synthesized from the 72-run `fdc92d9` Playwright-vs-CUL browser comparison, observation-size evaluations, Windows 11 `0d19a9e` test/UIA audits, and supervised Desktop Pilot v1 manifests.
- **Isolated TSX/React SVG Visualization Suite ([`research_visuals/benchmark_report/`](research_visuals/benchmark_report/)):** Created an isolated TypeScript/React/SVG workspace (zero Python runtime dependencies) implementing `FIG-01` through `FIG-09` plus the `CulCover.tsx` GitHub social preview, exporting SVG + 2x PNG assets and `figures_manifest.json` under [`docs/assets/benchmarks/`](docs/assets/benchmarks/figures_manifest.json).
- **Official SVG Logo ([`docs/assets/brand/logo.svg`](docs/assets/brand/logo.svg)):** Integrated the owner-supplied `64×64` SVG mark verbatim (verified well-formed XML, zero scripts or external URIs) across the `README.md`, social cover preview, and exported benchmark figures.
- **Canonical Benchmark & Security Documentation:** Added [`docs/BENCHMARK_COMPARISON.md`](docs/BENCHMARK_COMPARISON.md), [`docs/BENCHMARK_METHODOLOGY.md`](docs/BENCHMARK_METHODOLOGY.md), and [`docs/SECURITY_AND_LIMITATIONS.md`](docs/SECURITY_AND_LIMITATIONS.md); updated [`docs/INDEX.md`](docs/INDEX.md) and [`README.md`](README.md); added sanitized synthetic Windows audit captures (`docs/assets/evidence/`).
- **Version Metadata & CI Hygiene:** Aligned `pyproject.toml`, `CITATION.cff`, `src/computer_use_lite/__init__.py` (`__version__` via `importlib.metadata` with `"0.1.0a1"` fallback), `.gitignore`, and `scripts/verify_copyright_headers.py` (`.ts`/`.tsx`/`.mjs`/`.js` header audit + `node_modules` exclusion).

### Mandatory Evidence & Limitation Disclosures
- **Historical vs Current Evidence Separation:** `0.1.0a0` (`0d19a9e`) historical release notes were NOT retroactively altered; post-`0.1.0a0` audit and benchmark artifacts belong strictly to `0.1.0a1`.
- **Browser MCP Confounds (`fdc92d9`, `72` runs):** `b11_dense_90_grid_filter` exposed CUL's `filter_query` hint in both arms' shared prompts, Playwright MCP called `browser_run_code_unsafe` once on `b12` run 1, and CUL used `~40.0%` higher median total tokens (`176,506` vs `126,087`), `50%` more median steps (`4.5` vs `3.0`), and `+1.5%` slower median wall time (`26.87s` vs `26.48s`). Not a Native OpenAI Computer Use benchmark.
- **Observation Proxy (`112` vs `1,196` est. tokens):** `round(text_length / 4)` reflects single-step payload estimates on fixtures, NOT actual API provider billing.
- **Desktop Pilot Incomplete:** `CUL T1` recorded `2/2` passing trials; `CUL T2` was incomplete and Native-vs-CUL desktop benchmarking was not completed.

---

## [0.1.0a0] (`0.1.0-alpha` historical baseline @ `0d19a9e`) — 2026-11-26

> Preserved exact historical Git tag `v0.1.0a0` at commit `0d19a9e12527ed12f5020709ea660c169b23e76d` (including historical Workstream A Cursor Overlay, Phase 1 `P0-1..P0-5`, and CI/Playwright compatibility fixes verified in the repository prior to the `0.1.0a1` benchmark publication).

### Original Unreleased Notes Preserved Below (`0.1.0-alpha` through pre-public `d47b4e9` / public `0d19a9e`)

> Note: Source and regression test commits below landed on `main` after the `698861d` (`0.1.0-alpha`) documentation baseline (`7c7b9b4..d47b4e9`). No aggregate full-suite `pytest` count for `d47b4e9` was executed during that earlier documentation consolidation pass.

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

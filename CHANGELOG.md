# Changelog

All notable changes to **Computer Use Lite** are documented here.
Release classification: **Public Research Preview — Experimental — Not Production Ready**.

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

### Documented Unresolved Limitations & Rejected Paths
- Cross-origin embeds still drop inner controls under Chrome strict site isolation (`--site-per-process` and live third-party video/ad frames).
- HTTP `302` redirects after initial `validate_navigation_url()` approval and Chromium-internal DNS rebinding remain open against adversarial web targets.
- Windows `#32770` Save As dialogs can desynchronize between `IValueProvider::SetValue` and `IFileSaveDialog`; multi-tab `target="_blank"` browser sessions lack tab switching; `desktop_uia.py` / `snapshot.py` restrict cross-platform Linux imports.
- Archived / rejected paths preserved in `experiments/` & `archive/`: browser/desktop grid cursor probing (`H1`, `H1b`, `H2`, `H3`), UIA `CoreAutomationRemoteOperation` (`Exp 5`), single-frame JS extraction (`Exp 6`), and top-frame `MutationObserver` (`Exp 9`).
- The 20-task VLM paired agent benchmark (`benchmarks/bench_agent_20tasks.py`) has deterministic oracle validation only (`0` live VLM API calls executed).

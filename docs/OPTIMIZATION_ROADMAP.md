# Optimization Roadmap (`d47b4e9` Historical Baseline Snapshot)

> [!NOTE]
> **Superseded Snapshot Notice:** This roadmap preserves the phase plan established at `d47b4e9` (`0.1.0-alpha`). Most **`P1`** and **`P2`** items listed below (`P1-1` AX metadata, `P1-2` sticky-header offsets, `P1-4` RTL un-mirroring, `P1-5` Explorer tab/dedup filtering, `P2-1` Linux import safety, and `P2-3` `drag`/desktop Z-order occlusion/`hover`) have since been implemented in `v0.2.0a0` (`9bc5e97`) and `[Unreleased]` — see [`CHANGELOG.md`](../CHANGELOG.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) for current shipped vs. open boundaries.

This roadmap tracks the original performance, discovery, desktop, security, and evaluation tracks for **Computer Use Lite (`computer-use-lite`)**, consolidated from [FIX_PLAN.md](../research_archive/audits/2026-11-26-fix-plan.md) (`P-01..P-24`) and `research_trace/2026-11-26/OPTIMIZATION_PLAN.md` *(local-only, excluded from public git)* (`P0 -> P1 -> P2`).

> [!IMPORTANT]
> **Implementation Boundary Rule:** Items marked **Completed** or **Implemented in `src/`** exist in `HEAD` (`d47b4e9`). Items under **`P1`**, **`P2`**, or **Rejected** are **NOT implemented** — do not cite them as shipped functionality.

---

## Status Legend

- **Completed (Verified):** Shipped in `src/` and regression-verified on its cited commit baseline.
- **Implemented (`src/` + Tests; Unverified Live):** Landed in `HEAD` (`d47b4e9`) with unit/fixture tests passing at commit time, awaiting restarted live interactive MCP stress verification or full-suite `d47b4e9` re-run.
- **Proposal (`Unimplemented`):** Designed in research dossiers; zero code changes exist in `src/`.
- **Rejected:** Empirically dropped based on benchmark/experiment gates.

---

## 1. Pre-`0.1.0-alpha` Audit Fixes (`P-01..P-10`, `P-19b`, Completed at `698861d`)

| ID | Summary | Commit / Evidence | Status |
| :--- | :--- | :--- | :--- |
| `P-01` | Defer `is_occluded_in_snap()` to interactive candidates (`2,500`-cell Python `p50`: `824.40 -> 19.32 ms`) | `319382c` / `test_audit_fixes.py:123` | **Completed** |
| `P-03` | Map `<input type="search">` -> `searchbox` (`click,type` + `inspect` `read_value()`) | `P-03` / `test_audit_fixes.py:89` | **Completed** |
| `P-04` | Collapse `<label for=...>` & duplicate wrappers; ancestor `overflow` scroll-box clipping (`DualOriginCorpusServer` `1.0/1.0`) | `d0c4132` / `test_audit_fixes.py:327` | **Completed** *(gap remains around `button`/`clickable` wrappers -> see `P1-1`)* |
| `P-06` | `state_fsync=False` option for disposable MCP scratch `TaskState` (`6.10 -> 2.94 ms` state write) | `P-06` / `test_audit_fixes.py:193` | **Completed** |
| `P-09` | Prioritize `PrintWindow` before `ImageGrab` when `hwnd` is covered, non-foreground, minimized, or cloaked | `6a2f0fb` / `M1 #5` `WinSta0\Default` Settings crop | **Completed** *(RTL mirroring unfixed -> see `P1-4`)* |
| `P-10` | Store Notepad tab/title polling, kill child owning PID, eliminate pytest warnings & tracked `e2e_results.json` overwrite | `P-10` / `test_audit_fixes.py:289` | **Completed** |
| `P-19c` | Initial non-password plaintext leak warning disproved (`state.py` already SHA-256 redacts all non-`None` values) | `M0` audit / `state.py` | **NOT-REPRODUCED (Already Safe)** |

---

## 2. Workstream A — Cursor Overlay (`7c7b9b4..d47b4e9`)

| Unit | Summary | Evidence / Caveat | Status |
| :--- | :--- | :--- | :--- |
| Browser CSP-safe 3D Overlay | `cursor_overlay.py` (`64x64` Obsidian-Chrome vector registry, DOM+SVG bridge, `CUL_AGENT_CURSOR`, `CUL_AGENT_CURSOR_GLIDE_MS`) | `7c7b9b4`, `tests/test_cursor_overlay.py` | **Implemented in `src/`** *(pre-commit full-suite re-run at `d47b4e9` pending)* |
| Desktop `60 Hz` Layered Overlay | `desktop_cursor_overlay.py` (`WS_EX_LAYERED\|TRANSPARENT\|TOPMOST\|NOACTIVATE`, `_WDA_EXCLUDEFROMCAPTURE`, zero `SendInput` glides, `bring_window_to_front`) | `e3d0bd5`, `4f9bcef`, `d47b4e9` (`tests/test_cursor_overlay.py` locally `M` dirty; z-order test requires `Default` desktop) | **Implemented in `src/`** *(live interactive z-order re-run pending)* |
| MCP Headful Toggle & Outcome Cues | `CUL_MCP_HEADFUL` (`open_browser` `headless=None`), `HEADLESS:`/`CURSOR:` headers, `server_pid`+`headful_default`, `ok` vs `verified` visual cues | `5c0a01e`, `4f9bcef` (`mcp_server.py`, `api.py`) | **Implemented in `src/`** |

---

## 3. Phase 1 `P0` Correctness & Security (`77cd171..a3291b3`)

| Unit | Summary | Evidence & Remaining Boundary | Status |
| :--- | :--- | :--- | :--- |
| `P0-1` (`77cd171`) | Deterministic `--site-per-process` cross-origin OOPIF ground-truth discovery (`1.0` recall) & action verification test | `test_p0_1_site_per_process_oopif_discovery_gt_and_actions` (`tests/test_audit_fixes.py:421`). Direct `Target.setAutoAttach` flattened `AXTree` OOPIF demux was deferred; live third-party embeds (`youtube.com/embed`) remain unverified on restarted MCP. | **Fixture-Verified / Unverified Live on Public Embeds** |
| `P0-2` (`bee026e`) | Playwright context multi-tab tracking + MCP `navigate(list_tabs \| switch_tab \| close_tab, tab_index)` + cursor overlay continuity | `test_p0_2_*` & `test_mcp_multi_tab_target_blank_lifecycle` | **Implemented (`src/` + Unit/MCP Tests); Live MCP Stress Re-Run Pending** |
| `P0-3` (`16465bf`) | Win32 `#32770` Save As filename physical commit (`_commit_dialog_text`) + `DIALOG_ALERT:` static text surfacing | `test_p0_3_win32_save_as_commit_and_dialog_alerts` (`desktop_uia.py`, `api.py`) | **Implemented (`src/` + Fixture Test); Live Store Notepad Save Re-Run Pending** |
| `P0-4` (`965eb66`) | CDP `Fetch` request & `3xx` redirect SSRF blocking + IPv4-mapped/6to4/Teredo/NAT64 normalization (`validate_navigation_url`) | `test_p0_4_ssrf_redirects_ipv6_normalization_and_route_block`. **Open limit:** DNS-rebinding TOCTOU between Python pre-check and Chromium socket connect remains. | **Implemented (`src/` + Unit Test); DNS TOCTOU Open** |
| `P0-5` (`a3291b3`) | Exact-port `--remote-debugging-address=127.0.0.1` + `--remote-allow-origins=http://127.0.0.1:<port>` + `CUL_MCP_DIRECT_WS=0` gate | `test_p0_5_cdp_remote_debugging_origin_security_gate`. Same-host originless loopback clients can still access `/json/version` when `DirectWS=True`. | **Implemented (`src/` + Security Gate)** |

---

## 4. Phase 2 — `P1` Fidelity, Desktop & Telemetry (`[PROPOSAL — UNIMPLEMENTED]`)

Consists of unimplemented designs synthesized in ``research_trace/2026-11-26/OPTIMIZATION_PLAN.md`` (`research_trace/2026-11-26/OPTIMIZATION_PLAN.md`, local-only):

| ID | Proposed Change | Target Problem | Status |
| :--- | :--- | :--- | :--- |
| **`P1-1` (`U2`)** | Zero-RPC AX metadata extraction (`combobox.value`, `<option>` items, `slider` min/max/value, `checked`, `readonly` refusal), W3C `<style>`/`<script>` AccName skip (`T12`), and `<label>` pruning for `button`/`clickable` (`M1 #1`) | `HT2` `6/6` checkbox `verified=false`, `<input readonly>` `verified=true` FP, Polymer `.css-build` text leaks | **Proposal (`Not Implemented`)** |
| **`P1-2` (`U3`)** | Unified viewport-clamped click target `_visible_click_point()` across occlusion, `verify_fresh`, and `_center()` | Negative-`y` sticky-header boundary straddlers (`T13`, `P-15`) | **Proposal (`Not Implemented`)** |
| **`P1-3`** | Align `navigate(auto_discover=True)` wait semantics (`wait_until="load"` + layout settle) | Dynamic page zero-element race on `navigate` (`P-14`, `HT3`) | **Proposal (`Not Implemented`)** |
| **`P1-4`** | Un-mirror `PrintWindow` DIB output when `GWL_EXSTYLE & WS_EX_LAYOUTRTL (0x00400000)` + `exebox` `GetThreadDesktop` diagnostic warning (`P-12`) | Mirrored RTL Store Notepad screenshots (`M1 #6`); `exebox` silent `[]` window confusion | **Proposal (`Not Implemented`)** |
| **`P1-5`** | Scope `CabinetWClass` (Win11 File Explorer) to active visible `SHELLDLL_DefView` HWNDs (`P-08`) + deduplicate identical `<canvas>` blind boxes (`T07`, `M1 #3`) | Multi-tab Explorer inactive-tab item bleed & duplicate canvas crops | **Proposal (`Not Implemented`)** |
| **`P1-6`** | Populate `FastMCP` `serverInfo.version` (`pkg+git_short_sha`), `list_sessions()` target sync, and fail-closed `KillSwitch` initialization (`P-19d`) | Stale server detection & initial `GetCursorPos` `OSError` nuance | **Proposal (`Not Implemented`)** |

---

## 5. Phase 3 — `P2` Portability, Input & Live Agent Evaluation (`[PROPOSAL — UNIMPLEMENTED]`)

| ID | Proposed Change | Target Problem | Status |
| :--- | :--- | :--- | :--- |
| **`P2-1` (`P-11`)** | Lazy-guard `ctypes.WinDLL("user32"/"kernel32")` in `snapshot.py`, `desktop_uia.py`, and `session_manager.py` behind `sys.platform == "win32"` | Enables Linux/macOS browser + MCP server imports | **Proposal (`Not Implemented`)** |
| **`P2-2` (`P-07`)** | Batch CSS `:hover` box/attribute lookup inside JS (`_HOVER_TRIGGER_JS`) instead of `4*K` serial CDP round trips | `25.2 ms` overhead on CSS-heavy stylesheets | **Proposal (`Not Implemented`)** |
| **`P2-3`** | `<input type="date">` ISO value fill (`T01`, `M1 #4`), continuous mouse `drag` primitive (`T06`), desktop Z-order overlap check in `verify_fresh`, opt-in post-`act` compact `rediscover` option, and `hover.py` `known_before` count fix (`T09`) | Date input corruption (`02/02/61201`), slider/canvas drag support, multi-step discover turn share | **Proposal (`Not Implemented`)** |
| **`P2-4` (`P-18`)** | Run full paired live 20-task VLM evaluation (`benchmarks/bench_agent_20tasks.py`) across commercial/open models (`prompt_tokens` vs `screenshot_baseline`) + run full `d47b4e9` interactive `WinSta0\Default` regression suite | Closes **`0` live VLM run** gap and verifies post-P0/Overlay live behavior | **Unverified / Pending Execution** |

---

## 6. Permanently Rejected / Archived Items (`DO NOT BUILD`)

| Candidate | Reason Rejected | Archive Link |
| :--- | :--- | :--- |
| **Browser & Desktop Cursor Grids (`H1`, `H1b`, `H2 2B`, `H3`)** | `H1b` `sync=14.93 s`, `pipe_80=34.4%` agreement; `H2` invalidated by `(0, 87)` px offset and Notepad zero-hand signal; superseded by `blind_gap` crops | [../results/experiments/](../results/experiments/h1b_report.md), [../archive/stale_h2_grid/](../archive/stale_h2_grid/h2_report.md) |
| **`CoreAutomationRemoteOperation` Subtree Walk (`Exp 5` / `P-21`)** | Stops at cross-process / child HWND boundaries (`0.0179` Notepad / `0.0286` Chromium recall) | [../results/perf_study/BENCHMARK_REPORT.md](../results/perf_study/BENCHMARK_REPORT.md) |
| **Single-Frame JS Extractor (`Exp 6`) & Top-Frame `MutationObserver` (`Exp 9`)** | Drops closed Shadow DOM & OOPIF (`0.3812` GitHub recall JS; `0.8421` corpus recall MO) | [../results/perf_study/BENCHMARK_REPORT.md](../results/perf_study/BENCHMARK_REPORT.md) |
| **Standalone `verify_fresh` + `perform` Probe Merge (`P-05`, `-5.25 ms`)** | `< 0.2%` of multi-second LLM turns (`0` turns saved); deferred unless combined cleanly with future `DirectCdpClient` multiplexing (`P1`/`P-13`) | [Engine Audit Report](../research_archive/audits/2026-11-26-engine-audit-report.md) |

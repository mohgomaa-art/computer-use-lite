# Research History & Development Chronicle

Computer Use Lite evolved across five empirical phases spanning exploratory cursor-grid probing, a 9-experiment performance study, independent audits and live stress tests, principal full-stack root-cause analysis, and Workstream A + `P0-1..P0-5` hardening (`HEAD` `d47b4e9`). Negative results and superseded runs remain documented here and inside [../research_archive/INDEX.md](../research_archive/INDEX.md).

---

## Phase 1 — Exploratory Cursor Probing (`H1`, `H1b`, `H2`, `H3`)

Early experiments tested whether cursor transitions (`ARROW` -> `HAND` / `IBEAM`) could reconstruct clickable UI grids without structural trees:
- **`H1` ([`results/experiments/h1_report.md`](../results/experiments/h1_report.md)):** `880` Google Maps probes took `29.46 s` (`81.8%` hit rate) — far too slow.
- **`H1b` ([`results/experiments/h1b_report.md`](../results/experiments/h1b_report.md)):** Corrected non-rAF `sync` took `14.93 s`, while pipelined `pipe_80` (`0.77 s`) collapsed to `34.4%` agreement -> **REJECTED / DROPPED**.
- **`H2` ([`archive/stale_h2_grid/`](../archive/stale_h2_grid/h2_report.md), [`results/experiments/h2_gate0.json`](../results/experiments/h2_gate0.json)):** First grid sweep invalidated by a `(0, 87)` px browser-chrome offset bug; `Gate 0` calibrated `50 ms` canvas settle (`hand_rate=1.0, dead_fp=0.0`) vs arrow-only Win11 Notepad (`hand_rate=0.0`), while full Gate 2B grid scan was **DROPPED**.
- **`H3` ([`results/experiments/h3_report.md`](../results/experiments/h3_report.md)):** Never constructed (`NOT BUILT`).

---

## Phase 2 — Architecture & 9-Experiment Optimization Study (`results/perf_study/`)

See [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md) and [`BENCHMARK_REPORT.md`](../results/perf_study/BENCHMARK_REPORT.md):
- **Adopted (`KEEP`):** Dedicated UIA COM `MTA` worker (`AutoSetFocus=0`), 2-call `DOMSnapshot + AXTree` ablation (`Exp 6`), direct `DirectCdpClient` WebSocket (`Exp 7`), and targeted `verify_fresh()` validation (`Exp 8`, disclosing the `fsync` confound).
- **Rejected (`DROP`) / Deferred (`HOLD`):** Dropped `Cached HWND Root`, `NoBounds + N+1`, `Explicit RawView`, and `AutomationElementMode.None` for actions; held `CoreAutomationRemoteOperation` (`Exp 5`), `One-Call JS Extractor` (`Exp 6`), `OrCondition` (`Exp 3`), and top-frame `MutationObserver` (`Exp 9`).

---

## Phase 3 — Audits, Live Stress Testing & Skill Evaluation (`P-01..P-24`, `T01–T18`, `M5`)

- **Engine Audit & M0–M6 Fix Pass:** Identified `P-01..P-24` ([Archived Engine Audit](../research_archive/audits/2026-11-26-engine-audit-report.md)); resolved `P-01` dense DOM `O(N^2)` occlusion (`824.40 -> 19.32 ms`), `P-03` `searchbox`, `P-04` corpus pruning (`1.0/1.0` on localhost dual-origin fixture), `P-06` `fsync=False` scratch state, `P-09` `PrintWindow` ordering, `P-10` Store Notepad test hygiene, and refuted `P-19c` (`TaskState` already SHA-256 redacts all values) ([Archived Fix Report](../research_archive/audits/2026-11-26-fix-report.md)).
- **Live MCP Stress Run Forensics (`PID 4076` vs `PID 18036`):** Live tasks `T01–T18` (`8 PASS, 9 PARTIAL, 1 FAIL` in [Archived Stale-PID Run Report](../research_archive/live_runs/2026-11-26-run-report-stale-pid-4076.md)) executed against stale pre-fix `PID 4076` (`10:06:13`); follow-up `M1` probes and `M5` skill evaluations on restarted `PID 18036` (`14:02:29`) verified `P-09` on `Settings` while confirming live public OOPIF blindness (`youtube.com/embed`), `#32770` Save As UIA desync, and `WS_EX_LAYOUTRTL` mirroring (``skill_updates/2026-11-26_final/`` (`skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md`, local-only)).
- **Agent Harness & Release Baseline (`698861d`):** Built `benchmarks/bench_agent_20tasks.py` (`20/20` deterministic oracle validation, `0` VLM runs), executed attribution & secret scans, and created initial `v0.1.0-alpha` docs (`698861d`).

---

## Phase 4 — Principal Trace, Workstream A Cursor Overlay & Phase 1 `P0` Hardening (`3e67e49..d47b4e9`)

1. **Full-Stack Root-Cause Trace (``research_trace/2026-11-26/`` (`research_trace/2026-11-26/OPTIMIZATION_PLAN.md`, local-only)):** Synthesized `S1.1..S8.3` into `P0` / `P1` / `P2` plans anchored to primary W3C/CDP/Playwright/Microsoft Learn citations.
2. **Workstream A — Obsidian-Chrome 3D Cursor Overlay (`7c7b9b4`, `5c0a01e`, `e3d0bd5`, `4f9bcef`, `d47b4e9`):** Built non-interfering CSP-safe Chromium SVG overlay (`cursor_overlay.py`), dedicated `60.0 Hz` Win32 layered capture-excluded desktop overlay (`desktop_cursor_overlay.py`), `CUL_MCP_HEADFUL` / `CUL_AGENT_CURSOR` toggles, `HEADLESS:`/`CURSOR:` headers, outcome cues separating `ok` from `verified`, and transient Win11 UIA initialization `COMError` retry (`d47b4e9`).
3. **Phase 1 `P0-1..P0-5` (`77cd171..a3291b3`):** Added deterministic `--site-per-process` OOPIF verification (`P0-1`), Playwright context multi-tab `list_tabs`/`switch_tab`/`close_tab` (`P0-2`), `#32770` Save As `_commit_dialog_text` + `DIALOG_ALERT:` (`P0-3`), CDP `Fetch` redirect/sub-request SSRF guard + IPv6 normalization (`P0-4`), and exact-port `--remote-allow-origins` + `CUL_MCP_DIRECT_WS=0` (`P0-5`). `P1` and `P2` remain unimplemented ([OPTIMIZATION_ROADMAP.md](OPTIMIZATION_ROADMAP.md)).
4. **Documentation Consolidation:** Unified current docs under `docs/` and archived historical root/release-prep working reports under [../research_archive/INDEX.md](../research_archive/INDEX.md).

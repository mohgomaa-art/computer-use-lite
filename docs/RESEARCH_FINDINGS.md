# Research Findings

This document consolidates the core empirical conclusions of **Computer Use Lite (`computer-use-lite`)** across its experimental waves, including **negative results, invalidated runs, confounds, and open confidence boundaries**.

For evidence tag definitions and proxy disclosures, see [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md). Raw artifacts remain preserved and indexed in [../research_archive/INDEX.md](../research_archive/INDEX.md).

---

## Finding 1 — Visual Cursor-Grid Probing Cannot Replace Structural UI Discovery
- **Research Question:** Can probing cursor-shape transitions (`ARROW` -> `HAND` / `IBEAM`) across a pixel grid recover clickable UI on opaque canvases and Windows desktops fast and accurately enough for agent loops?
- **Method:** `H1` (`880`-point Google Maps canvas grid, step `32` px), `H1b` (`raf` vs `NO_RAF_PROBE_JS` `sync` vs pipelined `pipe_20`/`pipe_80`), `H2 Gate 0` + `H2 2B` (Win32 `GetCursorInfo` + `SendInput` across Chrome, canvas, and Notepad), and `H3` conditional visual hover diff ([experiments/](../experiments/), [results/experiments/](../results/experiments/)).
- **Result (`[MEASURED]`):**
  - `H1`: `81.8%` recall/precision across `880` probes took `29.46 s` (`33.5 ms/probe`) with viewport/control-denominator skew.
  - `H1b`: Corrected synchronous `NO_RAF_PROBE_JS` halved runtime to `14.93 s` (`16.97 ms/probe`, `100%` agreement), still ~5x slower than the `< 3.0 s` interactive gate; async CDP pipelining (`pipe_80` = `0.77 s`) collapsed agreement to `33.5%–34.4%` due to Chromium event coalescing.
  - `H2`: Initial Gate 0 / 2B (`26.7%/73.3%/53.3%`, `12.24 s`) was **invalidated** by a `(0, 87)` px browser-chrome offset ([`archive/stale_h2_grid/`](../archive/stale_h2_grid/)). Subsequent Gate 0 (`results/experiments/h2_gate0.json`) unlocked on canvas (`hand_rate=1.0, dead_fp=0.0, 50 ms` settle) while Win11 Notepad controls kept arrow cursors (`hand_rate=0.0, uia_recall=1.0`). No post-fix `H2 2B` grid ran; `H3` stayed `NOT BUILT`.
- **Confidence & Current Relevance:** **High (`[MEASURED]`)** — browser & desktop grid probing is permanently **REJECTED / DROPPED** in favor of structural `DOMSnapshot+AX` + UIA + targeted `blind_gap` image crops (`opaque_canvas`, `low_uia`).

---

## Finding 2 — Windows UIA Performance & Correctness Depend on COM `MTA` + `AutoSetFocus=0`, Not `RemoteOperations` or `RawView`
- **Research Question:** Which Win32 UIA threading model, tree scope, cache configuration, and IPC transport minimize discovery and action latency without losing control recall?
- **Method:** Isolated controlled experiments `Exps 1–5` (`benchmarks/run_all.py`, `benchmarks/bench_uia.py`, `benchmarks/bench_remote_ops.py`) on Win11 Notepad, File Explorer, Chromium, and Electron with SHA-256 engine immutability verification (`engine_untouched: true`).
- **Result (`[MEASURED]`):**
  - **Threading (`Exp 1`):** Dedicated COM `MTA` eliminated cold `STA` hangs (`446.03 ms` Notepad / `861.06 ms` Explorer -> `52.63 ms` / `162.58 ms`), while caching HWND roots added warm overhead (`69.69` vs `66.88 ms`).
  - **Focus Sync (`AutoSetFocus=0`):** Disabling `IUIAutomation2.AutoSetFocus` eliminated a `~2,000 ms` per-action Notepad `ValuePattern.SetValue` stall (`2,014.3 ms -> 1.71 ms`).
  - **TreeScope & Cache (`Exps 2–4`):** Default `ControlView` balanced coverage cleanly; `Explicit RawView` bloated Chromium (`66 -> 254` nodes, `0.4043` precision); dropping cached `BoundingRectangle` inflated IPCs (`2–3 -> 37–143`); `AutomationElementMode.None` forced `+6.51–38.79 ms` `RuntimeId` re-acquisition per action.
  - **`CoreAutomationRemoteOperation` (`Exp 5`):** Sped up homogeneous `K=30` batch reads (`25.12 -> 7.12 ms` Electron), **but** `RemoteOp::Navigate` halted at child HWND/process boundaries (`0.0179` Notepad / `0.0286` Chrome subtree recall).
- **Limitations & Relevance:** **High (`[MEASURED]`)** — `DesktopSession` locks `MTA` + `ControlView` + `AutoSetFocus=0` + `FindAllBuildCache`, permanently rejecting `RemoteOperations` for full subtree discovery. File Explorer (`CabinetWClass`) background DirectUI tab bleed remains an open `P1` issue (`P-08`).

---

## Finding 3 — 2-Call `DOMSnapshot+AXTree` Over `DirectCdpClient` Beats Single-Frame JS Extractors on Non-Trivial DOMs
- **Research Question:** Can single-script DOM JS extraction or `MutationObserver` incremental tracking replace full `DOMSnapshot + AXTree` calls cleanly, and how much overhead comes from Python occlusion vs CDP transport?
- **Method:** `Exps 6, 7, 9` (`benchmarks/bench_browser.py`), `DualOriginCorpusServer` (`open/closed Shadow DOM`, drawers, modal occlusion, overflow scroll, cross-origin iframe), real websites (`vs_control`), and `P-01`/`P-04` audit regressions (`tests/test_audit_fixes.py`).
- **Result (`[MEASURED]`):**
  - **JS Extractor vs CDP (`Exp 6`):** One-Call JS ran fast (`2.96 ms` corpus), **but** missed closed Shadow DOM and cross-origin frames (`0.8235` corpus recall; `0.3812` GitHub Trending / `0.6410` YouTube `vs_control` recall). Removing per-node `N * DOM.getBoxModel` (`CDP Ablation`) cut corpus discovery `25.07 -> 14.19 ms`.
  - **Direct WebSocket (`Exp 7`):** Bypassing Playwright's Node CDP proxy via `DirectCdpClient` (`websockets`) saved `-98.21 ms` `p50` on GitHub Trending (`1.1 MB` Snapshot+AX payload) and kept pings sub-millisecond (`0.51–0.82 ms`).
  - **Candidate-Only Occlusion (`P-01`):** Deferring `is_occluded_in_snap()` from `5,057` DOM nodes to interactive candidates dropped `2,500`-cell Python CPU `p50` from `824.40 ms -> 19.32 ms` (`-97.66%`).
  - **`MutationObserver` (`Exp 9`):** Top-frame binding coalesced DOM churn (`176–192 B` events), but missed closed Shadow DOM and iframes (`0.8421` recall) -> held only as future dirty-flag hint.
- **Limitations & Confidence:** **High (`[MEASURED]`)** for architecture choices; real-site `Exp 6` rows measure agreement **`vs_control`** rather than manual exhaustive DOM ground truth.

---

## Finding 4 — Compact `REV:N` Maps Reduce Estimated Input Tokens on Most Views, While Dense Uncapped Trees Exceed Screenshot Proxies
- **Research Question:** How compact are CUL `line_map` snapshots compared to sending a `1280x720` viewport screenshot, and does concise skill prompting reduce agent tool-token consumption?
- **Method:** `benchmarks/benchmark_real.py` (`n=1` point checks vs `1,229` static screenshot proxy using `TOKENS_EST = len/4`), `tests/test_e2e.py`, and internal `M5` agent skill prompt runs (``skill_updates/2026-11-26_final/`` (`skill_updates/2026-11-26_final/m5_runs/M5_RESULTS.md`, local-only)).
- **Result (`[MEASURED]` with Proxy Caveat):**
  - Capped (`<= 60` elements) maps used `54.2` (`form.html`, `0.04x`), `187.2` (`Gmail`, `0.15x`), `386.8` (`YouTube`, `0.31x`), `474.8` (`Notepad`, `0.39x`), `654.0` (`GitHub Trending`, `0.53x`), `690.8` (`Google Maps`, `0.56x`), and `711.0` (`File Explorer`, `0.58x`) `TOKENS_EST` against `1,229`.
  - Uncapped dense views exceeded the proxy (`1,263.8` GitHub = `1.03x`; `1,611.0` Explorer = `1.31x`), validating the `60`-element cap + `filter_query=` drill-down.
  - Across `18` controlled held-out subagent sessions (`M5` Round 2), updated concise skill instructions reduced session prompt consumption from `4,607.7–6,723.4` to `3,974.1–3,996.7` `TOKENS_EST` (`9/9` pass both).
- **Critical Limitations (`[UNVERIFIED]`):** `benchmarks/bench_agent_20tasks.py` has **`0` live VLM API calls** (`20/20` deterministic oracle only), `TOKENS_EST = len/4` is a rough estimator rather than exact provider BPE/vision-tile billing, and `M5` measured skill-prompt versions, not CUL vs screenshot-only computer-use agents.

---

## Finding 5 — Live & Post-Audit Stress Testing Uncovered Protocol, Dialog, and Frame Blind Spots (Driving `P0-1..P0-5`)
- **Research Question:** What failure modes appear on real interactive pages and native Windows 11 apps that local unit fixtures initially hid?
- **Method:** Forensic separation of stale-server live run (`PID 4076`, `T01–T18`), restarted-server `PID 18036` M1 probes (`skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md`), and `repro_head` / `repro_head2` CDP diagnostics (`research_trace/2026-11-26/`).
- **Result & Subsequent Evolution:**
  - **Localhost vs `--site-per-process` Divergence (`[MEASURED]`):** Default `DualOriginCorpusServer` (`127.0.0.1` + `localhost`) placed parent and child frames in one renderer (`docs=2`), hiding that `--site-per-process` and live `youtube.com/embed` spawned separate `iframe` targets (`docs=1`, `0` elements). Led to `P0-1` (`77cd171` deterministic `--site-per-process` test; live third-party embeds still pending restarted MCP verification).
  - **Tab Blindness & `#32770` Save As Desync (`[REPORTED]` -> `[VERIFIED-CODE]` in `P0-2`/`P0-3`):** Clicks opening `target="_blank"` tabs stranded sessions (`T08`), and Win32 `#32770` Save As accepted UIA `SetValue` visually without committing `IFileSaveDialog` paths (`T15`, `M1 #7`). `P0-2` added multi-tab `navigate` actions and `P0-3` added `_commit_dialog_text` + `DIALOG_ALERT:`; post-P0 live stress re-runs are still pending.
  - **SSRF Redirects & Origin Exposure (`[MEASURED]` -> `[VERIFIED-CODE]` in `P0-4`/`P0-5`):** Redirect chains bypassed initial URL entry validation until `P0-4` added CDP `Fetch` request/response interception; DNS-rebinding TOCTOU remains open.
  - **Still Open (`P1`/`P2` Proposals):** `<input type="date">` segmented keystrokes (`02/02/61201`), `<input readonly>` `verified: true` false positives, omitted AX `checked`/`slider`/`option` states, `4`-way negative-`y` sticky-header coordinate divergence (`T13`), `WS_EX_LAYOUTRTL` horizontal `PrintWindow` mirroring (`M1 #6`), Explorer background-tab bleed (`P-08`), and `Ctrl/SendInput` mouse drag absence (`T06`).

---

## Finding 6 — Cursor Visualization Must Be Strictly Decoupled From Input Injection & Capture Pipelines
- **Research Question:** How can an agent display live 3D visual cursor feedback in headful Chromium and Windows desktop apps without corrupting semantic discovery, polluting `blind_gap` crops, tripping pointer `KillSwitch`s, or misrepresenting action completion?
- **Method:** Architectural implementation in `Workstream A` (`7c7b9b4..d47b4e9`: `cursor_overlay.py`, `desktop_cursor_overlay.py`, `api.py`, `mcp_server.py`) verified via `tests/test_cursor_overlay.py` unit specs (`[VERIFIED-CODE]`).
- **Result & Limitations:**
  - Desktop animations run on a separate `60.0 Hz` Win32 `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE` thread using `_WDA_EXCLUDEFROMCAPTURE` without calling `SendInput` (`KillSwitch` safe), while Chromium injects CSP/Trusted-Types-safe DOM+SVG outside `discover` outputs, and `api.py` distinguishes dispatch `ok` from `state.verify` `verified`.
  - **Boundary (`[UNVERIFIED]`/`[BLOCKED]` in `exebox`):** Working-tree `tests/test_cursor_overlay.py` is currently modified locally, and z-order stacking checks require interactive `WinSta0\Default` desktops rather than non-input `exebox` desktops.

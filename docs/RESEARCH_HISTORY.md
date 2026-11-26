# Research History & Decision Log

Computer Use Lite (`v0.1.0-alpha`) evolved across four distinct empirical phases: exploratory pointer-grid probing (`H1`–`H3`), an isolated 9-experiment performance study, an independent code/live audit + targeted fix pass (`P-01`–`P-22`), and public research release preparation. Failed experiments and stale baselines are documented explicitly below so subsequent work does not repeat dead ends.

---

## Phase 1 — Exploratory Grid Probing (`H1`, `H1b`, `H2`, `H3`)

Early experiments tested whether cursor-shape transitions (`ARROW` -> `HAND` / `IBEAM`) across a visual grid could reconstruct clickable surfaces without DOM or UIA inspection:

- **`H1` (`experiments/h1_canvas_probe.py` -> [`results/experiments/h1_report.md`](../results/experiments/h1_report.md)):**  
  Full-viewport cursor probing took `29.46 s` across `880` probes on Google Maps (`81.8%` hit rate), too slow and fragile for interactive turn loops.
- **`H1b` (`experiments/h1b_latency_cluster.py` -> [`results/experiments/h1b_report.md`](../results/experiments/h1b_report.md)):**  
  Tightening probe settle windows traded speed for severe corruption: synchronized probing took `14.93 s`, while `pipe_80` ran in `0.77 s` at only `34.4%` canvas accuracy -> **REJECTED / DROPPED**.
- **`H2` (`archive/stale_h2_grid/`, `experiments/h2_desktop_gate0.py` -> [`results/experiments/h2_gate0.json`](../results/experiments/h2_gate0.json)):**  
  Initial desktop grid sweeps in `archive/stale_h2_grid/` suffered an `87` px vertical browser-chrome coordinate offset (`(0, 87)` px), invalidating the run; that entire run was quarantined with explicit warning notices. Subsequent `H2 Gate 0` established a `50 ms` canvas settle floor (`hand_rate=1.0`, `dead_fp=0.0`) vs `2 ms` UIA Notepad control (`hand_rate=0.0`), while full Gate 2B grid sweep was **DROPPED** in favor of direct `DOMSnapshot`/`AXTree` + Win32 `UIA` + `blind_gap` image crops.
- **`H3` ([`results/experiments/h3_report.md`](../results/experiments/h3_report.md)):**  
  Never constructed (`NOT BUILT`) after `H1b` and UIA+CDP experiments resolved target coverage faster.

---

## Phase 2 — Architecture & 9-Experiment Optimization Study

Detailed in [`docs/ARCHITECTURE_DECISION.md`](ARCHITECTURE_DECISION.md) and [`results/perf_study/BENCHMARK_REPORT.md`](../results/perf_study/BENCHMARK_REPORT.md):

- **Adopted (`KEEP`):**
  1. Dedicated COM `MTA` UIA worker thread (`AutoSetFocus=0`), removing `446 ms` Notepad / `861 ms` Explorer cold `STA` hangs (`Exp 1`).
  2. 2-call `DOMSnapshot` + `AXTree` ablation eliminating per-node `N * DOM.getBoxModel` round trips (`Exp 6`).
  3. Direct persistent `DirectCdpClient` WebSocket saving `-98.21 ms` `p50` on large GitHub Trending payloads (`Exp 7`).
  4. Targeted `verify_fresh()` validation in `execute_action()`, replacing full pre/post discovery scans (`Exp 8`, noting the `fsync` confound analyzed later).
- **Rejected (`DROP`) or Deferred (`HOLD`):**
  - Dropped `Cached HWND Root`, `NoBounds + N+1` (`37–143` IPCs), `Explicit RawView` (`254` nodes / `prec=0.4043` on Chrome), and `ElementMode.None` for interactive steps (`+6.51–38.79 ms` `RuntimeId` re-acquire).
  - Placed `HOLD` on `UIA RemoteOperations` (`RemoteOp::Navigate` halts at child HWND boundaries), `One-Call JS Extractor` (drops closed Shadow DOM & OOPIF), and top-frame `MutationObserver` (`0.8421` corpus recall).

---

## Phase 3 — Independent Code Audit & Targeted Remediation (`P-01`–`P-22`)

An independent engine audit + live desktop/browser test sequence identified defects and verification boundaries leading up to `HEAD`:

- **Stale Live-Process Forensics Discovered:**  
  Earlier live MCP validation had tested a pre-fix server process whose startup predated `src/` fixes; audit policy thereafter strictly required verifying live process timestamps vs git commit dates before citing runtime state as fixed.
- **Disproved Claim (`NOT-REPRODUCED`):**  
  An initial audit item warned that non-password `TaskState` inputs were written in plaintext; direct inspection of `state.py` (`record_action`) and disk checks verified `redact_value()` hashes **every** non-`None` action `"value"` (`value_sha256`, `value_length`, `value_redacted=true`).
- **Fixed & Regression-Tested Before `v0.1.0-alpha`:**
  - `P-01`: Replaced `$O(N^2)` paint occlusion scan (`824.40 ms -> 19.32 ms` Python `p50` on `2,500`-cell fixture).
  - `P-02` / `P-03` / `P-04`: Multi-document `DOMSnapshot` tag mapping, `<input type="search">` -> `searchbox`, `<label for>` + nested container + `overflow` pruning reaching `1.0` recall & precision on `DualOriginCorpusServer`.
  - `P-06`: Disabled `os.fsync()` on disposable `SessionManager` temp dirs (`6.10 -> 2.94 ms` `TaskState.record_action()`), while uniform `n=15` benchmarks showed end-to-end `SessionManager.act()` changed `-0.144 ms` (`within noise`).
  - `P-09`: Prioritized `PrintWindow` before `ImageGrab` for covered/minimized/cloaked desktop `hwnd` crops (`mocked` green; live cross-window `ImageGrab` visual diff `BLOCKED` inside `exebox`).
  - `P-10` & Doc Corrections: Stabilized Store Notepad UIA hydration polling in tests, added host/scheme SSRF checks on initial MCP URLs, and aligned `ARCHITECTURE_DECISION.md` §3 tables with `benchmarks_real.json`.

---

## Phase 4 — Agent Benchmark Harness, Skill Evaluation & Public Preview Preparation

- Built [`benchmarks/bench_agent_20tasks.py`](../benchmarks/bench_agent_20tasks.py) covering 20 tasks across browser and Windows desktop surfaces; validated **`20/20` deterministic fixture oracles (`0` live VLM inferences)** (`results/agent_benchmark/harness_validation.json`).
- Evaluated agent prompt instruction conciseness (`M5`: `9/9` tasks passed on two skill versions with prompt tokens dropping from `4,607.7–6,723.4` to `3,974.1–3,996.7` `TOKENS_EST`).
- Audited every tracked/untracked artifact for secrets (`0` leaks), third-party license compliance (all permissive Apache-2.0 compatible), personal filesystem paths (isolated from public files), and residual security boundaries (`302` SSRF redirect, local CDP loopback port) to ship **`v0.1.0-alpha` Public Research Preview**.

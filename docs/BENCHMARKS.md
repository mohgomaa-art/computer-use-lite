# Benchmarks & Empirical Evaluation

This document summarizes all verified benchmark suites, isolated microbenchmarks, E2E fixture checks, and unrun evaluation boundaries for **Computer Use Lite `v0.1.0-alpha`**. For measurement rules and disclosed confounds, read [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md) first.

---

## 1. Benchmark Environment & Suites Inventory

All local measured suites in `results/` ran on:
- **Host:** Windows 11 (`10.0.26200-SP0`), 11th Gen Intel Core i5-11400F @ 2.60 GHz (6C/12T), 15.84 GB RAM
- **Stack:** Python `3.12.10`, Playwright `1.64.0`, `websockets 17.2`, `comtypes 1.5.0`, `mcp 1.30.0`

| Suite | Command | Ground Truth / Metric Basis | Status on `HEAD` |
| :--- | :--- | :--- | :--- |
| **Test & Regression Suite** | `pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning` | Unit, audit-fix, corpus, MCP `stdio`, Windows desktop E2E | **`[MEASURED]` `52 passed in 68.86s`** |
| **Fixture E2E Check** | `tests/test_e2e.py` -> [`results/e2e/e2e_results.json`](../results/e2e/e2e_results.json) | 8 deterministic browser/Notepad/guard/blind-gap checks | **`[MEASURED]` `8/8` passed** |
| **Phase D Real Targets** | `python -m benchmarks.benchmark_real` -> [`benchmarks_real.json`](../results/benchmarks/benchmarks_real.json) | `n=1` snapshot latency + `TOKENS_EST` (`len/4`) vs `1,229` proxy | **`[MEASURED]` (`n=1` + proxy caveat)** |
| **9-Experiment Perf Study** | `python -m benchmarks.run_all --exp all` -> [`BENCHMARK_REPORT.md`](../results/perf_study/BENCHMARK_REPORT.md) | Isolated A/B microbenchmarks (`n_cold=1..3`, `n_warm=10..20`), SHA-256 verified | **`[MEASURED]` (`engine_untouched: true`)** |
| **20-Task Agent Harness** | `python -m benchmarks.bench_agent_20tasks --dry-run-oracle` | Multi-step browser + desktop task fixtures (`mode: oracle_harness_validation_only`) | **`[MEASURED]` `20/20` oracle only (`0` LLM runs)** |
| **Skill Prompt Validation (`M5`)** | Internal skill comparison | `TOKENS_EST` across 2 prompt versions (`9/9` pass both) | **`[MEASURED]` (NOT CUL vs screenshot baseline)** |

---

## 2. Deterministic E2E Suite ([`results/e2e/e2e_results.json`](../results/e2e/e2e_results.json))

| Test Case | Elements | Latency (ms) | `TOKENS_EST` (capped) | Vs `1,229` Proxy | Verified Mechanism / Outcome |
| :--- | ---: | ---: | ---: | ---: | :--- |
| `browser_fixture` | `4` | `16.7` | `54.8` | `0.04x` | Typed `'A-1042'`, clicked submit (`Output: 'Found order A-1042'`) -> `passed: true` |
| `desktop_notepad` | `25` | `73.3` | `310.5` | `0.25x` | `ValuePattern` write + `state_diff_verified: true` -> `passed: true` |
| `stale_guard` | — | — | — | — | Refused `revision`, `covered`, `moved`, `removed` -> `passed: true` |
| `blind_region` | `0` | — | — | — | Emitted `1` `opaque_canvas` PNG crop -> `passed: true` |
| `scroll_div_click` | — | — | — | — | Scrolled target click verified -> `passed: true` |
| `uia_patterns` | — | — | — | — | `toggle_pattern` + `selection_item_pattern` -> `passed: true` |
| `fg_refusal` | — | — | — | — | Out-of-foreground UIA target refused -> `passed: true` |
| `privacy_no_fp` | — | — | — | — | No false blind crop + SHA-256 redaction -> `passed: true` |

---

## 3. Phase D Multi-Target Perception Measurements ([`benchmarks_real.json`](../results/benchmarks/benchmarks_real.json))

> [!NOTE]
> These rows reflect **`n=1` point snapshots** comparing `TOKENS_EST = round(len(line_map)/4, 1)` against a static `1,229`-token `1280x720` screenshot proxy. Vendor image encoders bill differently (e.g., `1,196` tokens on 28x28 patch pricing, `1,548` tokens on 768x768 tiling, or 512px high-detail tiles). Live network sites (`GitHub Trending`, `YouTube`, `Gmail`, `Google Maps`) vary by session/DOM state.

| Target | Surface | Elements | Blind Crops | Latency (ms) | Capped Tokens (`<=60`) | Uncapped Tokens |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `form.html` (`fixture`) | Browser | — | — | `17.8` | `54.2` | — |
| `GitHub Trending` | Browser (`real`) | `120` | `0` | `215.5` | `654.0` | `1,263.8` |
| `YouTube` | Browser (`real`) | `27` | `0` | `125.2` | `386.8` | — |
| `Gmail` | Browser (`real`) | `14` | `0` | `54.8` | `187.2` | — |
| `Google Maps` | Browser (`canvas`) | `64` | `1` | `273.2` | `690.8` | `712.5` |
| `Notepad (Win11)` | Desktop UIA | `36` | — | `140.2` | `474.8` | — |
| `File Explorer` | Desktop UIA | `140` | — | `387.7` | `711.0` | `1,611.0` |
| `Chromium UIA` (`WM_GETOBJECT` / `--force-renderer-accessibility`) | Desktop UIA | — | — | `76.1` / `62.8` | — | — |

---

## 4. Isolated 9-Experiment Performance & Accuracy Study ([`results/perf_study/`](../results/perf_study/))

Verdicts derived deterministically in [`benchmarks/run_all.py`](../benchmarks/run_all.py) (`engine_untouched: true`):

| Exp | Candidate Evaluated | Decision | Key Measured Numbers & Caveats |
| :---: | :--- | :--- | :--- |
| **Exp 1** | Dedicated UIA `MTA` Worker vs `STA` + Cached HWND Root | **KEEP MTA / DROP Cached Root** | Eliminates cold `STA` spike (`446.033 ms` Notepad, `861.063 ms` Explorer -> `52.63 ms` / `162.576 ms` `MTA`). Mean warm `p50`: `STA=65.94`, `MTA_Fresh=66.88`, `MTA_CachedRoot=69.69 ms` (`parity=1.0`). |
| **Exp 2** | `CacheRequest` Property Trimming / `NoBounds + N+1` | **DROP `NoBounds+N+1` / HOLD Minimal** | Dropping cached bounds inflates IPCs (`2–3 -> 37–143`) and raises mean `p50` `65.94 -> 80.0 ms`. |
| **Exp 3** | `TreeFilter`: `ControlView` vs `RawView` vs `OrCondition` | **DROP `RawView` / HOLD `OrCondition`** | Default `TreeFilter` verified == `ControlViewCondition` (`True`). `RawView` bloats Chrome `66 -> 254` nodes (`92.31 ms`, `prec=0.4043`). `OrCondition` min recall `0.9615` (misses `TabControl 50018`). |
| **Exp 4** | `AutomationElementMode.None` + `RuntimeId` Re-acquire | **DROP for Interaction** | Discovery `p50` `68.65` vs `66.88 ms` (zero gain), while per-action `RuntimeId` re-acquire adds `+6.51–38.79 ms`. |
| **Exp 5** | UIA `RemoteOperations` (`CoreAutomationRemoteOperation`) | **HOLD Batch Reads / DROP Walk** | `K=30` batch property reads faster (`16.88 -> 8.95 ms` Chrome; `25.12 -> 7.12 ms` Electron), **but** `RemoteOp::Navigate` halts at child HWND/process boundaries (`0.0179` Notepad / `0.0286` Chrome subtree recall). |
| **Exp 6** | 2-Call `CDP Ablation` (No `N*getBoxModel`) vs One-Call JS | **KEEP CDP Ablation / HOLD JS** | Corpus `initial_viewport`: `Control CDP` `25.068 ms` -> `Ablation CDP` `14.193 ms` (`recall=0.9412`, `prec=0.8`, drops 1 OOPIF); `One-Call JS` `2.964 ms` drops closed shadow DOM & OOPIF (`recall=0.8235`, `modal_occluded=0.6`). Real sites (`vs_control` circular reference): GitHub `373.03 -> 351.66 ms`, Maps `106.21 -> 79.67 ms` (`recall=1.0`), whereas JS real-site recall fell to `0.3812` (GitHub) / `0.641` (YouTube). |
| **Exp 7** | `DirectCdpClient` WS (`websockets`) vs Playwright `CDPSession` | **KEEP** | `ping_scroll` `p50`: `1.852 -> 0.583 ms` GitHub, `3.635 -> 0.512 ms` Maps. 2-call `Snapshot+AX` `p50`: `12.969 -> 7.168 ms` corpus, `220.309 -> 122.103 ms` GitHub (`-98.206 ms`), `59.151 -> 43.832 ms` Maps. |
| **Exp 8** | Targeted `verify_fresh()` in `execute_action()` | **KEEP** *(Confound Disclosed)* | Isolated browser `39.269 -> 9.543 ms` `p50` (`6/6` safety parity `1.0`); Notepad `2094.35 -> 2013.98 ms` (`~2006 ms` `ValuePattern.SetValue` floor). **Confound:** Exp 8 control omitted `fsync=False`; uniform `n=15` `SessionManager.act()` changed `-0.144 ms` (`23.159 -> 23.015 ms`, within noise). |
| **Exp 9** | Top-Frame `MutationObserver` + `Runtime.addBinding` | **HOLD (Dirty Hint Only)** | Coalesces `500 ms` churn (`24 -> 26` pushes, `20` events, `176–192 B`), but top-frame coverage misses closed shadow DOM (`1`) and OOPIF (`2`), capping corpus recall at `0.8421`. |

---

## 5. Audit-Fix & Corpus Accuracy Improvements (`P-01`–`P-10` on `HEAD`)

Targeted patches verified on `HEAD` prior to `v0.1.0-alpha` (`FIX_REPORT` & unit tests in `tests/test_audit_fixes.py`):

- **`P-01` Dense DOM Occlusion (`2,500`-cell fixture):** Python CPU `p50` improved from `824.401 ms` to `19.32 ms` (total `1056.166 -> 273.085 ms`).
- **`P-04` Dual-Origin Corpus Accuracy (`DualOriginCorpusServer`):** `Api.discover_interactables()` improved from `recall=0.9412, prec=0.8421` to **`recall=1.0, prec=1.0`** via `<label for>` dedup, nested container pruning, and `overflow` ancestor clipping *(note: local dual-origin test did not launch Chromium with strict `--site-per-process`; see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md))*.
- **`P-06` Disposable Temp State `fsync=False`:** Isolated `TaskState.record_action()` fell from `6.103 ms` (`20` fsyncs) to `2.944 ms` (`0` fsyncs) for `SessionManager` scratch dirs while retaining `state_fsync=True` default for callers.

---

## 6. Unverified Live Agent Benchmarks (Important Explicit Gap)

- **20-Task Agent Benchmark ([`benchmarks/bench_agent_20tasks.py`](../benchmarks/bench_agent_20tasks.py)):**  
  [`results/agent_benchmark/harness_validation.json`](../results/agent_benchmark/harness_validation.json) validates **`20/20` fixtures via deterministic oracle actions only (`0` live VLM inferences)** (`mode: "oracle_harness_validation_only"`). No comparative multi-step live LLM pass-rate or end-to-end API billing benchmark between screenshot-only agents and CUL exists yet.
- **Agent Skill Prompt Comparison (`M5`):**  
  Validated across `9` tasks on two prompt versions (`3,974.1–3,996.7` vs `4,607.7–6,723.4` `TOKENS_EST`, `9/9` pass both), demonstrating prompt compactness rather than CUL vs pure-vision agent accuracy.

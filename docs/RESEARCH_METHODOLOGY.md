# Research Methodology & Epistemic Standards

Computer Use Lite (CUL) is developed as an empirical engineering research project. Every architectural choice, benchmark claim, and failure mode in this repository follows explicit evidence rules so readers can separate measured facts from unverified hypotheses or unimplemented proposals. For the central navigation map, see [INDEX.md](INDEX.md) and [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md).

---

## 1. Epistemic Evidence Tags

Documentation and experimental records use strict classification tags:

| Tag | Meaning & Verification Requirement |
| :--- | :--- |
| **`[FACT]` / `[VERIFIED-CODE]`** | Directly verified in checked-in source (`src/`), tests (`tests/`), git history, or tool schemas. |
| **`[MEASURED]`** | Directly observed in raw command output, test execution, structured JSON results, or runtime probes executed against the cited revision. |
| **`[REPORTED]`** | Recorded in earlier audit, validation, or live-run reports and preserved transparently, but not independently re-executed on current `HEAD` (for example, manual interactive `Default`-desktop UI observations or stale-process logs labeled clearly). |
| **`[DOCUMENTED]`** | Derived directly from authoritative primary third-party specifications or package metadata (W3C, Chrome DevTools Protocol, Microsoft Win32/UIA, Playwright, MCP SDK). |
| **`[INFERRED]` / `[HYPOTHESIS]`** | Analytical diagnosis connecting verified observations or an untested causal hypothesis. |
| **`[PROPOSAL]`** | Unimplemented design or roadmap recommendation (`P1` / `P2`). Never cited as shipped code. |
| **`[UNKNOWN]` / `[UNVERIFIED]` / `[BLOCKED]`** | Never run, interrupted by sandbox/desktop isolation (`exebox-*` vs interactive `WinSta0\Default`), or lacking live model runs (`0` VLM inferences). |

---

## 2. Measurement Discipline & Fairness Rules

1. **Production Code Immutability During Benchmark Studies:**  
   `benchmarks/common.py` computes SHA-256 digests (`engine_hashes()`, `verify_engine_untouched()`) of every `.py` file under `src/computer_use_lite/` before and after `benchmarks/run_all.py` executes, recording `"engine_untouched": true` only if zero bytes changed during benchmarking.
2. **Cold vs. Warm Distribution Reporting:**  
   Microbenchmarks separate cold initial invocations (`n_cold`) from warm iterations (`n_warm`) and report `p50`, `p95`, `p99`, min/max, CPU time, RSS delta, IPC round trips, and payload bytes rather than cherry-picking best-case means (`benchmarks/common.summarize_timings()`).
3. **Adversarial Dual-Origin Fixtures vs. Real-Site Baselines:**  
   - **Controlled Corpus (`benchmarks/corpus.py`):** Evaluates browser extraction against deterministic HTML/JS ground truth (`extract_corpus_ground_truth()`), exercising open Shadow DOM, closed Shadow DOM, dynamic drawers, modal occlusion, hidden scroll overflow containers, and iframes.
   - **Real Web Targets:** Because live public websites (`GitHub Trending`, `YouTube`, `Gmail`, `Google Maps`) change continuously without programmatic ground truth across every DOM subtree, `Exp 6` real-site precision/recall rows score candidates **`vs_control`** (against viewport-filtered `Control CDP`), making `Control CDP` `1.0000` by definition. This is disclosed explicitly rather than claimed as universal ground truth.
4. **Control vs. Ablation vs. Candidate Separation:**  
   Optimization candidates were evaluated in isolated A/B harnesses before merging into production code (`benchmarks/run_all.py` `_keep_drop_hold()`).

---

## 3. Disclosed Proxy Metrics & Confounds

1. **Token Count Proxy (`TOKENS_EST = len(text) / 4` & `1,229` Screenshot Baseline):**  
   `Api.last_stats["tokens"]` and `benchmarks/benchmark_real.py` compute `round(len(line_map) / 4, 1)` as a deterministic character-ratio estimator, NOT an exact BPE tokenizer count. `SHOT_TOKENS = 1229` is a fixed `1280x720` static reference proxy; actual vendor image tokenization differs materially (patch/tiling schemes on OpenAI, Anthropic, and Gemini). Exact cost claims require provider-reported `prompt_tokens`.
2. **Action Verification vs. Semantic Completion:**  
   `Api.execute_action()` and MCP `act` return `"verified": true` based on targeted pre-checks and lightweight post-dispatch signature diffs. **This does NOT verify downstream semantic intent** (`<input readonly>` focus acceptance, framework-swallowed synthetic clicks).
3. **20-Task Agent Benchmark Scope (`0` Live LLM Calls):**  
   [`results/agent_benchmark/harness_validation.json`](../results/agent_benchmark/harness_validation.json) records `mode: "oracle_harness_validation_only"` (`20/20` deterministic fixture validation only). **No comparative live VLM study** has executed yet.
4. **`Exp 8` Freshness Confound:**  
   In [`results/perf_study/exp8_freshness.json`](../results/perf_study/exp8_freshness.json), isolated browser `execute_action()` dropped `39.269 -> 9.543 ms` `p50`, **but** the control arm omitted the `fsync=False` setting applied in the candidate setup. Follow-up uniform `n=15` runs on `SessionManager.act()` (`23.159 -> 23.015 ms`, within `stddev=3.52 / 4.716 ms`) confirmed end-to-end `act` time is governed by CDP IPCs rather than `os.fsync()`.
5. **Skill Prompt Evaluation (`M5`) vs. Engine Evaluation:**  
   ``skill_updates/2026-11-26_final/m5_runs/M5_RESULTS.md`` (`skill_updates/2026-11-26_final/m5_runs/M5_RESULTS.md`, local-only) compared two prompt instruction versions (`3,974.1–3,996.7` vs `4,607.7–6,723.4` `TOKENS_EST`, `9/9` pass both); it did **not** benchmark CUL against a pure-vision screenshot agent.
6. **Negative Evidence Preservation:**  
   Rejected or invalidated experiments (`H1`, `H1b`, `H2`, `H3`, `archive/stale_h2_grid/`, `PID 4076` live logs) are preserved in [../research_archive/INDEX.md](../research_archive/INDEX.md) with explicit warning headers rather than erased.

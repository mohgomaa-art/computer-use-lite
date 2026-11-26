# Research Methodology & Epistemic Standards

Computer Use Lite (CUL) is developed as an empirical engineering research project. Every architectural choice, benchmark claim, and failure mode in this repository follows explicit evidence rules so readers can separate measured facts from unverified hypotheses.

---

## 1. Epistemic Evidence Tags

Documentation and experimental records use strict classification tags:

| Tag | Meaning & Verification Requirement |
| :--- | :--- |
| **`[MEASURED]`** | Directly observed in raw command output, test execution, structured JSON results, or runtime probes executed against the referenced revision. |
| **`[VERIFIED-CODE]`** | Observed directly in checked-in source files (`src/`), tests (`tests/`), or harness definitions (`benchmarks/`). |
| **`[REPORTED]`** | Recorded in earlier audit, validation, or live-run reports and preserved transparently, but not re-measured in the latest automated run (for example, manual interactive `Default`-desktop UI observations). |
| **`[DOCUMENTED]`** | Derived directly from authoritative third-party specifications or package metadata (e.g., W3C, Chrome DevTools Protocol, Microsoft UIA, Playwright). |
| **`[INFERRED]`** | Architectural diagnosis or interpretation connecting verified observations; marked as analytical inference rather than raw telemetry. |
| **`[UNVERIFIED]` / `[BLOCKED]`** | Never run, interrupted by sandbox/desktop isolation (such as interactive `Default`-desktop overlap checks inside `exebox`), or lacking live model runs. |

---

## 2. Measurement Discipline & Fairness Rules

1. **Production Code Immutability During Benchmark Studies:**  
   `benchmarks/common.py` computes SHA-256 digests (`engine_hashes()`, `verify_engine_untouched()`) of every `.py` file under `src/computer_use_lite/` before and after `benchmarks/run_all.py` executes, recording `"engine_untouched": true` only if zero bytes changed during benchmarking.
2. **Cold vs. Warm Distribution Reporting:**  
   Microbenchmarks separate cold initial invocations (`n_cold`) from warm iterations (`n_warm`) and report `p50`, `p95`, `p99`, min/max, CPU time, RSS delta, IPC round trips, and payload bytes rather than cherry-picking best-case means (`benchmarks/common.summarize_timings()`).
3. **Adversarial Dual-Origin Fixtures vs. Real-Site Baselines:**  
   - **Controlled Corpus (`benchmarks/corpus.py`):** Evaluates browser extraction against deterministic HTML/JS ground truth (`extract_corpus_ground_truth()`), explicitly exercising open Shadow DOM, closed Shadow DOM, dynamic drawers, modal occlusion, hidden scroll overflow containers, and a dual-origin `iframe` (`127.0.0.1` vs `localhost`).
   - **Real Web Targets:** Because live public websites (`GitHub Trending`, `YouTube`, `Gmail`, `Google Maps`) change continuously and have no authoritative programmatic ground truth across every DOM subtree, `Exp 6` real-site precision/recall rows score candidates **`vs_control`** (against viewport-filtered `Control CDP`), making `Control CDP` `1.0000` by construction. We disclose this explicitly rather than presenting `vs_control` as universal web ground truth.
4. **Control vs. Ablation vs. Candidate Separation:**  
   Performance hypotheses were tested in isolated A/B harnesses before touching production code: `Control` (baseline mechanism), `Ablation` (e.g., removing per-element `N * DOM.getBoxModel` RPCs), and `Candidate` (e.g., single-frame JS or UIA `RemoteOperations`), with pre-specified `KEEP` / `DROP` / `HOLD` criteria computed programmatically in `benchmarks/run_all.py` (`_keep_drop_hold()`).

---

## 3. Disclosed Proxy Metrics & Confounds

To prevent accidental misinterpretation by reviewers, all known measurement proxies and experimental confounds are documented alongside their numbers:

1. **Token Count Proxy (`TOKENS_EST = len(text) / 4` & `1,229` Screenshot Baseline):**  
   `Api.last_stats["tokens"]` and `benchmarks/benchmark_real.py` compute `round(len(line_map) / 4, 1)` as a deterministic character-ratio estimator, NOT an exact vendor BPE tokenizer count. Comparisons against `SHOT_TOKENS = 1229` (`benchmarks/benchmark_real.py:30`) represent a fixed `1280x720` reference proxy; vendor image tokenization varies materially across providers (for instance, patch/tile schemes such as `1,196` tokens on 28x28 patches or `1,548` tokens at 768x768 tiling on Gemini, and tile sizing in OpenAI Vision). Exact billing comparisons require live provider usage accounting (`prompt_tokens`).
2. **Action Verification vs. Semantic Completion:**  
   `Api.execute_action()` and MCP `act` return `"verified": true` when pre-action identity/visibility guards pass and dispatch completes without throwing. **This does NOT verify downstream semantic intent**: typing into `<input readonly>` or dispatching `ValuePattern.SetValue` inside a Windows `#32770` Save As box that ignores COM dialog selection state can still leave the underlying task incomplete (`[REPORTED]` / `[VERIFIED-CODE]`).
3. **20-Task Agent Benchmark Scope (`0` Live LLM Calls):**  
   `results/agent_benchmark/harness_validation.json` records `mode: "oracle_harness_validation_only"` (`20/20` deterministic fixture oracle validation). **No end-to-end live VLM comparison** (`--provider openai|gemini|ollama`) has been published yet in this release (`v0.1.0-alpha`).
4. **Exp 8 Freshness Confound:**  
   In `results/perf_study/exp8_freshness.json`, isolated browser `execute_action()` dropped from `39.269 ms` to `9.543 ms` `p50`, but the control arm omitted the disposable `fsync=False` optimization applied in the candidate setup. Follow-up uniform `n=15` measurement on `SessionManager.act()` (`23.159 -> 23.015 ms`, within `stddev=3.52 / 4.716 ms`) demonstrated that end-to-end `act` latency is governed by CDP `verify_fresh` + `perform` + `signature()` rather than `TaskState` `os.fsync()`.
5. **Skill Prompt Evaluation (`M5`) vs. Engine Evaluation:**  
   Internal agent-skill validation (`M5`) measured whether an updated skill prompt (`TOKENS_EST` `3,974.1–3,996.7` vs prior `4,607.7–6,723.4`, `9/9` pass both) lowered agent prompt consumption between two instruction revisions; it did **not** benchmark CUL against a screenshot-only computer-use agent.
6. **Negative Evidence Preservation:**  
   Rejected paths — including `H1` / `H1b` / `H2` / `H3` cursor probing and `archive/stale_h2_grid/` (which suffered a `(0, 87)` px browser-chrome coordinate offset bug) — are intentionally preserved in `experiments/` and `archive/` rather than silently deleted.

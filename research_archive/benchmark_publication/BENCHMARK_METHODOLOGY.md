# Benchmark Publication Methodology

This document defines the provenance rules, statistical definitions, proxy assumptions, and disclosed confounds behind [benchmark_data.json](benchmark_data.json) and the `docs/assets/benchmarks/` figure suite (`0.1.0a2`).

## 1. Canonical Single-Source Pipeline

All nine figures (`FIG-01` through `FIG-09`) render directly from [benchmark_data.json](benchmark_data.json) via React + SVG components under [../../research_visuals/benchmark_report/](../../research_visuals/benchmark_report/). No figure hardcodes separate headline metrics.

## 2. Browser Agent Benchmark Protocol (`FIG-01` – `FIG-04`)

- **Arms Compared:**
  - **Arm A (`Playwright MCP`):** `@playwright/mcp@0.0.86`, CDP attached at `--cdp-endpoint=http://127.0.0.1:<fresh-port>`, `1280×720` viewport (`116` total tool calls).
  - **Arm B (`CUL Browser MCP`):** Commit `fdc92d9` (`CUL_MCP_BROWSER_ONLY=1`, exposing `11` browser tools without desktop tools), `152` total tool calls (`36/36` runs used CUL).
- **Important Comparison Boundary:** Playwright MCP uses structured accessibility snapshots. This dataset compares two **semantic browser MCP servers** — it does **NOT** evaluate Native OpenAI Computer Use (`@oai/sky`) or pure-vision screenshot loops.
- **Design:** `12` synthetic local HTML tasks × `3` repetitions per arm = `72` runs, shuffled with fixed seed `2040777688`, Codex CLI `0.166.0`, requested model `gpt-6-luna`.
- **Statistical Summaries:**
  - Success intervals: 95% Wilson score intervals (`86.11%`: `71.34%–93.92%`; `100.0%`: `90.36%–100.0%`).
  - `p95`: Linear interpolation at rank `(n - 1) × 0.95`.
  - Wall time: End-to-end harness runtime (browser profile launch through oracle completion).
- **Mandatory Confounds:**
  1. **`b11_dense_90_grid_filter` Prompt Contamination:** The shared prompt wording explicitly told both arms `"(use filter_query if needed)"`, naming a CUL-specific parameter. Both arms succeeded `3/3`; Playwright MCP used `88,216` median tokens vs CUL's `164,300` median tokens.
  2. **Arm A `browser_run_code_unsafe` Usage:** On `b12_opaque_canvas_click` run 1, Playwright MCP invoked `browser_run_code_unsafe` (`page.mouse.click(199, 271)`), so Arm A was not strictly snapshot-only across all 36 runs.
  3. **Commit Provenance:** CUL ran on `fdc92d9` (browser-only worktree commit), not `0d19a9e`.

## 3. Observation Size Proxy (`FIG-05`)

- **Metric Definition:** `TOKENS_EST = round(text_length / 4, 1)` on single `discover()` / `line_map` strings vs `ceil(1280/28) × ceil(720/28) = 46 × 26 = 1,196` `28×28`-pixel image patches.
- **Provenance Distinction:** `112` estimated tokens came from a `12-task × 5-run` (`60` observations; min `23`, max `664`) headless Chromium browser benchmark pass, alongside checked-in [../../results/agent_benchmark/harness_validation.json](../../results/agent_benchmark/harness_validation.json) (`115.07` single-pass browser mean) and [../../results/benchmarks/benchmarks_real.json](../../results/benchmarks/benchmarks_real.json) (`1,229` static screenshot baseline; up to `1,611.0` uncapped File Explorer tokens).
- **Cost Caveat:** Observation size per single call is NOT provider billing across a task. In the live 72-run agent benchmark (`FIG-03`), CUL consumed `+40.0%` more median total tokens because revision-enforced `discover -> act` steps increased turns (`4.5` vs `3.0`).

## 4. Test Coverage vs Agent Evaluation (`FIG-06` & `FIG-07`)

- `70 passed` (`197.50s` at `0d19a9e`) in `FIG-06` is software unit/integration test coverage on Windows 11 Pro (`10.0.26200`), NOT an AI-agent benchmark score.
- Desktop Pilot v1 (`FIG-07`) completed `2/2` supervised CUL T1 trials (verified via SHA-256 fixture checks) while T2 and Native-vs-CUL desktop comparisons remain incomplete.

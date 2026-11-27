# Computer Use Lite — Benchmark Comparison (`v0.2.0a0`)

> [!IMPORTANT]
> **Comparison Boundary:** Section 1 preserves the historical paired **semantic-vs-semantic browser MCP study** (`@playwright/mcp@0.0.86` vs CUL Browser MCP at `fdc92d9`, NOT Native OpenAI Computer Use `@oai/sky`). Sections 5–6 add the frozen `post-fix-v1` evaluation comparing preserved baseline `v0.1.0a0` (`0d19a9e`) against repaired `v0.2.0a0` (`a33a8f2`). Every chart is rendered directly from [../research_archive/benchmark_publication/benchmark_data.json](../research_archive/benchmark_publication/benchmark_data.json).

---

## 1. Browser Agent Benchmark (`72` Runs — Commit `fdc92d9`)

### FIG-01 — Browser Task Success Rate
![FIG-01 Browser Task Success Rate](assets/benchmarks/fig-01-browser-success.svg)

- **TSX Source:** [`Fig01BrowserSuccess.tsx`](../research_visuals/benchmark_report/src/figures/Fig01BrowserSuccess.tsx) · **PNG Preview:** [`fig-01-browser-success.png`](assets/benchmarks/fig-01-browser-success.png) · **Methodology:** [BENCHMARK_METHODOLOGY.md](BENCHMARK_METHODOLOGY.md)
- **Disclosed Confound:** Task `b11_dense_90_grid_filter` shared prompt text exposed CUL's parameter name (`filter_query`) to both arms, and Playwright MCP called `browser_run_code_unsafe` once on `b12_opaque_canvas_click` run 1.

### FIG-02 — Median End-to-End Task Wall Time
![FIG-02 Median End-to-End Task Wall Time](assets/benchmarks/fig-02-wall-time.svg)

- **TSX Source:** [`Fig02WallTime.tsx`](../research_visuals/benchmark_report/src/figures/Fig02WallTime.tsx) · **PNG Preview:** [`fig-02-wall-time.png`](assets/benchmarks/fig-02-wall-time.png)
- Lower wall time is faster. CUL's median end-to-end duration (`26.87s`, p95 `34.70s`) was `+1.5%` slower than Playwright MCP (`26.48s`, p95 `35.73s`).

### FIG-03 — Median Total Conversation Tokens
![FIG-03 Median Total Conversation Tokens](assets/benchmarks/fig-03-token-estimates.svg)

- **TSX Source:** [`Fig03TokenEstimates.tsx`](../research_visuals/benchmark_report/src/figures/Fig03TokenEstimates.tsx) · **PNG Preview:** [`fig-03-token-estimates.png`](assets/benchmarks/fig-03-token-estimates.png)
- Lower token total uses less context. CUL consumed `+40.0%` more median total conversation tokens (`176,506` vs `126,087`) due to revision-checked `discover` + `act` turns.

### FIG-04 — Median Interaction Steps
![FIG-04 Median Agent Interaction Steps](assets/benchmarks/fig-04-interaction-steps.svg)

- **TSX Source:** [`Fig04InteractionSteps.tsx`](../research_visuals/benchmark_report/src/figures/Fig04InteractionSteps.tsx) · **PNG Preview:** [`fig-04-interaction-steps.png`](assets/benchmarks/fig-04-interaction-steps.png)
- CUL executed `4.5` median steps (`152` total calls) vs Playwright MCP's `3.0` median steps (`116` total calls).

### Summary & Per-Task Breakdown

| Metric | Playwright MCP | CUL Browser MCP (`fdc92d9`) | Paired Outcome / Notes |
|---|---:|---:|---|
| **Successful runs** | `31/36` (`86.11%`) | `36/36` (`100.0%`) | `+5` CUL paired wins (`5W / 0L / 31T`) |
| **95% Wilson CI** | `71.34% – 93.92%` | `90.36% – 100.0%` | Confidence intervals overlap above `90%` |
| **Median total tokens** | `126,087` | `176,506` | CUL `+40.0%` higher (`7W / 29L`) |
| **Median steps** | `3.0` | `4.5` | CUL `+50.0%` more calls (`0W / 28L / 8T`) |
| **Median wall time** | `26.48s` | `26.87s` | CUL `+1.5%` slower median (`15W / 21L`) |

Notable task divergence: Playwright MCP failed `b08_closed_shadow_dom` (`0/3`) and partially failed `b12_opaque_canvas_click` (`1/3`, succeeding once via `browser_run_code_unsafe`), while CUL completed `3/3` on both using CDP closed-Shadow-DOM snapshot visibility and `blind_gap` canvas crops — at higher median step/token cost across the other `10` tasks.

---

## 2. Semantic Observation Size Proxy (`FIG-05`)

![FIG-05 Estimated Observation Size](assets/benchmarks/fig-05-observation-size.svg)

- **TSX Source:** [`Fig05ObservationSize.tsx`](../research_visuals/benchmark_report/src/figures/Fig05ObservationSize.tsx) · **PNG Preview:** [`fig-05-observation-size.png`](assets/benchmarks/fig-05-observation-size.png)
- **Label:** `Estimated Observation Size — Not Actual API Token Usage`.
- `112` estimated tokens (`round(text_length / 4)`) vs `1,196` `28×28`-patch tokens (`1280×720`) reflects **single-step discovery payload proxies on synthetic fixtures**, not total billed provider tokens (see `FIG-03`, where total multi-turn Codex tokens were `+40%` higher for CUL, and [BENCHMARKS.md](BENCHMARKS.md), where uncapped File Explorer reached `1,611.0` estimated tokens).

---

## 3. Cross-Platform & Automated Test Coverage (`FIG-06`)

![FIG-06 Cross-Platform & Automated Test Suite](assets/benchmarks/fig-06-windows-tests.svg)

- **TSX Source:** [`Fig06WindowsTests.tsx`](../research_visuals/benchmark_report/src/figures/Fig06WindowsTests.tsx) · **PNG Preview:** [`fig-06-windows-tests.png`](assets/benchmarks/fig-06-windows-tests.png)
- Recorded on Windows 11 Pro (`10.0.26200`) at commit `a33a8f2`: **`95 passed, 0 failed, 0 skipped` in `106.93s`** (`79 passed, 16 deselected` in `87.20s` under `CUL_SKIP_DESKTOP=1 -m "not windows_desktop"`), plus verified non-Windows import on real **WSL2 `kali-linux` (`Python 3.14.7`)**. Historical baseline at `0d19a9e` passed `70/70` (`197.50s`).

---

## 4. Historical Desktop Pilot Status (`FIG-07`)

![FIG-07 Desktop Pilot Status](assets/benchmarks/fig-07-desktop-pilot-status.svg)

- **TSX Source:** [`Fig07DesktopPilotStatus.tsx`](../research_visuals/benchmark_report/src/figures/Fig07DesktopPilotStatus.tsx) · **PNG Preview:** [`fig-07-desktop-pilot-status.png`](assets/benchmarks/fig-07-desktop-pilot-status.png)
- **Status:** `CUL T1` passed `2/2` supervised runs with fixture SHA-256 checks; `CUL T2` remained **incomplete**; and the **Native vs CUL desktop comparison was never completed**. A standalone pre-pilot Native Calculator smoke check is not a comparative benchmark.

---

## 5. Post-Fix Comparative Regression & MCP Replay (`FIG-10`, `0d19a9e` vs `v0.2.0a0`)

![FIG-10 Post-Fix Verification & MCP Replay](assets/benchmarks/fig-10-post-fix-regression-mcp.svg)

- **TSX Source:** [`Fig10PostFixRegressionAndMcp.tsx`](../research_visuals/benchmark_report/src/figures/Fig10PostFixRegressionAndMcp.tsx) · **PNG Preview:** [`fig-10-post-fix-regression-mcp.png`](assets/benchmarks/fig-10-post-fix-regression-mcp.png)
- **Track A Paired Checks (`n = 32`):** Baseline `0d19a9e` passed **`2/32` (`6.25%`, 95% Wilson CI `[1.73%, 20.15%]`)**; fixed `v0.2.0a0` passed **`32/32` (`100.0%`, 95% Wilson CI `[89.28%, 100.0%]`)** (`+30` fixed wins, `0` losses, `2` ties).
- **Track B2 Deterministic Stdio MCP Replay (`n = 18` scripted tasks — NOT LLM reasoning):** Baseline `0d19a9e` passed **`12/18` (`66.67%`, failing `s01`–`s06`)**; fixed `v0.2.0a0` (`Pipe` default) passed **`18/18` (`100.0%`, median wall `2656.17 ms`)**.
- **Track B1 Live LLM Benchmarks (`codex-cli 0.166.0` / Native `@oai/sky`):** Strictly **`NOT_RUN`** — Codex CLI pre-flight hit usage quota (`returncode=1` until Dec 26, 2026); `@oai/sky`, `ollama`, and API keys are absent.

---

## 6. Engine Latency, Transport Tradeoff & Cursor `rAF` (`FIG-11`, Track C `N = 10`)

![FIG-11 Engine Latency & Transport Tradeoff](assets/benchmarks/fig-11-post-fix-engine-perf.svg)

- **TSX Source:** [`Fig11PostFixEnginePerf.tsx`](../research_visuals/benchmark_report/src/figures/Fig11PostFixEnginePerf.tsx) · **PNG Preview:** [`fig-11-post-fix-engine-perf.png`](assets/benchmarks/fig-11-post-fix-engine-perf.png)
- **Transport Tradeoff (`CUL-SEC-002`):** Switching default transport to Pipe eliminates unauthenticated localhost CDP TCP exposure while raising `dense_2500` discovery `p50` (`163.45 ms -> 367.09 ms`). Setting `CUL_MCP_DIRECT_WS=1` recovers **`152.43 ms` `p50`**, while standard forms (`9.46 ms`) and `dense_90` (`25.26 ms`) remain fast over Pipe.
- **Adaptive Hover & Cursor Overlay:** Adaptive settle cuts `hover_adaptive` `p50` **4.3x (`387.39 ms -> 90.83 ms`)**; cursor busy-delay (`350ms`) + `addScriptToEvaluateOnNewDocument` cuts rapid busy DOM rebuilds **`6 -> 1`** and navigation `eval` injection **`48,234 B -> 0 B`** at locked **`16.7 ms`** (60 FPS).

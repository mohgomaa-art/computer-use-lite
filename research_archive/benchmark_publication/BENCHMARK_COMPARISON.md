# Benchmark Comparison Summary (`v0.1.0a2`)

> [!IMPORTANT]
> Canonical publication view linked to [benchmark_data.json](benchmark_data.json). For full methodology and prompt-contamination details, see [BENCHMARK_METHODOLOGY.md](BENCHMARK_METHODOLOGY.md) and [LIMITATIONS.md](LIMITATIONS.md).

## 1. Browser Agent Comparison (`72` Runs, Seed `2040777688`)

| Metric | Playwright MCP (`@playwright/mcp@0.0.86`) | CUL Browser MCP (`fdc92d9`) | Paired Outcome / Delta |
|---|---:|---:|---|
| **Successful runs** | `31/36` (`86.11%`) | `36/36` (`100.0%`) | `+5` paired wins for CUL (`5/0/31`) |
| **95% Wilson CI** | `71.34% – 93.92%` | `90.36% – 100.0%` | Narrower upper bound; overlapping region above `90%` |
| **Median total tokens** | `126,087` (`p95: 175,285.5`) | `176,506` (`p95: 236,080.8`) | CUL `+40.0%` higher (`7` wins / `29` losses) |
| **Median steps** | `3.0` (`p95: 4.25`) | `4.5` (`p95: 5.0`) | CUL `+50.0%` more steps (`0` wins / `28` losses / `8` ties) |
| **Median wall time** | `26.48s` (`p95: 35.73s`) | `26.87s` (`p95: 34.70s`) | CUL `+1.5%` slower median (`15` wins / `21` losses) |

**Key Takeaway:** On these `12` synthetic browser tasks (`3` reps each), CUL Browser MCP eliminated the `b08_closed_shadow_dom` (`0/3 -> 3/3`) and `b12_opaque_canvas_click` (`1/3 -> 3/3`) failures, **at the cost of `+40.0%` higher median token consumption, `+50.0%` more median steps, and `+1.5%` slower median wall time**. Because `b11` prompts mentioned `filter_query` and both arms operated on local synthetic pages, universal superiority cannot be inferred.

## 2. Single-Step Observation Size vs Full Task Usage

- **Single discovery observation estimate:** `112` estimated tokens (`round(text_length / 4)`) vs `1,196` `28×28`-patch screenshot tokens (`~10.7x` ratio).
- **Mandatory distinction:** This proxy applies to **individual discovery payloads on structured web tasks** — NOT multi-turn total API billing (where CUL's `discover -> act` cycle raised total median task tokens to `176,506` vs `126,087`).

## 3. Windows Automated Suite & Unfinished Desktop Pilot

- **Windows 11 `pytest` (`0d19a9e`):** `70 passed, 0 failed, 0 skipped` in `197.50s` (`58 passed, 12 skipped` in `86.66s` under `CUL_SKIP_DESKTOP=1`).
- **Desktop Pilot Status:** `CUL T1` achieved `2/2 passed` supervised runs; `CUL T2` remained **incomplete** and `Native vs CUL` head-to-head comparison remained **not completed**.

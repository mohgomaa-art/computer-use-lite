# Computer Use Lite — Benchmark Methodology (`v0.1.0a2`)

This methodology specification governs the `0.1.0a2` Benchmark Research Publication, canonical data files in [`research_archive/benchmark_publication/`](../research_archive/benchmark_publication/benchmark_data.json), and original TSX/SVG chart suite in [`research_visuals/benchmark_report/`](../research_visuals/benchmark_report/).

---

## 1. Epistemic & Provenance Architecture

1. **Single Canonical Data Source:** Every displayed chart (`FIG-01`–`FIG-09`) imports [benchmark_data.json](../research_archive/benchmark_publication/benchmark_data.json) rather than duplicating metrics in visualization components.
2. **Evidence Provenance Separation:**
   - **Historical Baseline Release (`v0.1.0a0` @ `0d19a9e`):** Preserved unmodified from initial repository baseline.
   - **Browser Agent Benchmark (`FIG-01`–`FIG-04`):** Measured externally in local worktree commit `fdc92d9` (`CUL_MCP_BROWSER_ONLY=1`, 72 runs).
   - **Observation Size Proxy (`FIG-05`):** Measured via `round(len(text)/4)` across `12 × 5 = 60` headless browser observations (`112` avg) paired with checked-in `harness_validation.json` (`115.07` single-pass browser mean) and `benchmarks_real.json` (`1,229` static baseline; `1,196 = ceil(1280/28) × ceil(720/28)`).
   - **Windows Audit & Regression Suite (`FIG-06`, `FIG-09`):** Independent audit on Windows 11 Pro (`10.0.26200`) against commit `0d19a9e`.
   - **Supervised Desktop Pilot (`FIG-07`):** Separate partial pilot (`2/2` CUL T1 passing manifests; T2 incomplete; Native comparison uncompleted).

---

## 2. Paired Browser Agent Study (`FIG-01` – `FIG-04`)

- **Isolation & Randomization:** Seed `2040777688` shuffled `72` runs (`12` synthetic browser tasks `b01..b12` × `3` reps × `2` arms). Each run launched a fresh browser profile (`1280×720`) and fresh Codex CLI `0.166.0` process (`gpt-6-luna` requested, cap `30` tool calls, `180s` timeout, `0` shell calls).
- **Arms Compared:**
  - `Playwright MCP` (`@playwright/mcp@0.0.86`) using accessibility snapshots.
  - `CUL Browser MCP` (`fdc92d9`, `CUL_MCP_BROWSER_ONLY=1`, exposing `11` browser tools without Windows UIA tools).
- **Mandatory Validity Disclosures:**
  1. **Not Native Computer Use:** Playwright MCP operates on accessibility trees, so this does not measure CUL against pure pixel-based agents.
  2. **`b11` Contamination:** `b11_dense_90_grid_filter` contained `"(use filter_query if needed)"` in the prompt supplied to both arms (`benchmarks/agent_tasks.py:249`).
  3. **`b12` Unsafe Code Call:** Arm A called `browser_run_code_unsafe` once on `b12_opaque_canvas_click` run 1 (`page.mouse.click(199, 271)`).
  4. **Commit Difference:** Arm B ran `fdc92d9`, not `0d19a9e`.
  5. **Metric Caveat:** Token totals represent CLI session input/output token counts (`not monetarily priced`); median wall time includes harness setup/teardown.

---

## 3. Observation Size Proxy (`FIG-05`)

- **Formula:** `TOKENS_EST = round(len(line_map) / 4, 1)` (`src/computer_use_lite/api.py:60`).
- **Screenshot Patch Grid:** `ceil(1280/28) × ceil(720/28) = 46 × 26 = 1,196` tokens (`docs/BENCHMARKS.md:43` also documents `1,229`).
- **Why Observation Size != Task Cost:** Single discovery payloads shrink dramatically (`112` vs `1,196`), yet multi-turn conversation loops accumulate system prompts, tool schemas, prior history, and post-action re-discovery steps (`4.5` vs `3.0` median steps), producing `+40.0%` higher total tokens in `FIG-03`. Non-ASCII/Arabic text also tokenizes far less densely than `chars/4`, and uncapped desktop trees (`File Explorer = 1,611.0`) can exceed static screenshots.

---

## 4. Test Coverage & Desktop Pilot Separation (`FIG-06` & `FIG-07`)

- **Software Suite (`FIG-06`):** `pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning` (`70 passed`, `197.50s` at `0d19a9e`) verifies deterministic code assertions and local UIA/CDP fixtures. It never implies VLM task completion rates or runtime absence of `FIG-09` security bugs.
- **Desktop Pilot (`FIG-07`):** Only `CUL T1` (`draft.txt` move/rename, `2/2` trials) ran under operator SHA-256 fixture checks (`T1-*.json` prepare manifests archived). `T2` remained prepared in `input.txt` without Calculator verification, and paired Native-vs-CUL runs never completed.

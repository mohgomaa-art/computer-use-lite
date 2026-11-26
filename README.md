# Computer Use Lite

> **Project Status: Work in Progress (`0.1.0`)**  
> Code, benchmarks, directory structure, and evaluation results are actively evolving and should not be treated as final.

## Purpose

Computer Use Lite is a local-first UI perception and action engine for **browser automation (via Playwright + Chrome DevTools Protocol)** and **Windows desktop automation (via UI Automation `FindAllBuildCache`)**.  
Instead of capturing full-screen screenshots on every step, the engine exposes a compact text element map (`Api.line_map()`, capped at 60 elements by default with `filter_query=` drill-down), targeted stale-element checks before actions, redacted task state logging, and on-demand PNG crops only when opaque regions (such as large or sparse `<canvas>` elements or low-UIA windows) are detected.

## Platform Requirements

- **Python:** `>= 3.10` (see [`pyproject.toml`](pyproject.toml))
- **Browser module (`BrowserSession`):** Chromium via Playwright (`playwright>=1.40`)
- **Windows Desktop modules (`DesktopSession`, `snapshot`, `blind_gap` desktop crops, `experiments/win32_probe.py`, `experiments/h2_*.py`):**
  - **Windows-only:** Relies on Win32 DLLs (`user32.dll`, `kernel32.dll`, `dwmapi.dll`), COM (`comtypes`), and `UIAutomationCore.dll`.
  - **Interactive desktop requirement:** Live OS input injection (`SendInput`), foreground enforcement (`GetForegroundWindow` / `SetForegroundWindow`), physical cursor kill-switch (`KillSwitch`), `GetCursorInfo` (in `experiments/h2_*.py`), and full-screen `ImageGrab.grab` require an interactive `Default` Windows desktop and fail with access-denied errors in isolated non-input sessions.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,benchmarks]"
playwright install chromium
```

## Quick Start

Browser example (from `computer_use_lite` or compatibility alias `engine`):

```python
from computer_use_lite import Api, BrowserSession

session = BrowserSession(url="https://example.com", headless=True, viewport=(1280, 720))
try:
    api = Api(session)
    print(api.discover_interactables())
    # Inspect or act on a discovered ID (e.g., e1)
    # details = api.inspect_element("e1")
    # result = api.execute_action("e1", "click")
finally:
    session.close()
```

Windows desktop example (Windows interactive session, targeting an existing window handle `hwnd`):

```python
from computer_use_lite import Api, DesktopSession

session = DesktopSession(hwnd)
api = Api(session)
print(api.discover_interactables())
```

Backwards-compatible imports (`from engine import Api, BrowserSession, DesktopSession, ...`) are preserved via `src/engine/`.

## MCP Server (Model Context Protocol)

Computer Use Lite ships an ultra-low-latency `stdio` MCP server (`computer_use_lite.mcp_server` / CLI entrypoint `computer-use-lite-mcp`) exposing 13 unified tools with MCP `ToolAnnotations`, thread-pinned isolated sessions (`state_fsync=False` on disposable temp `TaskState`), `http(s)` public URL validation blocking loopback, private (RFC1918/ULA), link-local/metadata, and unspecified targets by default (`CUL_MCP_ALLOW_PRIVATE_URLS=1` opt-in for private/local HTTP; `CUL_MCP_ALLOW_FILE_URLS=1` opt-in for `file://`), and automatic inline `ImageContent` crops **only** when an opaque canvas or sparse-UIA blind region is detected.

- **Start directly:** `computer-use-lite-mcp` (or `python -m computer_use_lite.mcp_server`)
- **Available tools:** `open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`

Example client configuration (**Claude Desktop** `claude_desktop_config.json`, **Cursor** `.cursor/mcp.json`, or any stdio MCP host):

```json
{
  "mcpServers": {
    "computer-use-lite": {
      "command": "python",
      "args": ["-m", "computer_use_lite.mcp_server"],
      "cwd": "/path/to/computer-use-lite"
    }
  }
}
```

## Architecture Overview

Package modules in `src/computer_use_lite/`:

- **`snapshot.py` (M0):** Captures target window geometry (`DwmGetWindowAttribute` / `GetWindowRect`), process name, client origin, and thread-safe monotonic revisions.
- **`browser_cdp.py` (M1-Browser):** Discovers interactive DOM/AX nodes (including `searchbox` and semantic tags/roles in cross-origin OOPIF `DOMSnapshot` frames) using `DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree`, prunes redundant `<label>`/nested fragments and overflow-clipped nodes, performs lazy candidate occlusion filtering, checks live occlusion via `elementFromPoint`, clears/scrolls inputs, and selects active tabs in `connect` mode.
- **`desktop_uia.py` (M1-Windows, Windows-only):** Runs HWND-scoped UIA `FindAllBuildCache` on a COM worker thread, executes `Invoke -> Toggle -> SelectionItem -> ExpandCollapse -> SendInput`, activates Chromium/Electron accessibility (`WM_GETOBJECT` / temporary `SPI_SETSCREENREADER`), and enforces foreground + 5 px `KillSwitch` safety.
- **`blind_gap.py` (M2):** Detects large (`>= 25%`) or sparse (`>= 5%`) `<canvas>` elements and low-UIA desktop surfaces (`< 6` controls), exporting cropped PNGs on demand (prioritizing `PrintWindow` before `ImageGrab` when a desktop `hwnd` is covered, non-foreground, minimized, or cloaked). Cursor-probing prototypes were not shipped into the engine (see [`docs/ARCHITECTURE_DECISION.md`](docs/ARCHITECTURE_DECISION.md)).
- **`resolver.py` (M3):** Performs IoU deduplication (`0.75`), assigns stable `eN` IDs, tracks hover deltas (`reconcile_hover`), and enforces `assert_fresh` (revision mismatch, disappearance/disabled, occlusion, or `> 2` px movement).
- **`hover.py` (M4):** Explicit single-element `hover_and_diff()` that prunes disappeared controls and appends newly revealed controls.
- **`api.py` & `state.py` (M5):** Implements `discover_interactables`, `inspect_element`, `execute_action`, capped/filtered `line_map`, and atomic `TaskState` persistence with SHA-256 + length value redaction.

## Repository Layout

- `src/computer_use_lite/` — Core engine source package (`src/engine/` provides backwards-compatible imports)
- `tests/` — Audit regression tests ([`tests/test_engine_audit.py`](tests/test_engine_audit.py)), live E2E suite ([`tests/test_e2e.py`](tests/test_e2e.py)), benchmark contracts ([`tests/test_benchmarks_study.py`](tests/test_benchmarks_study.py)), and HTML fixtures
- `experiments/` — Standalone exploration scripts (`h1_*`, `h2_*`, `win32_probe.py`) and fixtures
- `benchmarks/` — Multi-target real-app runner ([`benchmark_real.py`](benchmarks/benchmark_real.py)), isolated 9-candidate study suite ([`run_all.py`](benchmarks/run_all.py), [`bench_uia.py`](benchmarks/bench_uia.py), [`bench_remote_ops.py`](benchmarks/bench_remote_ops.py), [`bench_browser.py`](benchmarks/bench_browser.py), [`bench_action_freshness.py`](benchmarks/bench_action_freshness.py)), and 20-task paired agent harness ([`bench_agent_20tasks.py`](benchmarks/bench_agent_20tasks.py), [`agent_tasks.py`](benchmarks/agent_tasks.py))
- `results/` — Recorded experiment, benchmark, E2E, and study outputs ([`results/perf_study/BENCHMARK_REPORT.md`](results/perf_study/BENCHMARK_REPORT.md))
- `docs/` — Architecture decision record ([`docs/ARCHITECTURE_DECISION.md`](docs/ARCHITECTURE_DECISION.md))
- `archive/` — Historical, invalidated, or ephemeral artifacts retained with status labels (see [`archive/README.md`](archive/README.md))

## Running Tests

Full Windows local run (headless Chromium + Windows UIA tests):

```powershell
pytest -v
python tests/test_e2e.py
```

Non-interactive CI-safe run (skips live Windows UIA / headful desktop tests marked `@pytest.mark.windows_desktop`):

```powershell
$env:CUL_SKIP_DESKTOP = "1"
pytest -v -rs
```

## Known Limitations

- Desktop automation (`DesktopSession`, `snapshot`, `experiments/h2_*`) does not run on Linux/macOS and does not walk the Windows Desktop Root (`HWND`-scoped only).
- Importing `computer_use_lite` loads Windows `user32` bindings at import time in `desktop_uia.py` and `snapshot.py` (while `blind_gap.py` invokes `user32` inside desktop `export()`).
- Live Win32 cursor/input/screen-grab verification fails inside isolated non-interactive desktops (`ERROR_ACCESS_DENIED`).
- Opaque UIs (`<canvas>`, unaccessible native widgets) are exposed as cropped PNG regions for caller inspection rather than decoded into semantic controls automatically.
- Copyright holder attribution in [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), and [`pyproject.toml`](pyproject.toml) still uses a `[TODO: Copyright Holder]` placeholder pending author confirmation.

---

## Benchmarks & Controlled Performance Study Methodology

- **Machine & Runtime Environment:** Windows 11 (`10.0.26200-SP0`), `11th Gen Intel(R) Core(TM) i5-11400F @ 2.60GHz` (6 physical / 12 logical cores), `15.84 GB RAM`, Python `3.12.10`, Playwright `1.64.0`, `comtypes 1.5.0`.
- **Single-Variable Benchmark Protocol ([`results/perf_study/BENCHMARK_REPORT.md`](results/perf_study/BENCHMARK_REPORT.md)):**
  - **UIA (`Exps 1–4`, `exp1_4_uia.json`):** `n_cold = 3`, `n_warm = 20` iterations per variant (`30` warm uncached `ElementFromHandle` calls) across Windows 11 Notepad, File Explorer, Chromium (`chrome://`/fixture with `--force-renderer-accessibility`), and Electron (Obsidian). Cold runs capture first-call initialization on a freshly spawned worker/apartment; warm statistics report `p50`, `p95`, `p99`, IPC count, and per-iteration CPU time.
  - **UIA Remote Operations (`Exp 5`, `exp5_remote_ops.json`):** `n_cold = 3`, `n_warm = 15` comparing `FindAllBuildCache` vs `CoreAutomationRemoteOperation` subtree walk and `K=30` batch property reads.
  - **Browser Discovery & Transport (`Exps 6–7, 9`, `exp6_7_9_browser.json`):** `n_cold = 1, n_warm = 10` across 4 adversarial corpus states (`initial_viewport`, `drawer_open`, `modal_occluded`, `scrolled_view`) and `n_cold = 2, n_warm = 10` on real sites (GitHub Trending, YouTube, Gmail sign-in, Google Maps); `n_cold = 2, n_warm = 15` for Exp 7 transport comparison.
  - **Post-Action Targeted Freshness (`Exp 8`, `exp8_freshness.json`):** `n_cold = 2, n_warm = 15` (Browser) and `n_cold = 2, n_warm = 10` (Desktop Notepad), testing `stale_safety_parity_rate = 1.0` across all 6 browser adversarial conditions (`stale_revision`, `modal_occluded`, `moved_gt_2px`, `disabled_dynamically`, `scrolled_out_of_viewport`, `removed_from_dom`) and both desktop conditions (`stale_revision`, `moved_gt_2px`).
- **Ground Truth (GT) & Statistical Noise Caveats:**
  - **Adversarial Corpus (`Exp 6`, `Exp 9`):** Evaluated against deterministic DOM/Shadow-DOM/cross-origin-iframe GT (`extract_corpus_ground_truth()`), explicitly verifying closed Shadow DOM (`closed_shadow_dom`) and cross-origin OOPIF (`cross_origin_iframe`) visibility.
  - **Real Public Sites (`Exp 6`):** No external curated GT exists; `ablation_cdp_no_boxmodel_loop` and `candidate_js_single_frame` are scored (`vs_control`) against viewport-filtered `Control CDP` (`BrowserSession.discover()`), which explains why Control CDP appears as `1.0000` in comparison tables. On GitHub Trending, `Control CDP` emits `629` raw nodes -> `160` in the `1280x720` viewport (including `106` `cursor:pointer` items and full-viewport wrapper containers) -> `120` after `Resolver.merge()` IoU deduplication, so JS recall is `38.12%` vs raw viewport Control (`49.17%` vs `Resolver`-deduplicated `120` controls).
  - **Measurement Noise & Direct WebSocket Reality:** Differences of `±3–5 ms` on `p50` fall within Windows scheduling and live-site layout noise. Direct persistent CDP WebSockets save `1.0–3.1 ms` on tiny ping calls (`ping_scroll`), while larger wins (`-98.2 ms` on GitHub Trending, `-15.3 ms` p50 / `-101.7 ms` p95 on Google Maps) come from removing Playwright's Node IPC serialization overhead on `0.7–1.4 MB` `DOMSnapshot` + `AXTree` payloads.
  - **Windows UIA `~2,000 ms` Action Floor Root Cause:** Diagnostic profiling proved the `~2,006 ms` per-action floor on Win11 Notepad (`SetValue`), Explorer (`Invoke`/`Toggle`/`SetValue`/`Select`), Chromium UIA, and native Win32 controls comes from `IUIAutomation` (`CUIAutomation`) defaulting to `AutoSetFocus = 1`. Switching to `CUIAutomation8` (`IUIAutomation2`) with `AutoSetFocus = 0` drops Notepad `SetValue` from `2,014.32 ms` to `1.71 ms` while preserving semantic background execution.
- Multi-target token/latency report & raw JSON: [`results/benchmarks/benchmarks_real.md`](results/benchmarks/benchmarks_real.md), [`results/benchmarks/benchmarks_real.json`](results/benchmarks/benchmarks_real.json)
- Isolated 9-candidate study & script: [`results/perf_study/BENCHMARK_REPORT.md`](results/perf_study/BENCHMARK_REPORT.md), [`benchmarks/benchmark_real.py`](benchmarks/benchmark_real.py)

## Test & Verification Results

- Audit & regression suite: [`tests/test_engine_audit.py`](tests/test_engine_audit.py), [`tests/test_audit_fixes.py`](tests/test_audit_fixes.py)
- Live E2E suite (writes JSON to temp directory by default unless `--write-results <path>` is passed) & archived Phase D baseline: [`tests/test_e2e.py`](tests/test_e2e.py), [`results/e2e/e2e_results.json`](results/e2e/e2e_results.json)
- Benchmark contract suite: [`tests/test_benchmarks_study.py`](tests/test_benchmarks_study.py)

## Experiments, Failed Hypotheses, and Architecture Decisions

- Decision log & keep/drop status: [`docs/ARCHITECTURE_DECISION.md`](docs/ARCHITECTURE_DECISION.md)
- Browser canvas cursor probes (H1 / H1b): [`results/experiments/h1_report.md`](results/experiments/h1_report.md), [`results/experiments/h1b_report.md`](results/experiments/h1b_report.md), [`results/experiments/h1b_report.json`](results/experiments/h1b_report.json)
- Desktop Gate 0 calibration (H2 Gate 0): [`results/experiments/h2_gate0.json`](results/experiments/h2_gate0.json), [`results/experiments/h2_gate0_probes.json`](results/experiments/h2_gate0_probes.json)
- Hover visual diff precondition status (H3): [`results/experiments/h3_report.md`](results/experiments/h3_report.md)
- Stale / invalidated pre-fix H2 Grid artifacts (negative historical record): [`archive/stale_h2_grid/README.md`](archive/stale_h2_grid/README.md)

## License

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

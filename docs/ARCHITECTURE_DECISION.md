# Architecture Decision - Computer Use Lite

Re-validated on Windows (Python 3.12, Chromium headless/headful), 2026-11-24.
Every number below comes from measured runs in `experiments/`, `benchmarks/`, and `tests/`; nothing is estimated except the `~1229`-token 1280x720 screenshot baseline.
> Note: Paths updated for M2 repository layout (`results/`, `experiments/`, `archive/stale_h2_grid/`). A subsequent `Default`-desktop Gate 0 run passed in `results/experiments/h2_gate0.json` (`21:37`), while no post-fix Grid Scan has run; H2 remains DROPPED / NOT SHIPPED.

## 1. Scorecard

| hypothesis | what was measured | recall | precision | latency | verdict |
| --- | --- | --- | --- | --- | --- |
| **H1** browser canvas cursor probe | 880 probes, step 32, Maps @ Times Sq (`h1_report.md`) | 81.8% | 81.8% | 29.46 s (33.5 ms/probe) | **SIGNAL PASS / PRACTICAL REJECTED** |
| **H1b** latency + pipelining + clustering (re-validated) | 880 probes, Google Maps: single-rAF vs no-rAF `sync` vs `yield2` vs pipelined `pipe_20`/`pipe_80` (`h1b_report.json`) | 100% agreement (`sync`, `yield2`); 33.5%-34.4% (`pipe_20`/`pipe_80`) | - | `raf` 29.39 s (33.40 ms/pt); `sync` 14.93 s (16.97 ms/pt); `pipe_80` 0.77 s (0.87 ms/pt) | **SIGNAL-ONLY / PRACTICAL REJECTED** |
| **H2 Gate 0** per-toolkit calibration | Prior run invalidated by ~87 px `client_origin` offset (`a2_origin_proof.png`: `(0, 87)` px shift) and truncated 50 ms sweep; fixes applied (`[2, 5, 10, 15, 30, 50, 80, 120]` ms, randomized + ordered, `content_origin`) | *invalidated; live re-run blocked in `exebox` desktop* | *invalidated* | *invalidated* | **BLOCKED IN `exebox` (`ERROR_ACCESS_DENIED` on `GetCursorInfo`)** |
| **H2 2B** desktop grid scan | Prior 240-pt run invalidated by ~87 px offset and constant `50 ms` settle; fixed script requires `Default`-desktop re-run | *invalidated; pending `Default` desktop run* | *invalidated* | *invalidated* | **NOT SHIPPED (pending `Default` desktop validation)** |
| **H3** hover visual diff | Not run | - | - | - | **NOT BUILT** |

### Why H1b changed in numbers (verdict unchanged: `SIGNAL-ONLY` / DROP browser cursor probe)

- **Old invalid claim:** `h1b_latency_cluster.py` previously imported `PROBE_JS` (which awaited `requestAnimationFrame` inside JS), causing `"sync"` and `"yield2"` to wait 1 rAF (`33.33 ms/probe`) and `"raf"` to wait 2 rAFs (`50.11 ms/probe`).
- **Re-validated reality (`h1b_report.json`):** With a synchronous `NO_RAF_PROBE_JS` and a 1-rAF baseline:
  - Single-rAF wait WAS roughly half the latency (`29.39 s` -> `14.93 s` in `sync`, `16.97 ms/probe`), maintaining `100.0%` agreement.
  - Sequential CDP round trips (`14.93 s`) still fail the `< 3.0 s` gate by ~5x.
  - Async CDP pipelining (`pipe_20` = `0.90 s` / `1.02 ms/pt`, `pipe_80` = `0.77 s` / `0.87 ms/pt`) clears `< 3.0 s`, **but hit agreement collapses to `33.5%–34.4%`** (far below `>= 90%`) as Chromium coalesces/drops intermediate `mouseMoved` cursor updates.
  - No mode passes both `>= 90%` agreement and `< 3.0 s`; **M2 browser cursor probe stays DROPPED**.

### Why H2 numbers are marked invalidated rather than kept

- Visual inspection + `a2_origin_proof.png` proved `client_origin(hwnd)` sat `(0, 87)` px above `Chrome_RenderWidgetHostHWND` (`(28, 20)` vs `(28, 107)`), shifting old Gate 0 and grid points into Chrome's tab/omnibox chrome and invalidating old `26.7%` UIA recall, `73.3%` hand rate, and `53.3%` grid precision/recall.
- Inside this agent's `exebox` isolated Windows desktop (`GetThreadDesktop = exebox-...`), `GetCursorInfo` / `GetCursorPos` / `SendInput` / `ImageGrab.grab` return `ERROR_ACCESS_DENIED (5)`. Fixed `experiments/h2_desktop_gate0.py`, `experiments/h2_desktop_grid.py`, and `experiments/win32_probe.py` are ready to run from a `Default`-desktop terminal; until that run clears all gates, **desktop cursor probing stays DROPPED / NOT SHIPPED**.

## 2. KEEP / DROP

| layer | decision | evidence |
| --- | --- | --- |
| M0 `snapshot.py` bounds + monotonic revision | **KEEP** | `window()` no longer bumps revision on `bounds()` calls; `TaskState` keeps revision monotonic across runs |
| M1-Browser `browser_cdp.py` DOMSnapshot + AXTree | **KEEP** | Captures role-less `clickable` + `switch`, viewport scroll-adjusted coords, disabled/occlusion filtering, `connect` active-tab detection, `scrollIntoView` + safety check |
| M1-Windows `desktop_uia.py` `FindAllBuildCache` | **KEEP** | Lightweight O(1) `signature()`, cached `GetCachedPropertyValue` patterns/RuntimeId, `Invoke->Toggle->SelectionItem->ExpandCollapse->SendInput` chain, `WM_GETOBJECT` a11y activation, foreground/kill-switch guards |
| M2 cursor probe - browser | **DROP** | Re-validated `sync` = `14.93 s` (> 3.0 s); `pipe_80` = `0.77 s` at `34.4%` agreement (< 90%) |
| M2 cursor probe - desktop | **DROP** | Prior run invalidated by `(0, 87)` px origin bug; live `Default`-desktop re-run pending (`exebox` blocks `GetCursorInfo`) |
| M2 blind-region crop exporter (`blind_gap.py`) | **KEEP** | Detects `>= 25%` canvas and `>= 5%` sparse canvas without false positives on normal DOM pages; preserves negative virtual-desktop coords |
| M3 `resolver.py` dedupe + stale guard | **KEEP** | Enforces revision mismatch, modal occlusion, removal, and > 2 px movement; reconciles disappeared hover elements |
| M4 `hover.py` on-demand hover | **KEEP** | Single settle wait (removed duplicate 350 ms sleep) + zombie element cleanup |
| M5 `api.py` line map + `state.py` | **KEEP** | Capped at 60 elements (`filter_query` drill-down), atomic writes, failed action logging, SHA-256 + length redaction for typed/secret values |
| H3 hover visual diff | **NOT BUILT** | Precondition unmet |

## 3. Measured Token & Latency Benchmarks (`results/benchmarks/benchmarks_real.json`, vs 1229-token screenshot)

| target | kind | elements | blind regions | latency (ms) | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/fixtures/form.html` | **fixture** | 4 | 0 | 17.4 | 54.2 (0.04x) | 54.2 (0.04x) |
| GitHub Trending | real browser | 120 | 0 | 292.2 | 654.0 (0.53x) | 1263.8 (1.03x) |
| YouTube | real browser | 27 | 0 | 143.7 | 386.8 (0.31x) | 386.8 (0.31x) |
| Gmail (sign-in) | real browser | 14 | 0 | 75.8 | 187.2 (0.15x) | 187.2 (0.15x) |
| Google Maps (`@40.7580,-73.9855,17z`) | real canvas | 64 | 1 | 210.5 | 697.8 (0.57x) | 719.5 (0.59x) |
| Notepad (Win11) | real desktop | 25 | 0 | 82.8 | 307.0 (0.25x) | 307.0 (0.25x) |
| File Explorer | real desktop | 90 | 0 | 188.0 | 712.0 (0.58x) | 1036.5 (0.84x) |
| Chromium shell (before a11y trigger) | real desktop | 14 interactive (36 total) | - | - | - | - |
| Chromium shell (after `WM_GETOBJECT`) | real desktop | 18 | 0 | 26.7 | 194.5 (0.16x) | 194.5 (0.16x) |
| Chromium shell (`--force-renderer-accessibility`) | real desktop | 18 | 0 | 39.3 | 194.5 (0.16x) | 194.5 (0.16x) |

Uncapped dense DOM/UIA trees (e.g. GitHub Trending at `1263.8` tokens = `1.03x`) can exceed a single viewport screenshot, which is why `Api.line_map()` caps output at 60 elements by default (`0.53x` on GitHub Trending) with `filter_query=` drill-down.

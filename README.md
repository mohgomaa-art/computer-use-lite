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

## Architecture Overview

Package modules in `src/computer_use_lite/`:

- **`snapshot.py` (M0):** Captures target window geometry (`DwmGetWindowAttribute` / `GetWindowRect`), process name, client origin, and thread-safe monotonic revisions.
- **`browser_cdp.py` (M1-Browser):** Discovers interactive DOM/AX nodes using CDP `DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree`, applies scroll offsets, filters disabled/occluded elements, checks occlusion via `elementFromPoint`, clears/scrolls inputs, and selects active tabs in `connect` mode.
- **`desktop_uia.py` (M1-Windows, Windows-only):** Runs HWND-scoped UIA `FindAllBuildCache` on a COM worker thread, executes `Invoke -> Toggle -> SelectionItem -> ExpandCollapse -> SendInput`, activates Chromium/Electron accessibility (`WM_GETOBJECT` / temporary `SPI_SETSCREENREADER`), and enforces foreground + 5 px `KillSwitch` safety.
- **`blind_gap.py` (M2):** Detects large (`>= 25%`) or sparse (`>= 5%`) `<canvas>` elements and low-UIA desktop surfaces (`< 6` controls), exporting cropped PNGs on demand. Cursor-probing prototypes were not shipped into the engine (see [`docs/ARCHITECTURE_DECISION.md`](docs/ARCHITECTURE_DECISION.md)).
- **`resolver.py` (M3):** Performs IoU deduplication (`0.75`), assigns stable `eN` IDs, tracks hover deltas (`reconcile_hover`), and enforces `assert_fresh` (revision mismatch, disappearance/disabled, occlusion, or `> 2` px movement).
- **`hover.py` (M4):** Explicit single-element `hover_and_diff()` that prunes disappeared controls and appends newly revealed controls.
- **`api.py` & `state.py` (M5):** Implements `discover_interactables`, `inspect_element`, `execute_action`, capped/filtered `line_map`, and atomic `TaskState` persistence with SHA-256 + length value redaction.

## Repository Layout

- `src/computer_use_lite/` — Core engine source package (`src/engine/` provides backwards-compatible imports)
- `tests/` — Audit regression tests, E2E suite, and HTML test fixtures
- `experiments/` — Standalone exploration scripts (`h1_*`, `h2_*`, `win32_probe.py`) and fixtures
- `benchmarks/` — Multi-target real-app benchmark runner (`benchmark_real.py`)
- `results/` — Recorded experiment, benchmark, and E2E outputs
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

## [TODO] Benchmarks

> **TODO:** Summarize verified final latency and token benchmarks once all pending runs stabilize.

- Real-application benchmark report & raw JSON: [`results/benchmarks/benchmarks_real.md`](results/benchmarks/benchmarks_real.md), [`results/benchmarks/benchmarks_real.json`](results/benchmarks/benchmarks_real.json)
- Benchmark script: [`benchmarks/benchmark_real.py`](benchmarks/benchmark_real.py)

## [TODO] Test & Verification Results

> **TODO:** Record finalized CI and full-desktop test verification summaries here.

- Audit & regression suite: [`tests/test_engine_audit.py`](tests/test_engine_audit.py)
- Live E2E suite & recorded output: [`tests/test_e2e.py`](tests/test_e2e.py), [`results/e2e/e2e_results.json`](results/e2e/e2e_results.json)

## [TODO] Experiments, Failed Hypotheses, and Invalidated Runs

> **TODO:** Document final conclusions once the remaining `Default`-desktop `experiments/h2_desktop_grid.py` run completes.

- Decision log & keep/drop status: [`docs/ARCHITECTURE_DECISION.md`](docs/ARCHITECTURE_DECISION.md)
- Browser canvas cursor probes (H1 / H1b): [`results/experiments/h1_report.md`](results/experiments/h1_report.md), [`results/experiments/h1b_report.md`](results/experiments/h1b_report.md), [`results/experiments/h1b_report.json`](results/experiments/h1b_report.json)
- Desktop Gate 0 calibration (H2 Gate 0): [`results/experiments/h2_gate0.json`](results/experiments/h2_gate0.json), [`results/experiments/h2_gate0_probes.json`](results/experiments/h2_gate0_probes.json)
- Hover visual diff precondition status (H3): [`results/experiments/h3_report.md`](results/experiments/h3_report.md)
- Stale / invalidated pre-fix H2 Grid artifacts (negative historical record): [`archive/stale_h2_grid/README.md`](archive/stale_h2_grid/README.md)

## License

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

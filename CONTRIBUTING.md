# Contributing to Computer Use Lite

This project is an early-stage work in progress (`Apache-2.0`).

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,benchmarks]"
playwright install chromium
```

## Running Tests

- **Full local Windows run** (requires an interactive Windows desktop session):
  ```powershell
  pytest -v
  python tests/test_e2e.py
  ```
- **CI / non-interactive run** (skips `@pytest.mark.windows_desktop` tests):
  ```powershell
  $env:CUL_SKIP_DESKTOP = "1"
  pytest -v -rs
  ```

## Guidelines

1. **SPDX headers:** Add `# SPDX-License-Identifier: Apache-2.0` to the top of any new Python file (below shebang if present).
2. **Windows / desktop boundaries:** Mark tests that open headful desktop apps or require live UIA/SendInput/cursor access with `@pytest.mark.windows_desktop` and skip cleanly when `CUL_SKIP_DESKTOP=1` or `sys.platform != "win32"`.
3. **No personal paths or secrets in tracked outputs:** Generated runtime artifacts, crops, and local screenshots must write into gitignored locations (`results/crops/`, `results/runtime/`, `archive/`) and never commit user-specific home directory paths (`%USERPROFILE%`).
4. **Preserve negative evidence:** Keep failed or invalidated experiment outputs under `archive/` with explicit labels rather than silently deleting them.

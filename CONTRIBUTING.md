# Contributing to Computer Use Lite

Computer Use Lite is an open experimental research project (`Apache-2.0`) authored by Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/)). Read [docs/INDEX.md](docs/INDEX.md) and [docs/RESEARCH_METHODOLOGY.md](docs/RESEARCH_METHODOLOGY.md) before proposing architectural or benchmark changes.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,benchmarks]"
playwright install chromium
```

## Environment Flags for Local Runs & Tests

- `CUL_SKIP_DESKTOP=1`: skips `@pytest.mark.windows_desktop` tests on headless CI / non-interactive desktops (non-interactive `@pytest.mark.windows_only` Win32/UIA COM checks still execute on Windows; Windows host required at import time).
- `CUL_MCP_HEADFUL=1`: opens MCP `open_browser` sessions headfully when `headless` is omitted.
- `CUL_AGENT_CURSOR=0|1` & `CUL_AGENT_CURSOR_GLIDE_MS=<0..600>`: controls the 3D cursor overlay.
- `CUL_MCP_DIRECT_WS=0`: disables loopback `--remote-debugging-port` WebSocket transport and uses Playwright `CDPSession`.
- `CUL_MCP_ALLOW_PRIVATE_URLS=1` / `CUL_MCP_ALLOW_FILE_URLS=1`: local fixture opt-ins only.

## Running Tests

- **Full local Windows run** (all `70` tests; requires an active interactive Windows desktop session):
  ```powershell
  pytest -v -rs --strict-markers -W error::pytest.PytestReturnNotNoneWarning
  python tests/test_e2e.py
  ```
- **Dedicated Windows Desktop & Cursor Overlay native integration run** (`12` `@pytest.mark.windows_desktop` tests):
  ```powershell
  pytest -m windows_desktop -v -rs --strict-markers -W error::pytest.PytestReturnNotNoneWarning
  pytest tests/test_cursor_overlay.py -m windows_desktop -v -rs --strict-markers
  ```
- **CI / non-interactive run** (`58` non-interactive tests + `12` skipped `@pytest.mark.windows_desktop` tests):
  ```powershell
  $env:CUL_SKIP_DESKTOP = "1"
  pytest --collect-only -q --strict-markers -m "not windows_desktop"
  pytest -v -rs --strict-markers -W error::pytest.PytestReturnNotNoneWarning
  python scripts/verify_copyright_headers.py
  ```

## Guidelines

1. **SPDX & Attribution Headers:** Preserve existing copyright/SPDX headers (`# SPDX-License-Identifier: Apache-2.0`) and add SPDX headers cleanly to new source files ([NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md)).
2. **Windows / Desktop Markers:** Mark tests requiring headful apps, live UIA, `SendInput`, `#32770` native dialogs, layered overlay windows, or pointer movement with `@pytest.mark.windows_desktop` and skip cleanly when `CUL_SKIP_DESKTOP=1` or `sys.platform != "win32"`. Mark non-interactive Win32/COM tests with `@pytest.mark.windows_only`.
3. **No Personal Paths or Secrets in Tracked Docs/Outputs:** Runtime crops, screenshots, and local logs belong in gitignored folders (`results/crops/`, `results/runtime/`, `live_runs/`, `fix_runs/`, etc.); never commit workstation user paths (`%USERPROFILE%`).
4. **Preserve Negative Evidence & Provenance:** Do not delete or rewrite failed or invalidated experiment records; archive superseded reports in [research_archive/](research_archive/INDEX.md) and update [`docs/`](docs/INDEX.md) with explicit commit provenance and epistemic tags (`[MEASURED]`, `[VERIFIED-CODE]`, `[REPORTED]`, `[PROPOSAL]`).

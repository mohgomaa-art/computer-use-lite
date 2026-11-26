# Computer Use Lite (CUL)

**Author:** Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/) · [AUTHORS.md](AUTHORS.md))  
**Version Baseline:** `0.1.0-alpha` + post-`0.1.0-alpha` P0 & Cursor Overlay work on `main` (`d47b4e9`)  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**License:** [Apache-2.0](LICENSE) ([NOTICE](NOTICE), [CITATION.cff](CITATION.cff))

> [!WARNING]
> **Experimental Research Preview:** Computer Use Lite is an open research project exploring hybrid semantic UI perception, targeted visual fallbacks, and live visual cursor feedback for AI agents. Verified security boundaries, unrun live VLM evaluations, and open platform limits remain explicitly documented in [SECURITY.md](SECURITY.md) and [Known Limitations](docs/KNOWN_LIMITATIONS.md). **Do not deploy against untrusted multi-tenant hosts or arbitrary untrusted web navigation.**

---

## 1. Overview & Research Problem

Purely vision-based computer-use agents that attach full-resolution screenshots on every step incur recurring token, latency, and coordinate-grounding costs even when interacting with structured web DOM forms or native Windows controls.

**Computer Use Lite (CUL)** investigates a local-first hybrid alternative:

1. **Semantic-first discovery:** Extract interactive controls via Chromium CDP (`DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree`) and scoped Windows UI Automation (`CUIAutomation8` COM MTA), formatting output as a compact `REV:N` `line_map` (`eN|role|name|x,y,w,h|actions`).
2. **Revision-checked element resolution:** Bind actions to short element IDs (`e1`, `e2`, ...) validated against monotonic revisions (`REV:N`), `<= 2` px geometry stability, and viewport occlusion/hit-test checks (`StaleElementError`) before clicking or typing.
3. **Targeted visual fallback:** Export inline PNG crops (`blindN`) **only** when `blind_gap` detects an unmapped opaque `<canvas>` or a sparse-UIA desktop surface (`low_uia`).
4. **Non-interfering Cursor Overlay:** Render an optional Frosted Obsidian-Glass & Satin Chrome 3D cursor overlay in headful Chromium (CSP-safe DOM+SVG) and Windows desktop sessions (`60 Hz` click-through `WS_EX_LAYERED` HWND excluded from screen capture) without shifting discovery results or tripping pointer safety guards.

This repository preserves **positive benchmarks, negative/abandoned hypotheses, audit trails, and open security constraints together** so external researchers and engineers can verify every conclusion from raw artifacts. See [docs/INDEX.md](docs/INDEX.md) for the complete documentation map.

---

## 2. Implemented Capabilities (`HEAD` `d47b4e9`)

| Layer | Modules ([src/computer_use_lite/](src/computer_use_lite/)) | Current Scope & Status |
| :--- | :--- | :--- |
| **Browser CDP Engine** | [`browser_cdp.py`](src/computer_use_lite/browser_cdp.py), [`hover.py`](src/computer_use_lite/hover.py) | Persistent `DirectCdpClient` WebSocket (`websockets`) + Playwright Chromium lifecycle (`direct_ws` optional via `CUL_MCP_DIRECT_WS=0`), 2-call `DOMSnapshot` + `AXTree`, paint-order & ancestor `overflow` clipping, multi-tab context tracking (`list_tabs`, `switch_tab`, `close_tab`), `--site-per-process` multi-doc fixture extraction, hover delta tracking, `elementFromPoint` freshness check, CDP `Fetch` SSRF redirect/sub-request guard |
| **Windows Desktop UIA** | [`desktop_uia.py`](src/computer_use_lite/desktop_uia.py) | **Windows-only:** dedicated COM MTA worker (`CUIAutomation8`, `AutoSetFocus=0`, transient init `COMError` retry), single-HWND `FindAllBuildCache`, UIA pattern invocation -> `SendInput` fallback, Win32 `#32770` Save As text commit (`_commit_dialog_text`) + `DIALOG_ALERT:` static text extraction, foreground enforcement, 5 px cursor `KillSwitch` |
| **3D Cursor Overlay** | [`cursor_overlay.py`](src/computer_use_lite/cursor_overlay.py), [`desktop_cursor_overlay.py`](src/computer_use_lite/desktop_cursor_overlay.py) | `64x64` vector cursor registry, CSP/Trusted-Types-safe browser overlay, dedicated `60.0 Hz` Win32 `WS_EX_LAYERED \| WS_EX_TRANSPARENT \| WS_EX_TOPMOST \| WS_EX_NOACTIVATE` desktop overlay (`_WDA_EXCLUDEFROMCAPTURE`, zero `SendInput` animation glide), `CUL_AGENT_CURSOR`, `CUL_AGENT_CURSOR_GLIDE_MS`, `CUL_MCP_HEADFUL` |
| **Semantic API & Guards** | [`api.py`](src/computer_use_lite/api.py), [`resolver.py`](src/computer_use_lite/resolver.py), [`snapshot.py`](src/computer_use_lite/snapshot.py) | Unified `Api` (`discover_interactables`, `inspect_element`, `execute_action`, `hover_element`, `line_map`), `60`-element default cap with `filter_query`, `searchbox` `read_value()` + password redaction, action outcome cursor cues (`ok` vs `verified`) |
| **Visual Gap Fallback** | [`blind_gap.py`](src/computer_use_lite/blind_gap.py) | Crops bounded regions only for `opaque_canvas`, `small_opaque_canvas`, or desktop `low_uia` (`< 6` controls); prioritizes Win32 `PrintWindow` over `ImageGrab` when target windows are covered, minimized, or cloaked |
| **State & Redaction** | [`state.py`](src/computer_use_lite/state.py) | Atomic temp-file `TaskState` persistence (`fsync=False` option for disposable MCP scratch sessions); strips non-`None` action `"value"` payloads to `{value_length, value_sha256, value_redacted: true}` |
| **MCP Server (`stdio`)** | [`mcp_server.py`](src/computer_use_lite/mcp_server.py), [`session_manager.py`](src/computer_use_lite/session_manager.py) | `FastMCP` `stdio` server exposing `13` tools with per-session thread isolation (`MAX_SESSIONS=16`), SSRF host/scheme/IP normalization checks (`CUL_MCP_ALLOW_PRIVATE_URLS`, `CUL_MCP_ALLOW_FILE_URLS`), `HEADLESS:`/`CURSOR:` headers, bounded inputs, blocked OS Win/Meta hotkeys |
| **Compatibility Shims** | [`src/engine/`](src/engine/) | Backwards-compatible `importlib` module aliases re-exporting core engine symbols |

---

## 3. Documentation & Repository Structure

- **Documentation Hub:** [docs/INDEX.md](docs/INDEX.md)
  - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Engine components, discovery/action lifecycle, Cursor Overlay, and MCP/security flows
  - [docs/ARCHITECTURE_DECISION.md](docs/ARCHITECTURE_DECISION.md) — Architectural Decision Records & `KEEP`/`DROP`/`HOLD` empirical scorecard
  - [docs/RESEARCH_FINDINGS.md](docs/RESEARCH_FINDINGS.md) — Consolidated empirical conclusions (positive, negative, and live-probe results)
  - [docs/RESEARCH_METHODOLOGY.md](docs/RESEARCH_METHODOLOGY.md) — Epistemic tags, proxy metrics (`TOKENS_EST`, `1,229` baseline), and confounds
  - [docs/BENCHMARKS.md](docs/BENCHMARKS.md) — Test suites, `benchmarks_real`, `perf_study` Exps `1–9`, `20`-task oracle harness, and unrun gaps
  - [docs/OPTIMIZATION_ROADMAP.md](docs/OPTIMIZATION_ROADMAP.md) — `P0` completed/fixture-verified fixes vs unimplemented `P1`/`P2` proposals
  - [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) — Verified platform, discovery, security, and benchmark boundaries
  - [docs/RESEARCH_HISTORY.md](docs/RESEARCH_HISTORY.md) — Chronological evolution across all development waves
- **Historical Archive:** [research_archive/INDEX.md](research_archive/INDEX.md) — Preserved audit reports, stale-process stress runs, skill validation dossiers, release-prep snapshots, and links to anchored raw experiment data ([results/](results/), [archive/](archive/), [experiments/](experiments/)).
- **Code & Suites:** [src/computer_use_lite/](src/computer_use_lite/), [tests/](tests/), [benchmarks/](benchmarks/), [experiments/](experiments/).

---

## 4. Installation

**Requirements:**
- **OS:** Windows 10/11 required at runtime (`desktop_uia.py` and `snapshot.py` bind `ctypes.WinDLL("user32")` on module import; see [Known Limitations](docs/KNOWN_LIMITATIONS.md)).
- **Python:** `>=3.10` (tested in CI and benchmarks on Python `3.12`).

```powershell
git clone https://github.com/mohgomaa-art/computer-use-lite.git
cd computer-use-lite

python -m pip install -e ".[dev,benchmarks]"
python -m playwright install chromium
```

Dependencies declared in [`pyproject.toml`](pyproject.toml): `playwright>=1.40`, `pillow>=10.0`, `websockets>=14.0`, `mcp>=1.25.0,<2`, plus Windows dependencies `uiautomation>=2.0.29` and `comtypes>=1.5.0` (see [NOTICE](NOTICE)).

---

## 5. Quick Start

### Python API (Browser)

```python
from pathlib import Path
from computer_use_lite import Api, BrowserSession

session = BrowserSession(
    url="https://example.com",
    headless=True,
    viewport=(1280, 720),
)
try:
    api = Api(
        session,
        state_path=Path("./runtime/task_state.json"),
        crops_dir=Path("./runtime/crops"),
    )
    line_map = api.discover_interactables(max_elements=60)
    print(line_map)
    # Example output:
    # REV:1 | WIN:Example Domain | ELEMENTS:1 | BLIND_REGIONS:0
    # e1|link|More information...|...,...,...,...|click

    # Execute against explicit element ID + revision:
    result = api.execute_action("e1", "click", revision=1)
    print(result)
finally:
    session.close()
```

### Windows Desktop Session (`DesktopSession`)

```python
from computer_use_lite import Api, DesktopSession
from computer_use_lite.desktop_uia import list_windows

windows = list_windows(title_contains="Notepad")
if windows:
    session = DesktopSession(windows[0]["hwnd"])
    try:
        api = Api(session)
        print(api.discover_interactables(max_elements=40))
    finally:
        session.close()
```

### MCP Server (`stdio`)

Launch via console script or module entrypoint:

```powershell
computer-use-lite-mcp
# or
python -u -m computer_use_lite.mcp_server
```

Example MCP client snippet:

```json
{
  "mcpServers": {
    "computer-use-lite": {
      "command": "python",
      "args": ["-u", "-m", "computer_use_lite.mcp_server"],
      "env": {}
    }
  }
}
```

Relevant MCP environment toggles verified in source:
- `CUL_MCP_HEADFUL=1`: launch `open_browser` headful by default when `headless` is omitted.
- `CUL_AGENT_CURSOR=0|1`: disable or force the Obsidian-Chrome 3D cursor overlay.
- `CUL_AGENT_CURSOR_GLIDE_MS=140`: smooth visual glide duration (`0..600` ms).
- `CUL_MCP_ALLOW_PRIVATE_URLS=1` / `CUL_MCP_ALLOW_FILE_URLS=1`: opt-in overrides for local fixture testing only.
- `CUL_MCP_DIRECT_WS=0`: disable `--remote-debugging-port` TCP socket and force Playwright's internal `CDPSession` adapter.

**Exposed `13` MCP tools:**  
`open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate` (`goto`, `back`, `list_tabs`, `switch_tab`, `close_tab`), `scroll`, `press_key`, `click_at`.

---

## 6. Verification & Benchmark Commands

```powershell
# Headless browser, security, audit-fix, MCP stdio & benchmark-contract tests
$env:CUL_SKIP_DESKTOP = "1"
pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning

# Full Windows suite including @pytest.mark.windows_desktop E2E & overlay tests
# (requires an interactive unlocked Windows user desktop)
pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning

# Compile sanity check + benchmark runners
python -m compileall -q src experiments benchmarks tests
python -m benchmarks.benchmark_real
python -m benchmarks.run_all --exp all
python -m benchmarks.bench_agent_20tasks --dry-run-oracle
```

- **Test Provenance Disclosure:** On the `v0.1.0-alpha` release-prep baseline (`698861d`), the full Windows suite recorded `52 passed in 68.86s`. Subsequent commits added `11` tests in `tests/test_cursor_overlay.py` (`7c7b9b4..4f9bcef`, currently modified locally) and `5` `P0-*` regression tests in `tests/test_audit_fixes.py` (`77cd171..a3291b3`). **No full-suite `pytest` re-run was executed during this documentation-only pass (`HEAD` `d47b4e9`), so post-`698861d` full-suite aggregate counts remain unverified here.**

---

## 7. Key Findings & Honest Limitations

Detailed datasets and confounds live in [docs/RESEARCH_FINDINGS.md](docs/RESEARCH_FINDINGS.md), [docs/BENCHMARKS.md](docs/BENCHMARKS.md), and [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md):

- **Compact maps & low discovery latency on structured UIs (`[MEASURED]` pre-P0 baselines):** Dual-origin corpus fixtures reached `recall=1.0, precision=1.0`, `P-01` cut `2,500`-cell Python occlusion CPU `p50` from `824.40 ms -> 19.32 ms`, COM `MTA` + `AutoSetFocus=0` eliminated `446–861 ms` cold `STA` and `~2,000 ms` per-action stalls, and `DirectCdpClient` saved `-98.21 ms` `p50` on GitHub Trending (`1.1 MB` Snapshot+AX payloads).
- **Documented rejections (`DROP`):** Browser and desktop cursor probing (`H1` `29.46 s`, `H1b` `14.93 s` / `34.4%` pipelined, `H2 2B` invalidated `(0, 87)` px origin, `H3` not built), `CoreAutomationRemoteOperation` UIA subtree walking (`Exp 5`), single-frame JS extraction (`Exp 6`), and top-frame `MutationObserver` (`Exp 9`).
- **Unverified / open scope:**
  - `benchmarks/bench_agent_20tasks.py` has **`20/20` deterministic oracle validation (`0` live VLM API calls executed)** — there is **no** comparative end-to-end live VLM win-rate claim over screenshot baselines.
  - `P0-1` OOPIF support passes deterministic `--site-per-process` unit fixtures, while live third-party cross-origin embeds (e.g., `youtube.com/embed`) remain unverified on restarted MCP.
  - `P1` and `P2` items (AX `checked`/`value`/`slider`/`readonly` metadata extraction, unified sticky-header clamping, `WS_EX_LAYOUTRTL` un-mirroring, Explorer inactive-tab filtering, Linux/macOS import decoupling, mouse drag-and-drop) remain **unimplemented proposals** ([docs/OPTIMIZATION_ROADMAP.md](docs/OPTIMIZATION_ROADMAP.md)).
  - `validate_navigation_url` + CDP `Fetch` interception blocks HTTP `3xx` redirect SSRF hops (`P0-4`), **but** OS-level DNS-rebinding TOCTOU between Python pre-check and Chromium socket connect remains open ([SECURITY.md](SECURITY.md)).

---

## 8. Contributing & Citation

- **Contributions:** See [CONTRIBUTING.md](CONTRIBUTING.md) and `.github/` templates.
- **Security Reports:** See [SECURITY.md](SECURITY.md).
- **Citation:** See [CITATION.cff](CITATION.cff).

```text
Computer Use Lite — Copyright 2026 Mohamed Gomaa (@mohgomaa-art)
Licensed under the Apache License, Version 2.0 (LICENSE / NOTICE)
```

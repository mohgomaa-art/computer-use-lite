# Computer Use Lite (CUL)

**Version:** `0.1.0-alpha`  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**Creator & Lead Developer:** Mohamed Gomaa ([AUTHORS.md](AUTHORS.md))  
**License:** [Apache-2.0](LICENSE) ([NOTICE](NOTICE), [CITATION.cff](CITATION.cff))

> [!WARNING]
> **Experimental Research Preview:** Computer Use Lite is an open research prototype investigating hybrid semantic UI perception and revision-checked control for AI agents. It has verified **open security and platform boundaries** (see [SECURITY.md](SECURITY.md) and [Known Limitations](docs/KNOWN_LIMITATIONS.md)) and is **not production-hardened** for untrusted web navigation or multi-tenant environments.

---

## 1. Overview & Research Problem

Visual "computer-use" agents that send full-resolution viewport or desktop screenshots at every interaction step pay recurring token, latency, and grounding costs, even when interacting with structured DOM forms or native Windows controls.

**Computer Use Lite (CUL)** investigates a narrower hybrid hypothesis:

1. **Semantic first:** Extract interactive elements directly from browser accessibility/DOM snapshots (`DOMSnapshot.captureSnapshot` + `Accessibility.getFullAXTree`) and native Windows UI Automation (`CUIAutomation8`), returning a compact token representation (`REV:N` + short IDs `e1`, `e2`, ...).
2. **Coordinate-free revision binding:** Bind actions to element IDs validated against revision counters (`REV:N`), pre-action geometry drift (`> 2` px), and hit-test / occlusion checks rather than blind `(x, y)` coordinates.
3. **Targeted visual fallback:** Crop PNG regions (`blind_N`) **only** for detected opaque `<canvas>` surfaces or low-UIA areas (`blind_gap.py`).

The repository preserves **both verified improvements and negative/unsolved findings** (including rejected cursor-grid experiments, cross-origin iframe gaps under strict Chromium site isolation, and unrun live VLM evaluations) so researchers and engineers can evaluate the architecture transparently.

---

## 2. Implemented Capabilities

| Layer | Implementation ([src/computer_use_lite/](src/computer_use_lite/)) | Current Scope & Status |
| :--- | :--- | :--- |
| **Browser Perception & Control** | [`browser_cdp.py`](src/computer_use_lite/browser_cdp.py), [`hover.py`](src/computer_use_lite/hover.py) | Persistent `DirectCdpClient` WebSocket (`websockets`) + Playwright Chromium launch/attach, 2-call `DOMSnapshot` + `AXTree`, paint-order & `overflow` clipping, hover reveal checks, `elementFromPoint` target checks |
| **Windows Desktop UIA** | [`desktop_uia.py`](src/computer_use_lite/desktop_uia.py) | **Windows-only:** dedicated COM MTA worker (`CUIAutomation8`, `AutoSetFocus=0`), `FindAllBuildCache`, UIA pattern execution -> `SendInput` fallback, foreground HWND enforcement, `KillSwitch` pointer abort |
| **Semantic Element API** | [`api.py`](src/computer_use_lite/api.py), [`resolver.py`](src/computer_use_lite/resolver.py), [`snapshot.py`](src/computer_use_lite/snapshot.py) | Unified `Api`, `REV:N` compact `line_map` (default `60`-element cap, `filter_query`), `> 2` px drift/occlusion/removal refusal, `inspect_element()` password redaction |
| **Targeted Visual Fallback** | [`blind_gap.py`](src/computer_use_lite/blind_gap.py) | Emits PNG crops only when unmatched `<canvas>` (`>= 240x160` px or sparse UI `< 6` controls) or `low_uia` surfaces exist; prioritizes Win32 `PrintWindow` over `ImageGrab` when target windows are covered |
| **State & Value Redaction** | [`state.py`](src/computer_use_lite/state.py) | Atomic temp-file `TaskState` persistence; strips raw non-`None` action `"value"` fields to `{value_length, value_sha256, value_redacted: true}` |
| **MCP Server** | [`mcp_server.py`](src/computer_use_lite/mcp_server.py), [`session_manager.py`](src/computer_use_lite/session_manager.py) | `stdio` FastMCP server exposing `13` tools with per-session worker thread isolation, host/scheme SSRF entry checks, viewport/limit clamping, and blocked OS modifier hotkeys |
| **Compatibility Shims** | [`src/engine/`](src/engine/) | Thin `importlib` module aliases re-exporting `computer_use_lite.*` |

Full component diagrams and module notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 3. Repository Map

- [src/computer_use_lite/](src/computer_use_lite/) — Core engine and `stdio` MCP server (`src/engine/` holds module alias shims).
- [tests/](tests/) — Unit, audit-fix regression, MCP `stdio`, benchmark-contract, and E2E suites.
- [benchmarks/](benchmarks/) — Phase D multi-target benchmark, 9-experiment performance study, dual-origin corpus, and 20-task agent harness.
- [experiments/](experiments/) & [archive/stale_h2_grid/](archive/stale_h2_grid/) — Historical exploratory scripts (`H1`, `H1b`, `H2`, `win32_probe.py`) and explicitly archived invalid experiments preserved as negative evidence.
- [results/](results/) — Measured JSON/Markdown datasets for `H1`–`H3`, `benchmarks_real`, `e2e_results`, `perf_study`, and `agent_benchmark` oracle validation.
- [docs/](docs/) — Canonical research and engineering documentation:
  - [ARCHITECTURE.md](docs/ARCHITECTURE.md)
  - [ARCHITECTURE_DECISION.md](docs/ARCHITECTURE_DECISION.md) *(historical architecture decision baseline)*
  - [RESEARCH_METHODOLOGY.md](docs/RESEARCH_METHODOLOGY.md)
  - [BENCHMARKS.md](docs/BENCHMARKS.md)
  - [KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)
  - [RESEARCH_HISTORY.md](docs/RESEARCH_HISTORY.md)

---

## 4. Installation

**Requirements:**
- **OS:** Windows 10/11 required for runtime execution (`desktop_uia.py` and `snapshot.py` load `ctypes.WinDLL("user32")` at import time; see [Known Limitations](docs/KNOWN_LIMITATIONS.md#platform--windows-uia-boundaries)).
- **Python:** `>=3.10` (verified in CI and local benchmarks on Python `3.12`).

```bash
git clone <repository-url>
cd computer-use-lite

python -m pip install -e ".[dev,benchmarks]"
python -m playwright install chromium
```

Dependencies installed automatically: `playwright>=1.40`, `pillow>=10.0`, `websockets>=14.0`, `mcp>=1.25.0`, plus Windows extras `uiautomation>=2.0.29` and `comtypes>=1.5.0` (see [NOTICE](NOTICE) for third-party licenses).

---

## 5. Quick Start

### Python API (Browser Example)

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
    # Example output header: "REV:1" followed by compact rows such as:
    # "e1 link 'More information...' [x,y,w,h]"

    # Execute against explicit revision + element ID from line_map:
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

Start via console script or module entrypoint:

```bash
computer-use-lite-mcp
# or
python -m computer_use_lite.mcp_server
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "computer-use-lite": {
      "command": "python",
      "args": ["-m", "computer_use_lite.mcp_server"],
      "env": {}
    }
  }
}
```

Set `"CUL_MCP_ALLOW_PRIVATE_URLS": "1"` in `env` **only** when testing trusted localhost/private network fixtures (`open_browser` / `navigate` block loopback, private, and link-local hosts by default).

**Exposed `13` MCP tools:**  
`open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`.

---

## 6. Running Tests & Benchmarks

### Test Suite

```bash
# Headless browser, security, audit-fix, MCP stdio & benchmark-contract tests
# (Windows desktop tests skipped when CUL_SKIP_DESKTOP=1)
CUL_SKIP_DESKTOP=1 pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning

# Full Windows suite including @pytest.mark.windows_desktop E2E & MCP desktop tests
# (requires an active, unlocked Windows user session)
pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning
```

On the pre-release Windows baseline (`HEAD`), the full suite measured **`52 passed in 68.86s`**.

### Benchmark Suites

```bash
# 1. Compile sanity check across all modules
python -m compileall -q src experiments benchmarks tests

# 2. Multi-target real application token/latency check (browser + desktop)
python -m benchmarks.benchmark_real

# 3. Isolated 9-experiment performance & accuracy study
python -m benchmarks.run_all --exp all

# 4. 20-task benchmark harness deterministic oracle check (0 LLM API calls)
python -m benchmarks.bench_agent_20tasks --dry-run-oracle
```

To run an actual live VLM comparison (`screenshot_baseline` vs `computer_use_lite`), pass `--provider openai|gemini|ollama` and `--model <name>` to `benchmarks.bench_agent_20tasks`.

---

## 7. Key Verified Findings & Honest Scope

Detailed tables, environments, confounds, and negative outcomes live in [docs/BENCHMARKS.md](docs/BENCHMARKS.md) and [docs/RESEARCH_HISTORY.md](docs/RESEARCH_HISTORY.md).

- **Verified strengths (`[MEASURED]` on local Windows `3.12` environment):**
  - Dual-origin fixture discovery (`DualOriginCorpusServer`) reached `recall = 1.0` and `precision = 1.0` after `P-04` pruning (`<label>` dedup, nested container collapsing, ancestor `overflow` clipping), and `P-01` reduced Python occlusion processing on a `2,500`-cell dense DOM from `824.40 ms` to `19.32 ms` `p50`.
  - Targeted `line_map` output stays compact against the repo's `1,229`-token `1280x720` screenshot proxy across tested targets (`form.html`: `54.2` tokens in `17.8 ms`; Notepad: `474.8` tokens in `140.2 ms`; GitHub Trending capped `60`: `654.0` tokens in `215.5 ms`, uncapped `1,263.8`; Explorer capped `60`: `711.0` tokens in `387.7 ms`, uncapped `1,611.0`).
  - `DirectCdpClient` WebSocket reduces 2-call CDP `Snapshot+AXTree` serialization latency on heavy DOMs (`220.31 -> 122.10 ms` `p50` on GitHub Trending in `Exp 7`), and dedicated COM `MTA` eliminates `446 ms` Notepad / `861 ms` Explorer cold STA initialization stalls (`Exp 1`).
- **Explicit caveats & negative results:**
  - **`H1` / `H1b` / `H2` / `H3` cursor probing rejected/abandoned:** Synchronized cursor probing took `14.93 s`, dropping settle windows to `80` px corrupted canvas accuracy to `34.4%`, and `H3` was never built (`results/experiments/h*_report.md`).
  - **Cross-origin iframe (`OOPIF`) gap remains open:** Under Chrome strict `--site-per-process` and tested live embeds (e.g., `youtube.com/embed`), `DOMSnapshot` + top-session discovery dropped inner controls (`0` elements, `0` blind regions).
  - **20-task LLM evaluation unrun:** `results/agent_benchmark/harness_validation.json` contains **deterministic oracle checks only (`20/20`, `0` LLM inference runs)** — no live VLM end-to-end token or task-completion victory is claimed yet.
  - **`TOKENS_EST` is a heuristic (`len(text) / 4`), not an exact BPE tokenizer count**, and `1,229` tokens is a static baseline proxy rather than a cross-vendor billing exact match.

---

## 8. Critical Known Limitations & Security Posture

- **Open SSRF Redirect & Loopback CDP Risk (`[MEASURED]`):** `validate_navigation_url()` blocks loopback, private, CGNAT, link-local, obfuscated IPv4/IPv6 literals, and non-HTTP schemes on initial entry, **but** Chromium `page.goto()` still follows HTTP `302` redirects toward `127.0.0.1` once an external host passes initial validation, and Python-side DNS checks cannot eliminate Chromium-internal DNS rebinding. Local `--remote-debugging-port` endpoints also expose unauthenticated `/json/version` and origin-less WebSocket control to local processes (though Chromium `1.64` rejects browser-originated `Origin:` WS upgrades with `HTTP 403`).
- **`verified=true` != Semantic Task Completion:** Action `verified=true` verifies targeted element pre-checks/dispatch semantics, not downstream business state (e.g., typing into `<input readonly>` or Win32 `#32770` Save As UIA `ValuePattern.SetValue` vs `IFileSaveDialog` desync).
- **Platform & Desktop Caveats:** Non-Windows Python import fails without Win32 `user32`; Store Notepad async UIA hydration/tab persistence; `WS_EX_LAYOUTRTL` horizontal coordinate mirroring in `PrintWindow` on RTL Notepad windows; no multi-tab `target="_blank"` browser tab switching.

Read [SECURITY.md](SECURITY.md) and [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) before running CUL on any untrusted page or desktop session.

---

## 9. Roadmap (`v0.1.0-alpha` -> Beyond)

1. Intercept Chromium navigation redirects / sub-frame hops inside `context.route()` to enforce host validation across `302` chains.
2. Lazy-load Win32 `user32` / COM bindings so browser-only mode imports cleanly on Linux/macOS.
3. Implement OOPIF target attachment (`Target.setAutoAttach`) + `<iframe src>` cross-origin blind-region fallback under `--site-per-process`.
4. Add multi-tab session tracking (`Page` target switching) and `KillSwitch` fail-closed initialization.
5. Run paired live VLM evaluations on the 20-task benchmark (`benchmarks/bench_agent_20tasks.py`) across open and commercial vision models.

---

## 10. Contributing & Citation

Contributions focusing on reproducible bug reports, cross-origin frame tests, platform decoupling, and empirical benchmarks are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). To report security issues responsibly, consult [SECURITY.md](SECURITY.md).

If you cite Computer Use Lite or its empirical methodology in academic or engineering work, see [CITATION.cff](CITATION.cff).

```text
Copyright 2026 Mohamed Gomaa
Licensed under the Apache License, Version 2.0 (LICENSE / NOTICE)
```

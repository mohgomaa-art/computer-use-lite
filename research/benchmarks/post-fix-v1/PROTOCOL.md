# Post-Fix Comparative Evaluation Protocol (`post-fix-v1`)

**Freeze Timestamp:** `2026-11-27`  
**Status:** FROZEN PRIOR TO EXECUTION  
**Evaluator Host:** Microsoft Windows 11 Pro (`10.0.26200`), Python `3.12.10`, Playwright Chromium, Node `v24.21.0`, WSL2 `kali-linux` (`Python 3.14.7`)

## 1. Compared Builds & Isolation Rules

1. **Historical Baseline (`baseline_0d19a9e`):** Read-only worktree at immutable commit `0d19a9e12527ed12f5020709ea660c169b23e76d` (`v0.1.0a0`). Executed via explicit `sys.path[0] = <baseline>/src` in fresh isolated subprocesses so editable installs never shadow imports.
2. **Fixed Candidate (`fixed_v0_2_0a0`):** Working branch `fixes/security-reliability-research-release` (`HEAD` after `P0`–`P3` + Cursor fixes). Executed under default hardened flags (`CUL_MCP_DIRECT_WS` unset -> Pipe transport) AND where noted in Track C also with `CUL_MCP_DIRECT_WS=1` opt-in so transport cost vs code-path changes remain separable.
3. **Immutability:** Previous `benchmark-worktree-20261126` (`fdc92d9`), `v0.1.0a0`, `v0.1.0a1`, and `v0.1.0a2` data files are never rewritten or merged into `post-fix-v1` measurements.

## 2. Benchmark Tracks & Honest Scope Boundaries

### Track A — Paired Security, Accuracy & Cursor Regression Matrix (`n = 32` paired checks)
- Evaluates identical fixtures on `baseline_0d19a9e` and `fixed_v0_2_0a0`:
  - `A01..A03`: Cross-frame same-origin, nested 2-level, and `--site-per-process` OOPIF overlay occlusion (`CUL-ACC-001`).
  - `A04..A06`: Sensitive field redaction, benign non-redaction (`address_shipping`, `opinion`, `spinner`), zero raw secret SHA-256 hash leakage (`CUL-PRIV-001/002`).
  - `A07..A09`: DNS `gaierror` fail-closed, simulated DNS rebinding block, default disabled DirectWS (`CUL-SEC-001/002`).
  - `A10..A11`: `readonly` input & non-mutating no-op click `verified == False` (`CUL-ACC-002`).
  - `A12..A13`: `open_desktop` sensitive process/class blocklist & dangerous OS hotkey blocklist (`CUL-SEC-003/004`).
  - `A14..A18`: Real Win32 Z-order occlusion in `DesktopSession.verify_fresh`, `KillSwitch` fail-closed on `GetCursorPos` `OSError`, Windows 11 2-tab Explorer `CabinetWClass` inactive-tab exclusion, `WS_EX_LAYOUTRTL` un-mirrored `PrintWindow`, `_pulse_screenreader` cleanup (`CUL-DESK-001..005`).
  - `A19..A20`: Linux non-Win32 import check (`sys.platform='linux'`, `WinDLL`/`comtypes` disabled) & `[UNTRUSTED_UI_TEXT]` newline-injection framing (`CUL-DX-001`, `CUL-SEC-005`).
  - `A21..A26`: Cursor overlay fixes (`show_cursor=True` 0 blind regions, `<=1` SVG rebuild / 3 clicks, `900ms` error auto-revert, `clicks=2` double pulse/ripple, `<=5 deg` max tilt, `<1s` hidden-tab move + single init registration).
  - `A27..A32`: P3 capabilities (`input[type=date]`, `inspect_element` checked/readonly/range/options, sticky-header safe click clamp, semantic `Resolver` tie-break, `drag`, `read_page` / `discover(include_static_text=True)` + SessionManager idle TTL eviction).
- **Statistics:** Wilson 95% confidence intervals for pass rates; exact paired win/loss/tie counts.

### Track B — Live Agent MCP Availability & Deterministic Stdio MCP Protocol Replay
- **B1 Live LLM Agent Runs (`NOT_RUN` — Recorded Pre-Flight Diagnostic):**
  - Pre-flight check on `codex-cli 0.166.0` (`gpt-6-luna` via ChatGPT auth) exited with `turn.failed`: `"You've hit your usage limit. Upgrade to Plus to continue using Codex... try again at Dec 26th, 2026 7:46 PM."`
  - Native CUA / `@oai/sky`, `claude`, `ollama`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` are absent/logged-out.
  - Per strict zero-fabrication rules, **0 live LLM calls are simulated or faked**; Track B live LLM arms remain honestly classified as `NOT_RUN`.
- **B2 Deterministic Stdio MCP Replay (`n = 18` paired tasks per arm, scripted client):**
  - Exercises real `stdio_client` -> `mcp_server` -> Playwright -> Chromium on identical local HTML servers across 12 standard browser tasks (`b01..b12`, ZERO prompt tool leaks) plus 6 safety/ergonomic tasks (`s01..s06`), comparing `baseline_0d19a9e` vs `fixed_v0_2_0a0`.
  - Clearly labeled as **deterministic MCP tool-protocol replay**, never claimed as stochastic LLM reasoning.

### Track C — Isolated Engine Latency, Transport, `rAF` Frame Budget & Memory Profile (`n = 10` per condition)
- Runs `N = 10` repetitions (reporting median `p50`, `p95`, IQR, min, max, and `psutil` peak RSS delta) comparing `baseline_0d19a9e` (default DirectWS), `fixed_v0_2_0a0` (default Playwright Pipe), and `fixed_v0_2_0a0` (`CUL_MCP_DIRECT_WS=1` opt-in):
  1. `standard_form`: 12-element local HTML page cold `discover()` + `act()`.
  2. `dense_90`: 90-button workspace `discover()`.
  3. `dense_2500`: `50x50` (`2,500`-cell) dense DOM occlusion & `discover()`.
  4. `oopif_isolated`: `--site-per-process` dual-origin OOPIF `discover()` + click.
  5. `hover_adaptive`: Hover trigger + immediate menu reveal (`wait_ms=350` adaptive vs `wait_ms=0`).
  6. `cursor_raf`: Chrome CDP `show_cursor=True` sweep `rAF` frame duration (`p50`, `p95`), SVG DOM rebuilds across 3 clicks, init bytes uploaded over `Runtime.evaluate`.
  7. `desktop_uia`: Controlled Windows 11 `C:\audit_scratch` File Explorer & Win32 test window `discover()` + `verify_fresh()`.

### Track D — Platform & Portability Verification Matrix
- Executes and records verbatim counts/outputs for:
  1. Full Windows 11 `pytest --strict-markers` (interactive + headless tests; any hardware hook blocked by OS/sandbox marked `NOT VERIFIED`).
  2. CI headless profile (`CUL_SKIP_DESKTOP=1 pytest -m "not windows_desktop"`).
  3. Mocked Linux subprocess import check (`sys.platform='linux'`, `WinDLL`/`comtypes` disabled).
  4. Real WSL2 `kali-linux` (`Python 3.14.7`, `sys.platform == 'linux'`) import verification.

## 3. Acceptance & Reporting Rules
- Compute all summary statistics and Wilson 95% CIs exclusively from raw `results.jsonl` output via deterministic script (`analyze_post_fix.py`).
- Compute `SHA256_MANIFEST.txt` over `PROTOCOL.md`, `TASK_SPEC.json`, `SCHEMA.json` before benchmark run AND over raw results afterwards.

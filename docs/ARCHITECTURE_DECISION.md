# Architecture Decision — Computer Use Lite

Initial empirical baseline validated on Windows (Python `3.12`, Chromium `1.64`, `2026-11-24`), updated through `HEAD` (`d47b4e9`, `2026-11-26`) to record Workstream A (Cursor Overlay) and Phase 1 (`P0-1..P0-5`) architectural decisions. Every numeric metric below comes from measured runs in `experiments/`, `benchmarks/`, and `tests/`; only the `~1229`-token `1280x720` screenshot proxy and `TOKENS_EST = len/4` are heuristic estimators ([RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md)).

> **Historical Link Compatibility Note:** `src/computer_use_lite/__init__.py` references `docs/ARCHITECTURE_DECISION.md` for why browser and desktop cursor probing (`H1b` and `H2`) remain dropped/unshipped. Full narrative evidence and archived reports are indexed in [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) and [../research_archive/INDEX.md](../research_archive/INDEX.md).

---

## 1. Exploratory Cursor Probing Scorecard (`H1`–`H3`, `2026-11-24`)

| Hypothesis | What Was Measured | Recall | Precision | Latency | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **H1** browser canvas cursor probe | `880` probes, step `32`, Maps @ Times Sq ([`h1_report.md`](../results/experiments/h1_report.md)) | `81.8%` | `81.8%` | `29.46 s` (`33.5 ms/probe`) | **SIGNAL PASS / PRACTICAL REJECTED** |
| **H1b** latency + pipelining + clustering (re-validated) | `880` probes, Google Maps: `raf` vs no-rAF `sync` vs `yield2` vs pipelined `pipe_20`/`pipe_80` ([`h1b_report.json`](../results/experiments/h1b_report.json)) | `100%` agreement (`sync`, `yield2`); `33.5%–34.4%` (`pipe_20`/`pipe_80`) | — | `raf` `29.39 s` (`33.40 ms/pt`); `sync` `14.93 s` (`16.97 ms/pt`); `pipe_80` `0.77 s` (`0.87 ms/pt`) | **SIGNAL-ONLY / PRACTICAL REJECTED** |
| **H2 Gate 0** per-toolkit calibration | Initial run invalidated by `(0, 87)` px offset; subsequent `Default`-desktop run ([`h2_gate0.json`](../results/experiments/h2_gate0.json), `2026-11-24T21:36:08`) tested canvas + Win11 Notepad (`LibreOffice not installed`). Fails in `exebox` with `GetCursorInfo ERROR_ACCESS_DENIED`. | Canvas `hand_rate=1.0`, `dead_fp=0.0`; Notepad `uia_recall=1.0` (`25` controls, `hand_rate=0.0`) | `dead_fp=0.0` (canvas) | `50 ms` canvas settle | **GATE 2A UNLOCK (`h2_gate0.json`; `BLOCKED` in `exebox`)** |
| **H2 2B** desktop grid scan | Prior `240`-pt run invalidated by `~87 px` chrome offset and `50 ms` constant settle ([`archive/stale_h2_grid/`](../archive/stale_h2_grid/h2_report.md)); no post-fix grid scan run | *invalidated; unrun post-fix* | *invalidated* | *invalidated* | **NOT SHIPPED (DROPPED)** |
| **H3** hover visual diff | Precondition unmet (not built) ([`h3_report.md`](../results/experiments/h3_report.md)) | — | — | — | **NOT BUILT** |

### Why H1b Stayed `SIGNAL-ONLY` / Dropped
- With a corrected synchronous `NO_RAF_PROBE_JS` baseline (`h1b_report.json`), sequential probing still took `14.93 s` (exceeding `< 3.0 s` by ~5x), while pipelined probing (`pipe_80`, `0.77 s`) collapsed hit agreement to `33.5%–34.4%` due to Chromium pointer-event coalescing. Browser cursor probing stays **DROPPED**.

### Why Old H2 Numbers Are Marked Invalidated
- Screenshot inspection (`a2_origin_proof.png`) proved `client_origin(hwnd)` sat `(0, 87)` px above `Chrome_RenderWidgetHostHWND` (`(28, 20)` vs `(28, 107)`), throwing old probes into browser chrome and invalidating old `26.7%` UIA recall, `73.3%` hand rate, and `53.3%` grid precision/recall. Desktop cursor probing remains **DROPPED / NOT SHIPPED**.

---

## 2. Core Engine Layer Matrix (`KEEP` / `DROP`)

| Layer | Decision | Evidence |
| :--- | :--- | :--- |
| M0 `snapshot.py` bounds + monotonic revision | **KEEP** | `window()` avoids bumping revision on `bounds()` lookups; `TaskState` keeps revision monotonic across runs |
| M1-Browser `browser_cdp.py` DOMSnapshot + AXTree | **KEEP** | Captures role-less `clickable`, `switch`, `searchbox`, OOPIF multi-doc discovery + `--site-per-process` test (`P0-1`), multi-tab tracking (`P0-2`), `Fetch` SSRF guard (`P0-4`), exact-port CDP origin (`P0-5`), `overflow`/label pruning, lazy occlusion, `scrollIntoView` + safety check |
| M1-Windows `desktop_uia.py` `FindAllBuildCache` | **KEEP** | `MTA` + `AutoSetFocus=0` + transient init `COMError` retry, O(1) `signature()`, cached pattern/RuntimeId extraction, `Invoke->Toggle->SelectionItem->ExpandCollapse->SendInput`, `#32770` `_commit_dialog_text` + `DIALOG_ALERT:` (`P0-3`), foreground + `KillSwitch` guards |
| M2 cursor probe — browser & desktop | **DROP** | `H1b` `sync` `14.93 s` / `pipe_80` `34.4%`; `H2 2B` invalidated `(0, 87)` px origin and unrun post-fix |
| M2 blind-region crop exporter (`blind_gap.py`) | **KEEP** | Detects `>= 25%` and sparse `>= 5%` canvases without normal-DOM false positives; prioritizes `PrintWindow` for covered/non-foreground/minimized/cloaked HWNDs |
| M3 `resolver.py` dedupe + stale guard | **KEEP** | Revision mismatch, modal occlusion, removal, `> 2 px` drift checks, hover delta reconciliation |
| M4 `hover.py` on-demand hover | **KEEP** | Single settle wait + disappeared control cleanup |
| M5 `api.py` line map + `state.py` | **KEEP** | 60-element cap + `filter_query`, `searchbox` read-back, atomic temp-replace (`fsync=False` option for disposable MCP dirs), full non-`None` action `"value"` SHA-256 redaction |
| Workstream A `cursor_overlay.py` + `desktop_cursor_overlay.py` | **KEEP** | Opt-in/headful CSP-safe Chromium overlay + `60 Hz` capture-excluded layered desktop overlay without touching physical mouse input or DOM/UIA discovery |
| H3 hover visual diff | **NOT BUILT** | Precondition unmet |

---

## 3. Measured Token & Latency Reference (`results/benchmarks/benchmarks_real.json`, vs `1229`-Token Proxy)

| Target | Kind | Elements | Blind Regions | Latency (`ms`) | Capped `line_map` (`<=60`) | Uncapped `line_map` |
| :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| [`tests/fixtures/form.html`](../tests/fixtures/form.html) | **fixture** | 4 | 0 | 17.8 | 54.2 (`0.04x`) | 54.2 (`0.04x`) |
| GitHub Trending | real browser | 120 | 0 | 215.5 | 654.0 (`0.53x`) | 1263.8 (`1.03x`) |
| YouTube | real browser | 27 | 0 | 125.2 | 386.8 (`0.31x`) | 386.8 (`0.31x`) |
| Gmail (sign-in) | real browser | 14 | 0 | 54.8 | 187.2 (`0.15x`) | 187.2 (`0.15x`) |
| Google Maps (`@40.7580,-73.9855,17z`) | real canvas | 64 | 1 | 273.2 | 690.8 (`0.56x`) | 712.5 (`0.58x`) |
| Notepad (Win11) | real desktop | 36 | 0 | 140.2 | 474.8 (`0.39x`) | 474.8 (`0.39x`) |
| File Explorer | real desktop | 140 | 0 | 387.7 | 711.0 (`0.58x`) | 1611.0 (`1.31x`) |
| Chromium shell (`WM_GETOBJECT` / `--force-renderer-accessibility`) | real desktop | 18 | 0 | 76.1 / 62.8 | 194.5 (`0.16x`) | 194.5 (`0.16x`) |

Uncapped dense DOM/UIA trees (`1263.8` and `1611.0` tokens) exceed the `1229`-token proxy, motivating `Api.line_map()`'s default `60`-element cap with `filter_query=` drill-down.

---

## 4. Isolated 9-Candidate Optimization Study Decisions (`results/perf_study/BENCHMARK_REPORT.md`)

- **KEEP (Merged):** Dedicated UIA `MTA` Worker + `CUIAutomation8(AutoSetFocus=0)` (eliminates `446–861 ms` cold `STA` hangs and `~2,000 ms` focus stalls), `DirectCdpClient` WebSocket (`-98.2 ms` on GitHub Trending Snapshot+AX), 2-call CDP Ablation (removes `N * DOM.getBoxModel`), and targeted `verify_fresh()` (maintaining `safety_parity = 1.0`, while acknowledging `Exp 8`'s `fsync=False` confound).
- **DROP:** Caching HWND roots across scans, dropping `BoundingRectangle` (`+5–25 ms` N+1 regression), explicit `RawView` (`0.404` precision on Chrome), and `AutomationElementMode.None` (`+6.5–38.8 ms` `RuntimeId` re-acquire per action).
- **HOLD (`[PROPOSAL]` / Deferred):** UIA `RemoteOperations` (cross-HWND failure), `One-Call JS Extractor` (closed Shadow DOM & OOPIF drop), `OrCondition` (`TabControl 50018` miss), and top-frame `MutationObserver` (`0.8421` recall).

---

## 5. Post-`0.1.0-alpha` Architectural Decisions (`Workstream A` & `P0-1..P0-5`)

### ADR-A: Decoupled Obsidian-Chrome 3D Cursor Overlay (`7c7b9b4..d47b4e9`)
- **Decision:** Implement visual cursor feedback strictly as non-interfering side-channel renderers — CSP/Trusted-Types-safe DOM+SVG nodes in `cursor_overlay.py` and a dedicated `60.0 Hz` `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE` Win32 GUI-thread window in `desktop_cursor_overlay.py` (`_WDA_EXCLUDEFROMCAPTURE`, zero `SendInput` glides), keeping headless CI untouched unless opted in (`show_cursor=True`, `CUL_AGENT_CURSOR=1`, or `CUL_MCP_HEADFUL=1`).
- **Rationale:** Putting overlay drawing on `DesktopSession`'s COM MTA thread or driving cursor glides via `SendInput` would trigger `KillSwitch` (`5 px` physical pointer excursion guard) or stall UIA IPC; omitting `_WDA_EXCLUDEFROMCAPTURE` would pollute `blind_gap` crops; separating `ok` vs `verified` cues in `api.py` prevents visual green indicators on unverified or no-op dispatches.

### ADR-B: Keep `13`-Tool MCP Surface Across Multi-Tab Support (`P0-2`, `bee026e`)
- **Decision:** Add `list_tabs`, `switch_tab`, and `close_tab` actions + `tab_index` onto the existing `navigate` MCP tool rather than proliferating separate tab tools.
- **Rationale:** Preserves compact MCP schema token overhead for client agents while exposing context-level Playwright page management and rebinding `DirectCdpClient` + cursor overlays atomically on switch.

### ADR-C: Win32 `#32770` Physical Commit & Static Alert Surface (`P0-3`, `16465bf`)
- **Decision:** When `DesktopSession.hwnd` class is `#32770`, intercept `type` via `_commit_dialog_text` (foreground `Ctrl+A` + `Delete` + `SendInput` `KEYEVENTF_UNICODE`, falling back to `EM_SETSEL` + `WM_CHAR` if needed) and surface static `Text` controls via `DIALOG_ALERT:` lines in `Api.line_map()`.
- **Rationale:** `IFileSaveDialog` on Windows `#32770` dialogs accepts `IValueProvider::SetValue` visually without committing internal path buffers (`M1 #7` / `T15`), while `discover` normally strips static text controls, hiding modal invalid-filename errors.

### ADR-D: Browser-Wide CDP `Fetch` SSRF Guard & Loopback Origin Pinning (`P0-4` / `P0-5`, `965eb66` / `a3291b3`)
- **Decision:** Enforce URL/IP validation (with IPv4-mapped IPv6, 6to4, Teredo, and NAT64 normalization) on every CDP `Fetch.requestPaused` `Request` and `3xx` `Response` `Location` header when `url_validator` is present; bind self-launched `DirectCdpClient` to `127.0.0.1` + exact port `--remote-allow-origins=http://127.0.0.1:<port>` with `CUL_MCP_DIRECT_WS=0` escape hatch.
- **Rationale:** Initial entry URL validation (`validate_navigation_url`) missed `HTTP 302 -> 127.0.0.1` hops (`P0-4`); exact origin allowlisting blocks cross-origin browser tab WebSocket upgrades (`P0-5`) while preserving the fast `DirectCdpClient` WebSocket path. **Residual boundary:** OS-level DNS-rebinding TOCTOU between Python resolution and Chromium's socket connection remains unblocked at TCP connect time ([SECURITY.md](../SECURITY.md)).

# Known Limitations & Open Boundaries (`HEAD` `d47b4e9`)

This document reconciles boundaries fixed or mitigated since `0.1.0-alpha` (`P0-1..P0-5`, `Workstream A`) against **still-open functional gaps, platform assumptions, security threats, and unverified live behavior**.

---

## 1. Status Changes Since `v0.1.0-alpha` (`698861d -> d47b4e9`)

| Area | Status at `0.1.0-alpha` | Current Status on `HEAD` (`d47b4e9`) | Remaining Residual Limitation |
| :--- | :--- | :--- | :--- |
| **Site-Isolated OOPIFs (`P0-1`, `77cd171`)** | Returned `0` controls without `--site-per-process` test | **Fixture-Verified (`test_p0_1_site_per_process_oopif_discovery_gt_and_actions`)** using deterministic `--site-per-process` multi-frame fixture (`1.0` recall) | **Live public embeds (e.g., `youtube.com/embed`) remain UNVERIFIED** on restarted MCP; `DirectCdpClient` `Target.setAutoAttach(flatten=True)` parallel `AXTree` OOPIF demux was deferred. |
| **Multi-Tab Tracking (`P0-2`, `bee026e`)** | Stranded session on opener tab (`navigate` `goto`/`back` only) | **Implemented in `src/` + Unit/MCP Tests:** `BrowserSession.tabs`, `switch_tab`, `close_tab`, and MCP `navigate(list_tabs \| switch_tab \| close_tab, tab_index)` preserve overlay state | Post-`P0-2` live multi-tab MCP stress test (`T08` live site scenario) not yet re-run outside fixtures. |
| **`#32770` Save As Dialog (`P0-3`, `16465bf`)** | `SetValue` visually updated without committing `IFileSaveDialog` state | **Implemented in `src/` + Fixture Test:** `_commit_dialog_text` + `DIALOG_ALERT:` (`api.py`) | Real Store Notepad save-dialog re-run on `WinSta0\Default` pending; disk-content verification remains mandatory. |
| **`3xx` Redirect & Sub-Request SSRF (`P0-4`, `965eb66`)** | `validate_navigation_url()` checked initial URL only | **Implemented in `src/` + Unit Test:** CDP `Fetch` request/response interception + IPv6/6to4/Teredo/NAT64 normalization | **DNS-rebinding TOCTOU** between Python pre-check and Chromium TCP connect stays OPEN ([SECURITY.md](../SECURITY.md)). |
| **CDP Origin Restriction (`P0-5`, `a3291b3`)** | Bare `--remote-debugging-port` | **Implemented in `src/` + Gate:** `--remote-debugging-address=127.0.0.1` + `--remote-allow-origins=http://127.0.0.1:<port>` + `CUL_MCP_DIRECT_WS=0` | Local host origin-less processes on the same machine can still reach loopback `/json/version` when `DirectWS=True`. |

---

## 2. Open Browser Engine Limitations

1. **Unimplemented `AXTree` Metadata & Role Enrichment (`[VERIFIED-CODE]` / `[PROPOSAL]` `P1-1`):**  
   `inspect_element()` only reads live `"value"` on `textbox` and `searchbox`. Checkboxes/radios (`checked`), sliders (`<input type="range">` `min`/`max`/`value`), `<option>` lists inside closed/native `<select>`, and `readonly` flags on textboxes are omitted or discarded from `getFullAXTree` (`<input readonly>` can report `verified: true` on focus/no-op typing).
2. **Boundary-Straddling Sticky-Header Clipping (`[REPORTED]` / `[VERIFIED-CODE]`):**  
   Partially negative-`y` elements clipped under sticky headers can retain non-matching coordinates between layout occlusion, `_NODE_PROBE_JS`, and center hit-testing (`T13`).
3. **`<input type="date">` & Range Widgets (`[REPORTED]`):**  
   Formatted `<input type="date">` controls expose `clickable` rather than structured date input (`T01`/`M1 #4`: raw typing can corrupt digits into `02/02/61201`), and `<input type="range">` / sliders lack a pointer drag primitive (`T06`).
4. **No Continuous Mouse Drag Primitive (`[VERIFIED-CODE]`):**  
   Neither `Api` nor the `13`-tool MCP schema exposes pointer `mousedown`/`mousemove`/`mouseup` dragging (`click`, `type`, `focus`, `hover`, `scroll`, `press_key`, `click_at` only).
5. **Polymer Inline `<style>` Text & `<label>` Pruning Edge Cases (`[REPORTED]` / `[VERIFIED-CODE]`):**  
   Fallback child text extraction does not filter inline `<style>`/`<script>` elements (`T12`), and `<label>` wrappers around `button`/`clickable` targets stay unpruned (`M1 #1`).
6. **Closed Shadow DOM & Read-Only Static Page Text (`[VERIFIED-CODE]`):**  
   Closed Shadow DOM trees are unreachable via standard DOM inspection (unverified on live public sites `M1 #8`), and static non-interactive DOM text (paragraphs, alerts outside `#32770` dialogs) is omitted from `line_map`.
7. **`verified=true` != Semantic Task Completion (`[VERIFIED-CODE]`):**  
   `verified` in `act` reflects pre-check + signature change heuristics (`url`, `focus`, `title`, element count), not business-logic completion.

---

## 3. Platform & Windows Desktop UIA Limitations

1. **Windows-Only Top-Level Import Coupling (`[VERIFIED-CODE]` — `P2-1` Open):**  
   `desktop_uia.py` and `snapshot.py` execute `ctypes.WinDLL("user32")` / `"kernel32"` at module import time, breaking Linux/macOS `import computer_use_lite` even for browser-only MCP execution.
2. **Windows 11 File Explorer (`CabinetWClass`) Inactive-Tab Bleed (`[REPORTED]` — `P1-5` Open):**  
   DirectUI `FindAllBuildCache` scans on multi-tab File Explorer windows leak controls from inactive tabs (`IsOffscreen=False`) and emit 4 cell boxes per file row.
3. **`PrintWindow` Right-to-Left (`WS_EX_LAYOUTRTL`) Mirroring (`[REPORTED]` — `P1-4` Open):**  
   Arabic/RTL Store Notepad (`المفكرة`, `WS_EX_LAYOUTRTL` `0x400110`) renders horizontally mirrored under Win32 `PrintWindow` compared to screen grabs, whereas non-mirrored UWP frames (`الحاسبة`) do not (`M1 #6`).
4. **Desktop Overlay & Isolated Sandbox Desktops (`exebox-*`) (`[MEASURED]` / `[VERIFIED-CODE]`):**  
   Isolated `exebox` shells return `EnumWindows total=0`, `GetCursorInfo ERROR_ACCESS_DENIED`, and skip desktop overlay/z-order checks; interactive z-order verification of `DesktopCursorOverlay` (`tests/test_cursor_overlay.py`, currently `M` modified locally) requires an unlocked `WinSta0\Default` desktop session.
5. **`KillSwitch` Initialization Nuance (`[VERIFIED-CODE]` — `P1-6` Open):**  
   `desktop_uia.move_mouse()` silently passes an initial `OSError` from `GetCursorPos()` rather than failing closed immediately.
6. **Single-Key Layout & Non-UIA Electron/Chromium Windows (`[VERIFIED-CODE]`):**  
   UIA single-character key lookup (`VkKeyScanW`) follows active thread layout; Chromium/Electron windows launched without `--force-renderer-accessibility` may require `WM_GETOBJECT` fallback (`_a11y_tried`) or still yield sparse `low_uia` trees.
7. **Desktop `verify_fresh()` Lacks Z-Order Occlusion Check (`[VERIFIED-CODE]`):**  
   `DesktopSession.verify_fresh()` verifies UIA bounds, enabled, and offscreen state but hardcodes `"occluded": False`.

---

## 4. Benchmark, Telemetry & Verification Gaps

1. **Zero Live LLM Calls on 20-Task Agent Benchmark (`[MEASURED]`):**  
   [`results/agent_benchmark/harness_validation.json`](../results/agent_benchmark/harness_validation.json) validates deterministic oracles only (`20/20`, `0` VLM runs).
2. **Pending Post-P0 & Post-Overlay Full Suite Re-Run (`d47b4e9`):**  
   The canonical `52 passed` baseline belongs to pre-Overlay/pre-P0 `698861d`; no fresh full-suite `pytest` + live `PID` stress sweep was run during this documentation-only assignment.
3. **Active IDE Agent Skill Lag (`[VERIFIED-CODE]`):**  
   `.agents/skills/computer-use-lite/*.md` remains anchored to pre-Overlay/pre-P0 `3e67e49` (preserved intentionally during public docs consolidation; see [DOCUMENTATION_REORGANIZATION_REPORT.md](../DOCUMENTATION_REORGANIZATION_REPORT.md)).
4. **Heuristic Token Metric (`TOKENS_EST` & `1,229` Proxy):**  
   `round(len(text) / 4, 1)` and `1,229` are comparative proxies, not exact provider BPE/vision-tile billing.

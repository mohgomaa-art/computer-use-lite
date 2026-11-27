# Master Audit Synthesis (`computer-use-lite`)

**Synthesis Baseline:** Historical experimental commit `0d19a9e12527ed12f5020709ea660c169b23e76d` (`v0.1.0a0`, whose 13 runtime modules under `src/computer_use_lite/` are SHA-identical ignoring CRLF/metadata version fallback to `de27b49cae143c99028ff014aa5a0a2a7eb96a95` / `v0.1.0a2` on `main`, aside from `__version__`).  
**Frozen Evidence Bundle:** `C:\Users\mnile\Desktop\Computer-use-lite\EVIDENCE\PRE_FIX_2026-11-27\` (`496` SHA-256 verified files, tag `baseline-pre-fix-2026-11-27`).

---

## 1. Source Provenance Matrix (Environments Never Merged)

| Source Artifact | Environment & Commit | Scope & Runtime Access | Summary Result |
| :--- | :--- | :--- | :--- |
| **`computer-use-lite_ المميزات والعيوب (2026-11-27).pdf`** (`PDF-1`, 5 pp.) | Design/code/benchmark synthesis (pre-`v0.1.0a1`) | Qualitative + metric review of `0d19a9e` architecture & `fdc92d9` benchmark | Identified core token efficiency (~112 vs ~1,196 est. tokens), fast semantic action design, plus cross-frame/privacy/desktop/portability flaws. |
| **`computer-use-lite_ تقرير الهجوم الشامل (2026-11-27).pdf`** (`PDF-2`, 10 pp.) | Adversarial security/functional review (`0d19a9e` / `698861d`) | Static analysis + claimed task sweeps + exploit hypotheses | Listed `P0`/`P1`/`P2` attacks & bugs; contained two verified errors (`C19`: claimed `d01-d08 20/20` when actual is `8/8`; `A19`/`C42`: claimed `src/engine/` duplicate copy when files are 16-line `importlib` shims). |
| **`AUDIT_REPORT (1).md`** (`Linux-Audit`, `18,210 B`) | **Ubuntu Linux sandbox**, commit `0d19a9e` | Python unit/Node checks + Playwright headless; zero Windows desktop runtime (`WinDLL` failed at import -> 6 test collection errors) | Confirmed Linux import failure (`CUL-DX-001`), SSRF/regex/CDP static findings; marked Windows desktop findings `NOT_RUN`. |
| **`audit_2026-11-27/AUDIT_REPORT.md`** (`Windows-Audit`, `79 KB`, `296` lines) | **Windows 11 real host** (`exebox` + unlocked desktop probes), `0d19a9e` | Executed `pytest` (`70 passed in 197.50s` unlocked; `CUL_SKIP_DESKTOP=1`: `58 passed, 12 skipped`), Win32 Explorer, `#32770`, RTL `PrintWindow`, Chrome CDP | Empirically proved B5 cross-frame overlay click bug, B6 secret regex misses/over-redaction, B7 `readonly` `verified:true`, B8 DNS `gaierror` fail-open, B9 Explorer 2-tab leak (`71->85`), B12 RTL mirror, B14-1 `1280x720` wake-canvas crop, plus exact `A1-A20` line verifications. |
| **`AUDIT_REPORT_FINAL.md` + `OPEN_QUESTIONS_FINAL.md`** (`Merged-Audit`) | Combined Windows 11 + Linux cross-checked package | Reconciled both `0d19a9e` audits, corrected symbol names (`A3`, `A4`, `A8`, `A14`, `A19`), recomputed `fdc92d9` JSON aggregates | Established canonical classification (`VERIFIED-RUN` vs `VERIFIED-READ` vs `NOT_RUN` vs `REFUTED`) and flagged open Win32 occlusion / cursor timing questions. |
| **`downloads/cursor-audit-fix.patch.txt` + `CUL_cursor_strict_prompt-919dc90a.txt`** | Chrome CDP audit + Windows cursor inspection on `0d19a9e` | 7 cursor root causes (`A-G`), Win32 `GetCursorInfo` open theory, animation budget, optional takeover glow | Confirmed patch fixes A–E in JS & G in Python, but leaves `desktop_cursor_overlay.py` `set_busy` bug unfixed (`cursor_id="progress"` still set immediately) and Fix F still re-evaluating init script instead of session-cached `Page.addScriptToEvaluateOnNewDocument`. |
| **`runs/20261126_195128/` (`fdc92d9`) + `DESKTOP_NATIVE_VS_CUL_PILOT.md`** | Pre-fix Browser (`72` runs) & Desktop Pilot (`T1`/`T2` preflight/smoke) | Playwright MCP vs CUL (`36+36` browser runs); Native `@oai/sky` preflight/smoke | Confirmed `33/36` CUL vs `36/36` Playwright browser completion (`+40.0%` higher CUL tokens, `1.5%` slower median wall time, `b11` prompt leak confound); Desktop Pilot completed only `3` harness manifests and blocked before paired scoring due to desktop isolation gate. |

---

## 2. Executive Synthesis of Baseline Defects vs Strengths

### Verified Strengths Preserved Across Repairs
1. Compact `REV:N` element line maps genuinely reduce single-observation context footprint (`DEFAULT_LINE_MAP_CAP = 60`, compact pipe-delimited schema).
2. `P-01` dense-DOM occlusion scan (`2,500` cells in `~19.32 ms` Python CPU p50) and dedicated COM MTA thread (`AutoSetFocus=0`) eliminate UIA cross-thread stalls.
3. `P0-3` `#32770` Save As physical commit and `P0-4` CDP `Fetch` 302 redirect blocking work reliably when reached.
4. Cursor overlay `64x64` vector registry (`cursor_overlay.py`) works under strict CSP (`require-trusted-types-for 'script'`) using `adoptedStyleSheets`.

### Critical & High Failure Modes Requiring Remediation Before `v0.2.0a0`
1. **Safety & Truthfulness (`P0`):** Cross-frame clicks inside an iframe behind a transparent parent overlay hit the parent overlay while reporting `ok=True, verified=True`; `readonly` inputs and no-op actions do the same; secret redaction misses `card`/`ssn`/`iban`/`otp`/`autocomplete="cc-number"` while over-redacting `address_shipping`/`opinion`/`spinner` via unanchored substrings; `validate_navigation_url` fails open on `socket.gaierror`; `DirectCdpClient` exposes an unauthenticated loopback CDP WebSocket by default; and cursor overlay `<canvas>` in Shadow DOM triggers false `1280x720` `opaque_canvas` blind crops (`B14-1`).
2. **Cursor Subsystem Bugs (`Cur A-G` + Section 3–5):** Every `<350 ms` action flashes the `progress` glyph; `not-allowed` error glyph remains stuck; double-click `clicks=2` is ignored; post-spring tilt exceeds `5 deg`; hidden-tab `rAF` hangs CDP `Runtime.evaluate`; the `~60 KB` init script is re-evaluated repeatedly; and physical `SendInput` OS cursor leakage needs empirical `GetCursorInfo` measurement on Windows 11.
3. **Windows Desktop Reliability & Policy (`P1`):** `open_desktop` lacks a process/window deny list; `DesktopSession.verify_fresh()` hardcodes `"occluded": False`; `_BLOCKED_KEY_TOKENS` permits `Alt+Tab`, `Alt+F4`, `Ctrl+Esc`, `Ctrl+Shift+Esc`; `KillSwitch` swallows initial `GetCursorPos` errors; File Explorer (`CabinetWClass`) leaks inactive-tab elements; RTL `PrintWindow` mirrors Arabic UIs; `_pulse_screenreader` lacks `atexit`/state crash restoration.
4. **Portability & DX (`P2`):** Module-level `ctypes.WinDLL` / `WINFUNCTYPE` / `comtypes` crash non-Windows imports (`6` pytest collection errors on Linux); `psutil` is absent from `[dev]`; UI strings lack explicit `[UNTRUSTED]` boundary framing; redacted values still store partial SHA-256 prefixes.
5. **Performance & Capabilities (`P3`):** Fixed `350 ms` hover sleep, sparse `AXTree` metadata on checkboxes/radios/sliders/select/readonly, broken `input[type=date]` digit entry, no continuous `drag`, no `read_page` static text observation, sticky-header click clipping, unbounded `MAX_SESSIONS` idle persistence, and confusing `TOKENS_EST` multi-script heuristic.

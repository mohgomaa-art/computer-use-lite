# Final Skill Update Report (`computer-use-lite`)

## 1. Executive Summary & Environment Provenance

This update revises the [computer-use-lite skill](.agents/skills/computer-use-lite/SKILL.md) and its references using primary repository evidence across source code (`src/computer_use_lite/*.py`), the `13` MCP `.json` schemas, headless/mocked post-fix checks (`tests/test_audit_fixes.py`, `fix_runs/`), raw M5 `transcript_full.jsonl` logs from `HT1`–`HT3`, `8` newly executed live gap probes (`M1`) on `WinSta0\Default`, and `18` fresh non-overlapping held-out validation runs (`M5` `F1`–`F3`).

- **Pre-update Repository `HEAD`:** `b4ca9b54aefc025eaf5ce7984fec5ae195ac30e9`
- **Latest `src/` Code Commit:** `6a2f0fbbf2c4198871b7d1a60ac556d609382b46` (`2026-11-26T12:09:59+02:00`, covered-window `PrintWindow` priority)
- **Active MCP Server Process:** `PID 18036` (`python.exe -u -m computer_use_lite.mcp_server`), started `2026-11-26T14:02:29.5128990+02:00` (confirmed post-`6a2f0fbb`; `list_sessions()` `count == 0` at start and end)
- **Local Checkpoints Created (no pushes, no edits to `src/`, `tests/`, `benchmarks/`, `.json` schemas, or historical reports):**
  - M0–M2 checkpoint: `cf95469f28f2a42ad26b5d8bae446dcb56baec22`
  - M3–M4 + Locked M5 Plan: `e7599897d9a8fa6bf30e936099307fb3808fe071`

### Strict Evidence Separation
1. **Stale Pre-Fix Live Suite (`live_runs/2026-11-26/`, `T01`–`T18`):** Executed against `PID 4076` (`2026-11-26T10:06:13+02:00`), predating commits `47bea1bb..6a2f0fbb`. Treated strictly as pre-fix baseline unless re-verified live on `HEAD`.
2. **Post-Fix Headless/Mocked Suite (`HEAD` `abebcff`–`6a2f0fbb`):** Verified `5/5` consecutive runs (`52` pytest + `8/8` CLI E2E, `0` warnings, `0` leaked PIDs) using headless Chromium fixtures and `CreateWindowExW` mocks (`P-09` live `Default`-desktop contrast previously `BLOCKED` in `exebox`).
3. **Post-Restart Live Browser + Desktop Verification (`PID 18036`, `HEAD`):** Confirmed live via `18` `HT1`–`HT3` runs, `8` `M1` live probes ([m1_gap_probes/RESULTS.md](skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md)), and `18` fresh `F1`–`F3` held-out runs ([M5_RESULTS.md](skill_updates/2026-11-26_final/m5_runs/M5_RESULTS.md)).

---

## 2. Historical Report vs. Raw Evidence Conflicts Resolved

| Conflict Identified | Report Claim | Primary Raw Truth | Resolution Recorded in Skill / Ledger |
| :--- | :--- | :--- | :--- |
| **`TaskState` plaintext leak (`P-19(c)`)** | `AUDIT_REPORT.md` claimed non-password `value` stayed plaintext | `src/computer_use_lite/state.py:L72-76`, `test_audit_fixes.py` pop & redact **all** non-`None` `value` fields | Documented accurate full redaction (`value_redacted: true`). |
| **Step 6 baseline sum** | Iteration-1 walkthrough stated `13/15` | Raw `benchmark.json` evals `0, 1, 2` sum to `14/16` (`5/5`, `3/5`, `6/6`) | Recorded walkthrough arithmetic error in [M0_CORPUS_LEDGER.md](skill_updates/2026-11-26_final/M0_CORPUS_LEDGER.md). |
| **`Exp 8` freshness numbers** | Early note mixed `9.543 ms` / `2013.98 ms` | Confounded by mismatched `os.fsync` durability & pre-`AutoSetFocus=0` desktop run | Disqualified confounded benchmark citation. |
| **`benchmarks_real` GitHub latency** | Old doc stated `292 ms` & `"BLOCKED IN exebox"` | Raw `results/benchmarks/benchmarks_real.json` measures `215.5 ms` | Followed raw benchmark artifact. |
| **VLM speedup claims (`~300–700` vs `100k`)** | Prior V1 skill claimed huge token reduction over screenshots | `HARNESS_VALIDATION.md` ran `0` LLM calls; no live multi-turn VLM screenshot baseline exists | Removed all uncalibrated VLM claims cleanly. |

---

## 3. Live `HEAD` Gaps Resolved (`M1` Probes on `PID 18036` + Raw `HT1`–`HT3` Logs)

1. **Cross-Origin OOPIF Live Divergence (`P-02`, `M1` Probe #2):** Although localhost dual-origin fixtures pass (`test_m4_p02` `recall=1.0`, `precision>=0.95`), testing `practice.expandtesting.com/iframe` live on `HEAD` `PID 18036` (`p2_oopif_mid.png`) revealed that while same-origin iframes improved (`textbox` + `button`), **site-isolated third-party embeds (`youtube.com/embed` buttons visibly rendered at `y=70..320` + third-party ads) STILL emitted `0` controls and `BLIND_REGIONS:0`**. Corrected prior skill wording from `"unverified live"` to honest runtime discovery omission reporting.
2. **Covered-Window `PrintWindow` (`P-09`, `M1` Probe #5):** Upgraded from `"unverified live"` (`BLOCKED` in `exebox`) to **verified live on `WinSta0\Default`**. Attaching covered `Settings` (`hwnd=788016`, `ELEMENTS:0 | BLIND_REGIONS:1`) rendered the covered UI cleanly via `PrintWindow` without foreground bleed-through (noting translucent Mica surfaces render black `#000000`).
3. **RTL `PrintWindow` Mirroring Asymmetry (`M1` Probe #6):** On `HEAD`, Arabic Store Notepad (`المفكرة`, `WS_EX_LAYOUTRTL`) rendered `100%` horizontally mirrored under `PrintWindow` vs `ImageGrab` (`p5_notepad_pw.png` vs `p5_notepad_screen.png`), whereas Arabic UWP Calculator (`الحاسبة`) rendered un-mirrored (`p5_calc_printwindow.png`).
4. **Native Win32 `#32770` Save As `ValuePattern` Desync (`M1` Probe #7):** Confirmed live on `HEAD` (`T15` + `M1` `s25`): `act("type")` via `ValuePattern.SetValue` on `#32770` `Edit` `1001` returned `verified: true` AND `inspect("s25", "e45")` returned the typed full path `notepad_m1_test.txt` — yet clicking `Save` (`e49`) never created `notepad_m1_test.txt` on disk (`exists: False`), instead saving the pre-filled filename (`M1-SAFE-2026.txt`, cleaned up afterward) into the open directory.
5. **Input/Label/Focus False Signals (`M1` Probes #1, #3, #4 + `HT1`–`HT3` Logs):**
   - `<input readonly>` returned `verified: true` via focus move (`BODY` -> `INPUT`) without changing value (`inspect()` caught unchanged `"Readonly input"`).
   - `browser_cdp.py:L876` excludes `button` and `clickable` from `<label>` deduplication (`M1` #1).
   - `<input type="date">` corrupted `2026-12-01` -> `02/02/61201` twice (`T01` + `M1` #4).
   - `jspaint.app` emitted duplicate `blind0`/`blind1` identical boxes live on `HEAD` (`M1` #3).
   - Adjacent `<input type="checkbox">` / `<input type="radio">` without distinct `.value` share `"on"`, producing `verified: false, state_delta: {}` in `6/6` `HT2` runs; native `<select>` exposes `0` `<option>` elements (`6/6` `HT2`); unassociated `<label>` siblings emit `name=""` (`6/6` `HT3`); `open_browser(auto_discover=True)` raced SPA hydration (`365.0 -> 507.5`) in `2/6` `HT3` runs; `File Explorer` (`M1` #6) exposes `172` elements (`listitem` + `4` column `textbox` cells per row), mixed Arabic/English labels, and virtual-screen multi-monitor bounds past `1920`.

---

## 4. Changes Applied Under `/skill-creator`, `/code-simplification`, and `/code-review-and-quality`

All `5` updated skill files under `.agents/skills/computer-use-lite/` trace 1-to-1 via [EVIDENCE_MAP.md](skill_updates/2026-11-26_final/EVIDENCE_MAP.md) to [LESSONS.md](skill_updates/2026-11-26_final/LESSONS.md):
- **[SKILL.md](.agents/skills/computer-use-lite/SKILL.md) (`126` -> `111` lines):** Consolidated redundant `Runtime Capability Detection` repetition into orthogonal workflow sections without losing behavior, integrated native `<select>` keyboard selection, `open_browser` initial SPA hydration settle awareness, `readonly` `inspect()` verification, unlabeled `<label>` vertical-geometry disambiguation, `button`/`clickable` duplicate `<label>` quirks, File Explorer multi-cell/multi-monitor/mixed-locale notes, live third-party site-isolated embed `BLIND_REGIONS:0` reporting, Win32 file-save `inspect()` vs disk desync, covered `PrintWindow` RTL/Mica notes, and non-blocking `list_sessions()` navigation lag.
- **[references/mcp_tools.md](.agents/skills/computer-use-lite/references/mcp_tools.md) (`73` lines):** Updated parameter behavior notes for `open_browser`, `list_desktop_windows`, `discover`, `inspect`, and `act` using only schema-verbatim constants (`13`, `1280`, `720`, `40`, `60`, `350`, `400`, `1`, `0`, `>2 px`) and non-numeric internal cap wording.
- **[references/python_api_and_safety.md](.agents/skills/computer-use-lite/references/python_api_and_safety.md) (`103` lines):** Updated `BrowserSession` boundaries (local-origin fixture pass vs live third-party embed omission, shared `.value` signature cause) and `DesktopSession` boundaries (`ValuePattern` Save As desync, live covered `PrintWindow` behavior, RTL mirroring asymmetry, dark Mica backdrop).
- **[evals/evals.json](.agents/skills/computer-use-lite/evals/evals.json) & [evals/trigger_eval.json](.agents/skills/computer-use-lite/evals/trigger_eval.json):** Updated expectations cleanly to test `<select>` keyboard handling, `readonly` `inspect()` verification, Save As disk-vs-`inspect()` desync, and covered `PrintWindow`/RTL caveats without overlapping `M5` held-out targets.

---

## 5. M4 Mechanical Hardcode & Validation Verification

From [lint_output.txt](skill_updates/2026-11-26_final/lint_output.txt) (`lint_skill.py` `rc=0`) and `quick_validate.py` (`rc=0`):
- **Instruction files scanned:** `references/mcp_tools.md`, `references/python_api_and_safety.md`, `SKILL.md`
- **Unjustified instruction hardcode / site / app / locale / banned-word flags:** `0` (`0` URLs, `0` domains, `0` site/app names, `0` locale strings, `0` forbidden words)
- **Schema/packaging-justified hits:** `68` (strictly schema defaults, section headings, SPDX/dependency bounds, `SHA-256`, `>2 px`)
- **Packaging structural validation (`quick_validate.py`):** `Skill is valid!` (`rc=0`)

---

## 6. M5 Held-Out Live Validation (`prior_skill` vs `final_skill` on `HEAD` `PID 18036`)

All `18` sequential alternating subagent executions across `3` repeats of `3` brand-new held-out tasks (`F1`: `docs.python.org/3/` `<select>` version switcher + `Quick search`; `F2`: `httpbin.org/forms/post` + `scrapethissite.com/pages/forms/`; `F3`: non-destructive `File Explorer` multi-monitor/multi-cell/mixed-locale `Address Bar` + covered `Settings` `PrintWindow` crop) ran against `PID 18036` with `0` headless violations, `0` shell GUI launches, `0` contamination reads, and `0` leaked sessions (`list_sessions().count == 0`). Raw counts from [m5_summary.json](skill_updates/2026-11-26_final/m5_runs/m5_summary.json) & [M5_RESULTS.md](skill_updates/2026-11-26_final/m5_runs/M5_RESULTS.md):

| Arm | Repeat | Pass | MCP Calls | Discover Calls | Crop-Suppress Flags | Combobox `act(type)` | Stale Retries | MCP Unexp Err | Non-MCP Err | Wall s | Lat Med ms | Map `TOKENS_EST` | Subagent Non-Cached Tok |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `prior_skill` | 1 | 3/3 | 56 | 16 | 4 | 1 | 0 | 0 | 0 | 401.0 | 51.5 | 5309.5 | 331109 |
| `prior_skill` | 2 | 3/3 | 58 | 17 | 0 | 0 | 0 | 0 | 0 | 443.0 | 53.1 | 6723.4 | 334091 |
| `prior_skill` | 3 | 3/3 | 54 | 13 | 0 | 1 | 0 | 0 | 0 | 418.0 | 54.4 | 4607.7 | 330233 |
| `final_skill` | 1 | 3/3 | 59 | 13 | 9 | 0 | 0 | 0 | 0 | 441.0 | 50.8 | 3996.7 | 324781 |
| `final_skill` | 2 | 3/3 | 55 | 13 | 5 | 0 | 0 | 0 | 0 | 416.0 | 50.1 | 3996.7 | 320358 |
| `final_skill` | 3 | 3/3 | 54 | 13 | 12 | 0 | 0 | 0 | 1 | 413.0 | 53.6 | 3974.1 | 352306 |

### Run-to-Run Spread & Variance Decisions
- **Pass Rate:** `prior_skill` `[3, 3, 3]` (`9/9`) vs `final_skill` `[3, 3, 3]` (`9/9`) -> **no measurable change (overlaps run-to-run spread)**.
- **MCP Calls per 3-task Run:** `prior_skill` `54..58` (med `56`) vs `final_skill` `54..59` (med `55`) -> **no measurable change (overlaps run-to-run spread)**.
- **Discover Calls per 3-task Run:** `prior_skill` `13..17` (med `16`) vs `final_skill` `13..13` (med `13`) -> **no measurable change (overlaps run-to-run spread)**, though `final_skill` held constant `13` across all `3` repeats.
- **Map `TOKENS_EST` Sum per 3-task Run:** `prior_skill` `4607.7..6723.4` (med `5309.5`) vs `final_skill` `3974.1..3996.7` (med `3996.7`) -> **non-overlapping across `3` repeats** (`final_skill` avoided wasteful `discover(max_elements=120)` `<select>` expansion attempts, extra Explorer role filters, and `0/3` vs `2` `combobox` `act(type)` guesses in `F1`).
- **Explicit Crop-Suppression Flag Usage (`include_blind_images=False` / `export_crops=False`):** `prior_skill` `[4, 0, 0]` (`4` calls total) vs `final_skill` `[9, 5, 12]` (`26` calls total across `F1`, `F2`, `F3`).
- **Wall Time s, Discover Latency Med ms, and Subagent Non-Cached Tokens:** `prior_skill` (`401.0..443.0 s`, `51.5..54.4 ms`, `330233..334091` tok) vs `final_skill` (`413.0..441.0 s`, `50.1..53.6 ms`, `320358..352306` tok) -> **no measurable change (overlaps run-to-run spread)**.
- **Error Transparency:** `0` unexpected MCP tool errors (`"ok":false`) across all `18` runs; `1` non-MCP `read_file` error (`file does not exist`) occurred in `final_skill` Repeat `3` `F1` (`6d620462` step `29`) before inspecting the final OS capture cleanly on `PASS`.
- *(Historical M5 context from [skill_updates/2026-11-26/m5_runs/M5_RESULTS.md](skill_updates/2026-11-26/m5_runs/M5_RESULTS.md): earlier comparison between V1 `old_skill` and `prior_skill` on `HT1`–`HT3` already established the non-overlapping shift in `navigate(auto_discover=True)` from `9/9` to `0/9` alongside non-overlapping MCP Calls `72..76` vs `56..70` and `TOKENS_EST` `4765.3..4824.5` vs `4495.9..4593.7`, which `final_skill` preserved.)*

---

## 7. What I Did NOT Verify

- Did **not** re-run the full `pytest` repository test suite (source code `src/` and `tests/` were strictly unmodified by boundary; latest source suite check remains commit `abebcff` `FIX_REPORT.md` `5/5` consecutive `52` pytest + `8/8` CLI E2E).
- Did **not** verify Closed Shadow DOM on a live public page (`mdn.github.io/.../closed-shadow-dom` returned HTTP `404` in `M1` probe #8 and remaining checked pages used open Shadow DOM).
- Did **not** execute `evals/evals.json` or `evals/trigger_eval.json` as additional LLM grading runs after updating `evals/` assertions (held-out live verification focused on fresh `F1`–`F3` subagent runs strictly disjoint from `evals/`).
- Did **not** stress-test concurrent `MAX_SESSIONS` = `16` real live Chromium + UIA processes simultaneously.
- Did **not** execute keyboard `SendInput` replacement (`Ctrl+a` + physical typing) as a recovery path inside Win32 `#32770` Save As dialogs live (to avoid non-US `VkKeyScanW` side effects on user IME state).
- Did **not** test single-character printable desktop `press_key()` on non-US input locales (`VkKeyScanW` in `desktop_uia.py:L272`), nor test execution on Linux/macOS (blocked at module import by `ctypes.WinDLL("user32")`).

---

## 8. Rules I Am Least Sure About

- **Win32 `#32770` Save As workaround boundary:** While `ValuePattern.SetValue` desync on `#32770` Save As (`Edit` `1001`) is doubly verified live (`T15` + `M1` #7, deceiving even `inspect()`), I have not tested live whether `click_at` + `Ctrl+a` + clipboard paste or typing via `SendInput` reliably fixes `IFileSaveDialog` across locales without introducing `VkKeyScanW` bugs; therefore the skill conservatively instructs independent disk verification and honest `PARTIAL / FAIL (Native Dialog UIA Desync)` reporting rather than an untested keyboard workaround.
- **Exact UI framework trigger for RTL `PrintWindow` mirroring:** `M1` probe #6 showed RTL Arabic `Notepad.exe` (`المفكرة`) mirrored horizontally under `PrintWindow` while UWP Arabic `الحاسبة` rendered un-mirrored, whereas `Settings` (`SystemSettings.exe`) on LTR mode rendered un-mirrored. Because only two RTL desktop apps were tested live, the skill qualifies RTL mirroring as `"check for horizontal mirroring on WinUI/Win32 PrintWindow crops (some UWP frames remain un-mirrored)"` rather than claiming a universal Win32/WinUI law.
- **Third-party vs localhost OOPIF boundary:** Localhost fixture `test_m4_p02` extracts cross-origin frames while live `practice.expandtesting.com/iframe` omitted `youtube.com/embed` and ad frames (`BLIND_REGIONS:0`). Without inspecting/modifying `src/` CDP target-attachment logic across Chromium site-isolation flags, the exact boundary between same-process vs out-of-process third-party iframe omission relies on runtime `discover()` observation.

---

## 9. Evidence Gaps (Lessons I Could Not Turn Into Rules)

1. **No VLM vs compact-map token comparison exists in the repository:** `HARNESS_VALIDATION.md` executed `0` LLM calls and zero live VLM screenshot baselines were run, so no rule can state numeric end-to-end LLM cost or wall-time savings ratios.
2. **Closed Shadow DOM live site interaction remains unobserved:** Because no reachable public non-captcha closed-Shadow-DOM test target was found, the skill treats closed Shadow DOM solely as a documented omission boundary (`report discovery omission if missing`).
3. **Non-US `VkKeyScanW` single-character mapping in `press_key()`:** Because mutating the user's Windows input locale was out of bounds and risky, single-character printable keystroke mapping on non-US layouts remains unverified live and excluded from confident usage rules.
4. **Full `16`-session concurrent OS stress behavior:** Only single/dual-session concurrency (`T18`, `F3`) was tested live; resource saturation limits remain unit-only.
5. **Non-Windows execution (`Linux` / `macOS`):** Because Win32 `ctypes.WinDLL("user32")` imports at load time, cross-platform behavior could not be turned into supported runtime rules.

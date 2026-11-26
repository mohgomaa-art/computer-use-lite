> [!NOTE]
> **Archival Provenance:** Moved from `SKILL_UPDATE_REPORT.md` (pre-move SHA-256: `AF84136021AE4DD266B32B6F33607A1A5BCB34DDE350C16C2D8F66348059225B`). Archived Skill Update Report (Round 1). Superseded by [Round 2 Final Skill Report](2026-11-26-skill-update-report-final.md). Note: `skill_updates/2026-11-26/verify_report_numbers.py` still expects the original root filename if re-executed unmodified. See also [Archive Index](../INDEX.md) and [README](../../README.md).
> *(Absolute local workstation URIs and relative paths were normalized for archival portability; original findings, figures, and scope claims below are preserved verbatim.)*

# Skill Update Report — `computer-use-lite` (`2026-11-26`)

## 1. Executive Summary & Provenance
- **Scope:** Updated skill files strictly under `.agents/skills/computer-use-lite/` (`SKILL.md`, `references/mcp_tools.md`, `references/python_api_and_safety.md`, `evals/evals.json`, `evals/trigger_eval.json`) alongside working artifacts under `skill_updates/2026-11-26/`. Zero changes were made to `src/`, `tests/`, benchmarks, past reports, or MCP tool schemas.
- **Stale Server Discovery:** During M0, running MCP process `PID 4076` was confirmed to have started at `2026-11-26T10:06:13` (`m0_env_git.txt`), predating all `8` source fix commits (`47bea1bb..6a2f0fbb`, ending `2026-11-26T12:09:59+02:00`). Therefore, `T01`–`T18` live runs (`RUN_REPORT.md`, `summary_metrics.json`) were treated as pre-fix observations where `src/` changed later, whereas `tests/test_audit_fixes.py` / `fix_runs/2026-11-26/` represented headless/fixture/mocked post-fix behavior.
- **M5 Server Restart Verified:** Prior to held-out M5 runs, the IDE MCP server was reloaded (`PID 18036`, `CreationDate: 2026-11-26T14:02:29.5128990+02:00`, documented in `skill_updates/2026-11-26/m5_runs/server_check.json`) and verified at runtime via `open_browser("http://127.0.0.1:9/")` returning `PermissionDenied` (`CUL_MCP_ALLOW_PRIVATE_URLS=1`).
- **Commit History:**
  - `f0fd6ba`: Committed M0–M2 audit (`m0_claim_inventory.md`, `LESSONS.md`, `DESIGN.md`, `old_skill_snapshot/`) before modifying any skill files.
  - `ace5c5f`: Committed updated skill (`M3`), lint results (`M4`), and locked pre-M5 held-out criteria (`M5_HELD_OUT_PLAN.md`) before running M5.

---

## 2. Changes Made & Evidence Mapping

| Target File | Key Revisions Made | Evidence / Traceability |
| :--- | :--- | :--- |
| `.agents/skills/computer-use-lite/SKILL.md` | Removed unverified numeric token-saving claims (`100k-token`, `~300–700 tokens`) and hardcoded IDs/boxes (`e12`, `420,180,96,36`, `Sign in`); removed undocumented internal caps (`16`, `4`, `5 px`); added **Runtime Capability Detection** (schema + `inspect` probe + error-driven env gates); fixed `navigate` default to `auto_discover=False` with hydration settle rule; documented `inspect` limitation on `combobox`/`checkbox`/slider controls; added central **Independent Verification Discipline** table; added explicit **When This Fails, Report It Like This** protocols (new tabs, drag-and-drop, frame/collapsed-browser omissions, native Save As UIA desync, `exebox` invisibility); fixed `TaskState` redaction claim to reflect all-value redaction. | `EVIDENCE_MAP.md`, `LESSONS.md`, `summary_metrics.json` (`13.0..1151.2`), `benchmarks_real.json` (`1611.0`), `api.py`, `state.py` |
| `.agents/skills/computer-use-lite/references/mcp_tools.md` | Kept all `13` exact schema tables and defaults (`1280`, `720`, `40`, `60`, `350`, `400`, `1`, `>2 px` in `act.json`); stripped non-schema caps (`200..3840`, `200..2160`, `1..200`, `1..300`, `0..5000`, `1..3`, `4096`, `16`, `4`); added `CUL_MCP_ALLOW_PRIVATE_URLS=1` default private/loopback block, `searchbox` parity in `inspect`, `list_desktop_windows` offscreen filter warning, `list_sessions` post-click URL lag, and unhandled `Error` (`recoverable: false`). | `mcp_server.py`, `session_manager.py`, `test_audit_fixes.py`, `LESSONS.md` (`L1.2`, `L3.1`, `L10.1`, `L13.1`, `L14.1`) |
| `.agents/skills/computer-use-lite/references/python_api_and_safety.md` | Removed magic constants from `blind_gap.py` and `KillSwitch`; fixed `capture_desktop_region` description (`PrintWindow` prioritized first for covered/cloaked HWNDs, marked unverified live on `Default` pixel contrast); clarified multi-document OOPIF discovery (unverified live on real public sites) vs closed Shadow DOM omission; clarified `CUL_SKIP_DESKTOP=1` applies to headless Windows CI due to import-time `WinDLL('user32')`. | `blind_gap.py`, `desktop_uia.py`, `browser_cdp.py`, `FIX_REPORT.md`, `test_audit_fixes.py`, `repro_findings.txt` |
| `.agents/skills/computer-use-lite/evals/{evals.json, trigger_eval.json}` | Removed banned phrasing and non-schema caps from `evals.json` assertions; updated expectations for independent verification and `inspect` role scope; updated `trigger_eval.json` CI query to headless Windows CI and included loopback URL policy flag alongside local file URLs. | `m0_claim_inventory.md`, `repro_findings.txt`, `test_audit_fixes.py` |

---

## 3. M4 Mechanical Hardcode Lint & Schema Check
- **`skill_updates/2026-11-26/lint_skill.py` -> `skill_updates/2026-11-26/lint_output.txt` (`exit_code = 0`):**
  - Instruction files scanned (`3`): `SKILL.md`, `references/mcp_tools.md`, `references/python_api_and_safety.md`.
  - **Unjustified instruction flags:** `0`.
  - **Justified schema/packaging/standard tokens:** `67` (strictly tool defaults `1280`, `720`, `40`, `60`, `350`, `400`, `1`, `0`, `>2 px` from `act.json`, `13` tools, `Windows 10/11`, SPDX/dependency versions in frontmatter, section numbers `1`–`5`, and `SHA-256`).
  - **Eval fixture prompt flags (`evals/` user prompt strings excluded from M5):** `15`.
- **`quick_validate.py`:** `returncode = 0`, output `"Skill is valid!"`.

---

## 4. M5 Held-Out Validation (`old_skill` vs `new_skill`, `3` Runs per Arm)

Executed sequentially (`1` live `headless=False` browser task at a time, alternating arm order across Repeats `1`–`3`) on NEW held-out targets (`HT1`: `quotes.toscrape.com/js/` + `books.toscrape.com/`, `HT2`: `selenium.dev/selenium/web/web-form.html` + `127.0.0.1` policy check, `HT3`: `todomvc.com/examples/react/dist/` + `playwright.dev/` searchbox) using `PID 18036` (`m5_runs/m5_summary.json`, `m5_runs/M5_RESULTS.md`):
- Compliance checks across all `18` subagent transcripts (`transcript_full.jsonl`): `0` contamination reads, `0` `headless=True` violations, `0` unexpected tool errors, `0` leaked open sessions, `0` leftover `cul_mcp_*` temp dirs.

| Metric (3-Task Suite Run, `n = 3` Repeats / Arm) | `old_skill` (`min..max`, med / list) | `new_skill` (`min..max`, med / list) | Variance Assessment |
| :--- | :--- | :--- | :--- |
| Task Pass Rate | `3/3, 3/3, 3/3` (`9/9`) | `3/3, 3/3, 3/3` (`9/9`) | **No measurable change** (both `9/9`) |
| MCP Tool Calls per Run | `72..76`, med `75` (`223` total) | `56..70`, med `68` (`194` total) | Non-overlapping across `3` repeats (`new_skill` lower) |
| `navigate(auto_discover=True)` Count | `3, 3, 3` (`9` total) | `0, 0, 0` (`0` total) | Non-overlapping adherence difference (`0` `playwright.dev` `navigate` `StaleElementError`s on `new_skill` vs `3/3` runs hitting it on `old_skill`) |
| `StaleElementError` Retries per Run | `1..2` (`1, 1, 2`, `4` total) | `0..1` (`0, 1, 0`, `1` total) | **No measurable change** (overlaps run-to-run spread; `new_skill` Run `2` hit `1` on `open_browser(auto_discover=True)`) |
| End-to-End Wall Time (`s`) per Run | `454.0..481.0`, med `457.0` | `395.0..479.0`, med `452.0` | **No measurable change** (overlaps run-to-run spread) |
| Discover `LATENCY_MS` Median (`ms`) | `23.9..25.0` | `23.5..27.4` | **No measurable change** (overlaps run-to-run spread) |
| Map `TOKENS_EST` Sum per Run | `4765.3..4824.5` | `4495.9..4593.7` | Non-overlapping across `3` repeats (`new_skill` lower) |
| Subagent Non-Cached LLM Tokens (`in + out`) | `349446..421714` | `325984..350084` | **No measurable change** (overlaps run-to-run spread: `349446 <= 350084`) |

- **Behavior noted on `HEAD` `PID 18036` during M5:** Both `HT2` (`127.0.0.1` `PermissionDenied` SSRF block) and `HT3` (`playwright.dev` `searchbox` `"value": "locator"` read-back via `inspect`) succeeded live across all `6/6` relevant attempts (`3` `old`, `3` `new`). On `HT2`, both arms visually verified non-textbox controls (`checkbox`, `radio`, `combobox`) because the prompt explicitly required stating what tools could vs could not confirm.

---

## 5. What I did NOT verify
1. **Live Windows Desktop UIA workflows on restarted `PID 18036`**: Held-out validation `HT1`–`HT3` covered browser workflows only (including live `searchbox` `inspect` and live `127.0.0.1` SSRF block). I did **not** run live interactive desktop held-out tasks (`open_desktop`, `ForegroundMismatch` dialog attachment, native Save As dialogs, or `PrintWindow` covered-window ordering `P-09` on `WinSta0\Default`).
2. **Live external public-site OOPIF (`P-02`) and `<label>`/`overflow` pruning (`P-04`) on restarted `PID 18036`**: Both fixes passed local headless localhost/corpus checks in `tests/test_audit_fixes.py` (prior commit `abebcff`), not live third-party public pages in this session.
3. **Closed Shadow DOM, localized `press_key`, non-Windows import, and `16`-session saturation live tests**: None of these were exercised in live runs.
4. **Re-running `pytest tests` or `tests/test_e2e.py` in this session**: Because zero `src/` or `tests/` files were modified, the existing repository code suites were not re-executed here (prior commit `abebcff` results live in `FIX_REPORT.md` / `fix_runs/2026-11-26/m6_final_runs/summary.json`, not newly run here).

---

## 6. Rules I am least sure about
1. **Layered overlapping `<canvas>` emitting duplicate `blind<k>` crops (`SKILL.md` §4 / `LESSONS.md` `L9.1`)**: Seen once in `T07.json` on pre-fix `PID 4076` and not re-verified on `HEAD` `PID 18036` or in M5 held-out runs.
2. **`<input type="date">` / formatted non-textbox widget corruption under `act(..., "type")` (`SKILL.md` §3 / `LESSONS.md` `L3.2`)**: Observed once in `T01.json` (`02/02/61201`) and not tested on restarted `PID 18036` or in M5 held-out tasks.
3. **Win32 `PrintWindow` horizontal mirroring on RTL Windows locales (`SKILL.md` Independent Verification / `LESSONS.md` `L12.1`)**: Observed once on a single Arabic Windows 11 host in `T15.json`; not re-tested across restarted `PID 18036` or other RTL applications/locales, and `P-09` live `Default`-desktop contrast remains unverified.

---

## 7. Evidence gaps (lessons I could not turn into rules)
- **Closed Shadow DOM live browser behavior**: Zero public interactive closed-Shadow-DOM targets were tested (`T05` noted absence on target); empirical behavior beyond synthetic benchmarks could not be converted into a confident recovery rule.
- **VLM end-to-end token savings claims**: `HARNESS_VALIDATION.md` ran zero vision-LLM turns and `AUDIT_REPORT.md` confirmed no VLM screenshot-loop baseline exists; any numeric VLM token reduction rule had to be omitted rather than rewritten.
- **Non-US keyboard layout behavior on desktop `press_key()`**: `desktop_uia.py` uses `VkKeyScanW` on single printable characters, which was untested live on RTL/non-US layouts; could not establish exact failure/success conditions for non-ASCII single-key `press_key`.
- **Live multi-window `Default` desktop `PrintWindow` pixel fidelity (`P-09`)**: `FIX_REPORT.md` marked live `Default` pixel contrast `BLOCKED` due to `exebox` shell isolation, so real occluded-window pixel fidelity could not be turned into a verified guarantee.
- **Non-Windows compatibility and `MAX_SESSIONS` live ceiling**: `snapshot.py` imports `ctypes.WinDLL('user32')` on load (`repro_findings.txt`), and live saturation up to `MAX_SESSIONS` was never exercised; Linux execution and high-concurrency degradation rules could not be authored from evidence.

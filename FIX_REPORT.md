# Audit Verification & Fix Report (`2026-11-26`)

> Scope: Fixes executed strictly against [`FIX_PLAN.md`](FIX_PLAN.md) (`bc7b72f`) starting from pre-audit source/test snapshot `0e42dde` (`HEAD` at M0 was `8744f98`). All measurements below come verbatim from raw artifacts under `fix_runs/2026-11-26/` on `Windows-11-10.0.26200-SP0`, Python `3.12.10`, `playwright 1.64.0`, `comtypes 1.5.0`, `websockets 17.2`, `mcp 1.30.0`, `pillow 12.3.0`, `pytest 9.1.1`, `anyio 4.15.1` (`ThreadDesktop: exebox-ZZCPDTPBZLIC6SSDOAVVSJYEEB`, `InputDesktop: Default`).

---

## 1. Summary Scorecard

| Status | Count | Scope Breakdown |
| :--- | ---: | :--- |
| **`FIXED-VERIFIED`** | **9** | `M2-1` (`P-03`), `M2-2` (`P-01`), `M2-3` (`P-06`), `M2-4` (`P-19b`), `M3` (`P-10`), `M4-1` (`P-02`), `M4-2` (`P-04`), `M4-3a` (`P-09` ordering/cloaking + `exebox` `PrintWindow`), `M6` (verified doc errors) |
| **`FIXED-UNVERIFIED`** | **0** | None |
| **`NOT-REPRODUCED`** | **1** | `P-19(c)` (`TaskState` non-password plaintext persistence) |
| **`BLOCKED`** | **1** | `M4-3b` (`P-09` live `Default`-desktop `ImageGrab` foreground occlusion contrast in `exebox` isolation) |
| **`SKIPPED`** | **6** | Deferred out-of-scope audit items (`P-05`, `P-11`, `P-14`, `P-15`, `P-16`, `P-19a`) |

---

## 2. Status Table by Item

| Item / Audit ID | Status | Check Type | Commit Hash | Saved Evidence Path & Observed Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **`M2-1` (`P-03`)** Search input `searchbox` role & `inspect` | **`FIXED-VERIFIED`** | `LIVE` (headless Chromium + `Api`) | `47bea1b` | Red: `role=clickable`, `has_value_in_inspect=False` ([repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt), [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt) `EXIT_CODE=1`). Green: `TARGETED_EXIT_CODE=0`, `SUITE_EXIT_CODE=0` (`44 passed`, [m2_1_p03.txt](fix_runs/2026-11-26/m2_fixes/m2_1_p03.txt)); final `52 passed` (`m6_final_runs/run_1.txt`). |
| **`M2-2` (`P-01`)** Dense-DOM occlusion & lazy boxes (`2,500` cells) | **`FIXED-VERIFIED`** | `LIVE` (headless Chromium + parity check) | `319382c` | Red: `627.17 ms` local Python `p50` (`EXIT_CODE=1`, [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `PARITY_EXIT_CODE=0` (`dense=1`, `corpus=20`), `TARGETED_EXIT_CODE=0`, `SUITE_EXIT_CODE=0` ([m2_2_p01.txt](fix_runs/2026-11-26/m2_fixes/m2_2_p01.txt)); M5 `python_ms p50=19.32 ms` ([m5_comparison.txt](fix_runs/2026-11-26/m5_perf/m5_comparison.txt)). |
| **`M2-3` (`P-06`)** Skip `os.fsync` on disposable temp `TaskState` | **`FIXED-VERIFIED`** | `LIVE` (disk `TaskState` + `SessionManager`) | `51143f7` | Red: `TypeError` on `fsync=False` ([pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `0` `os.fsync` calls for `fsync=False` / `SessionManager.act`, `1` call per `save()` for default `fsync=True`, `TARGETED_EXIT_CODE=0`, `SUITE_EXIT_CODE=0` ([m2_3_p06.txt](fix_runs/2026-11-26/m2_fixes/m2_3_p06.txt)); M5 `p50=2.944 ms` vs `6.103 ms`. |
| **`M2-4` (`P-19b`)** Private/loopback/link-local SSRF guard + `A1` opt-in | **`FIXED-VERIFIED`** | `LIVE` (stdio MCP server + `SessionManager` + unit checks) | `e416ba5` | Red: accepted `127.0.0.1:9222`, `localhost:8000`, `169.254.169.254`, `10.0.0.1`, `[::1]:8080` ([repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt), [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: stdio MCP returned `isError=True`, `error_type=PermissionDenied` (`MCP_SSRF_EXIT_CODE=0`, `TARGETED_EXIT_CODE=0`, `SUITE_EXIT_CODE=0`, [m2_4_p19b.txt](fix_runs/2026-11-26/m2_fixes/m2_4_p19b.txt)). |
| **`P-19(c)`** Non-password plaintext in persisted `TaskState` | **`NOT-REPRODUCED`** | `LIVE` (`TaskState` disk JSON inspection) | `0e42dde` (unchanged) | Both M0 ([repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt)) and M6 (`test_m2_p19b_ssrf_guard_and_state_redaction`) confirmed `contains SECRET-CUSTOMER-999 = False` and `value_redacted=True`. Production `state.py` redaction left untouched. |
| **`M3` (`P-10`)** Store Notepad tab/PID/UIA hydration cleanup, non-overwrite, zero return warnings | **`FIXED-VERIFIED`** | `LIVE` (`exebox` Win11 Notepad + subprocess `pytest` + CLI E2E) | `fef1d5a`, `2280fcc` | Red: `PytestReturnNotNoneWarning` x`8`, `new_hwnds=set()` on tabbed Notepad ([repro_notepad_and_grab.txt](fix_runs/2026-11-26/m0_baseline/repro_notepad_and_grab.txt), [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `5/5` on `m3_reliability` (`summary.json`) AND `5/5` on final `abebcff` (`52 passed` + `8/8 passed`, `0` leaked PIDs, `git_diff_results_unchanged=true`, [m6_final_runs/summary.json](fix_runs/2026-11-26/m6_final_runs/summary.json)). |
| **`M4-1` (`P-02`)** Cheaper OOPIF `DOMSnapshot` semantic discovery | **`FIXED-VERIFIED`** | `LIVE` (`DualOriginCorpusServer` + headless Chromium) | `58d55fc` | Red: `recall=0.9412`, `cross_origin_iframe=1`, `OOPIF Email` `role=clickable` ([repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt), [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `recall=1.0`, `cross_origin_iframe=0`, `Cross Origin Save`=`button`, `OOPIF Email`=`textbox`, `OOPIF_EXIT_CODE=0`, `SUITE_EXIT_CODE=0` ([m4_1_p02.txt](fix_runs/2026-11-26/m4_accuracy/m4_1_p02.txt)). |
| **`M4-2` (`P-04`)** `<label>` / duplicate clickable / overflow scroll clipping | **`FIXED-VERIFIED`** | `LIVE` (`DualOriginCorpusServer` + hidden-input `<label>` test) | `d0c4132` | Red: `prec=0.8421` API / `0.8` raw, `false_positive_count=3` API / `4` raw ([repro_corpus_split.txt](fix_runs/2026-11-26/m0_baseline/repro_corpus_split.txt), [pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `precision=1.0`, `recall=1.0`, `false_positive_count=0`, `CORPUS_EXIT_CODE=0`, `TARGETED_EXIT_CODE=0`, `SUITE_EXIT_CODE=0` ([m4_2_p04.txt](fix_runs/2026-11-26/m4_accuracy/m4_2_p04.txt)). |
| **`M4-3a` (`P-09`)** Covered/background/cloaked `PrintWindow` priority | **`FIXED-VERIFIED`** | `MOCKED` (`ImageGrab`/cloaked) + `LIVE` (`exebox` overlapped Chrome) | `6a2f0fb` | Red: `method='imagegrab'` ([pytest_m1_red.txt](fix_runs/2026-11-26/m1_red/pytest_m1_red.txt)). Green: `test_m4_p09` `PASSED` (`MOCKED` foreground overlap returns `(0, 255, 0)` + cloaked skips `ImageGrab`) + `LIVE_EXEBOX_PW method=printwindow size=(120, 120) center_px=(22, 163, 74)` (`LIVE_PW_EXIT_CODE=0`, `FULL_SUITE_EXIT_CODE=0`, [m4_3_p09.txt](fix_runs/2026-11-26/m4_accuracy/m4_3_p09.txt)). |
| **`M4-3b` (`P-09`)** Live `Default`-desktop `ImageGrab` vs `PrintWindow` pixel contrast | **`BLOCKED`** | Attempted `LIVE` (`exebox`) | — | Inside `exebox-ZZCPDTPBZLIC6SSDOAVVSJYEEB`, `ImageGrab.grab()` raises `OSError: screen grab failed` ([repro_notepad_and_grab.txt](fix_runs/2026-11-26/m0_baseline/repro_notepad_and_grab.txt), [environment.txt](fix_runs/2026-11-26/m0_baseline/environment.txt)). Live `Default`-desktop verification requires running outside `exebox`. |
| **`M6` (`P-22`)** Docs corrections (`README.md`, `ARCHITECTURE_DECISION.md`) | **`FIXED-VERIFIED`** | Verified against source files & `5/5` final run | `abebcff` | Fixed Gate 0 wording contradiction, updated §3 table to exact `benchmarks_real.json` values, documented `CUL_MCP_ALLOW_PRIVATE_URLS=1`, `fsync=False`, OOPIF/FP filters, `PrintWindow` priority, and `test_e2e.py` temp output (`FINAL_SUMMARY_ALL_OK=True`, [m6_final_runs/summary.json](fix_runs/2026-11-26/m6_final_runs/summary.json)). |
| **`P-05`, `P-11`, `P-14`, `P-15`, `P-16`, `P-19a`** | **`SKIPPED`** | — | — | Deliberately omitted from `FIX_PLAN.md` scope (see Section 6). |

---

## 3. Before / After Performance & Accuracy

Measured on identical hardware (`0e42dde` worktree vs final `HEAD`) via [`run_m5_benchmarks.py`](fix_runs/2026-11-26/m5_perf/run_m5_benchmarks.py) (`LIVE` headless Chromium & stdio MCP; outputs saved in [m5_before.json](fix_runs/2026-11-26/m5_perf/m5_before.json), [m5_after.json](fix_runs/2026-11-26/m5_perf/m5_after.json), [m5_comparison.json](fix_runs/2026-11-26/m5_perf/m5_comparison.json), and [m5_comparison.txt](fix_runs/2026-11-26/m5_perf/m5_comparison.txt); `M5_EXIT_CODE=0`).

### Latency (`p50`, `p95`, `stddev` across `n >= 12` warm repeats)

| Benchmark Metric (`LIVE`) | `n` | Before `p50` (ms) | Before `p95` (ms) | Before `stddev` (ms) | After `p50` (ms) | After `p95` (ms) | After `stddev` (ms) | Delta `p50` | Assessment |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Dense `2,500`-cell `discover()` total | 15 | 1056.166 | 1284.986 | 174.669 | 273.085 | 334.292 | 33.125 | `-783.081 ms (-74.14%)` | Real win outside `stddev` |
| Dense `2,500`-cell local Python (`total - cdp`) | 15 | 824.401 | 1016.166 | 163.974 | 19.32 | 30.458 | 5.205 | `-805.081 ms (-97.66%)` | Real win (`< 30.0 ms` threshold passed) |
| Dense `2,500`-cell CDP RPC (`DOMSnapshot` + `AXTree`) | 15 | 256.425 | 298.209 | 22.676 | 257.694 | 305.331 | 29.394 | `+1.269 ms (+0.49%)` | Chromium IPC unchanged (within noise) |
| `TaskState.record_action()` (`fsync=True` vs `fsync=False`) | 20 | 6.103 | 8.092 | 1.31 | 2.944 | 4.808 | 0.98 | `-3.159 ms (-51.76%)` | Real isolated I/O win (`0` vs `20` fsyncs) |
| `SessionManager.act()` end-to-end | 15 | 23.159 | 30.566 | 3.52 | 23.015 | 30.816 | 4.716 | `-0.144 ms (-0.62%)` | Within end-to-end `stddev` noise (`0` vs `15` fsyncs) |
| `DualOriginCorpusServer` `Api.discover_interactables` | 12 | 18.087 | 50.911 | 19.088 | 17.106 | 19.332 | 1.525 | `-0.981 ms (-5.42%)` | Maintained/lower latency & tighter tail |
| Direct `Api.discover_interactables` (fixture) | 15 | 13.255 | 15.005 | 1.002 | 12.965 | 18.392 | 2.512 | `-0.29 ms (-2.19%)` | Within noise |
| MCP stdio `discover` (fixture) | 15 | 13.497 | 19.292 | 3.17 | 13.764 | 17.22 | 2.351 | `+0.267 ms (+1.98%)` | Within noise (`discover_overhead_p50_ms=0.799`) |
| Direct `Api.execute_action` (fixture) | 15 | 22.347 | 25.111 | 1.917 | 22.116 | 28.564 | 3.478 | `-0.231 ms (-1.03%)` | Within noise |
| MCP stdio `act` (fixture) | 15 | 20.314 | 29.49 | 4.57 | 18.297 | 20.169 | 1.193 | `-2.017 ms (-9.93%)` | Within pre-fix `stddev` (`act_overhead_p50_ms=-3.819`) |

*(Note: After `abebcff`, `m5_after.json` also measured durable `fsync_true` in the same run: `p50=6.169`, `p95=8.168`, `stddev=1.253`, `fsync_calls=20` vs `fsync_false` `p50=2.944`, `fsync_calls=0`. Also `mcp_overhead.benchmark_mcp_overhead_summary` reported `after` `direct_discover_p50_ms=15.28`, `mcp_discover_p50_ms=13.27`, `direct_act_p50_ms=23.96`, `mcp_act_p50_ms=17.57`.)*

### Accuracy on `DualOriginCorpusServer` (`corpus_main.html`, `baseline_count=17`)

| Target / Mode (`LIVE`) | Candidate Count | Matched Count | Recall | Precision | Role Accuracy | Missing (`cross_origin_iframe`) | False Positives | Raw File |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Before `Api.discover_interactables` (`0e42dde`) | 19 | 16 | `0.9412` | `0.8421` | `0.9375` | `1` (`1`) | `3` | [m5_before.json](fix_runs/2026-11-26/m5_perf/m5_before.json) |
| After `Api.discover_interactables` (`HEAD`) | 17 | 17 | **`1.0`** | **`1.0`** | **`1.0`** | **`0`** (`0`) | **`0`** | [m5_after.json](fix_runs/2026-11-26/m5_perf/m5_after.json) |
| Before `BrowserSession.discover()` raw (`0e42dde`) | 20 | 16 | `0.9412` | `0.8` | `0.9375` | `1` (`1`) | `4` | [m5_before.json](fix_runs/2026-11-26/m5_perf/m5_before.json) |
| After `BrowserSession.discover()` raw (`HEAD`) | 18 | 17 | **`1.0`** | `0.9444` | **`1.0`** | **`0`** (`0`) | `1` (`Below Fold Action`) | [m5_after.json](fix_runs/2026-11-26/m5_perf/m5_after.json) |

---

## 4. 5-Run Test Reliability Summary

Executed on two checkpoints:
1. **At M3 commit (`fef1d5a`, [m3_reliability/summary.json](fix_runs/2026-11-26/m3_reliability/summary.json)):** `5` consecutive runs (`[80.19, 80.55, 78.61, 72.55, 80.78]` s) of pre-M4 suites + targeted M2/M3 checks (`-W error::pytest.PytestReturnNotNoneWarning`) + `python tests/test_e2e.py` — `0` failures, `0` warnings, `TOTAL_LEAKED=0`, `git_diff_results_unchanged=true` across all `5` runs.
2. **At final commit (`abebcff`, after Notepad UIA hydration fix `2280fcc` and M6 doc fixes, [m6_final_runs/summary.json](fix_runs/2026-11-26/m6_final_runs/summary.json)):** `5` consecutive **unfiltered** full runs (`python -m pytest tests -v -rs --tb=short -W error::pytest.PytestReturnNotNoneWarning` + `python tests/test_e2e.py`):
   - **Pass/fail:** `5/5` runs exited `0` (`pytest_full_rc=0`, `test_e2e_cli_rc=0`), passing `52` pytest cases + `8/8` CLI E2E checks in every run (`[84.7, 82.81, 80.08, 86.19, 82.36]` s).
   - **Skipped tests & warnings:** `0` skipped tests (`-rs` clean), `0` warnings (`-W error::pytest.PytestReturnNotNoneWarning`).
   - **Leaked processes:** `TOTAL_LEAKED=0` (`leaked_pids={}` across all `5` runs monitoring `notepad.exe`, `chrome.exe`, and `computer_use_lite.mcp_server`). *(Note: `3` pre-existing `notepad.exe` processes `7092`, `7800`, `13196` from Session 3 prior to this workflow are recorded in `procs_before_all` and unchanged across all runs.)*
   - **Tracked `results/` / `archive/` untouched:** `git_diff_results_unchanged=true` across all `5` runs ([git_diff_results_before.patch](fix_runs/2026-11-26/m6_final_runs/git_diff_results_before.patch)); note `results/e2e/e2e_results.json` was previously modified during M0 standalone `test_e2e.py` before M3 (backed up at [e2e_results_pre_m0.json](fix_runs/2026-11-26/m0_baseline/e2e_results_pre_m0.json)).

---

## 5. Fixed Thresholds (`FIX_PLAN.md`) vs Observed Measurements

| `FIX_PLAN.md` Threshold | Observed Measurement | Raw Evidence File | Result |
| :--- | :--- | :--- | :--- |
| **`M2-1`:** `<input type="search">` maps to `searchbox`, `click,type`, `type` `ok=True`, `inspect` returns value (redacts if `is_password=True`) | `test_m2_p03_searchbox_role_and_inspect PASSED` (`Search site`, `click,type`, `mcp query`, `[REDACTED]`) | [m2_1_p03.txt](fix_runs/2026-11-26/m2_fixes/m2_1_p03.txt), [m6_final_runs/run_1.txt](fix_runs/2026-11-26/m6_final_runs/run_1.txt) | **`FIXED-VERIFIED`** |
| **`M2-2`:** `2,500`-cell local Python `p50 < 30.0 ms`; exact element parity on dense DOM & `DualOriginCorpusServer` | M5 Python `p50=19.32 ms` (`< 30.0 ms`, `n=15`); `PARITY_EXIT_CODE=0` (`dense=1`, `corpus=20`); modal test `PASSED` | [m2_2_p01.txt](fix_runs/2026-11-26/m2_fixes/m2_2_p01.txt), [m5_comparison.txt](fix_runs/2026-11-26/m5_perf/m5_comparison.txt) | **`FIXED-VERIFIED`** |
| **`M2-3`:** `fsync=False` / MCP `SessionManager` `0` `os.fsync` calls; default `fsync=True` `1` per `save()`; `fsync=False p50 <= 60%` of `fsync=True p50` | `0` fsyncs on `fsync=False` & `SessionManager.act`, `1` on `durable`; M5 `2.944 ms / 6.103 ms` (`-51.76%`) | [m2_3_p06.txt](fix_runs/2026-11-26/m2_fixes/m2_3_p06.txt), [m5_comparison.txt](fix_runs/2026-11-26/m5_perf/m5_comparison.txt) | **`FIXED-VERIFIED`** |
| **`M2-4`:** Unset opt-in blocks loopback/private/link-local (`PermissionError` / MCP `PermissionDenied`), permits `https://example.com/`, `CUL_MCP_ALLOW_PRIVATE_URLS=1` permits loopback; `0` plaintext values in `TaskState` | Stdio MCP blocked all `5` targets with `PermissionDenied` (`MCP_SSRF_EXIT_CODE=0`); unit test checked all `12` URLs + `example.com` + `SECRET-CUSTOMER-999` redaction | [m2_4_p19b.txt](fix_runs/2026-11-26/m2_fixes/m2_4_p19b.txt), [m6_final_runs/run_1.txt](fix_runs/2026-11-26/m6_final_runs/run_1.txt) | **`FIXED-VERIFIED`** |
| **`M3`:** `5` consecutive full runs (`pytest` + `test_e2e.py`): `0` failures, `0` warnings, `0` leaked PIDs, `0` `results/`/`archive/` changes | `m6_final_runs` `5/5` runs exited `0`, `0` skipped, `0` warnings, `TOTAL_LEAKED=0`, `git_diff_results_unchanged=true` | [m6_final_runs/summary.json](fix_runs/2026-11-26/m6_final_runs/summary.json), [run_1.txt](fix_runs/2026-11-26/m6_final_runs/run_1.txt) | **`FIXED-VERIFIED`** |
| **`M4-1`:** `cross_origin_iframe` failure `1 -> 0`; `Cross Origin Save`=`button`, `OOPIF Email`=`textbox`; corpus `recall == 1.0` | `cross_origin_iframe=0`, `Cross Origin Save`=`button`, `OOPIF Email`=`textbox`, `recall=1.0` (`17/17`) | [m4_1_p02.txt](fix_runs/2026-11-26/m4_accuracy/m4_1_p02.txt), [m5_after.json](fix_runs/2026-11-26/m5_perf/m5_after.json) | **`FIXED-VERIFIED`** |
| **`M4-2`:** Corpus `Api` `precision >= 0.95` & `recall == 1.0`; `Scroll Inner Hidden` dropped; hidden-input `<label>` preserved | `Api` `precision=1.0`, `recall=1.0`, `false_positive_count=0`; `test_m4_p04_hidden_input_label_stays_discoverable PASSED` | [m4_2_p04.txt](fix_runs/2026-11-26/m4_accuracy/m4_2_p04.txt), [m5_after.json](fix_runs/2026-11-26/m5_perf/m5_after.json) | **`FIXED-VERIFIED`** |
| **`M4-3`:** `MOCKED` covered/cloaked `PrintWindow` ordering passes + `LIVE` `exebox` overlapped `PrintWindow` capture; `Default` desktop `ImageGrab` check `BLOCKED` | `test_m4_p09` `PASSED` (`MOCKED`); `LIVE_EXEBOX_PW method=printwindow center_px=(22, 163, 74)` (`LIVE_PW_EXIT_CODE=0`); `Default` desktop comparison `BLOCKED` | [m4_3_p09.txt](fix_runs/2026-11-26/m4_accuracy/m4_3_p09.txt), [environment.txt](fix_runs/2026-11-26/m0_baseline/environment.txt) | **`FIXED-VERIFIED`** (`MOCKED` + `exebox`) / **`BLOCKED`** (`Default` desktop `ImageGrab`) |

---

## 6. Blocks, Skipped Items, and Limitations

- **`BLOCKED` — Live `Default`-Desktop Covered-Window `ImageGrab` vs `PrintWindow` Verification (`P-09`):**
  Running inside an isolated agent desktop (`ThreadDesktop: exebox-ZZCPDTPBZLIC6SSDOAVVSJYEEB`, [environment.txt](fix_runs/2026-11-26/m0_baseline/environment.txt)) causes `PIL.ImageGrab.grab()` to fail with `OSError: screen grab failed` ([repro_notepad_and_grab.txt](fix_runs/2026-11-26/m0_baseline/repro_notepad_and_grab.txt)). Z-order overlap preference and cloaked-window refusal of `ImageGrab` are verified under `MOCKED` Win32/ImageGrab conditions (`test_m4_p09_capture_desktop_region_occluded_and_cloaked`), and `PrintWindow` background capture of a covered Chrome HWND succeeded `LIVE` in `exebox` ([m4_3_p09.txt](fix_runs/2026-11-26/m4_accuracy/m4_3_p09.txt)). Live side-by-side `ImageGrab` occlusion prevention on an unlocked `WinSta0\Default` desktop remains **`BLOCKED`** here.
- **`SKIPPED` Items (Outside `FIX_PLAN.md` Scope):**
  1. **`P-05`** Targeted `verify_fresh()` vs `execute_action()` RPC speedup (`verify_fresh` stayed `2.31 ms` in M0 baseline).
  2. **`P-11`** Lazy loading `user32` in `desktop_uia.py` / `snapshot.py` for non-Windows imports.
  3. **`P-14`** Enforcing `validate_navigation_url()` inside direct Python `BrowserSession.navigate()` (enforced at MCP `SessionManager` boundary; direct library `BrowserSession` still permits `file://` fixtures in local Python tests).
  4. **`P-15`** Partial negative-coordinate clipping nuance in `resolver.visible()`.
  5. **`P-16`** `blind_gap` canvas action state-diff focus heuristic ambiguity.
  6. **`P-19(a)`** Chromium `--remote-debugging-port` localhost binding auth (local-only loopback socket without external binding).
- **Environment & Fixture Caveats:**
  - `tests/test_mcp_server.py` fixtures (`_server_params()` and `test_err12...`) pass explicit `CUL_MCP_ALLOW_PRIVATE_URLS=1` so localhost `_FixtureHttpServer` integration tests run while keeping default MCP SSRF blocking active.
  - Note from task-2818 root-cause trace: Store Notepad (`Microsoft.WindowsNotepad`) persists accumulated session tabs on abrupt termination and hydrates `DocumentControl` asynchronously after frame creation; both `tests/test_e2e.py` and `tests/test_mcp_server.py` now poll for `textbox` hydration before acting (`2280fcc`). Multi-window contention on a live shared user desktop outside `exebox` remains a known operational boundary.

---

## 7. Disagreements with `AUDIT_REPORT.md`

1. **`P-19(c)` Non-Password Plaintext Persistence (`NOT-REPRODUCED`):**
   `AUDIT_REPORT.md` reported `TaskState` stores plaintext typed input values when `is_password=False`. Direct source inspection of `src/computer_use_lite/state.py` (`record_action` lines 70–74) and M0/M6 live disk checks proved `redact_value()` already redacts **every** `value` passed to `record_action()` regardless of password status (`contains SECRET-CUSTOMER-999 = False`, `value_redacted=True`; [repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt)).
2. **`P-06` End-to-End Significance:**
   While isolated `TaskState.record_action()` improved by `-3.159 ms (-51.76%)` with `0` `os.fsync` calls (`2.944 ms` vs `6.103 ms`), `n=15` `LIVE` uniform before/after measurements proved end-to-end `SessionManager.act()` moved by only `-0.144 ms (-0.62%)` (`23.159 -> 23.015 ms`, `stddev=3.52` / `4.716 ms`) and `mcp_act` moved `-2.017 ms (-9.93%)` (within before `stddev=4.57 ms`, [m5_comparison.txt](fix_runs/2026-11-26/m5_perf/m5_comparison.txt)), confirming end-to-end action latency is dominated by CDP `verify_fresh` + `perform` + `signature()` rather than `fsync`.
3. **M0 Baseline Contention vs Isolated `exebox` Behavior & Doc Check Sums (`P-22`):**
   Earlier pre-audit runs on shared desktops hit Store Notepad contention (`43/44`), whereas clean M0 baseline in fresh `exebox` initially passed `44/44` once ([pytest_full.txt](fix_runs/2026-11-26/m0_baseline/pytest_full.txt)), yet tab accumulation/async UIA hydration later triggered failures (`test_windows_desktop_end_to_end` and `test_mcp_windows_desktop_notepad_flow` on `6a2f0fb` before `2280fcc`), confirming the underlying `P-10` Store Notepad tab/startup race. Separately, M0 verified `P-22`: Step 6 without-skill raw JSON summed `14/16` vs walkthrough `'13/15'`, and `docs/ARCHITECTURE_DECISION.md` §3 held 9 stale benchmark rows vs `results/benchmarks/benchmarks_real.json` ([repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt)).

# Fix Plan & Immutable Pass/Fail Thresholds (`2026-11-26`)

> **Rule:** Every pass/fail threshold below is locked **before** editing any production or test code. Thresholds may not be loosened afterward; if any proves impossible or wrong, work stops and reports rather than editing the threshold.

---

## Git & Test-Fixture Handling Notes (Approved Prior to Edits)
1. **Atomic M0 Baseline Snapshot:** At M0 (`HEAD=8744f98`), `src/computer_use_lite/`, `tests/`, `pyproject.toml`, and `requirements.txt` already held uncommitted Step 2–6 changes. Immediately after committing `FIX_PLAN.md`, those pre-existing M0 source/test files (`src/`, `tests/`, `pyproject.toml`, `requirements.txt` — **never** `results/` or `archive/`) will be committed as one explicit baseline snapshot so each M2–M4 fix commit remains atomic (`one commit per fix`) and cleanly revertible.
2. **Test Loopback Opt-In (`tests/test_mcp_server.py`):** Enforcing private/loopback/link-local refusal by default breaks existing local `_FixtureHttpServer` calls (`http://127.0.0.1:<port>`) in `tests/test_mcp_server.py`. Per approved plan, `_server_params()` and fixture `SessionManager` tests in `tests/test_mcp_server.py` will pass explicit opt-in (`CUL_MCP_ALLOW_PRIVATE_URLS=1`) without relaxing any existing assertions, while dedicated default-env tests verify refusal (`PermissionError`/`PermissionDenied`) when `CUL_MCP_ALLOW_PRIVATE_URLS` is unset.

---

## M0 Reproduction Summary & Scope Decisions
- **`P-19(c)` Persisted `TaskState` Non-Password Plaintext (`NOT-REPRODUCED`):** Direct code inspection ([src/computer_use_lite/state.py:70-74](src/computer_use_lite/state.py#L70-L74)) and M0 execution ([m0_baseline/repro_findings.txt](fix_runs/2026-11-26/m0_baseline/repro_findings.txt)) show `TaskState.record_action()` already pops `value` and replaces it with `redact_value()` (`value_length`, `value_sha256`, `value_redacted=True`) for all typed values regardless of password status. Per contract: **NOT-REPRODUCED — no fix to `state.py` redaction logic** (regression coverage added only).
- **Live Desktop Environment Limit (`exebox-*` Isolation):** Shell commands execute on isolated desktop `exebox-*` (`EnumWindows total=0`, `ImageGrab.grab() -> OSError: screen grab failed`). Covered-window `ImageGrab` pixel-leak tests requiring an unlocked `WinSta0\Default` desktop are marked **BLOCKED** for live verification here (deterministic/mocked ordering tests verify logic without claiming live verification).

---

## Planned Fixes, Thresholds & Measurement Plans

### `M2-1` (`P-03`): Search Input Role Mapping (`searchbox`)
- **Verified Mechanism:** Chromium `AXTree` emits `role="searchbox"` for `<input type="search">`. Because `"searchbox"` is missing from `browser_cdp.ROLES`, `resolver.INTERACTIVE`, `api.ACTIONS`, and `api.inspect_element()`'s `read_value()` check (`== "textbox"`), search boxes degrade to `role="clickable"` (`click` only) and omit `value` in `inspect_element()`.
- **Intended Change:** Add `"searchbox"` to `browser_cdp.ROLES`, `resolver.INTERACTIVE`, `api.ACTIONS["searchbox"] = "click,type"`, and `api.inspect_element()` `role in ("textbox", "searchbox")`.
- **Cheapest Alternative:** Map AX `searchbox` -> `textbox` inside `browser_cdp.py` (~2 LOC).
- **Fixed Pass/Fail Threshold:**
  1. `<input type="search" aria-label="Search site">` line-map output includes `click,type` actionability (`type` supported).
  2. `Api.execute_action(..., "type", "mcp query")` returns `ok=True` and updates input value to `"mcp query"`.
  3. `Api.inspect_element()` returns `info["value"] == "mcp query"` (and `"[REDACTED]"` if marked password-like).
  4. Full `pytest` suite passes with `0` regressions.
- **Measurement:** Unit/integration pytest (`test_audit_fixes.py`) + raw output saved under `fix_runs/2026-11-26/m2_fixes/`.
- **Risk:** Very low; additive role set change.

### `M2-2` (`P-01`): Dense-DOM $O(N^2)$ Occlusion Optimization
- **Verified Mechanism:** `browser_cdp.py:502-504` executes `is_occluded_in_snap(ni, b)` across *all* layout boxes (`5,057` nodes on a `2,500`-cell `<table>`), costing `[810.3, 629.5, 600.6, 584.1, 686.4] ms` total `discover()` (`~295+ ms` local Python CPU) on `5,056` non-interactive `<td>`/`#text` elements.
- **Intended Change:** Defer `is_occluded_in_snap()` in `BrowserSession.discover()` until *after* interactive candidates (`isClickable`, `cursor:pointer`, `AX` roles, non-disabled/non-root/non-viewport-backdrop) are collected, and prune `lay_items` checks using fast coordinate bounds filtering (`ob[0] <= cx <= ob[0]+ob[2]` etc. / spatial bucket or candidate-only loop), preserving exact same-document ancestor and paint-order rules so emitted element sets remain identical to M0.
- **Cheapest Alternative:** Move `is_occluded_in_snap` check to iterate only candidate `ni` nodes (~10 LOC) without changing `lay_items` structure.
- **Fixed Pass/Fail Threshold:**
  1. On synthetic `2,500`-cell `<table>...<button>OK</button>` DOM (`n_cold=2, n_warm=10` repeats), **local Python processing `p50` drops below `30.0 ms`** (`discover()` total `p50` strictly reduced with non-overlapping difference beyond timing variance).
  2. Returned elements on both the `2,500`-cell DOM and `DualOriginCorpusServer` remain **100% identical** (`recall == 1.0`, `precision == 1.0`, identical `(role, name, box, ref)` set vs pre-change `BrowserSession.discover()` snapshot).
- **Measurement:** Benchmark script (`n_cold=2, n_warm=10`) decomposing CDP RPC vs Python CPU time before and after, reporting `p50`, `p95`, and `stddev`.
- **Risk:** Low; verified for exact output parity against M0 corpus snapshot.

### `M2-3` (`P-06`): Skip Unnecessary `os.fsync` on Disposable Temp Session `TaskState`
- **Verified Mechanism:** `TaskState.save()` calls `os.fsync()` (`4.85 ms` `p50` vs `1.65 ms` without `fsync`) on every `record_action()`, even when `_SessionWorker` allocates disposable `task_state.json` inside `tempfile.TemporaryDirectory`.
- **Intended Change:** Add `fsync: bool = True` to `TaskState.__init__()` and `state_fsync: bool = True` to `Api.__init__()`; pass `state_fsync=False` from `_SessionWorker` (preserving `fsync=True` default everywhere else and preserving atomic `mkstemp` + `os.replace` writes).
- **Cheapest Alternative:** Auto-skip `fsync` whenever `path` is inside `tempfile.gettempdir()` (rejected: would alter durability for tests intentionally verifying `tmp_path` persistence).
- **Fixed Pass/Fail Threshold:**
  1. Disposable `TaskState(path, fsync=False)` / MCP `_SessionWorker` triggers **`0` calls to `os.fsync`** across `record_action()`, still writes valid JSON with monotonic revision and `0` leftover `*.tmp` files.
  2. Default `TaskState(path)` (`fsync=True`) still triggers **`1` `os.fsync` call per `save()`**.
  3. Over `n_warm=10` repeats (`n_cold=2`), `record_action()` `p50` with `fsync=False` is lower than `fsync=True` (`<= 60%` of `fsync=True` `p50`, outside `stddev` noise).
- **Measurement:** Unit spy test + M5 `10`-repeat timing JSON.
- **Risk:** Low; durable default unchanged for non-temporary persistent paths.

### `M2-4` (`P-19(b)`): Private, Loopback & Link-Local Navigation Guard + Opt-In
- **Verified Mechanism:** `validate_navigation_url()` only checks `http`/`https` schemes, allowing `http://127.0.0.1:9222/json`, `http://localhost:8000/`, `http://169.254.169.254/latest/meta-data/`, `http://10.0.0.1/`, `http://[::1]:8080/`.
- **Intended Change:** Refuse loopback (`localhost`, `*.localhost`, `127.0.0.0/8`, `::1`, IPv4-mapped `::ffff:127.0.0.1`), private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`), link-local (`169.254.0.0/16`, `fe80::/10`, `metadata.google.internal`, `*.local`), unspecified (`0.0.0.0`, `::`), and resolved private/loopback/link-local targets unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` is explicitly set (catching `socket.gaierror` cleanly so offline FQDN syntax validation still works on public domains). Update ONLY fixture env setup in `tests/test_mcp_server.py` (per approved A1 resolution) so existing local HTTP fixture tests pass `CUL_MCP_ALLOW_PRIVATE_URLS=1`, while running dedicated default-env tests confirming refusal (`PermissionError`/`PermissionDenied`).
- **Cheapest Alternative:** Check host string/literal IP ranges only (without best-effort `socket.getaddrinfo` private-IP check).
- **Fixed Pass/Fail Threshold:**
  1. When `CUL_MCP_ALLOW_PRIVATE_URLS` is unset: `http://127.0.0.1:9222/`, `http://localhost/`, `http://169.254.169.254/`, `http://10.0.0.1/`, `http://172.16.0.1/`, `http://192.168.1.1/`, `http://[::1]/`, `http://[::ffff:127.0.0.1]/`, `http://0.0.0.0/` all raise `PermissionError` (and MCP `open_browser`/`navigate` return `isError=True`, `error_type="PermissionDenied"`).
  2. Public URL `https://example.com/` passes validation cleanly.
  3. When `CUL_MCP_ALLOW_PRIVATE_URLS=1` is set: `http://127.0.0.1:<port>/` is permitted.
  4. Persisted `TaskState` on non-password fields continues storing `0` plaintext user input values (`value_redacted=True`).
- **Measurement:** Unit + live MCP stdio refusal tests saved to `fix_runs/2026-11-26/`.
- **Risk:** Low; public browsing unaffected, SSRF attack surface closed by default.

---

### `M3` (`P-10`): Test Reliability, Store Notepad Tab Tolerance, Process Cleanup & Tracked File Protection
- **Verified Mechanism:**
  1. `test_e2e.py:108` and `test_mcp_server.py:459` rely solely on `after - before` HWND diffs; Win11 Store Notepad opens files in a tab of an existing window (`new_hwnds = set()`), timing out after `15.0s`.
  2. `proc.terminate()` terminates only the `AppExecutionAlias` stub PID (`12432`), leaking child `WindowsApps\...\Notepad.exe` processes (`11260` etc.).
  3. `tests/test_e2e.py:380-383` unconditionally overwrites tracked `results/e2e/e2e_results.json`.
  4. All `8` tests in `tests/test_e2e.py` return `True`, emitting `8` `PytestReturnNotNoneWarning` warnings.
- **Intended Change:**
  - Wait for either a newly created `Notepad` HWND **or** an existing `Notepad` HWND whose title matches `tmp.stem`;
  - Record pre-test `Notepad.exe` PIDs, and in `finally:` cleanly close/terminate only any newly created test window (via `Ctrl+W` if reusing a pre-existing HWND, or `WM_CLOSE` + `taskkill`/process termination of owning PID if test spawned a new HWND/process) so `0` `Notepad.exe` processes leak;
  - Write `test_e2e.py` JSON output to a temporary/non-tracked path by default (`--write-results <path>` optional);
  - Remove `return True` from `test_e2e.py` test functions (preserving every `record(...)` & `assert` unmodified).
- **Cheapest Alternative:** Same helper shared cleanly in tests without altering assertions.
- **Fixed Pass/Fail Threshold:**
  1. **`5` consecutive full runs** of `python -m pytest tests -v -rs --tb=short` + `python tests/test_e2e.py`: **`0` failures**, **`0` pytest warnings**, **`0` newly leaked processes** (`Notepad.exe`, `chrome.exe`, `python` MCP workers) compared to pre-run snapshot.
  2. **`0` tracked files under `results/` or `archive/` modified or overwritten** (`git diff results/` identical before vs after all `5` runs).
- **Measurement:** Automated `5`-run harness script recording stdout, exit code, PID deltas, and `git diff results/` per run to `fix_runs/2026-11-26/m3_reliability/`.
- **Risk:** Low; desktop test inside `exebox` exercises isolated `exebox` Store Notepad (user-desktop multi-window conflict outside `exebox` remains documented).

---

### `M4-1` (`P-02`): Cheaper Cross-Origin OOPIF Discovery Coverage
- **Verified Mechanism:** `Accessibility.getFullAXTree` queries only the main renderer target (`Cross Origin Save` `<button>` omitted -> `recall=0.9412`), whereas `DOMSnapshot.captureSnapshot` already returns child frame documents (`docs[1..]`) with node tags/attributes and frame-offset bounds (`OOPIF Email` appeared as `isClickable`).
- **Intended Change:** Inside `BrowserSession.discover()` when `d_idx > 0` (`docs[1..]`) and a node's `backendNodeId` was omitted from `AXTree`, map standard interactive HTML tags (`button`, `a[href]`, `select`, `textarea`, `input` by `type`) and explicit `role` / `onclick` / `tabindex` nodes directly from `DOMSnapshot` attributes/text (without spawning extra CDP OOPIF sessions unless threshold fails).
- **Cheapest Alternative:** This *is* the audit's cheaper option (~30 LOC in `browser_cdp.py`, `0` extra CDP RTTs). Escalate to multiplexed `Target.setAutoAttach(flatten=True)` only if cheaper option fails threshold.
- **Fixed Pass/Fail Threshold:**
  1. On `DualOriginCorpusServer` (`corpus_main.html`): `cross_origin_iframe` failure count drops **`1 -> 0`**.
  2. `"Cross Origin Save"` is discovered with `role == "button"` and `"OOPIF Email"` has `role == "textbox"`.
  3. Overall `corpus_main` **`recall == 1.0000` (`17/17`)** (`>= 1.0`, strictly higher than M0 `0.9412`).
- **Measurement:** `compare_elements()` on `DualOriginCorpusServer` before vs after (`M4` + `M5`).
- **Risk:** Low; affects `docs[d_idx]` (`d_idx > 0`) fallback only when `bid` absent from `AXTree`.

### `M4-2` (`P-04`): Duplicate, `<label>`, and Scroll-Clipped False-Positive Removal
- **Verified Mechanism:** `DualOriginCorpusServer` `prec` is `0.8421` (`Api`/viewport-filtered) and `0.80` (`raw_discover`) due to: (1) `<label for="query_input">Search SKU</label>` marked `isClickable` alongside `textbox` `Search SKU`, (2) `cursor:pointer` child `#text` inside `div[onclick]` (`Custom Div Action`) not pruned by `_prune_nested_clickables()`, and (3) `Scroll Inner Hidden` (`y=336`) clipped below its `90 px` `overflow-y:auto` `.scroll-box` ancestor.
- **Intended Change:**
  1. Exclude `<label for="...">` from emitting a separate `clickable` element when its referenced `id` corresponds to an active discovered control in the same document;
  2. Include `"clickable"` non-native container ancestors inside `_prune_nested_clickables()` when collapsing redundant matching/blank inner fragments;
  3. Request `overflow-x` / `overflow-y` in `DOMSnapshot` `computedStyles` and skip descendants whose midpoints fall outside an ancestor clipping rect (`hidden`/`auto`/`scroll`/`clip`).
- **Cheapest Alternative:** Prune `<label for>` + `"clickable"` children (handles 2/3 viewport FPs) without `overflow` ancestor clipping (`prec = 0.8947`, which fails `>= 0.95`! Therefore `overflow` scroll clipping IS required to hit `>= 0.95`).
- **Fixed Pass/Fail Threshold:**
  1. On `DualOriginCorpusServer` (`corpus_main.html`), `Api.discover_interactables()` and viewport-filtered `BrowserSession.discover()` achieve **`precision >= 0.95`** (target `1.0000`, `<= 0` FPs from `<label>`, duplicate `div[onclick]`, or `Scroll Inner Hidden`) while keeping **`recall == 1.0000`** (`>= 0.9412` never lower).
  2. Hidden-input `<label for>` toggle regression test confirms label clicks remain discoverable when the `<input>` itself is zero-sized / visually hidden.
- **Measurement:** `compare_elements()` on `DualOriginCorpusServer` + custom `sr-only` `<label>` test + real-site smoke check.
- **Risk:** Medium-low; validate `overflow` ancestor walk does not clip valid elements on normal/complex sites (`DOMSnapshot` `styles` adds 2 tiny interned strings).

### `M4-3` (`P-09`): Window-Capture Ordering (`PrintWindow` vs `ImageGrab` / Cloaked Check)
- **Verified Mechanism:** `blind_gap.capture_desktop_region(box, hwnd=None)` executes `ImageGrab.grab(bbox=..., all_screens=True)` unconditionally first, only falling back to `_capture_hwnd_printwindow(hwnd, bbox)` on exception. When another window covers `hwnd` on `Default` desktop (or when `hwnd` is cloaked by DWM), `ImageGrab` returns wrong foreground pixels.
- **Intended Change:** When `hwnd is not None` (Win32): query `DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED=14)` and `IsIconic(hwnd)` — if cloaked or minimized, attempt `_capture_hwnd_printwindow` or raise/flag cleanly without screen-grabbing another app; check `GetForegroundWindow() != hwnd` or Z-order upper-window rect overlap (`GW_HWNDPREV` on visible non-cloaked windows intersecting `bbox`) and call `_capture_hwnd_printwindow(hwnd, bbox)` **first** whenever covered/non-foreground (falling back to `ImageGrab` only if `PrintWindow` fails and window is uncloaked & foreground).
- **Cheapest Alternative:** Call `_capture_hwnd_printwindow` whenever `hwnd is not None and GetForegroundWindow() != hwnd`.
- **Fixed Pass/Fail Threshold:**
  1. **`MOCKED` check:** Given a simulated non-foreground/occluded `hwnd` (`GetForegroundWindow != hwnd` and/or upper overlapping window in Z-order) and `ImageGrab.grab` returning red `(255, 0, 0)` covering pixels, `capture_desktop_region(..., hwnd=target)` **calls `_capture_hwnd_printwindow` first, never returns `(255, 0, 0)` covering pixels**, and succeeds with `"printwindow"` method; cloaked `hwnd` refuses `ImageGrab` screen grab fallback.
  2. **`LIVE` check (`exebox` caveat):** Verify real `_capture_hwnd_printwindow` capture on a real overlapped window in `exebox`; mark live `Default`-desktop `ImageGrab`-vs-`PrintWindow` comparison **`BLOCKED` by `exebox` desktop isolation** unless run on `Default` desktop.
- **Measurement:** Mocked unit test + live `PrintWindow` pixel check in `exebox`.
- **Risk:** Low; preserves `test_printwindow_fallback_in_blind_gap` mock behavior when `ImageGrab` fails.

---

## M6 Documentation Corrections Scope
- Correct claims **only** where raw audit/fix evidence proved existing `README.md` or `docs/ARCHITECTURE_DECISION.md` wrong or stale (e.g., Gate 0 contradictory `"BLOCKED IN exebox"` wording, §3 mismatched table vs `benchmarks_real.json`, known search/OOPIF/desktop limits). Leave `archive/` and tracked `results/` files untouched; record fresh outputs in `FIX_REPORT.md` & `fix_runs/2026-11-26/`.

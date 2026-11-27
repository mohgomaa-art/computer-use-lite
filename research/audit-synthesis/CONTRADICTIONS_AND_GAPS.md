# Contradictions, Discrepancies, and Open Gaps Log

1. **Linux Import Crash vs Windows Suite Pass (`CUL-DX-001`):**
   - *Linux sandbox (`0d19a9e`):* Reported `6` pytest collection errors because importing `computer_use_lite` invoked Win32 `WinDLL`/`WINFUNCTYPE`/`comtypes` at module import time.
   - *Windows 11 (`0d19a9e` / `de27b49`):* Passed `70/70` interactive tests (`58/58` with `CUL_SKIP_DESKTOP=1`) because Win32 DLLs exist locally.
   - *Reconciliation:* Both reports were accurate for their respective platforms! Non-Windows compatibility requires lazy Win32 imports (`P2`).
2. **Duplicate `src/engine/` Claim (`CUL-REF-001`):**
   - *Attack PDF / Linux report:* Claimed `src/engine/` held an outdated duplicate codebase (`A19`, `C42`).
   - *Inspection (`0d19a9e` & `de27b49`):* **REFUTED** — every file under `src/engine/*.py` is a `16`-line `importlib` shim forwarding directly to `computer_use_lite.*`.
3. **Desktop Task Count Claim (`CUL-REF-002`):**
   - *Attack PDF (`C19`):* Stated `d01-d08` was `20/20`.
   - *Inspection (`benchmarks/agent_tasks.py:237-260`):* **REFUTED** — desktop benchmark catalog contains `8` tasks (`d01`–`d08`).
4. **Symbol Name Mismatches Corrected by Merged Audit (`audit_2026-11-27`):**
   - Prior prose used wrong/paraphrased identifiers (`hover.py:19` -> actual `:22,28`; `CAP_MAP_LINE_DEFAULT` -> `DEFAULT_LINE_MAP_CAP`; `_JS_PROBE_NODE` -> `_NODE_PROBE_JS`; `WM_GETOBJECT` claim -> `_pulse_screenreader`).
5. **`DIALOG_ALERT:` Scope (`CUL-SEC-005`):**
   - *Prior claim:* Implied browser `alert()` prompts mapped through `DIALOG_ALERT:`.
   - *Code reality (`api.py:81-98` + `desktop_uia.py`):* `DIALOG_ALERT:` surfaces Win32 `#32770` static alert text (`<=240x8`), while both browser DOM names and desktop dialog strings still lack explicit `[UNTRUSTED]` boundary delimiters.
6. **Cursor Reference Patch Gaps (`cursor-audit-fix.patch.txt` vs Spec):**
   - Patch still mutates `self._state["cursor_id"] = "progress"` synchronously in `desktop_cursor_overlay.py:set_busy`, violating Fix A's `>=350ms` delay on Windows desktop!
   - Patch only checks `window[Symbol.for('cul.agent.cursor')]` in JS instead of registering once via `Page.addScriptToEvaluateOnNewDocument` + ID caching per session (Fix F).
   - Patch does NOT include Section 3 (`GetCursorInfo` probe), Section 4 (critically damped spring / reduced motion / morph / single-rAF perf), or Section 5 (`CUL_TAKEOVER_GLOW=1`).
7. **Environment Gaps Carrying Forward:**
   - **Native `@oai/sky`:** Not installed as standalone CLI/MCP in this execution environment (`NOT_RUN` in Track B).
   - **`exebox` vs `WinSta0\Default`:** Isolated `exebox` denies `GetForegroundWindow()` / `GetCursorPos()` (error 5); Win32 low-level hook / `GetCursorInfo` checks require real unlocked desktop execution or explicit `NOT VERIFIED` marking.

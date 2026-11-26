# Known Limitations & Open Boundaries (`v0.1.0-alpha`)

This document inventories every verified functional gap, platform assumption, experimental non-reproducibility boundary, and open security limitation in **Computer Use Lite `v0.1.0-alpha`**.

---

## 1. Browser Engine Limitations (`browser_cdp.py`, `resolver.py`, `hover.py`)

1. **Cross-Origin Iframe (`OOPIF`) Blindness Under Strict Site Isolation (`[MEASURED]` / `[REPORTED]`):**  
   `BrowserSession` queries top-session `DOMSnapshot.captureSnapshot` and `Accessibility.getFullAXTree` without recursively attaching out-of-process iframe (`OOPIF`) CDP sessions (`Target.setAutoAttach`). While the local `DualOriginCorpusServer` fixture reached `recall=1.0` without explicit `--site-per-process` process isolation, live tests on strict cross-origin embeds (`youtube.com/embed`) returned `0` inner elements and `BLIND_REGIONS:0`.
2. **No Multi-Tab / `target="_blank"` Switching (`[REPORTED]` / `[VERIFIED-CODE]`):**  
   `BrowserSession` binds to a single `page` / `DirectCdpClient` WebSocket target. Clicking links or buttons that open popups or new tabs leaves the session inspecting the opener tab (`navigate` supports `goto`/`back` only).
3. **Partial Sticky-Header & Negative-Coordinate Clipping Nuance (`[VERIFIED-CODE]`):**  
   `resolver.visible()` treats any rectangle with `r[2] > 0`, `r[3] > 0`, and `r[1] + r[3] > 0` within `[0, vh)` as visible; controls partially scrolled above the top edge (`r[1] < 0`) or under non-topmost sticky headers require manual inspection of scroll position.
4. **Hover Timing Fragility:**  
   CSS `:hover` menus (`hover(wait_ms=350)`) rely on fixed dwell timing and cursor persistence; fast transitions or mouse-move resets between `hover()` and subsequent `act()` can collapse transient dropdowns.
5. **`verified=true` != Downstream Task Completion (`[VERIFIED-CODE]` / `[REPORTED]`):**  
   `Api.execute_action()` verifies pre-action identity/visibility (`> 2` px drift, disabled, modal occlusion) and dispatch success. It does **not** guarantee semantic mutation (e.g., `<input readonly>` accepts focus/dispatch silently, and JavaScript frameworks may swallow synthetic events).

---

## 2. Platform & Windows Desktop UIA Limitations (`desktop_uia.py`, `blind_gap.py`)

1. **Windows-Only Top-Level Import Coupling (`[VERIFIED-CODE]`):**  
   `desktop_uia.py` and `snapshot.py` execute `ctypes.WinDLL("user32", use_last_error=True)` at module import time, breaking `import computer_use_lite` on Linux and macOS even for browser-only workloads.
2. **Windows `#32770` Save As Dialog UIA Desync (`[REPORTED]`):**  
   In native Win32 Common Item `Save As` (`#32770`) dialogs, `IValueProvider::SetValue` on the filename edit control can populate visible text without committing internal `IFileSaveDialog` filename state, requiring keyboard/Enter confirmation or verifying resulting disk files independently (`not verified safe by tool output alone`).
3. **Win11 Store Notepad Async Hydration & Tab Persistence (`[VERIFIED-CODE]`):**  
   Modern Win11 `Microsoft.WindowsNotepad` hydrates its `DocumentControl` asynchronously after HWND creation and restores prior open tabs across abrupt process kills (`tests/` explicitly poll for `textbox` readiness before typing).
4. **`PrintWindow` Right-to-Left (`WS_EX_LAYOUTRTL`) Mirroring (`[REPORTED]`):**  
   Live captures on Store Notepad Windows with extended layout flag `0x400110` (`WS_EX_LAYOUTRTL`) exhibited horizontal mirroring inside `PrintWindow` bitmaps, whereas Win32 Calculator did not mirror; DWM-cloaked/WinUI3 Mica surfaces can also yield dark/black backing layers under `PrintWindow`.
5. **Covered-Window Live `ImageGrab` vs. `PrintWindow` Verification Gap (`[BLOCKED]`):**  
   While mocked unit tests (`test_audit_fixes.py::test_m4_p09_*`) verify `PrintWindow` priority when `hwnd` is covered, minimized, or cloaked, live cross-window overlapping `ImageGrab`-vs-`PrintWindow` visual diffs could not run automatically inside headless/isolated `exebox` test desktops (`[BLOCKED]`).
6. **`KillSwitch` Initialization Fail-Open Nuance (`[VERIFIED-CODE]`):**  
   `desktop_uia.move_mouse()` ignores an `OSError` from the first `GetCursorPos()` baseline sample (`try ... except OSError: pass`), allowing physical mouse injection to proceed unguarded if cursor-position polling fails at start.
7. **UIA `RemoteOperations` Subtree Limitation (`[MEASURED]` `Exp 5`):**  
   UIA `CoreAutomationRemoteOperation::Navigate` stops at child HWND / cross-process boundaries (`recall=0.0179` on Notepad, `0.0286` on Chrome), preventing single-operation remote subtree replacement of `FindAllBuildCache`.

---

## 3. Security Boundaries (`OPEN` in `v0.1.0-alpha`)

All security probes were verified on `HEAD` (`sec_probes.json` / [SECURITY.md](../SECURITY.md)):

1. **SSRF Via HTTP `302` Redirects (`[MEASURED]` `OPEN`):**  
   `validate_navigation_url()` only inspects the URL string passed into `open_browser()` or `navigate()`. If an external public origin passes validation and replies with `HTTP 302 Location: http://127.0.0.1:<port>/...`, Chromium follows the redirect directly without re-checking private/loopback rules.
2. **DNS-Rebinding TOCTOU (`[VERIFIED-CODE]` `OPEN`):**  
   Python's `socket.getaddrinfo()` check occurs before Playwright/Chromium opens TCP connections independently, leaving a time-of-check-to-time-of-use DNS-rebinding window. Additionally, offline `socket.gaierror` / NXDOMAIN lookups do not block navigation.
3. **Unauthenticated Local CDP Port (`[MEASURED]` `OPEN`):**  
   When Chrome runs with `--remote-debugging-port=<free_port>`, `http://127.0.0.1:<port>/json/version` serves WebSocket debugger URLs without auth, and same-machine processes sending WebSocket upgrades **without** an `Origin` header can execute `Runtime.evaluate`. *(Browser-tab CSWSH requests carrying `Origin: https://evil.example` or `http://127.0.0.1` ARE rejected with `HTTP 403` by Chromium `1.64`.)*
4. **Direct Python API Bypass (`[VERIFIED-CODE]`):**  
   SSRF host refusal (`validate_navigation_url`) lives inside MCP `SessionManager`, not raw Python `BrowserSession(url=...)` / `BrowserSession.navigate()`, so local fixtures (`file://`, `127.0.0.1`) work directly in Python scripts/tests.

---

## 4. Benchmark & Coverage Gaps

1. **Zero Live LLM Calls on 20-Task Agent Benchmark (`[MEASURED]`):**  
   [`results/agent_benchmark/harness_validation.json`](../results/agent_benchmark/harness_validation.json) validated fixture oracles (`20/20`), not real OpenAI/Gemini/Ollama VLM agent loops.
2. **Untested Multi-Session Saturation Ceiling:**  
   `MAX_SESSIONS` concurrency degradation and long-running leak stability beyond 2 concurrent sessions remain unmeasured live.
3. **Proxy Token Metric (`len / 4` & `1,229` Baseline):**  
   Character-divided token estimates differ from exact model BPE tokenizers and model-specific vision tile/patch pricing.

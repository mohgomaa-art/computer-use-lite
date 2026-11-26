# Live Task Execution Plan (`2026-11-26`)

> **Rules:** Every task runs visibly (`headless=False` for all browser sessions). Maximum **3** attempts per task. Pass/fail criteria below are locked prior to M2 execution and require independent verification outside `verified=true`.

## M0 Preflight Record
- **Git HEAD:** `efa0ff7bd677c8343bd9a0962ff4089d4c958537` (`docs(m6): add audit verification and fix report FIX_REPORT.md`)
- **Pre-existing dirty tracked paths:** `benchmarks/*`, `results/benchmarks/*`, `results/e2e/e2e_results.json`
- **OS / Python / Locale:** `Windows-11-10.0.26200-SP0`, Python `3.12.10`, `locale=('Arabic_Egypt', '1252')`, `preferredencoding=utf-8`
- **Library versions:** `comtypes 1.5.0`, `websockets 17.2`, `PIL 12.3.0`, `pytest 9.1.1`, `psutil 7.2.2` (`playwright`, `mcp`, `anyio` checked via `m0_env.json`)
- **Desktops:** Shell `ThreadDesktop=exebox-REOZNBROE35WILPHWIY6NXNXUA`, `InputDesktop=Default`, `PrimaryScreen=1920x1080`, `VirtualScreen=[-1080, -720, 3000, 1920]`
- **MCP Visible Browser Check:** Passed (`open_browser("https://example.com/", headless=False)` opened `hwnd=12191112`, `chrome.exe`, `box=[17, 10, 1282, 801]`, viewed in [m0_visible_browser.png](live_runs/2026-11-26/evidence/m0_visible_browser.png) and [m0_screen_grab.png](live_runs/2026-11-26/evidence/m0_screen_grab.png); closed cleanly via `close_session`).
- **Pre-existing MCP sessions / desktop windows:** `0` MCP sessions; `14` desktop windows saved in [m0_baseline_windows.json](live_runs/2026-11-26/evidence/m0_baseline_windows.json).
- **MCP tools under test:** `open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`.
- **Evidence & Scratch Folder:** `live_runs/2026-11-26/evidence/` and `live_runs/2026-11-26/scratch/`.

---

## Planned Tasks (`T01`–`T18`, `max_attempts = 3` per task)

### Browser Tasks (`T01`–`T13`, all `headless=False`)

1. **`T01` — Form Validation, Dynamic Fields & Confirmation**
   - **Target:** `https://practice.expandtesting.com/form-validation` then `https://practice.expandtesting.com/dynamic-controls`
   - **Goal:** Submit `/form-validation` with invalid input (`"invalid-phone"`) to trigger client-side validation feedback, then enter valid fake fields (`"Test User"`, `"012-3456789"`, `"2026-12-01"`, payment option) and submit to confirmation; navigate to `/dynamic-controls`, click `"Enable"`, discover dynamically enabled textbox, and type `"CUL-DYNAMIC-OK"`.
   - **Success Criterion:** Invalid submit stays off confirmation URL/page and displays validation state; valid submit reaches confirmation text (`Thank you for validating your ticket` or confirmation page); dynamically enabled input accepts `"CUL-DYNAMIC-OK"`.
   - **Independent Verification:** `inspect` textbox value (`"CUL-DYNAMIC-OK"`) + `discover` URL/elements + OS screenshot viewed via `read_file`.

2. **`T02` — Autocomplete / Filtered Combobox**
   - **Target:** `https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-list/`
   - **Goal:** Type `"Ca"` into the `"State"` combobox, discover filtered listbox options, select `"California"`, verify popup collapses and `"California"` persists.
   - **Success Criterion:** `inspect` on the `"State"` combobox returns `"California"`.
   - **Independent Verification:** Separate `inspect` call + OS screenshot viewed via `read_file`.

3. **`T03` — Infinite Scroll / Lazy-Loaded Content**
   - **Target:** `https://the-internet.herokuapp.com/infinite_scroll`
   - **Goal:** Run repeated `scroll(dy=900)` actions until additional lazy-loaded `.jscroll-added` paragraphs load below initial fold.
   - **Success Criterion:** Page scrolls down and reveals dynamically appended paragraph chunks beyond initial render without error; record whether `discover()` reflects new content/elements.
   - **Independent Verification:** Before/after OS screenshots comparing scrollbar position & visible newly appended text + raw MCP outputs.

4. **`T04` — Same-Origin & Cross-Origin Iframes**
   - **Target:** `https://practice.expandtesting.com/iframe`
   - **Goal:** Discover and act inside BOTH the same-origin subscribe iframe (`/iframe-email-subscribe`, typing `"fake-tester@example.invalid"` and clicking Subscribe) and inspect/interact with a control inside the cross-origin YouTube OOPIF iframe (`youtube.com/embed/...`).
   - **Success Criterion:** Same-origin iframe shows subscribed state AND cross-origin YouTube iframe control is discovered and acted on cleanly.
   - **Independent Verification:** Post-action `discover`/`inspect` + OS screenshot showing subscribed banner and YouTube iframe state.

5. **`T05` — Shadow DOM (Open & Nested)**
   - **Target:** `https://testautomationpractice.blogspot.com/` *(note: no reachable public closed-Shadow-DOM interactive page found in M0 probe; tests nested open Shadow DOM + explicitly records closed Shadow DOM gap)*
   - **Goal:** Discover controls inside `#shadow_host` (`<input type="text">`, `<input type="checkbox">`, `<a href="...">`), type `"Shadow-Live-1"` into the shadow text input and toggle the shadow checkbox.
   - **Success Criterion:** Both shadow text value `"Shadow-Live-1"` and checked checkbox state hold after action.
   - **Independent Verification:** `inspect` shadow text input (`value == "Shadow-Live-1"`) + OS screenshot showing checked box & typed text.

6. **`T06` — Slider & Drag-and-Drop**
   - **Target:** `https://the-internet.herokuapp.com/horizontal_slider` and `https://bonigarcia.dev/selenium-webdriver-java/drag-and-drop.html`
   - **Goal:** Move the horizontal slider away from `0` using `click_at` / keyboard (`ArrowRight`) to `>= 3.0`; test dragging `#draggable` onto `#target` on the drag-and-drop page using available MCP primitives (`click_at` / mouse actions).
   - **Success Criterion:** Slider reads `>= 3.0`, and drag-and-drop moves draggable box into target (note explicitly if MCP lacks pointer-drag primitives).
   - **Independent Verification:** OS screenshot + `discover`/`inspect` element boxes/text.

7. **`T07` — Interactive `<canvas>` via Blind-Region Crop & Coordinate Click**
   - **Target:** `https://jspaint.app/`
   - **Goal:** Open `jspaint.app`, confirm `discover()` detects an opaque `<canvas>` blind region and returns inline crop PNG, inspect the crop image visually, select pencil/brush/color or draw inside the canvas using `click_at` inside the crop bounds.
   - **Success Criterion:** `discover()` emits `blind_region` crop image; multiple `click_at` strokes draw visible marks onto the `<canvas>`.
   - **Independent Verification:** Before vs after OS screenshots inspected visually via `read_file`.

8. **`T08` — New Tab / Popup Window Switching**
   - **Target:** `https://the-internet.herokuapp.com/windows`
   - **Goal:** Click `"Click Here"` to open `"New Window"`, verify whether MCP discovers/switches to the new window or stays pinned on opener tab, interact with or inspect `"New Window"`, and return to `"The Internet"`.
   - **Success Criterion:** Popup `"New Window"` opens and can be targeted/inspected cleanly and execution returns to opener tab (`FAIL` if engine lacks tab switching).
   - **Independent Verification:** OS `list_desktop_windows` / OS screenshot + MCP `discover()` & `list_sessions()`.

9. **`T09` — Hover-Only Reveal Menu**
   - **Target:** `https://the-internet.herokuapp.com/hovers`
   - **Goal:** Verify `"View profile"` is hidden initially, call `hover()` on avatar #1, verify `View profile` appears in hover delta, click it, and verify arrival at `/users/1`.
   - **Success Criterion:** Browser navigates to `/users/1` (`title`/`URL` change).
   - **Independent Verification:** `discover`/`list_sessions` URL check + OS screenshot of `/users/1`.

10. **`T10` — Sortable & Paginated Table**
    - **Target:** `https://datatables.net/examples/data_sources/dom.html`
    - **Goal:** Sort a DataTables column (`Age` or `Office`), paginate to Page `2` (`"2"` or `"Next"`), filter search `"Tokyo"`, and verify matching filtered row `"Tokyo"` appears.
    - **Success Criterion:** Search/sort/pagination updates table rows and displays filtered `"Tokyo"` entries.
    - **Independent Verification:** Separate `discover` + OS screenshot opened and visually verified.

11. **`T11` — Right-to-Left (Arabic) Localized Control**
    - **Target:** `https://ar.wikipedia.org/wiki/%D8%A7%D9%84%D8%B5%D9%81%D8%AD%D8%A9_%D8%A7%D9%84%D8%B1%D8%A6%D9%8A%D8%B3%D9%8A%D8%A9`
    - **Goal:** Locate search input using Arabic label (`filter_query="ابحث"`), type `"القاهرة"`, submit search via `Enter` or `"بحث"` button, and open the `"القاهرة"` article.
    - **Success Criterion:** Browser navigates to Arabic `"القاهرة"` Wikipedia article.
    - **Independent Verification:** `list_desktop_windows` title containing `"القاهرة"` + OS screenshot opened & viewed.

12. **`T12` — Very Large DOM & Dense Real-World SPA Audit**
    - **Target:** `https://github.com/trending` and `https://www.youtube.com/`
    - **Goal:** Run `discover()` at default cap (`60`) and `max_elements=200`, record latency, token estimate, total count, and truncation delta, and compare OS screenshots vs returned `line_map` items.
    - **Success Criterion:** Both pages load visibly (`headless=False`), `discover()` returns structured `REV:N` output without crash, and omitted/truncated visible controls are documented from visual comparison.
    - **Independent Verification:** OS screenshots (`read_file`) vs raw `discover()` text outputs saved in `evidence/`.

13. **`T13` — Element Covered by Sticky Header / Overlay**
    - **Target:** `https://practice.expandtesting.com/`
    - **Goal:** Scroll down so a page link/button sits near the top under the fixed top navigation bar (`y < 60`) or modal/ad overlay, check whether `discover()` accurately hides covered elements or allows acting on visible controls without clicking the covering sticky navbar by mistake.
    - **Success Criterion:** Engine either marks covered control occluded / excludes it or clicks the intended scrolled control rather than misfiring on the sticky header.
    - **Independent Verification:** `discover` bounds + post-click URL/output + OS screenshot viewed via `read_file`.

---

### Desktop & Cross-App Tasks (`T14`–`T16`, visible interactive desktop windows — user opens Calculator & Notepad)

14. **`T14` — Windows Calculator Multi-Op & Mode Switch**
    - **Target:** Visible Windows Calculator (`ApplicationFrameWindow`, `"Calculator"` / `"الحاسبة"`, user-opened)
    - **Goal:** Attach `open_desktop`, compute `(125 + 375) * 4 =` (`2000`) via UIA button clicks, verify display `2000`, then open Navigation menu and switch mode from `Standard` to `Scientific`.
    - **Success Criterion:** Calculator result displays `2000` (`2,000` / locale formatted) and switches to `Scientific` showing scientific keypad buttons (`x^2`, `sin`, etc.).
    - **Independent Verification:** `inspect` / `discover` UIA read-back + OS `PrintWindow` screenshot viewed via `read_file`.

15. **`T15` — Store Notepad Typing, Native Save As Dialog & Byte-for-Byte Verification + Native File Open Dialog**
    - **Target:** Visible Windows 11 Store Notepad (`class="Notepad"`, user-opened) + scratch file `live_runs/2026-11-26/scratch/notepad_live_test.txt` + `<input type="file">` / Notepad Open dialog (`live_runs/2026-11-26/scratch/open_dialog_target.txt`)
    - **Goal:** Type `"CUL-LIVE-2026 | Cairo: القاهرة"` into Notepad editor via UIA `act()`, open native Windows `Save As` (`Ctrl+Shift+S`), drive native Save As dialog UIA controls (`File name` box + `Save` button) to write `notepad_live_test.txt`; also trigger native Windows `Open` dialog (`Ctrl+O` or Chrome `<input type="file">`) to select `open_dialog_target.txt` and verify loaded text.
    - **Success Criterion:** `notepad_live_test.txt` exists on disk matching typed UTF-8 bytes (`"CUL-LIVE-2026 | Cairo: القاهرة"`), and `open_dialog_target.txt` opens cleanly via native Windows Open dialog.
    - **Independent Verification:** Python disk read (`Path(...).read_bytes()`) in `run_command` + OS screenshot viewed via `read_file`.

16. **`T16` — Cross-App Copy (Browser -> Notepad) & Low-UIA Desktop Blind-Region Fallback**
    - **Target:** Visible Browser (`https://example.com/`) + Visible Store Notepad + Low-UIA desktop surface (visible Chrome canvas window `jspaint.app` attached via `open_desktop(hwnd=...)` or sparse UIA Paint/Chrome client)
    - **Goal:** Read heading/text from visible `https://example.com/` via browser `inspect`/UI, transfer the exact string into Notepad via `desktop` `act()`, confirm Notepad matches; separately attach `open_desktop` to a window exposing `< 6` UIA controls (or inspect how `open_desktop` behaves on Chrome canvas/non-UIA window) to test `low_uia` blind-region crop & `click_at`.
    - **Success Criterion:** Notepad editor holds exact browser-derived string, and `open_desktop` blind-region fallback (`low_uia` or documented limitation if Chrome UIA exposes `>= 6` chrome controls) is observed cleanly.
    - **Independent Verification:** Python/OS Notepad Save or UIA `inspect` + OS `PrintWindow` PNG viewed via `read_file`.

---

### Robustness & Isolation Tasks (`T17`–`T18`)

17. **`T17` — Stale Element Refusal/Recovery & Forbidden Actions**
    - **Target:** `https://practice.expandtesting.com/dynamic-controls` (live DOM mutation) + forbidden calls (`file:///C:/Windows/win.ini`, `http://127.0.0.1:9222/json`, `http://169.254.169.254/latest/meta-data/`, `click_at(5000, 5000)`, `press_key("Win+r")`)
    - **Goal:** Cache `e1` from `REV:N`, mutate DOM/revision via `"Remove"` button click, deliberately call `act` with old `e1` / `revision`, verify `StaleElementError` refusal, then re-`discover()` and recover; issue every forbidden URL/bounds/hotkey call and verify `isError=true` refusal.
    - **Success Criterion:** Stale `act` refuses cleanly and fresh re-discover succeeds; all 5 forbidden actions return `isError=true` without side effects or crashing sessions.
    - **Independent Verification:** Raw MCP error payloads + `list_sessions()` confirmation that active session remains healthy.

18. **`T18` — Dual Concurrent Sessions & Clean Shutdown Zero-Leak Audit**
    - **Target:** Two simultaneous visible browser sessions (`https://example.com/` and `https://bonigarcia.dev/selenium-webdriver-java/`)
    - **Goal:** Interleave `discover`, `navigate`, and `act` across both sessions (`sA`, `sB`), verify separate URLs/revisions do not leak across sessions, then `close_session` all sessions started in this run and confirm `list_sessions()` empty + `list_desktop_windows` returns strictly to the `14` M0 baseline windows (plus user's Calculator/Notepad closed/untouched per scope).
    - **Success Criterion:** Zero cross-session state contamination, `list_sessions().count == 0`, zero newly leaked Chrome/Python MCP child processes.
    - **Independent Verification:** `list_desktop_windows` diff vs [m0_baseline_windows.json](live_runs/2026-11-26/evidence/m0_baseline_windows.json) + `psutil` process list before vs after.

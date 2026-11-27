# Disclosed Benchmark, Platform & Security Limitations (`0.1.0a2`)

This release documents both benchmark constraints and verified audit findings transparently without overclaiming runtime fixes. All items verified against baseline `0d19a9e` remain **open** unless explicitly marked otherwise.

## 1. Benchmark & Evaluation Limits

1. **Not Native OpenAI Computer Use vs CUL:** The 72-run comparison evaluated two semantic MCP browser tools (`@playwright/mcp@0.0.86` vs `CUL Browser MCP` at `fdc92d9`), not pure pixel/vision loops.
2. **`b11` Prompt Contamination:** Both arms received `(use filter_query if needed)` in `b11_dense_90_grid_filter`.
3. **Efficiency Tradeoff:** CUL used `~40%` higher median total tokens (`176,506` vs `126,087`), `50%` more median steps (`4.5` vs `3.0`), and `+1.5%` slower median wall time (`26.87s` vs `26.48s`).
4. **Observation Proxy != Token Billing:** `112` vs `1,196` uses `round(text_length / 4)` and static `28×28` patches (`Estimated Observation Size — Not Actual API Token Usage`). Dense uncapped pages (File Explorer `1,611`, GitHub Trending `1,264`) and non-Latin/Arabic text exceed those compact estimates.
5. **Unfinished Desktop Comparison:** Desktop Pilot completed only `CUL T1 (2/2)`; `CUL T2` is incomplete and the paired Native-vs-CUL desktop matrix (`Native vs CUL`) was never completed.

## 2. Verified Security & Reliability Findings (`0d19a9e`)

| ID | Finding | Severity | Audit Evidence | Fix Status at `0.1.0a2` |
|---|---|---|---|---|
| **F-01** | Cross-frame wrong-target click (`position:fixed` overlay over `iframe`) returns `ok:true, verified:true` | Critical | `CONFIRMED` (`B5`) | `NOT FIXED` (`browser_cdp.py:97,129-134`) |
| **F-02** | Password/secret regex misses `card`/`ccnum`/`ssn`/`cc-number` & hides `address_shipping`/`opinion`/`spinner` | High | `CONFIRMED` (`B6`) | `NOT FIXED` (`browser_cdp.py:1863,2150`) |
| **F-03** | `show_cursor=True` Shadow DOM `<canvas>` produces false `1280×720` `opaque_canvas` blind crop | High | `CONFIRMED` (`B14-1`) | `NOT FIXED` (`cursor_overlay.py:494,517`) |
| **F-04** | DNS resolution failure fails open; DNS-rebinding TOCTOU remains unmitigated | Medium | `CONFIRMED` (`.invalid`) / `NOT RUN` (TOCTOU) | `NOT FIXED` (`session_manager.py:141-145`) |
| **F-05** | Loopback DirectWS CDP port open without per-connection auth by default | Medium | `PARTIAL` (code read; local exploit `NOT RUN`) | `NOT FIXED` (`browser_cdp.py:550-555`) |
| **F-06** | Desktop `verify_fresh` hardcodes `occluded: False` | Medium | `CONFIRMED` (`exebox` session) | `NOT FIXED` (`desktop_uia.py:786`) |
| **F-07** | File Explorer inactive-tab controls leak (`offscreen: false`) | Medium | `CONFIRMED` (`B9`, `71 -> 85` elements) | `NOT FIXED` |
| **F-08** | Win32 `PrintWindow` horizontally mirrors `WS_EX_LAYOUTRTL` windows | Medium | `CONFIRMED` (`B12` PNG + UIA coords) | `NOT FIXED` |
| **F-REF** | Hypothesis that `src/engine/` holds stale unpatched code | Info | `REFUTED` (`16`-line `importlib` shims only) | `NO DEFECT` |

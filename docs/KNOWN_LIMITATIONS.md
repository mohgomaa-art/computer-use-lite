# Known Limitations & Open Boundaries (`v0.2.0a0`)

This document reconciles barriers resolved between [`v0.1.0a0`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a0) (`0d19a9e`) and `v0.2.0a0` (`a33a8f2`) against **still-open functional boundaries, platform constraints, and unrun verification scopes**.

---

## 1. Status Changes (`0d19a9e` -> `v0.2.0a0` @ `a33a8f2`)

| Area | Status at `0d19a9e` | Status in `v0.2.0a0` (`a33a8f2`) | Remaining Residual Boundary |
| :--- | :--- | :--- | :--- |
| **Cross-Frame Overlays (`CUL-ACC-001`)** | Clicked parent overlay with `verified=True` | **FIXED + VERIFIED-RUN:** Top-level `DOM.getNodeForLocation` probe (`_verify_top_frame_hit`) | Unresolvable cross-origin hierarchy reports `verification_scope="cross_origin_unprovable"` with `verified=False`. |
| **Secret Redaction (`CUL-PRIV-001/002`)** | Missed `card`/`ssn`/`ccnum`; hid `address_shipping`; raw SHA-256 digests | **FIXED + VERIFIED-RUN:** Word-boundary token classifier + ephemeral HMAC | Visual `<canvas>` secrets without accessible attributes stay outside DOM value inspection. |
| **SSRF DNS Fail-Closed (`CUL-SEC-001`)** | `socket.gaierror` fell through open (`infos=[]`) | **MITIGATED & BOUNDED:** `gaierror`/empty resolve raises `PermissionError` + Python drift guard | Chromium's C++ network stack still resolves DNS independently at socket connect (`SECURITY.md`). |
| **Loopback CDP Exposure (`CUL-SEC-002`)** | `CUL_MCP_DIRECT_WS=1` by default | **FIXED + VERIFIED-RUN:** Pipe IPC default (`direct_ws=False`); opt-in via `CUL_MCP_DIRECT_WS=1` | Pipe adds latency on extreme `2,500`-cell DOMs (`367.09 ms` Pipe vs `152.43 ms` DirectWS Opt-In). |
| **Truthful `verified` (`CUL-ACC-002`)** | Focus shift alone or `<input readonly>` returned `verified=True`; 400-char text cap | **FIXED + VERIFIED-RUN:** `_target_signature` + full-body `innerText` FNV-1a + `state.verify` | Deferred async network mutations settling long after action return still require `discover`/`read_page`. |
| **Rich AX / Date / Drag (`CUL-ACC-003`/`PERF-001`)** | No `date` setter, `<select>` options, AX metadata, sticky offset, `drag`, `read_page`, or idle TTL | **FIXED + VERIFIED-RUN:** Implemented all cleanly; adaptive hover `387.39 -> 90.83 ms` | Polymer inline `<style>` child-text heuristic & `<label>` wrapper edge cases stay minor heuristic edges. |
| **Windows UIA & RTL (`CUL-DESK-001..005`, `SEC-003/004`)** | `occluded: False`, `KillSwitch` fail-open, Explorer tab leak, RTL `PrintWindow` mirror, dangerous keys | **FIXED + VERIFIED-RUN:** Z-order/cloaking verify, fail-closed `KillSwitch`, lower-Z tab exclude, RTL mirror, blocklists | Desktop `T2` (`Calculator` + `7006652.txt`) & external UAC focus races stay unverified end-to-end. |
| **Linux / Cross-Platform (`CUL-DX-001/002`)** | Top-level Win32 imports crashed non-Windows imports; `psutil` missing from `[dev]` | **FIXED + VERIFIED-RUN:** Guarded Win32 init + real **WSL2 `kali-linux` `Python 3.14.7`** import + `requirements-lock.txt` | Desktop `DesktopSession` automation naturally stays Windows-only (`win32`); browser MCP runs cross-platform. |
| **Cursor Overlay A–G (`CUL-CUR-001..010`)** | False `1280x720` `opaque_canvas`, pulse flashes, stuck error, `14.7 deg` tilt, hidden hang, `48 KB` eval | **FIXED + VERIFIED-RUN (`A21`–`A26`):** Zero blind leak, 6->1 rebuilds, 48KB->0B eval, `<=5°` tilt, `2.3 ms` hidden return | OS hardware hooks (`GetCursorInfo` / `WH_KEYBOARD_LL`) in `exebox` remain **`NOT VERIFIED`**. |

---

## 2. Genuine Open Engine & Security Boundaries (`v0.2.0a0`)

1. **Chromium Internal Socket DNS-Rebinding TOCTOU (`SECURITY.md`):**  
   Python pre-validation cannot force Chromium's internal socket layer to reuse resolved IPs; untrusted internet browsing without an egress/DNS proxy remains outside support scope.
2. **Closed Shadow DOM & Visual-Only Canvases:**  
   Closed Shadow DOM elements without CDP DOM backend exposure and raw WebGL/canvas graphics without accessible semantics fall back to `blind_gap` visual coordinates (`click_at`), where `verified` stays `false` unless DOM text/state mutates.
3. **Inline `<style>` / `<label>` Extraction Edges (`[REPORTED]`):**  
   Fallback child text aggregation on Polymer/web components can include nested `<style>` text (`T12`) and unpruned `<label>` wrappers (`M1 #1`).
4. **`DirectWS` Security vs Pipe Latency Tradeoff:**  
   Safe `Pipe` IPC adds ~200 ms `p50` on extreme `2,500`-element DOM tables (`367.09 ms` vs `152.43 ms` Opt-In `DirectWS`). Normal forms stay sub-10 ms (`9.46 ms`).

---

## 3. Open Windows & Benchmark Verification Scope

1. **Track B1 Live LLM Benchmarks (`NOT_RUN`):**  
   Pre-flight checks hit Codex CLI `0.166.0` usage limit until Dec 26, 2026 and `@oai/sky`/API keys are absent. Track B2 (`18/18` vs `12/18`) is deterministic scripted MCP replay, NOT live LLM reasoning.
2. **Isolated `exebox` Hook Verification (`NOT VERIFIED`):**  
   Interactive `GetCursorInfo()` & global `WH_KEYBOARD_LL` tests return `ERROR_ACCESS_DENIED` on restricted `exebox` desktops; physical `Esc` takeover glow guarantees remain unit-tested in Python rather than kernel-verified.
3. **Live Public Sites & Desktop Pilot `T2`:**  
   Real third-party embeds (`youtube.com/embed`), Store Notepad real Save As UIA on `WinSta0\Default`, and Desktop `T2` (`Calculator`) remain outside the local `post-fix-v1` harness.
4. **Heuristic Token Metric (`TOKENS_EST` & `utf8_bytes`):**  
   `Api.last_stats` now emits both `utf8_bytes` and `tokens_note` clarifying `round(chars / 4, 1)` is a byte/char heuristic rather than provider BPE billing.

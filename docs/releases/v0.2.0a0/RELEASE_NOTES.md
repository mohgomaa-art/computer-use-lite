# Computer Use Lite `v0.2.0a0` — Security, Reliability, Portability & Cursor Hardening Release

> **Experimental Research Preview:** Builds atop immutable historical baseline [`v0.1.0a0`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a0) (`0d19a9e`) and publication releases [`v0.1.0a1`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a1) / [`v0.1.0a2`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a2), resolving audited `P0`–`P3`, cross-platform portability, and Cursor Overlay findings verified on commit `a33a8f2`.

---

## Key Verified Improvements (`0d19a9e` -> `v0.2.0a0`)

### Security, Privacy & Truthfulness (`P0` / `P1` / `P2`)
- **Cross-Frame Compositor Hit Check (`F-01` / `CUL-ACC-001`):** `_verify_top_frame_hit()` verifies top-level `DOM.getNodeForLocation` before dispatching frame/iframe actions (`0` overlay leak hits in `A01`, `A03`, `s03`).
- **Word-Boundary Secret Redaction & Keyed HMAC (`F-02` / `CUL-PRIV-001/002`):** Tokenized matcher (`is_sensitive_name` + `_IS_SENSITIVE_ELEM_JS`) catches `card`/`ccnum`/`ssn`/`iban`/`otp`/`autocomplete`, avoids over-redacting benign tokens, and replaces deterministic secret SHA-256 hashes with ephemeral keyed HMACs.
- **SSRF DNS Fail-Closed & IP Drift (`F-04` / `CUL-SEC-001`):** `validate_navigation_url()` fails closed (`PermissionError`) on `socket.gaierror`/empty resolution and catches IP drift across repeated resolves (Chromium C++ socket DNS TOCTOU remains a documented boundary).
- **Pipe CDP Default (`F-05` / `CUL-SEC-002`):** `_resolve_direct_ws` defaults to `False` (Playwright Pipe IPC, zero open loopback WebSocket port), with explicit `CUL_MCP_DIRECT_WS=1` opt-in retained.
- **Truthful `verified` & Full-Body Digest (`CUL-ACC-002`):** Focus-only no-ops and `<input readonly>` edits return `verified: false`, while `_DIGEST_TEXT_JS` FNV-1a hashes `document.body.innerText` past 400 chars (`b11`).
- **Desktop Policy & Prompt Boundary (`CUL-SEC-003/004/005`):** Default blocklist for shells, password managers, credential brokers, and elevated admin windows (`validate_desktop_target`), dangerous OS hotkey blocking with Win11 Arabic `VkKeyScanW` ASCII fallback (`validate_key_spec`), and `[UNTRUSTED_UI_TEXT]` sanitization (`sanitize_ui_text`).

### Windows Desktop UIA, Linux Portability & Cursor Overlay
- **Desktop Reliability (`F-06`–`F-08` / `CUL-DESK-001..005`):** Win32 Z-order + DWM cloaking check in `DesktopSession.verify_fresh`, fail-closed `KillSwitch.ensure_armed`, active-tab File Explorer `ShellTabWindowClass` scoping, `WS_EX_LAYOUTRTL` `ImageOps.mirror` before `PrintWindow` crop, and serialized `atexit` `_restore_screenreader_state`.
- **Cross-Platform Portability (`CUL-DX-001/002`):** Guarded top-level Win32 imports (`snapshot.py`, `desktop_uia.py`, `desktop_cursor_overlay.py`), `psutil>=6.0` in `[dev]`, `requirements-lock.txt`, CI `test-linux-portability`, and verified real **WSL2 `kali-linux` (`Python 3.14.7`)** import.
- **Cursor Overlay Hardening & Capabilities (`F-03`, `CUL-CUR-001..010`, `CUL-ACC-003`, `CUL-PERF-001`):** Zero false `opaque_canvas` blind regions, `busyDelayMs=350`, `errorResetMs=900`, double-click ripple scheduling, `±5.0°` tilt clamp, hidden-tab short-circuit, `Page.addScriptToEvaluateOnNewDocument` cache (`48,234 B -> 0 B` nav eval), rich AX metadata, lossless `<input type=date>`, sticky-header safe offsets, `drag`, `read_page` (preserving 13 MCP tools), idle TTL reaping, and **4.3x faster** adaptive hover (`387.39 -> 90.83 ms` p50).

---

## Comparative Benchmark & Verification Summary

| Suite / Track | Baseline `0d19a9e` | Fixed `v0.2.0a0` | Notes |
|---|---:|---:|---|
| **Track A paired checks (`n=32`)** | `2/32` (`6.25%`) | **`32/32` (`100.0%`)** | 95% Wilson CI `[89.28%, 100.0%]` (`+30W / 0L / 2T`) |
| **Track B1 live LLM (`codex-cli` / `@oai/sky`)** | `—` | **`NOT_RUN`** | Codex CLI usage quota reached until Dec 26, 2026; `@oai/sky` absent |
| **Track B2 scripted stdio MCP (`n=18`)** | `12/18` (`66.67%`) | **`18/18` (`100.0%`)** | Scripted client (NOT LLM); baseline failed `s01`–`s06` |
| **Track D full Win11 `pytest`** | `70/70` (`197.50s`) | **`95 passed, 0 failed`** (`228.85s`) | CI subset `CUL_SKIP_DESKTOP=1`: **`79 passed, 16 deselected`** (`90.58s`) |
| **Track D Linux WSL2 `kali-linux`** | Crashed at import | **`WSL_LINUX_OK`** | Python `3.14.7` (`wsl2_kali_linux_python3_import`) |

---

## Disclosed Unverified & Residual Boundaries
1. **Live LLM Benchmarks (`NOT_RUN`):** No live VLM/LLM tasks executed due to Codex usage limit and absent cloud keys.
2. **Hardware OS Hooks in `exebox` (`NOT VERIFIED`):** `GetCursorInfo()` pointer behavior & `WH_KEYBOARD_LL` physical `Esc` interrupt tests return `ERROR_ACCESS_DENIED` inside isolated `exebox`.
3. **Chromium Socket DNS TOCTOU:** Python pre-checks fail closed on `gaierror` and IP drift, while Chromium C++ socket resolution stays outside Python control.
4. **Desktop Pilot `T2` & Live Public Embeds:** Store Calculator `T2` workflow and live third-party embeds (`youtube.com/embed`) remain unverified end-to-end.

Full documentation: [`ENGINEERING_CHANGE_HISTORY.md`](https://github.com/mohgomaa-art/computer-use-lite/blob/v0.2.0a0/docs/releases/v0.2.0a0/ENGINEERING_CHANGE_HISTORY.md) · [`POST_FIX_AUDIT_REPORT.md`](https://github.com/mohgomaa-art/computer-use-lite/blob/v0.2.0a0/research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md) · [`post-fix-v1/REPORT.md`](https://github.com/mohgomaa-art/computer-use-lite/blob/v0.2.0a0/research/benchmarks/post-fix-v1/REPORT.md)

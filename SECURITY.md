# Security Policy

**Project:** Computer Use Lite (`v0.2.0a0`, historical baseline [`v0.1.0a0`](https://github.com/mohgomaa-art/computer-use-lite/releases/tag/v0.1.0a0))  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**Creator & Lead Developer:** Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/))

---

## 1. Supported Versions & Trust Scope

| Baseline | Security Support Scope |
| :--- | :--- |
| `0.2.0a0` (latest preview) | Hardened single-user research release — **single-user local workstation / controlled testbed**. Resolves all P0–P3 & Windows UIA findings from `0d19a9e`, with documented browser socket DNS TOCTOU and OS hook caveats below. |
| `0.1.0a0` – `0.1.0a2` | Preserved historical baselines (unpatched `0d19a9e` engine; do not use on untrusted targets). |

---

## 2. Implemented Safeguards (`v0.2.0a0`)

- **SSRF Fail-Closed DNS & Redirect Interception (`session_manager.validate_navigation_url`, `browser_cdp.py`):** Rejects `file://` (unless `CUL_MCP_ALLOW_FILE_URLS=1`), `javascript:`, `data:`, `chrome://`, private/loopback/CGNAT/link-local/IPv6-mapped/NAT64/Teredo/6to4 ranges (`CUL_MCP_ALLOW_PRIVATE_URLS=1` opt-in), **fails closed (`PermissionError`) on `socket.gaierror` / empty resolution**, detects IP drift across repeated resolves, and intercepts `3xx` redirects & sub-requests via CDP `Fetch`.
- **Loopback CDP Port Disabled by Default (`CUL_MCP_DIRECT_WS=0`, `browser_cdp._resolve_direct_ws`):** Self-launched Chromium runs over Playwright's internal Pipe IPC with **zero open TCP debugging port** by default; setting `CUL_MCP_DIRECT_WS=1` is explicit opt-in (`--remote-debugging-address=127.0.0.1 --remote-allow-origins=http://127.0.0.1:<port>`).
- **Cross-Frame Overlay Hit Verification (`browser_cdp._verify_top_frame_hit`):** Checks top-level `DOM.getNodeForLocation` before dispatching frame/iframe actions; parent overlays raise `StaleElementError`, and unprovable cross-origin targets fail truthful verification (`verified=False, verification_scope="cross_origin_unprovable"`).
- **Desktop Process Blocklist & Safe Shortcuts (`state.py`, `session_manager.py`, `desktop_uia.py`):** `open_desktop` refuses terminals (`powershell.exe`, `pwsh.exe`, `cmd.exe`, `windowsterminal.exe`), password managers (`1password.exe`, `bitwarden.exe`, `keepass.exe`), `CredentialUIBroker.exe`, `Taskmgr.exe`, `regedit.exe`, `mmc.exe`, and sensitive classes unless overridden (`CUL_DESKTOP_ALLOW_SENSITIVE=1` / `CUL_DESKTOP_ALLOW_PROCESSES`). `validate_key_spec` blocks `Win/Meta`, `Alt+Tab`, `Alt+F4`, `Alt+Esc`, `Ctrl+Esc`, `Ctrl+Shift+Esc`, and `Ctrl+Alt+Del` (`CUL_ALLOW_SYSTEM_SHORTCUTS=1` override).
- **Fail-Closed `KillSwitch` & Z-Order Occlusion (`desktop_uia.py`, `blind_gap.py`):** `KillSwitch.ensure_armed()` fails closed (`RuntimeError`) if `GetCursorPos()` errors, and `DesktopSession.verify_fresh()` verifies both Win32 Z-order occlusion and DWM cloaking before dispatching input.
- **Word-Boundary Secret Redaction & Keyed HMAC (`state.py`, `browser_cdp.py`):** Tokenized secret classifier covers `card`/`ccnum`/`ssn`/`iban`/`otp`/`autocomplete=cc-number`, keeps benign words unredacted, and hashes secret deltas only with per-process ephemeral HMAC (`hmac:...`).
- **Untrusted UI Prompt Boundary (`state.sanitize_ui_text`, `mcp_server.py`):** Strips control chars, newlines, `|`, and `[UNTRUSTED_...]` lookalikes from UI strings and wraps titles/names/`DIALOG_ALERT:` payloads in `[UNTRUSTED_UI_TEXT]` framing.
- **CSP / Trusted-Types Cursor Overlay & Bounded Inputs (`cursor_overlay.py`, `desktop_cursor_overlay.py`):** Avoids `opaque_canvas` false positives, omits DOM string HTML sinks, clamps viewports/limits/coordinates, and enforces `SessionManager` idle TTL reaping (`CUL_SESSION_IDLE_TTL_S=1800`).

---

## 3. Known Open Security Boundaries (`v0.2.0a0`)

1. **Chromium Socket-Level DNS Rebinding TOCTOU (`OPEN BOUNDARY`):**  
   While Python `validate_navigation_url()` fails closed on `gaierror` and catches IP drift across Python resolution calls, Chromium's internal C++ network stack still resolves DNS independently when opening TCP sockets unless an external DNS-pinning proxy/firewall enforces policy at socket connect time.
2. **Explicit `CUL_MCP_DIRECT_WS=1` Opt-In (`OPT-IN TRADEOFF`):**  
   Safe default (`Pipe` IPC) eliminates the unauthenticated loopback port. When a user explicitly enables `CUL_MCP_DIRECT_WS=1` for extreme `>2,500`-node latency optimization, loopback `--remote-debugging-port` exposure applies on localhost for that session.
3. **Direct Python `BrowserSession` Outside MCP (`BY DESIGN`):**  
   Constructing `BrowserSession(url=...)` directly in Python omits `url_validator` unless passed explicitly (`url_validator=validate_navigation_url`).
4. **Hardware Hook Verification Scope (`NOT VERIFIED` in `exebox`):**  
   OS-level `GetCursorInfo()` pointer behavior and global `WH_KEYBOARD_LL` physical `Esc` interrupt paths cannot run under isolated `exebox` (`ERROR_ACCESS_DENIED`). Do not rely on `CUL_TAKEOVER_GLOW` interrupts as a hard security boundary on untrusted desktops.

---

## 4. Reporting a Vulnerability

> [!IMPORTANT]
> **Maintainer Notice Prior to Public Hosting:** A public maintainer email address is omitted from repository metadata. On GitHub, report vulnerabilities via **GitHub Security Advisories (Private Vulnerability Reporting)** once enabled by **Mohamed Gomaa** (`@mohgomaa-art`).

**How to report:**
- **Do NOT open public GitHub Issues** for exploitable vulnerabilities (such as CDP escapes, DNS-rebinding / SSRF chains outside documented limits, privilege escalation, or secret leakage).
- Use the repository's **GitHub Security Advisories ("Report a vulnerability")** workflow.
- Include: affected commit SHA, exact reproduction steps (preferring deterministic local fixtures), affected module (`browser_cdp`, `desktop_uia`, `mcp_server`, `session_manager`, `cursor_overlay`, `desktop_cursor_overlay`), and security impact.

# Security Policy

**Project:** Computer Use Lite (`v0.1.0-alpha` + `main` through `d47b4e9`)  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**Creator & Lead Developer:** Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/))

---

## 1. Supported Versions & Trust Scope

| Baseline | Security Support Scope |
| :--- | :--- |
| `0.1.0-alpha` -> `main` (`d47b4e9`) | Experimental research preview — **single-user trusted local workstation only**. Not hardened for untrusted multi-tenant hosts, arbitrary untrusted web browsing, or unisolated production automation. |

---

## 2. Implemented Safeguards (`HEAD` `d47b4e9`)

- **Initial URL Validation & IP Normalization (`session_manager.validate_navigation_url`):** MCP `open_browser` and `navigate` reject `file://` (unless `CUL_MCP_ALLOW_FILE_URLS=1`), `javascript:`, `data:`, `chrome://`, plus IPv4/IPv6 loopback, private RFC1918, CGNAT (`100.64.0.0/10`), cloud metadata link-local hosts (`169.254.169.254`, `metadata.google.internal`), obfuscated numeric/octal/hex hosts (`2130706433`, `0177.0.0.1`, `0x7f000001`), `.local`/`.localhost`, trailing-dot `localhost.`, IPv4-mapped IPv6 (`::ffff:127.0.0.1`), 6to4, Teredo, and NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` is explicitly set.
- **CDP `Fetch` Redirect & Sub-Request SSRF Interception (`P0-4`, `965eb66`):** When a `url_validator` is attached (all MCP `BrowserSession` instances), `browser_cdp.BrowserSession` installs a browser-wide CDP `Fetch` interceptor (`_install_browser_fetch_guard`, falling back to per-page `Fetch` sessions if needed) inspecting both `Request` and `3xx` `Response` `Location` headers and failing disallowed targets with `BlockedByClient` / `PermissionDenied` (unit-tested in `tests/test_audit_fixes.py::test_p0_4_*`; live external proxy/redirect stress testing remains unrun).
- **Exact-Port CDP Origin Restriction & `DirectWS` Gate (`P0-5`, `a3291b3`):** Self-launched Chromium instances using `DirectCdpClient` bind `--remote-debugging-address=127.0.0.1` alongside exact-port `--remote-allow-origins=http://127.0.0.1:<port>`, and callers can disable the TCP debugging port completely by setting `CUL_MCP_DIRECT_WS=0` (or `direct_ws=False` in Python), falling back to Playwright's internal `CDPSession` adapter.
- **CSP / Trusted-Types Safe Cursor Overlay (`7c7b9b4`, `e3d0bd5`):** Chromium's cursor overlay (`cursor_overlay.py`) injects vector SVG nodes cleanly via DOM creation APIs without inline string HTML sinks (`innerHTML` safe under strict CSP / Trusted Types), and desktop overlay capture uses `_WDA_EXCLUDEFROMCAPTURE` (`0x00000011`) on `desktop_cursor_overlay.py` while keeping `WS_EX_NOACTIVATE | WS_EX_TRANSPARENT`.
- **Value Redaction in Persistence (`state.py`):** `TaskState.record_action()` strips all non-`None` action `"value"` payloads to `{value_length, value_sha256, value_redacted: true}`, and `inspect_element()` returns `"[REDACTED]"` for password fields.
- **Blocked Dangerous OS Hotkeys (`desktop_uia.py`):** `press_key()` refuses `Win`, `LWin`, `RWin`, `Meta`, `Super`, `Command`, and `Cmd` (alone or inside hotkey chords).
- **Bounded Inputs (`session_manager.py` / `browser_cdp.py`):** Viewports clamped to `[200..3840] x [200..2160]`, `limit` clamped to `[1..200]`, `max_elements` clamped to `[1..300]`, and `click_coordinate` rejects coordinates outside active viewport bounds.

---

## 3. Known Open Security Limitations (`HEAD` `d47b4e9`)

The following boundaries remain **explicitly open** and are documented intentionally:

1. **DNS-Rebinding TOCTOU & Offline DNS Fallthrough (`OPEN`):**  
   `validate_navigation_url()` explicitly warns in its docstring that pre-connection URL/redirect validation does **not** eliminate OS-level DNS-rebinding time-of-check-to-time-of-use (TOCTOU) races between Python `socket.getaddrinfo()` checks and Chromium's own network socket connection. Offline `socket.gaierror` lookups also do not block entry validation on their own.
2. **Local Host TCP CDP Endpoint When `DirectWS` Is Active (`OPEN on Localhost`):**  
   When `DirectCdpClient` is enabled (`CUL_MCP_DIRECT_WS != 0`, default), Chromium listens on `127.0.0.1:<free_port>` without per-connection token authentication; while browser tabs carrying external `Origin` headers are blocked by `--remote-allow-origins=http://127.0.0.1:<port>`, other local OS processes on the same machine sending HTTP or origin-less WebSocket connections to that loopback port can read `/json/version` or send CDP commands. Set `CUL_MCP_DIRECT_WS=0` in stricter environments.
3. **Direct Python `BrowserSession` Outside MCP (`BY DESIGN`):**  
   Calling `BrowserSession(url=...)` directly in Python omits `url_validator` by default so local test fixtures (`file://`, `127.0.0.1`) operate without env overrides; callers building custom orchestrators over `BrowserSession` must pass `url_validator=validate_navigation_url` explicitly if untrusted URLs are possible.
4. **`KillSwitch` First-Sample Initialization Nuance (`OPEN`):**  
   `desktop_uia.move_mouse()` silently ignores an `OSError` during the initial `GetCursorPos()` read rather than failing closed immediately, which can leave mouse injection unguarded if pointer polling fails in restricted desktop contexts.
5. **Untrusted Desktop Context Isolation:**  
   `DesktopSession` relies on Win32 foreground checks and UIA `AutoSetFocus=0`; no OS-level sandboxing prevents malicious local desktop windows from racing UI focus changes between discovery and dispatch.

---

## 4. Reporting a Vulnerability

> [!IMPORTANT]
> **Maintainer Notice Prior to Public Hosting:** A public maintainer email address is omitted from repository metadata. On GitHub, report vulnerabilities via **GitHub Security Advisories (Private Vulnerability Reporting)** once enabled by **Mohamed Gomaa** (`@mohgomaa-art`).

**How to report:**
- **Do NOT open public GitHub Issues** for exploitable vulnerabilities (such as CDP escapes, DNS-rebinding / SSRF chains outside documented limits, privilege escalation, or secret leakage).
- Use the repository's **GitHub Security Advisories ("Report a vulnerability")** workflow.
- Include: affected commit SHA, exact reproduction steps (preferring deterministic local fixtures), affected module (`browser_cdp`, `desktop_uia`, `mcp_server`, `session_manager`, `cursor_overlay`, `desktop_cursor_overlay`), and security impact.

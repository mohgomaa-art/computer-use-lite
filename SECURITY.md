# Security Policy

**Project:** Computer Use Lite (`v0.1.0-alpha`)  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**Creator & Lead Developer:** Mohamed Gomaa

---

## 1. Supported Versions & Trust Scope

| Version | Security Support Scope |
| :--- | :--- |
| `0.1.0-alpha` | Experimental research preview — **single-user trusted local workstation only**. Not hardened for untrusted multi-tenant hosts, arbitrary untrusted web browsing, or unisolated production automation. |

---

## 2. Implemented Safeguards (`HEAD`)

- **Initial URL Validation (`session_manager.validate_navigation_url`):** MCP `open_browser` and `navigate` reject `file://`, `javascript:`, `data:`, `chrome://`, IPv4/IPv6 loopback, RFC1918 private ranges, CGNAT (`100.64.0.0/10`), cloud metadata link-local addresses (`169.254.169.254`, `metadata.google.internal`), obfuscated numeric/octal/hex hosts (`2130706433`, `0177.0.0.1`, `0x7f000001`), IPv6-mapped IPv4 (`[::ffff:127.0.0.1]`), `.local` / `.localhost`, and trailing-dot `localhost.` unless `CUL_MCP_ALLOW_PRIVATE_URLS=1` is explicitly set.
- **Value Redaction in Persistence (`state.py`):** `TaskState.record_action()` strips all non-`None` action `"value"` payloads to `{value_length, value_sha256, value_redacted: true}`, and `inspect_element()` returns `"[REDACTED]"` for password fields.
- **Blocked Dangerous OS Hotkeys (`desktop_uia.py`):** `press_key()` refuses `Win`, `LWin`, `RWin`, `Meta`, `Super`, `Command`, and `Cmd` (alone or inside hotkey chords).
- **Bounded Inputs (`session_manager.py` / `browser_cdp.py`):** Viewports clamped to `[200..3840] x [200..2160]`, `limit` clamped to `[1..200]`, `max_elements` clamped to `[1..300]`, and `click_coordinate` rejects coordinates outside active viewport bounds.

---

## 3. Known Open Security Limitations (`v0.1.0-alpha`)

The following behaviors are **documented open limitations** verified on `HEAD` and are **not** bugs unknown to the maintainer:

1. **HTTP `302` SSRF Redirects (`OPEN`):**  
   `validate_navigation_url()` validates initial entry URLs only; once a permitted external origin loads, Chromium `page.goto()` follows `HTTP 302 Location: http://127.0.0.1:<port>/...` without re-validating redirect destinations.
2. **DNS-Rebinding & Offline DNS Fallthrough (`OPEN`):**  
   Python `socket.getaddrinfo()` pre-checks occur separately from Chromium's own TCP connection resolution, leaving a time-of-check-to-time-of-use (TOCTOU) window, and offline `socket.gaierror` responses do not block navigation.
3. **Unauthenticated Local CDP Port (`OPEN` on Localhost):**  
   When Chrome launches with `--remote-debugging-port=<port>`, `http://127.0.0.1:<port>/json/version` is readable without authentication by local host processes, and WebSocket connections omitting an `Origin` header can invoke CDP commands. *(Browser-tab CSWSH requests carrying an `Origin` header are rejected with `HTTP 403` under Chromium `1.64` defaults.)*
4. **Direct Python `BrowserSession` Outside MCP:**  
   Calling `BrowserSession(url=...)` directly from Python intentionally omits MCP host blocking so local test fixtures (`file://`, `127.0.0.1`) operate without extra opt-in flags.
5. **`KillSwitch` Initialization Nuance (`OPEN`):**  
   `desktop_uia.move_mouse()` silently ignores an `OSError` during the first baseline `GetCursorPos()` read rather than failing closed immediately.

---

## 4. Reporting a Vulnerability

> [!IMPORTANT]
> **Maintainer Setup Notice Prior to Public Hosting:** A public maintainer email address has not yet been published in repository metadata. Before accepting external bug reports on GitHub, **Mohamed Gomaa** should enable **GitHub Private Vulnerability Reporting (Security Advisories)** in repository settings and/or add a verified security contact address here.

**How to report:**
- **Do NOT open public GitHub Issues** for exploitable vulnerabilities (such as CDP escape, SSRF chains outside documented limitations, arbitrary command execution, or privilege escalation).
- Use the repository's **GitHub Security Advisories ("Report a vulnerability")** channel once enabled on the hosted repository.
- Include: affected commit SHA, exact reproduction steps (preferring deterministic local fixtures), affected surface (`browser_cdp`, `desktop_uia`, `mcp_server`, `session_manager`), and potential security impact.

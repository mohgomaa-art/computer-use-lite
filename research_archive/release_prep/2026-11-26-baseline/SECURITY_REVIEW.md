> [!NOTE]
> **Archival Provenance:** Moved from `release_preparation/SECURITY_REVIEW.md` (pre-move SHA-256: `CE80D0087343C62F59AC844B3101219E4B8ADC3016CB998F0CBE4FDEB22BB84C`). Archived Release Preparation Security Scan captured at `HEAD=3e67e49` (pre-`P0-4` Fetch SSRF guard & pre-`P0-5` CDP allow-origins). Superseded for current threat posture by [SECURITY.md](../../../SECURITY.md). See also [Archive Index](../../INDEX.md) and [README](../../../README.md).
> *(Absolute local workstation URIs and relative paths were normalized for archival portability; original findings, figures, and scope claims below are preserved verbatim.)*

# Phase 1 — Security & Privacy Audit (`computer-use-lite`)

> **Audit Basis:** Direct static scanning across working tree + all `25` reachable Git commits (`150` unique blobs), direct inspection of `src/computer_use_lite/*.py`, and live read-only runtime probes executed on `2026-11-26` (`sec_probes.py` exit code `0`). No external scanner binaries (`gitleaks`, `trufflehog`, `detect-secrets`, `bandit`, `pip-audit`) were installed on this host, so custom deterministic regex/metadata/git-blob scanners verified every text blob and image file directly.

---

## 1. Status Vocabulary Used Below
- **`FIXED-VERIFIED`**: Defect patched in `src/` and re-verified on current code in this session.
- **`FIXED-UNVERIFIED`**: Behavior mitigated/configured or verified only under partial/non-production conditions.
- **`NOT-REPRODUCED`**: Audited claim did not reproduce on `HEAD`; code already guards safely.
- **`OPEN`**: Genuine security, privacy, or boundary risk verified on current `HEAD`.
- **`BLOCKED`**: Runtime verification prevented by environment boundary (e.g. non-interactive desktop isolation).
- **`NOT-TESTED`**: Path or mechanism not dynamically exercised here.

---

## 2. Part A — Secret, Credential, PII & Path Exposure Scan (`[MEASURED]`)

| Scan Category | Scope Checked | Result | Status & Required Action |
| :--- | :--- | :--- | :--- |
| **API Keys / Tokens / Private Keys** (`AIza*`, `sk-*`, `ghp_*`, `AKIA*`, `xox*`, PEM keys, Bearer JWTs) | `123` tracked + `155` untracked files + `150` git blobs across `25` commits (`phase0_1_scan.py`) | **`0` matches** | Clean — no API secrets found in tree or history. |
| **Cookies / Auth Headers** (`Set-Cookie`, `Cookie`, `sessionid`, `__Secure-*`, etc.) | Full working tree (non-git) | **`0` matches** | Clean — no session cookies or HAR auth payloads stored. |
| **Email Addresses** | Working tree + `150` historical git blobs | Only placeholder/test domains found: `todo@example.invalid`, `fake-tester@example.invalid`, `test@example.invalid`, `alice@example.com` | **Action:** Replace `git config` / doc placeholders (`todo@example.invalid`) cleanly without inventing an unconfirmed personal email. |
| **Image EXIF / PNG `tEXt` Metadata** | All `100+` `.png` captures across `archive/`, `live_runs/`, `results/`, `skill_updates/` | **`0` embedded non-DPI metadata chunks** | Raw screenshots still visually depict OS desktop/window chrome (`archive/screenshots/`, `live_runs/`), so keep non-curated captures `PRIVATE`. |
| **User-Specific Filesystem Paths & Machine Context** | `phase0_1_scan.py` & `phase0_1_extra.py` | **`OPEN` Privacy Exposure:** Local home-directory path segments containing the OS username (`92` occurrences across `25` git commits in `12` tracked files: `README.md:73`, `FINAL_SKILL_UPDATE_REPORT.md`, and `10` files in `skill_updates/`; plus `510+` occurrences in untracked `AUDIT_REPORT.md`, `RUN_REPORT.md`, `fix_runs/`, `live_runs/`, `research_trace/`). Commits `abebcff`, `f0fd6ba`, `ace5c5f`, `b4ca9b5`, `e759989`, `3e67e49` also expose local IDE paths and sandbox desktop names (`exebox-*`). | **Remediation:** Do NOT push existing `main` commits raw to a public remote if local username/IDE paths must stay private. Scrub `README.md:73` locally, classify `skill_updates/`, `live_runs/`, `fix_runs/`, `research_trace/`, and internal reports as `PRIVATE / REMOVE-FROM-RELEASE`, and export a clean curated release branch/orphan commit upon owner approval (preserving local history intact). |
| **Ownership Placeholder Tags (`[TODO: ...]`)** | Working tree | **`5` tracked hits:** `LICENSE:177`, `NOTICE` (`2` lines), `pyproject.toml:13`, `README.md:123` | **Resolved in Phase 3/4** (`Mohamed Gomaa`, Creator & Lead Developer). |

---

## 3. Part B — Security Architecture Review (`src/computer_use_lite/`)

> **Important Scope Discipline:** Targeted security mechanisms pass unit checks, but `Computer Use Lite` as a whole is an **experimental research engine**, NOT a hardened multi-tenant sandbox.

| Security Surface | Code Location (`HEAD`) | Measured Runtime / Code Behavior | Audit Status | Remediation / Release Note |
| :--- | :--- | :--- | :---: | :--- |
| **1. CDP Remote Debugging Port (`Origin` CSWSH & Local Socket)** | `browser_cdp.py:348-352` (`--remote-debugging-port=<free_port>`) | Live probe (`sec_probes.py` `[MEASURED]`): Chromium `1.64` rejects WebSocket upgrades carrying `Origin: https://evil.example` AND `Origin: http://127.0.0.1` with **`HTTP 403`** by default (mitigating cross-site browser tab CSWSH). **However**, `http://127.0.0.1:<port>/json/version` is exposed unauthenticated and origin-less local WebSocket clients (`Origin` omitted) execute `Runtime.evaluate("1+1")` cleanly (`accepted: true`). | **`FIXED-UNVERIFIED`** (browser CSWSH blocked by Chromium defaults) / **`OPEN`** (local unauthenticated TCP loopback access) | Document single-user trusted-host requirement in `SECURITY.md` + `KNOWN_LIMITATIONS.md`; future `src/` hardening may switch direct WS behind `--remote-allow-origins` confirmation or `--remote-debugging-pipe`. |
| **2. SSRF — Initial URL & Obfuscated IP Validation** | `session_manager.py:38-122` (`validate_navigation_url`) | Live probe (`sec_probes.py` `[MEASURED]`): blocks `file://`, `javascript:`, `data:`, `chrome://` (`PermissionError`), plus literal, decimal (`2130706433`), octal (`0177.0.0.1`), hex (`0x7f000001`), IPv6 (`[::1]`, `[::ffff:127.0.0.1]`, `[::ffff:169.254.169.254]`), CGNAT (`100.64.0.1`), link-local metadata (`169.254.169.254`, `metadata.google.internal`), `*.local`, `*.localhost`, and trailing-dot `localhost.` unless `CUL_MCP_ALLOW_PRIVATE_URLS=1`. | **`FIXED-VERIFIED`** | Keep default refusal strict; warn that DNS offline failures (`socket.gaierror`) fall through cleanly (`localhost.localdomain` allowed when NXDOMAIN). |
| **3. SSRF — HTTP `302` Redirects & DNS-Rebinding TOCTOU** | `session_manager.py:106-121`, `browser_cdp.py:355,1154` | Live probe (`sec_probes.py` `[MEASURED]`): once `open_browser`/`navigate` passes `validate_navigation_url()`, Chromium `page.goto()` follows HTTP `302 Location: http://127.0.0.1:<port>/secret` directly (`secret_hits: 1`, `final_url: http://127.0.0.1:.../secret`) without re-validating redirect hops or iframe sub-requests. Furthermore, separate Python `socket.getaddrinfo()` + Chromium TCP resolution leaves a DNS-rebinding TOCTOU window (`cannot claim DNS-rebinding protection from URL validation alone`). | **`OPEN`** (**Release-Blocking Security Gap for Untrusted Web Agents**) | Disclosed explicitly as `OPEN` in `SECURITY.md`, `KNOWN_LIMITATIONS.md`, & `FINAL_RELEASE_READINESS.md`. Requires owner approval to patch `src/` (`context.route` navigation hop validation + residual DNS-rebinding disclosure) or restrict public release warning to trusted URLs. |
| **4. `TaskState` Persistence Redaction** | `state.py:28-35,72-76` | Direct inspection & `tests/test_audit_fixes.py:263-270` (`[VERIFIED-CODE]`): `TaskState.record_action()` strips `"value"` on **every** non-`None` action and records only `value_length`, 12-char `value_sha256`, and `value_redacted=True`. `BrowserSession.signature()` hashes active values via SHA-256; `Api.inspect_element()` returns `"[REDACTED]"` for password inputs. | **`NOT-REPRODUCED`** (Already Safely Implemented) | Preserved intact. *(Note: `inspect_element()` intentionally returns plaintext `value` to caller on non-password `textbox`/`searchbox` controls in memory without persisting it to `task_state.json`.)* |
| **5. `KillSwitch` Failure Semantics** | `desktop_uia.py:118-138,173-179` | Code inspection (`[VERIFIED-CODE]`): `move_mouse` wraps initial `kill_switch.moved(cursor_pos())` inside `try: ... except OSError: pass`, silently continuing mouse injection if `GetCursorPos()` fails during initialization. Later `pre_move()` calls DO raise `OSError` unless not armed. | **`OPEN`** (Low-Medium inside `exebox`; fail-open init risk) | Flagged in `KNOWN_LIMITATIONS.md` & proposed future P2 fix (`fail closed after initialization error` — requires owner auth before `src/` edit). |
| **6. MCP Input Validation & Blocked OS Keys** | `session_manager.py:359,506,539`, `desktop_uia.py:248-280`, `browser_cdp.py:1171-1195` | Viewport clamped `[200..3840]x[200..2160]`; `limit` `[1..200]`; `max_elements` `[1..300]`; `click_coordinate` rejects out-of-bounds `[vx, vy, vw, vh]`; `press_key` blocks `Win`/`LWin`/`RWin`/`Meta`/`Super`/`Command`/`Cmd`. | **`FIXED-VERIFIED`** | Preserved intact. |
| **7. Process Lifecycle & Temp-File Hygiene** | `session_manager.py:66-123,265`, `state.py:55-70`, `mcp_server.py:148-154` | `TaskState` uses `tempfile.mkstemp` + atomic `os.replace` (`fsync=False` strictly for disposable MCP temp dirs); `tests/test_mcp_server.py` confirms `stdin` EOF kills child Chrome PIDs cleanly (`0` orphans). | **`FIXED-VERIFIED`** | Keep `TemporaryDirectory` cleanup on session close and `atexit` hook intact. |
| **8. Multi-Window Covered Desktop Capture (`PrintWindow` vs `ImageGrab`)** | `blind_gap.py:44-109,207-231` | Mocked `test_m4_p09` (`PASSED`) + prior M1 live report (`[REPORTED]` `Settings` on `WinSta0\Default` vs black WinUI3 Mica background + horizontal RTL mirroring on `Notepad.exe` `0x400110`). Live `ImageGrab` vs `PrintWindow` pixel contrast inside isolated `exebox` terminal remains `BLOCKED`. | **`FIXED-UNVERIFIED`** (Live `exebox` `BLOCKED`; RTL flip noted) | Documented cleanly in `KNOWN_LIMITATIONS.md` & `SECURITY.md` (unintended background disclosure mitigated by Z-order `PrintWindow` check, not cross-framework-verified on all RTL apps). |

---

## 4. Recommended Owner Actions Prior to Pushing Publicly

1. **DO NOT push raw `main` history directly** without addressing the `92` personal-path commits (`skill_updates/`, `FINAL_SKILL_UPDATE_REPORT.md`, `abebcff`). Export a curated release branch/orphan commit using [PUBLICATION_BOUNDARY.md](PUBLICATION_BOUNDARY.md).
2. **Decide on `src/` SSRF redirect gate (`session_manager.py` / `browser_cdp.py`)** before tagging `v0.1.0-alpha` if untrusted AI agents will browse arbitrary third-party web pages containing malicious redirects.
3. **Add a real security contact address** (or GitHub Security Advisories workflow once the repository exists) in `SECURITY.md`.

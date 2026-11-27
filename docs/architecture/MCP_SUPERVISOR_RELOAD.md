# Architecture Design: Reloadable MCP Stdio Supervisor (`computer_use_lite.supervisor`)

**Status:** Implemented & Verified Architecture Specification  
**Primary Platform:** Windows 11 (`win32`, Python `>=3.10`, binary newline-delimited UTF-8 JSON-RPC over stdio pipes)

---

## 1. Phase 1 Audit Findings & Root Cause

When an MCP client connects to `computer-use-lite`, it spawns a single child running `python -u -m computer_use_lite.mcp_server`:

1. **Single blocking stdio loop (`mcp_server.py:735-775`):** `main()` (`mcp_server.py:761-775`) calls `anyio.run(run_stdio_server)`, which wraps stdin/stdout (`mcp_server.py:737-740`) and blocks in `server._mcp_server.run(...)` (`mcp_server.py:746-750`) until EOF or signal.
2. **One-time static construction (`mcp_server.py:280-296, 731, 743`):** `run_stdio_server()` calls `build_server()` once, instantiating one `SessionManager()` (`mcp_server.py:282`) and registering closure callbacks once onto `FastMCP`.
3. **Python import cache (`sys.modules` + `mcp_server.py:34-37`, `session_manager.py:33-41`):** Imported modules (`session_manager`, `api`, `browser_cdp`, `desktop_uia`, `resolver`, `state`, `snapshot`, `blind_gap`, `takeover_guard`) remain bound in `sys.modules` and closures for the life of the process. On-disk edits are never reloaded.
4. **Long-lived stateful workers (`session_manager.py:173-325`):** Active sessions pin dedicated OS threads (`_SessionWorker._thread`, `session_manager.py:200-206`), Playwright `sync_api` greenlets/Chromium processes, Windows UIA COM MTA apartments, `Api`/`Resolver` `eN`/`REV:N` state, temporary directories, and Win32 overlays.

### State Lost on Respawn & Cleanup Guarantees
- **Lost upon child respawn:** All open `BrowserSession` instances (Chromium processes + CDP connections), `DesktopSession` UIA attachments + desktop cursor overlays, session IDs (`s1`, `s2`), in-memory `Resolver` element maps (`eN` / `REV:N`), and ephemeral temp directories.
- **Cleanup contract:** Supervisor initiates graceful EOF shutdown (`child.stdin.close()`) so `mcp_server.py:752-758` runs `await mgr.close_all()` before waiting up to `5.0s`. On Windows, every child is also assigned to a Win32 Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) and started with `CREATE_NEW_PROCESS_GROUP`; if EOF cleanup stalls or a child crashes, `TerminateJobObject` / `os.killpg` guarantees zero orphaned Chrome/Playwright/overlay processes survive.
- **Agent notification:** `cul_reload` explicitly notifies the agent that all prior `session_id`, `eN`, and `REV:N` values are invalid and must be re-established (`list_tools` -> `open_browser`/`open_desktop` -> `discover`).

---

## 2. Alternative Rejected: In-Process `importlib.reload()`

In-process `importlib.reload()` is rejected for four structural reasons:
1. **Cannot safely reload C/COM/greenlet extensions:** `playwright` Node drivers, greenlet thread affinity, `comtypes` generated interfaces, and Win32 DLL/overlay threads (`desktop_cursor_overlay`, `takeover_guard`) hold native state that corrupts or leaks on partial module re-execution.
2. **Stale closure & object graphs:** Existing `SessionManager`, `_SessionWorker`, `FastMCP` tool closures, module globals (`_EPHEMERAL_HMAC_KEY`, `_revision`), and `atexit` callbacks remain bound to pre-reload classes/functions, causing mixed-version `isinstance` bugs.
3. **Zero syntax-error resilience:** A single syntax or import error in an edited module leaves `sys.modules` partially torn or crashes the MCP process outright, severing client stdio.
4. **Hard process boundary solves cleanup cleanly:** Spawning fresh OS child processes guarantees clean Python imports, isolated memory/COM state, and reliable tree termination.

---

## 3. Supervisor Architecture (`src/computer_use_lite/supervisor.py`)

- **Thin stdlib-only entry point (`python -u -m computer_use_lite.supervisor`):** Imports **only Python standard library modules** (zero imports from `computer_use_lite.*` engine modules), so it never needs reloading on engine changes.
- **Hard Limitation (Supervisor Self-Update):** The supervisor **cannot reload itself** (`supervisor.py`). Editing `supervisor.py` still requires restarting the host MCP client.
- **Windows Binary Stdio Framing & Threading:**
  - Operates exclusively on `sys.stdin.buffer` / `sys.stdout.buffer` with explicit UTF-8 encoding and `.flush()` after every frame (preventing Windows text-mode `\r\n` and code-page corruption).
  - Never uses `select` on pipes (unsupported on Windows); uses dedicated daemon reader threads for client stdin and child stdout.
  - Serializes every write to client stdout via `_client_write_lock` so interleaved frames cannot corrupt JSON lines.
  - Routes all diagnostics strictly to `sys.stderr.buffer`; child `stderr` inherits/relays cleanly to supervisor `stderr`.
  - Spawns child via `[sys.executable, "-B", "-u", "-m", child_module, *child_args]` (`-c` bootstrap for LKG) with `PYTHONDONTWRITEBYTECODE=1` and an isolated empty per-supervisor `PYTHONPYCACHEPREFIX` so rapid same-second/same-size edits cannot accidentally load stale workspace `__pycache__/*.pyc` bytecode, alongside `CREATE_NEW_PROCESS_GROUP` + Win32 Job Object on Windows (`start_new_session=True` + process group signal on POSIX).
- **Generation Tracking:** Monotonic `_generation` counter tags every child instance and reader thread; output from superseded child generations is discarded.

---

## 4. Reload Triggers, Handshake Replay & Crash Safety

1. **Primary Trigger — Synthetic `cul_reload` Tool:**
   - Supervisor intercepts child `tools/list` responses and injects `cul_reload(reason?: string)` cleanly (ensuring no duplicate name).
   - When the client calls `cul_reload`, supervisor acquires `_swap_lock`, fails any already in-flight requests on the old child with JSON-RPC `-32603` (`"server reloaded, retry"`), and pre-spawns the new child generation + runs internal handshake **before** killing the old child:
     - Sends internal `initialize` (using cached client `initialize` params under synthetic id `"__cul_sup_init_<gen>"`, never forwarded to client).
     - Waits for child `initialize` response, sends cached `notifications/initialized`.
   - **If new child passes boot & handshake:** Swaps active generation to the pre-booted child, updates the temporary LKG snapshot, gracefully shuts down the old child (`stdin.close()` -> `5s` grace -> `TerminateJobObject` / `kill`) so Chrome/overlay handles are already closed before the caller proceeds, writes the `cul_reload` success result to client stdout, and emits `notifications/tools/list_changed` before releasing `_swap_lock`.
   - **Optional Secondary Trigger (`--watch DIR`):** Off by default to avoid mid-edit partial-save races; when explicitly enabled, polls `.py` mtimes with `0.6s` debounce and calls the same swap pipeline.

2. **Blocking Client Forwarding During Swap & In-Flight Request Handling:**
   - Normal requests from client stdin acquire `_swap_lock` so new client requests serialize cleanly around swaps rather than landing on a closing pipe.
   - Any requests already dispatched to the superseded child (`_pending_requests`) receive immediate JSON-RPC error `{"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": "server reloaded, retry"}}` so clients never hang on a dropped ID.

3. **Crash-Loop Backoff, Fast Error & Non-Destructive LKG Rollback:**
   - Whenever a candidate child or running child dies / fails handshake, supervisor captures its recent `stderr` lines, enters backoff state (`0.5s`, doubling up to `30.0s`, resetting after `10.0s` continuous healthy uptime), and answers normal incoming client requests immediately with `-32603` fast errors instead of hanging.
   - Calling `cul_reload` bypasses wait timers immediately once the agent fixes broken code.
   - **Non-Destructive Last-Known-Good (LKG) Snapshot Rollback (`--rollback-after N`, default `3` consecutive failed starts; `0` disables):** Whenever a child completes healthy initialization from a local `computer_use_lite` package dir, supervisor caches a clean temp copy `_lkg_root` without modifying workspace files. If `N` consecutive start attempts crash, supervisor boots the LKG snapshot by prepending `_lkg_root` inside the child invocation (while keeping working directory intact) and reports `"rolled_back": true` + the broken-edit error in `cul_reload` / status messages until fixed code succeeds on the next `cul_reload`.

4. **Client EOF & Clean Exit:**
   - Client EOF on supervisor stdin triggers graceful EOF teardown (`stdin.close()` -> `5s` -> kill/Job cleanup) and exits `0`.

5. **Clients Ignoring `notifications/tools/list_changed`:**
   - Some MCP clients cache initial `tools/list` and ignore `notifications/tools/list_changed`. Because `cul_reload` still returns `{ok, reloaded, generation, old_pid, new_pid, rolled_back, state_reset_warning}` and `tools/call` routes dynamically by tool name through the new child, existing tools invoke new implementations immediately; clients that ignore `list_changed` only miss newly added tool schemas unless the agent or user triggers a manual tool refresh.

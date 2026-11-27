# Windows MCP Setup: Codex, Antigravity, and Claude Code

This guide installs the Computer Use Lite (CUL) MCP server from this checkout and registers it with **Codex**, **Google Antigravity**, and **Claude Code**. The supplied installer uses a virtual environment inside the repository and merges only the `computer_use_lite` server entry into each user's configuration.

> **Safety:** CUL is experimental software. Its Windows Desktop UIA tools can operate applications in the interactive Windows session. Connect it only to an agent and desktop session you trust. The installer only installs dependencies and writes MCP configuration; it does not launch the server, open applications, or perform desktop actions.

## Requirements

- Windows 10 or 11, with an interactive Windows session for desktop UIA use.
- Native Windows Python 3.10 or newer. Python from WSL is not supported for the desktop backend.
- The repository checked out locally.
- Network access for pip to download missing packages.
- PowerShell, included with Windows.

The project's runtime dependencies include Playwright, Pillow, websockets, MCP, and Windows UI Automation packages. The installer uses the `setup` extra for its TOML-preserving Codex config editor. It does **not** install Playwright browser binaries; these are only needed for CUL's browser tools, not to connect or use Windows Desktop UIA.

## Quick setup

1. Close or save any editor changes to the MCP configs. The installer creates backups before changing an existing config.
2. From the repository root, double-click `scripts\setup_mcp_windows.bat`, or run it from Command Prompt:

   ```bat
   scripts\setup_mcp_windows.bat
   ```

3. Let setup finish. It creates `.venv` if needed, installs the project editable into it, and registers the server with all three clients.
4. Refresh/restart the server in each client as described below.
5. Confirm each client reports `computer_use_lite` connected and exposes the expected tools.

The setup can be run again. It updates the same server entry without adding duplicates. If the existing entry differs, it is replaced; other MCP servers and unrelated settings are retained.

## What the installer configures

The server uses the repository's `.venv\Scripts\python.exe` and launches by default via the thin stdlib reload supervisor:

```text
-u -m computer_use_lite.supervisor
```

The supervisor owns the MCP `stdio` pipe to the client, runs `python -u -m computer_use_lite.mcp_server` as a restartable child process (in a Win32 Job Object on Windows), and adds a `cul_reload` tool so an agent can reload edited server code mid-session without restarting Codex, Antigravity, or Claude Code. Pass `--direct` to `scripts/configure_mcp.py` if you specifically want `-u -m computer_use_lite.mcp_server` without the supervisor.

It sets `cwd` to this repository, `PYTHONPATH` to its `src` directory, and `PYTHONUNBUFFERED=1`.

| Client | User config file | How to reload |
| --- | --- | --- |
| Codex | `%CODEX_HOME%\config.toml` when `CODEX_HOME` is set; otherwise `%USERPROFILE%\.codex\config.toml` | In Codex, open **Settings > MCP Servers** and restart/reload `computer_use_lite`. If it does not appear, restart Codex and open a fresh chat. |
| Antigravity App / IDE / CLI | `%USERPROFILE%\.gemini\config\mcp_config.json` | In the app, use **Customizations > Installed > MCP Servers** and refresh/restart the server. In the IDE, use the agent panel's **MCP Servers** manager. In the CLI, open `/mcp` and reload/check the server. |
| Claude Code | `%CLAUDE_CONFIG_DIR%\.claude.json` when `CLAUDE_CONFIG_DIR` is set; otherwise `%USERPROFILE%\.claude.json` | Run `claude mcp list`, or open Claude Code and use `/mcp`. Start a new session if it was already running during setup. |

Codex's `CODEX_HOME` override is honored. Antigravity's file is its global user configuration; Antigravity also supports workspace-level MCP config, but this installer intentionally configures the global file so it is available across workspaces.
Claude Code is configured at user scope so it is available across projects. A Claude Code local or project server with the same name can take precedence over this user-scope entry.

### Manual configuration reference

The installer writes equivalent entries using the real repository and venv paths. If you configure the clients manually, replace `<REPO>` with the absolute checkout path. Use TOML single-quoted Windows paths for Codex and JSON-escaped backslashes for Antigravity and Claude Code.

Codex `config.toml`:

```toml
[mcp_servers.computer_use_lite]
command = '<REPO>\.venv\Scripts\python.exe'
args = ["-u", "-m", "computer_use_lite.supervisor"]
cwd = '<REPO>'
enabled = true
required = true
startup_timeout_sec = 30
env = { PYTHONPATH = '<REPO>\src', PYTHONUNBUFFERED = '1' }
```

Antigravity `mcp_config.json` entry under the existing top-level `mcpServers` object:

```json
{
  "computer_use_lite": {
    "command": "<REPO>\\\\.venv\\\\Scripts\\\\python.exe",
    "args": ["-u", "-m", "computer_use_lite.supervisor"],
    "cwd": "<REPO>",
    "env": {
      "PYTHONPATH": "<REPO>\\\\src",
      "PYTHONUNBUFFERED": "1"
    }
  }
}
```

When editing manually, merge the entry into the existing server map; do not replace the complete config file.

Claude Code stores user-scope MCP servers in the root `mcpServers` object in `.claude.json`:

```json
{
  "mcpServers": {
    "computer_use_lite": {
      "type": "stdio",
      "command": "<REPO>\\\\.venv\\\\Scripts\\\\python.exe",
      "args": ["-u", "-m", "computer_use_lite.supervisor"],
      "env": {
        "PYTHONPATH": "<REPO>\\\\src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

The installer preserves other root values and server entries in this file too.

## Backups and safe behavior

- Existing config files are backed up beside the original as `config.toml.bak-<timestamp>`, `mcp_config.json.bak-<timestamp>`, and `.claude.json.bak-<timestamp>` before replacement.
- A first-time config file has no pre-existing file to back up.
- If a config already contains `computer_use_lite`, only that server's settings are updated.
- Other Codex TOML settings/comments and unrelated Antigravity/Claude Code MCP entries are preserved.
- Invalid TOML/JSON, or an invalid `mcp_servers` / `mcpServers` value, stops setup with an error instead of overwriting it.
- The helper validates all three configs before writing. Writes are staged atomically; if a later write fails after an earlier one succeeded, earlier configs are rolled back.
- No global Python packages are installed, no Codex sandbox settings are changed, and no application is launched.

## Verify the installation

### Check the server process contract

Open Command Prompt in the repository and run:

```bat
.venv\Scripts\python.exe -u -m computer_use_lite.supervisor
```

This command is an MCP stdio server (via the reload supervisor): it waits for a client and is not intended to be tested by typing into its terminal. Press `Ctrl+C` to stop this manual process before reconnecting clients. Normally the MCP client starts it automatically.

### Check Codex

After reload/restart, open a new chat and inspect the connected MCP tool catalog. It should list `computer_use_lite` tools, including `list_desktop_windows`, `open_desktop`, `discover`, `act`, `press_key`, and `cul_reload`.

### Check Antigravity

Open the MCP manager and verify the server is connected. Antigravity may lazy-load MCP tool schemas; confirm the server's tool list in its manager if the tools are not all visible in the initial agent prompt.

### Check Claude Code

Run `claude mcp list` to check the server status, then use `/mcp` in an interactive session to inspect available tools. If the project defines a local or project MCP server with this same name, Claude Code can use that higher-priority definition instead.

When launched through `computer_use_lite.supervisor`, the server exposes `16` tools (`15` core automation tools: `open_browser`, `list_desktop_windows`, `open_desktop`, `close_session`, `list_sessions`, `discover`, `inspect`, `act`, `hover`, `navigate`, `scroll`, `press_key`, `click_at`, `drag_at`, and `type_text`, plus `cul_reload`). Launching `computer_use_lite.mcp_server` directly (`--direct`) exposes the `15` core tools without `cul_reload`.

## Hot-reloading edits mid-session (`cul_reload`)

- **Trigger:** Call `cul_reload` after editing files under `src/computer_use_lite/`. The supervisor pre-boots and MCP-handshakes a fresh child process before shutting down the previous child (via `close_all()`, stdin EOF, and Win32 Job Object cleanup) and updates a non-destructive last-known-good (`LKG`) snapshot in a temporary directory.
- **Session state is intentionally reset:** All open browser/desktop `SESSION:*` IDs, `eN`/`REV` element handles, CDP connections, Chrome children, and active cursor overlays belong to the old child process and are terminated cleanly. Call `open_browser` or `open_desktop` again after `cul_reload`.
- **Broken edits:** If your edited code raises an import or `SyntaxError` during child startup, the supervisor stays alive, returns a JSON-RPC error instead of crashing the client pipe, retries with exponential backoff, and (after `--rollback-after` consecutive failed starts, default `3`) serves the temporary `LKG` snapshot in-memory/via `sys.path` without overwriting your edited workspace files.
- **Self-update & client schema limits:** Edits to `src/computer_use_lite/supervisor.py` itself cannot hot-reload and still require restarting/refreshing the MCP server in the client. The supervisor emits `notifications/tools/list_changed` on reload; whether a host client dynamically refreshes newly added tool schemas depends on that client (`cul_reload` and the `15` core schemas remain callable regardless). See [MCP Supervisor Reload Architecture](architecture/MCP_SUPERVISOR_RELOAD.md).

## Troubleshooting

### Python was not found or the wrong Python was selected

Install native Windows Python 3.10+ and ensure the Python Launcher (`py`) or `python` is on `PATH`. Re-run the installer. It rejects non-Windows Python such as WSL Python.

### `pip install` fails

Check network access and retry setup. The venv is local to the repository; the installer does not fall back to a global environment. To recreate a broken venv, close clients using this server, remove the repository's `.venv` directory yourself, and rerun the installer.

### A config parse or merge error appears

The installer leaves config files untouched if validation fails. Fix malformed TOML/JSON manually, or restore from the backup beside the file if you need to undo a successful change. Then rerun setup.

### The server is configured but tools are missing

Confirm the client is using the expected user profile, reload/restart MCP servers, and start a fresh session. Check that `.venv\Scripts\python.exe` still exists. In Codex, inspect the active `CODEX_HOME` if one is set. In Antigravity, open its MCP manager and inspect connection diagnostics. In Claude Code, run `claude mcp get computer_use_lite` and inspect `/mcp`; check for a higher-priority project/local entry with the same name.

### Windows UIA reports no desktop or target windows

Make sure Windows is unlocked and the target app is visible in the same interactive session. CUL cannot control desktop UIA applications from WSL, a service-only session, or a disconnected desktop. The browser MCP tools may still work independently.

## Uninstall / remove the registration

Disable or remove `computer_use_lite` through each client's MCP manager, or edit the matching server entry in the config file. Claude Code supports `claude mcp remove --scope user computer_use_lite`. Do not delete an entire config file if it contains other settings or servers. To remove only the local Python environment after all clients are disconnected, delete this repository's `.venv` directory.

## References

- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Google Antigravity MCP documentation](https://antigravity.google/docs/mcp)
- [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp)
- [Computer Use Lite README](../README.md)

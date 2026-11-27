# Repair Dependency Graph

```mermaid
flowchart TD
    B0[Frozen Baseline: de27b49 / 0d19a9e] --> C_G[CUL-CUR-007: Canvas Overlay Exclusion]
    B0 --> C_AB[CUL-CUR-001..006: Cursor Fixes A-F]
    C_G --> C_THEORY[CUL-CUR-008: GetCursorInfo Empirical Probe]
    C_AB --> C_THEORY
    C_THEORY --> C_ANIM[CUL-CUR-009: Section 4 Spring + Morph + Reduced Motion]
    C_ANIM --> C_GLOW[CUL-CUR-010: Section 5 CUL_TAKEOVER_GLOW=1]

    C_GLOW --> P0_PRIV[CUL-PRIV-001 / 002: Shared Redaction + No Secret Hashes]
    C_GLOW --> P0_ACC1[CUL-ACC-001: Cross-Frame + OOPIF Overlay Hit-Test]
    P0_ACC1 --> P0_ACC2[CUL-ACC-002: Truthful verified Semantics]
    C_GLOW --> P0_SEC1[CUL-SEC-001: DNS Fail-Closed + Fetch SSRF]
    C_GLOW --> P0_SEC2[CUL-SEC-002: DirectCdpClient Default Off]

    P0_ACC2 --> P1_WIN[P1 Windows Safety: SEC-003/004, DESK-001..005]
    P0_SEC1 --> P1_WIN
    P0_SEC2 --> P1_WIN

    P1_WIN --> P2_PORT[CUL-DX-001: Lazy Win32 Imports]
    P2_PORT --> P2_DEPS[CUL-DX-002 + SEC-005: Dev Deps, Lockfile, Untrusted Markers]
    P2_DEPS --> P3_PERF[CUL-ACC-003 + CUL-PERF-001: AX State, Date, Sticky Header, Drag, ReadText, Session Eviction]
```

## Explicit Conflict Resolutions
1. **`CUL-SEC-002` (`CUL_MCP_DIRECT_WS=0`) vs Latency:** Keeping Playwright `CDPSession` default prioritizes local security; `CUL_MCP_DIRECT_WS=1` remains selectable for controlled benchmark/opt-in measurements (`Exp 7` tradeoff documented).
2. **Additive P3 Features (`drag`, `read_page`) vs `test_mcp_tool_roster_annotations_and_browser_workflow`:** Rather than breaking clients expecting the exact 13-tool MCP roster (`open_browser`, ..., `click_at`), expose `drag` via `act(..., action="drag", ...)` and static text via `discover(..., include_static_text=True)` + Python `Api.drag()` / `Api.read_page()`. Zero breaking schema churn!
3. **`CUL-CUR-008` (`GetCursorInfo`) Conditional Fix:** We only touch Win32 cursor hiding (`ShowCursor` / cursor blanking) if the empirical Win11 log proves the real cursor flashes/overrides during `SendInput`.

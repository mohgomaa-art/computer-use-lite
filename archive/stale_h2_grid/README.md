# STALE / INVALIDATED — Pre-Audit H2 Grid Scan (`2026-11-24T20:11–20:32`)

> [!WARNING]
> **DO NOT CITE OR TREAT AS VALID.** The files in this directory (`h2_probes.json`, `h2_report.md`) come from an invalidated pre-fix run of the H2 desktop grid probe and are preserved strictly as negative/historical evidence.

## Why these artifacts are invalidated
1. **Coordinate origin offset (`87` px):** The probe computed canvas origin from the top-level window `ClientToScreen` (`[28, 20]`) rather than `Chrome_RenderWidgetHostHWND` (`[28, 107]`), shifting coordinates into browser tab/omnibox chrome.
2. **Incomplete latency calibration:** Only `[5, 15, 30, 50]` ms were swept against `50 ms` without randomized point ordering.
3. **Current status:** Gate 0 was subsequently fixed and passed on `Default` desktop (`results/experiments/h2_gate0.json`, `[28, 107]`, `[2..120]` ms sweep, `settle_ms = 50`). No post-fix Grid Scan has been executed; H2 desktop cursor probing remains **DROPPED / HOLD** (not shipped in engine code).

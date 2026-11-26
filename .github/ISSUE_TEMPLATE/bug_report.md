---
name: Bug Report
about: Report a reproducible bug, perception mismatch, or Windows UIA / CDP failure in Computer Use Lite
title: "[Bug]: "
labels: ["bug"]
---

## Environment
- **Commit SHA / Version:** (e.g. `v0.1.0-alpha` or `git rev-parse --short HEAD`)
- **Operating System:** (e.g. Windows 11 Build `26200`)
- **Python Version:** (e.g. `3.12.10`)
- **Playwright / Chromium Version:** (e.g. `playwright 1.64.0`)
- **Surface Affected:** [Browser CDP / Windows UIA Desktop / MCP Server / Benchmarks / Tests]
- **Environment Flags:** (`CUL_SKIP_DESKTOP`, `CUL_MCP_ALLOW_PRIVATE_URLS`, etc.)

## Expected vs. Observed Behavior
Describe clearly what happened and what you expected. Distinguish **observed tool/test output** from hypotheses.

## Minimal Reproduction Steps
1. Command or short snippet to run
2. Redacted output or traceback

> **Privacy Reminder:** Before pasting screenshots, window titles, or logs, ensure local usernames, user directory paths, credentials, and private desktop windows are removed.

## Verification Checklist
- [ ] Tested against current clean `HEAD` (no stale background MCP process)
- [ ] Checked [docs/KNOWN_LIMITATIONS.md](../../docs/KNOWN_LIMITATIONS.md) and [SECURITY.md](../../SECURITY.md)

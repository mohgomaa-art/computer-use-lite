# Archive Index

This folder preserves historical, invalidated, or ephemeral artifacts instead of deleting them:

- `stale_h2_grid/` — Pre-fix H2 Grid Scan artifacts (`2026-11-24T20:11–20:32`). **STALE / INVALIDATED** due to the `(0, 87)` px browser-chrome offset bug and incomplete settle sweep (`[5, 15, 30, 50]` ms without randomized ordering).
- `screenshots/` *(gitignored locally)* — Raw PNG captures, overlays, and image crops kept out of version control because several browser screenshots display local filesystem `file:///<HOME>/...` paths in the Chrome address bar or exceed binary size guidelines.
- `runtime_state/` *(gitignored locally)* — Ephemeral `task_state*.json` logs generated during prior test runs.

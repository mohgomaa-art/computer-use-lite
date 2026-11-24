# Real-Application Benchmarks (Phase D)

Baseline 1280x720 screenshot: **1229 tokens**.

## Browser targets

| target | elements | blind regions | latency | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
| fixture (fixture) | 4 | 0 | 17.4 ms | 54.2 (0.04x) | 54.2 (0.04x) |
| GitHub Trending (real) | 120 | 0 | 292.2 ms | 654.0 (0.53x) | 1263.8 (1.03x) |
| YouTube (real) | 27 | 0 | 143.7 ms | 386.8 (0.31x) | 386.8 (0.31x) |
| Gmail (real) | 14 | 0 | 75.8 ms | 187.2 (0.15x) | 187.2 (0.15x) |
| Google Maps (real_canvas) | 64 | 1 | 210.5 ms | 697.8 (0.57x) | 719.5 (0.59x) |

## Windows desktop targets

| target | elements | blind regions | latency (ms) | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
| Notepad (Win11) | 25 | 0 | 82.8 | 307.0 (0.25x) | 307.0 (0.25x) |
| File Explorer | 90 | 0 | 188.0 | 712.0 (0.58x) | 1036.5 (0.84x) |
| Chromium shell (before a11y trigger) | 14 | - | - | - (-x) | - (-x) |
| Chromium shell (after B13 WM_GETOBJECT) | 18 | 0 | 26.7 | 194.5 (0.16x) | 194.5 (0.16x) |
| Chromium shell (--force-renderer-accessibility) | 18 | 0 | 39.3 | 194.5 (0.16x) | 194.5 (0.16x) |

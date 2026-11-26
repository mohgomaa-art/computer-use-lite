# Real-Application Benchmarks (Phase D)

Baseline 1280x720 screenshot: **1229 tokens**.

## Browser targets

| target | elements | blind regions | latency | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
| fixture (fixture) | 4 | 0 | 17.8 ms | 54.2 (0.04x) | 54.2 (0.04x) |
| GitHub Trending (real) | 120 | 0 | 215.5 ms | 654.0 (0.53x) | 1263.8 (1.03x) |
| YouTube (real) | 27 | 0 | 125.2 ms | 386.8 (0.31x) | 386.8 (0.31x) |
| Gmail (real) | 14 | 0 | 54.8 ms | 187.2 (0.15x) | 187.2 (0.15x) |
| Google Maps (real_canvas) | 64 | 1 | 273.2 ms | 690.8 (0.56x) | 712.5 (0.58x) |

## Windows desktop targets

| target | elements | blind regions | latency (ms) | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
| Notepad (Win11) | 36 | 0 | 140.2 | 474.8 (0.39x) | 474.8 (0.39x) |
| File Explorer | 140 | 0 | 387.7 | 711.0 (0.58x) | 1611.0 (1.31x) |
| Chromium shell (before a11y trigger) | 14 | - | - | - (-x) | - (-x) |
| Chromium shell (after B13 WM_GETOBJECT) | 18 | 0 | 76.1 | 194.5 (0.16x) | 194.5 (0.16x) |
| Chromium shell (--force-renderer-accessibility) | 18 | 0 | 62.8 | 194.5 (0.16x) | 194.5 (0.16x) |

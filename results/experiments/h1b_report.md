# H1b — Latency & Clustering Reality Check

- **Target:** `https://www.google.com/maps/@40.7580,-73.9855,17z`
- **Grid:** 880 points at step 32 px over 1280x720
- **H1_PRACTICAL:** **SIGNAL-ONLY**

## Latency

| mode | ms/probe | duration | pointer hits (distinct) | raw pointer probes | agreement vs rAF |
| --- | --- | --- | --- | --- | --- |
| raf | 33.40 | 29.39 s | 198 | 198 | baseline |
| sync | 16.97 | 14.93 s | 198 | 198 | 100.0% |
| yield2 | 22.55 | 19.84 s | 198 | 198 | 100.0% |
| pipe_20 | 1.02 | 0.90 s | 197 | 197 | 33.5% |
| pipe_80 | 0.87 | 0.77 s | 189 | 189 | 34.4% |

Agreement against the single-rAF baseline (Jaccard over pointer hit coordinates, rounded to 1 px):

| comparison | agreement | agreement >= 90% | duration < 3.0 s |
| --- | --- | --- | --- |
| sync vs rAF (1 frame) | 100.0% | yes | no |
| yield2 vs rAF (1 frame) | 100.0% | yes | no |
| pipe_20 vs rAF (1 frame) | 33.5% | no | yes |
| pipe_80 vs rAF (1 frame) | 34.4% | no | yes |

Fastest mode meeting the >= 90% agreement gate: **sync** at **14.93 s** (16.97 ms/probe) (gate: < 3.0 s).
Fastest pipelined mode (pipe_80): **0.77 s**,
agreement **34.4%** (fails agreement gate).

## Clustering

- Distinct pointer regions at radius 1.5 x step: **29** (from 198 distinct hits)
- Unlabeled region list: **~290 tokens** (29 x ~10)
- 1 viewport screenshot: **~1229 tokens**

## Gate

| gate | result |
| --- | --- |
| Hit agreement >= 90% | PASS |
| Full-viewport scan < 3.0 s (with >= 90% agreement) | REJECTED |
| **H1_PRACTICAL** | **SIGNAL-ONLY** |

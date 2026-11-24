# H1 — Browser Canvas Virtual Cursor Probe

- **Target:** `https://www.google.com/maps/@40.7580,-73.9855,17z`
- **Status:** SCORED - autonomous reviewer, see Review Scorecard below (H1_SIGNAL = PASS, H1_PRACTICAL = REJECTED)
- **Rule:** the script itself computes no verdict; the scorecard was filled by the agent reviewer from `h1_overlay.png`, not asserted by the probe code.

## Metrics

| Metric | Value |
| --- | --- |
| Viewport | 1280x720 |
| Grid step | 32 px |
| Canvas rect (viewport-clipped) | x=0 y=0 w=1280 h=720 |
| Readiness | canvas + paint settled after 664 ms, paint stable: yes (--wait 3500 ms) |
| Total probes | 880 |
| Total duration | 29.5 s (29457.6 ms) |
| Average per probe | 33.5 ms |
| DOM/AX baseline elements (viewport) | 175 |
| DOM/AX baseline elements overlapping canvas | 175 |
| `pointer` hits (clickable) | 192 |
| `text` / I-beam hits (not clickable) | 8 |
| `pointer` hits whose hovered node is the `<canvas>` itself | 114 |
| Distinct `pointer` regions after clustering (radius 1.5 x step) | 30 |
| Cursor mismatches (hovered vs canvas) | 109 |

## Cursor distribution

| cursor | count | counted as clickable |
| --- | --- | --- |
| `auto` | 675 | no |
| `pointer` | 192 | yes |
| `text` | 8 | no |
| `default` | 4 | no |
| `grab` | 1 | no |

## Top hovered tags

| tag | probes |
| --- | --- |
| `CANVAS` | 703 |
| `DIV` | 97 |
| `BUTTON` | 31 |
| `H1` | 24 |
| `A` | 8 |
| `INPUT` | 8 |
| `SPAN` | 6 |
| `LI` | 2 |

## Token cost estimate

Probing does not emit the raw grid to a model: adjacent hits are spatially clustered first and
only the regions travel. Each region carries a bounding box and centroid but **no semantic
label** — unlike a DOM/AX row (role + name + bbox) or a screenshot, where the model reads the
label off the pixels itself.

| Representation | Estimated tokens |
| --- | --- |
| DOM/AX element list (175 elements x ~18 tokens) | ~3150 |
| Clustered probe regions (30 regions x ~10 tokens, unlabeled) | ~300 |
| Raw grid points (880 points x ~4 tokens) — *not emitted, upper bound only* | ~3520 |
| 1 viewport screenshot (1280x720) | ~1229 |

## Probe regions (clustered)

| # | probes | box (x,y,w,h) | centroid | tags |
| --- | --- | --- | --- | --- |
| 1 | 42 | 816,16,448,320 | 1120,180 | BUTTON, CANVAS, DIV, IMG, SPAN |
| 2 | 38 | 48,16,544,64 | 341,42 | A, BUTTON, CANVAS, DIV |
| 3 | 17 | 1104,560,160,128 | 1181,643 | BUTTON, CANVAS, DIV, SPAN |
| 4 | 12 | 496,528,160,96 | 595,584 | CANVAS |
| 5 | 11 | 752,16,128,64 | 810,42 | A, BUTTON, CANVAS, SPAN |
| 6 | 10 | 48,592,160,96 | 102,656 | CANVAS, DIV |
| 7 | 8 | 176,464,160,32 | 256,480 | CANVAS |
| 8 | 6 | 240,208,128,32 | 315,213 | CANVAS |
| 9 | 5 | 816,432,128,0 | 880,432 | CANVAS |
| 10 | 5 | 368,656,96,32 | 426,682 | CANVAS |
| 11 | 4 | 656,16,32,32 | 672,32 | BUTTON, DIV |
| 12 | 4 | 80,176,96,0 | 128,176 | CANVAS |
| 13 | 4 | 560,240,96,0 | 608,240 | CANVAS |
| 14 | 3 | 688,304,64,0 | 720,304 | CANVAS |
| 15 | 3 | 560,336,64,0 | 592,336 | CANVAS |
| 16 | 3 | 464,464,64,0 | 496,464 | CANVAS |
| 17 | 2 | 624,176,32,0 | 640,176 | CANVAS |
| 18 | 2 | 176,368,32,0 | 192,368 | CANVAS |
| 19 | 2 | 1040,368,32,0 | 1056,368 | CANVAS |
| 20 | 1 | 48,112,0,0 | 48,112 | CANVAS |
| 21 | 1 | 816,240,0,0 | 816,240 | CANVAS |
| 22 | 1 | 272,272,0,0 | 272,272 | CANVAS |
| 23 | 1 | 528,400,0,0 | 528,400 | CANVAS |
| 24 | 1 | 752,400,0,0 | 752,400 | CANVAS |
| 25 | 1 | 720,464,0,0 | 720,464 | CANVAS |
| 26 | 1 | 1104,496,0,0 | 1104,496 | CANVAS |
| 27 | 1 | 368,528,0,0 | 368,528 | CANVAS |
| 28 | 1 | 784,528,0,0 | 784,528 | CANVAS |
| 29 | 1 | 944,560,0,0 | 944,560 | CANVAS |
| 30 | 1 | 176,592,0,0 | 176,592 | CANVAS |

## Review Scorecard

Scored visually from `h1_overlay.png` plus four quadrant crops at 1.5x. Scoring scope: the 114
`pointer` hits whose hovered node was the `<canvas>` itself. Hits inside green DOM chrome boxes
(78 of the 192 pointer hits) were excluded. Conservative counting: a POI counted as TP only if a
red dot visibly landed on its label text or icon; a region counted as FP if any of its dots landed
on a road label, empty map space, or the DOM side panel despite the canvas tag.

| Metric | Value | Gate |
| --- | --- | --- |
| TP clickable controls / POIs hit | 36 |  |
| FP clusters (road labels / panel / empty map) | 8 |  |
| FN blind clickables with no red dot | 8 |  |
| Blind Recall (TP / (TP + FN)) | 36 / 44 = **81.8%** | >= 50% PASS |
| Precision (TP / (TP + FP)) | 36 / 44 = **81.8%** | >= 80% PASS |
| **H1_SIGNAL** | **PASS** |  |

Caveats recorded honestly:

- The right-hand Maps panel is DOM, yet ~6 of its dots came back tagged `CANVAS` from
  `elementFromPoint`; those are counted as FP above rather than explained away.
- TP and FP are mixed units (controls vs clusters) exactly as the gate defines them.
- Google Maps makes nearly every POI label clickable, which flatters precision: the cursor signal
  agrees with the authored CSS, so high precision here is weak evidence for other canvas surfaces.
- Recall is dominated by grid density: at step 32 a label spanning ~4 x 1 cells is missed ~1 time in 3.

## Latency verdict (see `h1b_report.md`)

| gate | measured | verdict |
| --- | --- | --- |
| Hit agreement >= 90% vs rAF | sync 100.0%, 2 ms yield 100.0% | PASS |
| Full-viewport scan < 3.0 s | 29.33 s for 880 points (33.33 ms/probe) | REJECTED |
| **H1_PRACTICAL** | | **REJECTED** |

Removing the rAF wait changed nothing: 33.4 / 33.33 / 33.33 ms per probe for rAF / sync / 2 ms
yield. The cost is the two CDP round trips per point, not the frame wait, so no settle-delay
tuning can bring a full-viewport scan under 3 s in the browser.

**Phase 1 verdict: H1_SIGNAL = PASS (81.8% recall / 81.8% precision), H1_PRACTICAL = REJECTED
(29.3 s scan).** Browser cursor probing finds real blind controls but is too slow to be the
default discovery path; Phase 2 tests whether the same signal is cheap on the Windows desktop,
where there is no CDP round trip.

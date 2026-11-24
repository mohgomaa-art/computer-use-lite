# H3 - Local Hover Visual Diff

> **Note:** Decision (`NOT RUN / SKIPPED`) stands, while the Gate 0/2B numbers quoted below (`26.7%`, `73.3%`, `53.3%`) reference the **pre-audit invalidated H2 baseline** (`archive/stale_h2_grid/`). See `results/experiments/h2_gate0.json` for updated Gate 0 measurements (`0.0%` UIA recall, `100.0%` HAND on clickable at `50 ms` settle).

- **Status:** **H3 = NOT RUN (SKIPPED)** - precondition not met.

## Why it was skipped

Step 3 is conditional: *"Execute only if H2 failed due to static IDC_ARROW on UIA-blind
desktop controls."* H2 did not fail that way.

Gate 0 measured, on the UIA-blind canvas window:

| observation | value |
| --- | --- |
| UIA recall on the blind surface | 26.7% (blind) |
| P(IDC_HAND or CUSTOM | clickable) | 73.3% |
| P(IDC_HAND or CUSTOM | dead space) | 0.0% |

So the blind surface **does** change the Windows cursor over its controls (IDC_HAND), and the
hover-visual-diff hypothesis exists only to cover the case where it does not. H2 was instead
rejected by the measurements it did produce:

| gate (H2 2B) | measured | verdict |
| --- | --- | --- |
| Blind Recall >= 50% | 53.3% (8 of 15 controls) | PASS |
| Precision >= 80% | 53.3% | FAIL |
| Scan duration < 5.0 s | 12.24 s for 240 points (51.0 ms/point) | FAIL |

Running H3 would therefore mean testing a fallback for a failure mode that was not observed,
against a layer whose sibling already missed the 5 s budget by 2.4x. Per the anti-overengineering
guardrail, the third probing layer was not built.

## What would justify it later

If a real UIA-blind app on this machine is found that returns a static arrow over its controls
(Gate 0 `P(HAND/CUSTOM | clickable) < 50%`), H3 becomes worth measuring: 48x48 px crop diff
around each hovered point against the clean pre-hover screenshot. Expect the same latency wall -
one screenshot per point is ~10-25 ms on its own, before any hover settle delay.

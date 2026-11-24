# [STALE / INVALIDATED] H2 - Windows Desktop Cursor Probe

> **STALE / INVALIDATED ARTIFACT (2026-11-24T20:32):** Superseded by audit fixes A2/A3 (`content_origin = [28, 107]`, `[2..120]` ms ordered+randomized Gate 0 sweep). Kept for historical provenance only; no post-fix Grid Scan has been executed. See `archive/stale_h2_grid/README.md`.

- **Target:** H2 canvas probe fixture - Google Chrome for Testing (real Chromium window painting a `<canvas>` app, probed through Win32 only)
- **Calibrated settle delay:** 50 ms (Gate 0: first delay with >= 95% agreement against 50 ms)
- **Verdict:** **H2 = REJECTED**

## Gate 0 (per-toolkit calibration)

| target | UIA recall | UIA nodes | P(HAND/CUSTOM abs clickable) | P(HAND/CUSTOM abs dead) | settle |
| --- | --- | --- | --- | --- | --- |
| canvas (Chromium) | 26.7% (blind) | 216 | 73.3% | 0.0% | 50 ms |
| notepad (Win32) | 100% | 144 | 0.0% | 0.0% | 5 ms |
| libreoffice (VCL) | 100% | 15 | 0.0% | 0.0% | 5 ms |

Gate 2A: the canvas target is UIA-blind, 73.3% of its clickable points return IDC_HAND, and no
dead point does -> **unlocked 2B**. Notepad and LibreOffice expose their controls to UIA and
return a static arrow over them, so cursor probing adds nothing there.

## Progressive scan

| budget | points | step | duration | ms/point | click hits | clusters | blind recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 84 | 76 | 4276.6 | 50.91 | 14 | 7 | 26.7% | 57.1% |
| 250 | 240 | 48 | 12237.0 | 50.99 | 56 | 15 | 53.3% | 53.3% |

Expansion stopped after a pass exceeded the 5.0 s budget.

## Accuracy on the 240-point pass

| Metric | Value | Gate |
| --- | --- | --- |
| TP controls hit (of 15) | 8 |  |
| FP clusters (not inside any control) | 7 |  |
| FN controls with no hit | 7 |  |
| Text fields found by IBEAM (never counted as clickable) | 1 |  |
| Blind Recall | 53.3% | >= 50% PASS |
| Precision | 53.3% | >= 80% FAIL |
| Scan duration | 12.24 s | < 5.0 s FAIL |

Overlay: `h2_overlay.png` (green = UIA boxes in the window, red = HAND/CUSTOM hits, blue = IBEAM).

**H2 = REJECTED.** The cursor signal is real on this surface, but a 240-point pass
already costs 12.24 s at the honest settle delay, and the accuracy gates
would need a denser grid, not a sparser one.

## Visual inspection of h2_overlay.png

Inspected: red HAND dots sit inside the canvas-drawn buttons in roughly a 4-per-row pattern,
blue IBEAM dots sit on the two text fields, and the green UIA boxes only wrap the browser's own
chrome (tab strip, omnibox, menu buttons) - no UIA box covers any canvas button.

Two honest caveats from that inspection:

- The crop origin sits ~87 px above the canvas, so the screenshot includes the tab strip and
  omnibox. Dots are drawn in the same coordinate frame as the crop, so their positions relative
  to the drawn buttons are still truthful; only the framing is off.
- Some IBEAM reads (34 of 240) exceed the ~9.6% of canvas area the text fields occupy, and a few
  HAND reads land just outside a button. Both are consistent with the 50 ms settle still being
  too short for every transition on a live Chromium window - which is itself the reason the
  latency gate cannot be met by tuning the delay down.

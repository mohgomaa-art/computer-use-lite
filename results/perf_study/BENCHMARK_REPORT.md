# Computer Use Lite - Isolated Performance & Accuracy Study

> [!NOTE]
> **Empirical Provenance & Caveats:** Pre-merge isolated A/B study (`2026-11-24`). Read [BENCHMARKS.md](../../docs/BENCHMARKS.md) and [RESEARCH_METHODOLOGY.md](../../docs/RESEARCH_METHODOLOGY.md) alongside this dataset for the disclosed `Exp 8` (`fsync=False`) confound and real-site `vs_control` scoring caveats.

Generated: 2026-11-24 23:09:02
Engine untouched SHA-256 verification: `True`

## 0. Methodology, Environment & Statistical Caveats

- **Host Hardware & OS:** Windows 11 (`10.0.26200-SP0`), 11th Gen Intel Core i5-11400F @ 2.60GHz (6C/12T), 15.84 GB RAM, Python 3.12.10, Playwright 1.64.0, comtypes 1.5.0.
- **Iteration Counts:** Exps 1-4 UIA (`n_cold=3, n_warm=20`, uncached `ElementFromHandle` `n_warm=30`); Exp 5 RemoteOps (`n_cold=3, n_warm=15`); Exp 6 Browser (`n_cold=1, n_warm=10` corpus / `n_cold=2, n_warm=10` real sites); Exp 7 Transport (`n_cold=2, n_warm=15`); Exp 8 Freshness (`n_cold=2, n_warm=15` browser / `n_cold=2, n_warm=10` Notepad).
- **Ground Truth (GT) Method:** Corpus states score against `extract_corpus_ground_truth()` (open/closed Shadow DOM + cross-origin OOPIF). Real-site rows in Exp 6 score against viewport-filtered `Control CDP` (`vs_control`) rather than an external manual corpus GT, so `Control CDP` precision/recall appears as `1.0000` by definition. Raw GitHub Trending `Control CDP` emits `629` total -> `160` viewport -> `120` deduplicated controls (including container wrappers).
- **Stale Safety Coverage (`safety_parity = 1.0`):** Covers all 6 adversarial browser failure modes (`stale_revision`, `modal_occluded`, `moved_gt_2px`, `disabled_dynamically`, `scrolled_out_of_viewport`, `removed_from_dom`) and both desktop cases (`stale_revision`, `moved_gt_2px`).
- **Noise Caveat:** Differences of `+-3-5 ms` on `p50` are within scheduling/layout noise. Direct WebSocket savings on small calls (`ping_scroll`) are `1.0-3.1 ms`; larger gains (`-98.2 ms` on GitHub) come from 1.1 MB Snapshot/AX JSON serialization.

## 1. Explicit KEEP / DROP / HOLD Decisions

| Exp | Candidate | Decision | Evidence |
| ---: | --- | --- | --- |
| 1 | Dedicated UIA MTA Worker vs STA + Cached HWND Root | **KEEP MTA Worker / DROP Cached HWND Root** | Cold-first max STA=861.063ms vs MTA=162.576ms (eliminates Notepad 446ms / Explorer 861ms cold STA init); mean warm p50: STA=65.94ms, MTA_Fresh=66.88ms, MTA_CachedRoot=69.69ms (parity=1.0). |
| 2 | CacheRequest Tuning (Minimal Props / No TextPattern / No Bounds N+1) | **DROP NoBounds+N+1; HOLD Minimal Props (DROP dropping BoundingRectangle)** | Mean p50: Control=65.94ms, DropTextPattern=69.76ms, MinimalProps=65.31ms, NoBounds+N+1=80.0ms (NoBounds+N+1 inflates IPC from 2-3 to 37-143 and adds +5-25ms). |
| 3 | ControlView vs Explicit RawView vs OrCondition Interactive Filter | **DROP RawView; HOLD OrCondition (Needs TabControl + Pattern Conditions)** | TreeFilter verified == ControlViewCondition by default (not RawView). Explicit RawView inflates Chrome 66->254 nodes (92.3ms) with prec=0.4043; OrCondition min recall=0.9615 (omits TabControl 50018 & pattern-only custom controls). |
| 4 | AutomationElementMode.None (Read-Only) + RuntimeId Re-acquire | **DROP for Interactive Actions (HOLD Read-Only Only)** | Read-only recall>=0.99=True, mean discovery p50=68.65ms vs MTA_Fresh=66.88ms (no discovery speedup), while per-action RuntimeId re-acquire adds +6.506-38.791ms. |
| 5 | Windows UIA Remote Operations (CoreAutomationRemoteOperation) | **HOLD (Experimental Same-Connection Batch Inspector; DROP for Full Subtree Discovery)** | K=30 homogeneous batch reads p50 (Std vs RemoteOp): [('chromium', 16.88, 8.95), ('electron', 25.12, 7.12)]; subtree walk recall=[('notepad', 0.0179), ('explorer', 0.4286), ('chromium', 0.0286), ('electron', 0.7143)] (RemoteOp::Navigate stops at child HWND / cross-process boundaries). |
| 6 | CDP Ablation (No N*getBoxModel) vs One-Call JS Extractor | **KEEP CDP Ablation; HOLD JS Extractor (Open-DOM Fast-Path Only, Never Alone)** | CDP Ablation cuts IPCs to 2 with real-site viewport recall=[1.0, 1.0, 1.0, 1.0] & Google Maps p50 106.211->79.67ms (Corpus initial IoU 0.8678->1.0). JS Extractor p50=24.034ms on GitHub, but real-site viewport recall=[0.3812, 0.641, 1.0, 0.6538] & corpus recall=[0.8235, 0.8421, 0.6, 1.0] (drops Closed Shadow DOM & OOPIF). |
| 7 | Direct Persistent CDP WebSocket (`websockets`) vs Playwright CDPSession | **KEEP** | Ping p50 (PW vs DirectWS): [('corpus_main', 1.831, 0.821), ('GitHub Trending', 1.852, 0.583), ('Google Maps', 3.635, 0.512)]; 2-call Snapshot+AX p50 (PW vs DirectWS): [('corpus_main', 12.969, 7.168), ('GitHub Trending', 220.309, 122.103), ('Google Maps', 59.151, 43.832)]. |
| 8 | Targeted Freshness Validation in execute_action() (Eliminate 2x Full Discover) | **KEEP** | Browser p50: 39.269ms -> 9.543ms (safety_parity=1.0); Desktop p50: 2094.347ms -> 2013.981ms (safety_parity=1.0, removes ~80ms UIA discover; ~2006ms floor is ValuePattern.SetValue). |
| 9 | MutationObserver + Runtime.addBinding Incremental Updates | **HOLD (Top-Frame Dirty-Flag Hint Only)** | Coalesced 500ms churn to 26 pushes (20 binding events, ~176-192 B), but top-frame observer coverage vs GT recall=0.8421 (failure={'closed_shadow_dom': 1, 'cross_origin_iframe': 2}: misses Closed Shadow DOM & OOPIF). |

## 2. UIA TreeFilter Verification & Desktop Experiments (Exps 1-4)

- `IUIAutomationCacheRequest.TreeFilter` default pointer == `ControlViewCondition`: `True`
- `IUIAutomationCacheRequest.TreeFilter` default pointer == `RawViewCondition`: `False`

| App | Variant | Cold (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Nodes | Interactive | CPU/iter (ms) | Recall | Prec |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notepad | Control (STA, Full Cache) | 446.033 | 50.171 | 54.346 | 57.077 | 50 | 26 | 17.969 | 1.0 | 1.0 |
| notepad | Exp1 MTA Fresh Root | 52.63 | 51.135 | 52.929 | 53.738 | 50 | 26 | 17.188 | 1.0 | 1.0 |
| notepad | Exp1 MTA Cached Root | 53.849 | 56.705 | 59.998 | 63.135 | 50 | 26 | 18.75 | 1.0 | 1.0 |
| notepad | Exp2 Drop TextPattern | 58.154 | 58.591 | 61.684 | 63.622 | 50 | 26 | 21.875 | 1.0 | 1.0 |
| notepad | Exp2 Minimal Props | 54.651 | 54.514 | 57.502 | 57.672 | 50 | 26 | 17.969 | 1.0 | 1.0 |
| notepad | Exp2 NoBounds + N+1 Live | 67.633 | 66.296 | 69.379 | 69.522 | 50 | 26 | 18.75 | 1.0 | 1.0 |
| notepad | Exp3 ControlView (True) | 58.709 | 57.398 | 61.929 | 63.435 | 50 | 26 | 10.938 | 1.0 | 1.0 |
| notepad | Exp3 Explicit RawView | 76.582 | 60.392 | 65.793 | 72.76 | 72 | 29 | 14.844 | 1.0 | 0.8966 |
| notepad | Exp3 OrCondition (Interactive) | 52.472 | 54.116 | 57.731 | 59.905 | 25 | 25 | 15.625 | 0.9615 | 1.0 |
| notepad | Exp4 ElementMode.None | 56.053 | 56.07 | 58.858 | 61.143 | 50 | 26 | 19.531 | 1.0 | 1.0 |
| explorer | Control (STA, Full Cache) | 861.063 | 160.86 | 173.985 | 175.621 | 140 | 79 | 41.406 | 1.0 | 1.0 |
| explorer | Exp1 MTA Fresh Root | 162.576 | 161.746 | 166.842 | 167.907 | 140 | 79 | 41.406 | 1.0 | 1.0 |
| explorer | Exp1 MTA Cached Root | 178.694 | 168.777 | 176.418 | 179.123 | 140 | 79 | 38.281 | 1.0 | 1.0 |
| explorer | Exp2 Drop TextPattern | 159.809 | 163.458 | 173.932 | 178.814 | 140 | 79 | 37.5 | 1.0 | 1.0 |
| explorer | Exp2 Minimal Props | 163.968 | 152.86 | 163.233 | 165.685 | 140 | 79 | 38.281 | 1.0 | 1.0 |
| explorer | Exp2 NoBounds + N+1 Live | 195.498 | 185.643 | 193.112 | 193.347 | 140 | 79 | 37.5 | 1.0 | 1.0 |
| explorer | Exp3 ControlView (True) | 153.276 | 167.866 | 179.949 | 180.568 | 140 | 79 | 41.406 | 1.0 | 1.0 |
| explorer | Exp3 Explicit RawView | 168.688 | 177.593 | 182.819 | 186.79 | 200 | 98 | 51.562 | 1.0 | 0.8142 |
| explorer | Exp3 OrCondition (Interactive) | 163.216 | 158.437 | 166.016 | 173.692 | 91 | 78 | 24.219 | 0.9891 | 1.0 |
| explorer | Exp4 ElementMode.None | 175.303 | 162.753 | 170.023 | 170.512 | 140 | 79 | 46.875 | 1.0 | 1.0 |
| chromium | Control (STA, Full Cache) | 65.283 | 33.354 | 38.483 | 38.937 | 66 | 33 | 14.062 | 1.0 | 1.0 |
| chromium | Exp1 MTA Fresh Root | 34.091 | 33.163 | 34.894 | 35.288 | 66 | 33 | 9.375 | 1.0 | 1.0 |
| chromium | Exp1 MTA Cached Root | 36.893 | 34.343 | 41.812 | 45.864 | 66 | 33 | 8.594 | 1.0 | 1.0 |
| chromium | Exp2 Drop TextPattern | 33.515 | 34.7 | 39.264 | 39.4 | 66 | 33 | 14.062 | 1.0 | 1.0 |
| chromium | Exp2 Minimal Props | 44.936 | 34.19 | 36.656 | 39.159 | 66 | 33 | 10.938 | 1.0 | 1.0 |
| chromium | Exp2 NoBounds + N+1 Live | 53.254 | 43.561 | 46.885 | 47.406 | 66 | 33 | 14.062 | 1.0 | 1.0 |
| chromium | Exp3 ControlView (True) | 39.469 | 36.382 | 41.747 | 44.531 | 66 | 33 | 12.5 | 1.0 | 1.0 |
| chromium | Exp3 Explicit RawView | 90.455 | 92.31 | 98.984 | 100.509 | 254 | 61 | 39.062 | 1.0 | 0.4043 |
| chromium | Exp3 OrCondition (Interactive) | 34.873 | 32.392 | 35.67 | 35.956 | 37 | 32 | 7.031 | 0.9737 | 1.0 |
| chromium | Exp4 ElementMode.None | 36.951 | 34.076 | 37.744 | 38.561 | 66 | 33 | 10.156 | 1.0 | 1.0 |
| electron | Control (STA, Full Cache) | 42.783 | 19.374 | 22.06 | 24.726 | 35 | 6 | 8.594 | 1.0 | 1.0 |
| electron | Exp1 MTA Fresh Root | 23.128 | 21.467 | 23.723 | 24.768 | 35 | 6 | 6.25 | 1.0 | 1.0 |
| electron | Exp1 MTA Cached Root | 24.79 | 18.936 | 21.98 | 22.319 | 35 | 6 | 4.688 | 1.0 | 1.0 |
| electron | Exp2 Drop TextPattern | 23.267 | 22.292 | 24.86 | 25.228 | 35 | 6 | 6.25 | 1.0 | 1.0 |
| electron | Exp2 Minimal Props | 23.257 | 19.694 | 20.807 | 21.032 | 35 | 6 | 7.031 | 1.0 | 1.0 |
| electron | Exp2 NoBounds + N+1 Live | 26.91 | 24.487 | 26.247 | 26.7 | 35 | 6 | 10.938 | 1.0 | 1.0 |
| electron | Exp3 ControlView (True) | 23.64 | 20.62 | 21.787 | 22.808 | 35 | 6 | 7.031 | 1.0 | 1.0 |
| electron | Exp3 Explicit RawView | 24.94 | 25.088 | 27.611 | 28.341 | 53 | 7 | 10.938 | 1.0 | 0.8571 |
| electron | Exp3 OrCondition (Interactive) | 17.539 | 14.024 | 15.869 | 16.301 | 6 | 6 | 4.688 | 1.0 | 1.0 |
| electron | Exp4 ElementMode.None | 27.795 | 21.686 | 23.487 | 23.983 | 35 | 6 | 10.938 | 1.0 | 1.0 |

## 3. UIA Remote Operations (Exp 5)

| App | FindAll p50 (ms) | RemoteWalk p50 (ms) | TopRoot Nodes | Walk Recall | Std COM K-Reads p50 (ms) | RemoteOp K-Batch p50 (ms) | K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notepad | 57.644 | 1.193 | 1/56 | 0.0179 | 1.091 | 1.01 | 1 |
| explorer | 206.887 | 37.937 | 80/140 | 0.4286 | 0.393 | 0.333 | 1 |
| chromium | 39.01 | 0.68 | 1/35 | 0.0286 | 16.875 | 8.952 | 30 |
| electron | 20.69 | 10.119 | 1/35 | 0.7143 | 25.122 | 7.125 | 30 |

## 4. Browser Discovery Accuracy & Latency (Exp 6)

| Target | Variant | Cold (ms) | p50 (ms) | p95 (ms) | Nodes | Bytes | Recall | Prec | RoleAcc | NameF1 | Miss Categories |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Corpus:initial_viewport | Control CDP | 33.264 | 25.068 | 35.905 | 21 | 59400 | 0.9412 | 0.8 | 0.9375 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:initial_viewport | Ablation CDP (no N*BoxModel) | 12.822 | 14.193 | 16.437 | 21 | 57622 | 0.9412 | 0.8 | 0.9375 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:initial_viewport | One-Call JS Extractor | 5.113 | 2.964 | 3.596 | 14 | 2373 | 0.8235 | 1.0 | 1.0 | 1.0 | {"closed_shadow_dom": 1, "cross_origin_iframe": 2} |
| Corpus:drawer_open | Control CDP | 21.634 | 24.83 | 25.945 | 23 | 63233 | 0.9474 | 0.8182 | 0.9444 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:drawer_open | Ablation CDP (no N*BoxModel) | 10.989 | 12.022 | 21.08 | 23 | 61455 | 0.9474 | 0.8182 | 0.9444 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:drawer_open | One-Call JS Extractor | 3.338 | 2.565 | 2.952 | 16 | 2700 | 0.8421 | 1.0 | 1.0 | 1.0 | {"closed_shadow_dom": 1, "cross_origin_iframe": 2} |
| Corpus:modal_occluded | Control CDP | 19.297 | 18.632 | 22.405 | 6 | 67015 | 0.8 | 0.8 | 0.75 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:modal_occluded | Ablation CDP (no N*BoxModel) | 11.569 | 12.441 | 13.76 | 6 | 66398 | 0.8 | 0.8 | 0.75 | 1.0 | {"cross_origin_iframe": 1} |
| Corpus:modal_occluded | One-Call JS Extractor | 3.053 | 2.088 | 2.987 | 3 | 564 | 0.6 | 1.0 | 1.0 | 1.0 | {"cross_origin_iframe": 2} |
| Corpus:scrolled_view | Control CDP | 26.149 | 24.068 | 33.144 | 23 | 63433 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| Corpus:scrolled_view | Ablation CDP (no N*BoxModel) | 10.414 | 14.113 | 16.01 | 23 | 61495 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| Corpus:scrolled_view | One-Call JS Extractor | 2.694 | 2.802 | 3.927 | 1 | 243 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| GitHub Trending | Control CDP | 381.432 | 373.034 | 438.53 | 629 | 1107180 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | {} |
| GitHub Trending | Ablation CDP (no N*BoxModel) | 347.018 | 351.655 | 381.145 | 629 | 1102788 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| GitHub Trending | One-Call JS Extractor | 42.676 | 24.034 | 29.169 | 68 | 10917 | 0.3812 | 0.8971 | 0.9508 | 0.765 | {"unknown": 99} |
| YouTube | Control CDP | 143.152 | 143.275 | 153.394 | 45 | 1371796 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | {} |
| YouTube | Ablation CDP (no N*BoxModel) | 213.977 | 139.835 | 167.109 | 45 | 1371796 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| YouTube | One-Call JS Extractor | 18.66 | 8.3 | 10.263 | 36 | 6171 | 0.641 | 0.6944 | 0.84 | 0.56 | {"unknown": 14} |
| Gmail sign-in | Control CDP | 17.832 | 10.697 | 12.554 | 2 | 13189 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | {} |
| Gmail sign-in | Ablation CDP (no N*BoxModel) | 5.874 | 6.216 | 6.497 | 2 | 13189 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| Gmail sign-in | One-Call JS Extractor | 3.756 | 1.738 | 3.365 | 2 | 389 | 1.0 | 1.0 | 1.0 | 0.5 | {} |
| Google Maps | Control CDP | 51.098 | 106.211 | 164.404 | 105 | 712979 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | {} |
| Google Maps | Ablation CDP (no N*BoxModel) | 83.228 | 79.67 | 89.817 | 105 | 732671 | 1.0 | 1.0 | 1.0 | 1.0 | {} |
| Google Maps | One-Call JS Extractor | 14.947 | 7.765 | 9.171 | 70 | 15347 | 0.6538 | 0.9714 | 0.9559 | 0.7097 | {"unknown": 36} |

## 5. Transport Comparison (Exp 7: Playwright CDP vs Direct WebSocket)

| Target | Payload | Playwright p50 / p95 (ms) | Direct WS p50 / p95 (ms) | Delta p50 (ms) |
| --- | --- | ---: | ---: | ---: |
| corpus_main | ping_scroll | 1.831 / 2.398 | 0.821 / 1.103 | 1.01 |
| corpus_main | js_single_frame | 2.808 / 3.514 | 1.63 / 2.249 | 1.178 |
| corpus_main | cdp_snapshot_ax_2call | 12.969 / 13.852 | 7.168 / 8.027 | 5.801 |
| GitHub Trending | ping_scroll | 1.852 / 2.372 | 0.583 / 0.884 | 1.269 |
| GitHub Trending | js_single_frame | 20.048 / 22.675 | 18.659 / 21.33 | 1.389 |
| GitHub Trending | cdp_snapshot_ax_2call | 220.309 / 226.448 | 122.103 / 129.777 | 98.206 |
| Google Maps | ping_scroll | 3.635 / 5.353 | 0.512 / 1.583 | 3.123 |
| Google Maps | js_single_frame | 5.901 / 7.719 | 5.422 / 11.336 | 0.479 |
| Google Maps | cdp_snapshot_ax_2call | 59.151 / 152.155 | 43.832 / 50.459 | 15.319 |

## 6. Post-Action Validation & Stale Safety (Exp 8)

| Surface | Control Full Discover Action p50 / p95 (ms) | Targeted Freshness p50 / p95 (ms) | Stale Safety Parity |
| --- | ---: | ---: | ---: |
| browser | 39.269 / 46.318 | 9.543 / 12.063 | 1.0 |
| desktop_notepad | 2094.347 / 2103.411 | 2013.981 / 2025.197 | 1.0 |

## 7. Incremental MutationObserver + Runtime.addBinding (Exp 9)

- 500 ms churn test: raw_records=`24`, filtered_pushes=`26`, binding_events=`20`
- Top-frame coverage vs ground truth: recall=`0.8421`, prec=`1.0`, failure_breakdown=`{"closed_shadow_dom": 1, "cross_origin_iframe": 2}`

| Transition | Binding Received | Count | eval RTT (ms) | Total Incl Drain (ms) | Bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| open_drawer | True | 1 | 2.12 | 47.05 | 190 |
| open_modal | True | 1 | 5.9 | 46.63 | 189 |
| scroll_down | True | 1 | 1.59 | 47.29 | 191 |
| close_modal | True | 1 | 2.29 | 46.08 | 192 |
| scroll_top | True | 1 | 1.81 | 50.07 | 176 |

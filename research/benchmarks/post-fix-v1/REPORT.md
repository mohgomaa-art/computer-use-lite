# Post-Fix Comparative Evaluation Report (`post-fix-v1`)

- **Baseline Commit (`v0.1.0a0`):** `0d19a9e12527ed12f5020709ea660c169b23e76d`
- **Fixed Commit (`v0.2.0a0` candidate):** `a33a8f261fe4e7b9ef761e1763ac5ad2f2907faf`
- **Frozen Protocol SHA-256:** `c60498f1e0b854f2f88094b46a3ddff8627a06cb0e017c2da9ba4bee31067fc2`

## Track A — Security, Correctness & Cursor Regression Matrix (`n = 32` paired checks)

| Arm | Passed / Total | Rate (%) | 95% Wilson CI | Paired Delta vs Baseline |
| :--- | :---: | :---: | :---: | :--- |
| Baseline `0d19a9e` | 2 / 32 | 6.25% | [1.73, 20.15] | — |
| Fixed `v0.2.0a0` | 32 / 32 | 100.0% | [89.28, 100.0] | +30 fixed wins, 0 losses, 2 ties (both pass) |

## Track B — Live Agent & Deterministic MCP Replay

- **Track B1 Live LLM Agent (`codex-cli 0.166.0`):** **`NOT_RUN`** — pre-flight exited `returncode=1` with `"You’ve hit your usage limit. Upgrade to Plus to continue using Codex (https://chatgpt.com/explore/plus), or try again at Dec 26th, 2026 7:46 PM."`. Native `@oai/sky` / `ollama` / cloud API keys: **`NOT_RUN`** (absent).
- **Track B2 Deterministic Stdio MCP Replay (`n = 18` tasks per arm, scripted client — NOT LLM reasoning):**
  - Baseline `0d19a9e` MCP: **12/18** (66.67%, Wilson 95% `[43.75, 83.72]`, median wall `2667.26 ms`, failures: `['s01_readonly_truthful_verify', 's02_noop_button_truthful_verify', 's03_cross_origin_overlay_reject', 's04_date_input_and_inspect_select', 's05_sticky_header_click', 's06_continuous_drag_and_read_page']`)
  - Fixed `v0.2.0a0` MCP (`Pipe` default): **18/18** (100.0%, Wilson 95% `[82.41, 100.0]`, median wall `2656.17 ms`, failures: `[]`)

## Track C — Isolated Engine Latency, Transport, `rAF` & Memory Profile (`N = 10`)

| Surface | Baseline `0d19a9e` (DirectWS) | Fixed `v0.2.0a0` (Pipe Default) | Fixed `v0.2.0a0` (DirectWS Opt-In) |
| :--- | :--- | :--- | :--- |
| `standard_form` | p50 `6.11 ms` (p95 `14.41 ms`), RSS `49.36 MB` | p50 `9.46 ms` (p95 `19.34 ms`), RSS `47.97 MB` | p50 `6.57 ms` (p95 `9.05 ms`), RSS `49.82 MB` |
| `dense_90` | p50 `15.96 ms` (p95 `17.1 ms`), RSS `50.89 MB` | p50 `25.26 ms` (p95 `34.8 ms`), RSS `49.54 MB` | p50 `16.53 ms` (p95 `17.83 ms`), RSS `50.84 MB` |
| `dense_2500` | p50 `163.45 ms` (p95 `182.91 ms`), RSS `63.55 MB` | p50 `367.09 ms` (p95 `436.94 ms`), RSS `83.56 MB` | p50 `152.43 ms` (p95 `167.09 ms`), RSS `65.34 MB` |
| `oopif_isolated` | p50 `6.08 ms` (p95 `7.09 ms`), RSS `63.61 MB` | p50 `9.8 ms` (p95 `11.14 ms`), RSS `73.26 MB` | p50 `5.9 ms` (p95 `7.96 ms`), RSS `65.41 MB` |
| `hover_adaptive` | p50 `387.39 ms` (p95 `398.19 ms`) | p50 `90.83 ms` (p95 `99.51 ms`) | p50 `94.56 ms` (p95 `103.56 ms`) |
| `cursor_raf` | rAF p50 `16.7 ms`, rebuilds `6`, init_eval `48234 B` | rAF p50 `16.7 ms`, rebuilds `1`, init_eval `0 B` | rAF p50 `16.7 ms`, rebuilds `1`, init_eval `0 B` |
| `desktop_uia_explorer` | p50 `125.63 ms` (p95 `530.76 ms`), RSS `71.47 MB` | p50 `126.6 ms` (p95 `524.24 ms`), RSS `80.22 MB` | p50 `129.43 ms` (p95 `526.38 ms`), RSS `73.88 MB` |

## Track D — Cross-Platform & CI Matrix

- `windows11_full_pytest`: `rc=0`, passed=`95`, failed=`0`, skipped=`0`
- `windows11_ci_skip_desktop`: `rc=0`, passed=`79`, failed=`0`, skipped=`0`
- `simulated_linux_import`: `rc=0`, passed=`1`, failed=`0`, skipped=`0`
- `wsl2_kali_linux_python3_import`: `rc=0`, passed=`1`, failed=`0`, skipped=`0`

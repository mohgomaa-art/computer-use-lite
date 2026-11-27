# Security Findings & Open Limitations (`v0.1.0a1`)

> [!WARNING]
> **Unpatched Runtime Baseline (`0d19a9e`):** Release `v0.1.0a1` is a research documentation, visualization, and branding upgrade. It does **not** patch the verified engine defects documented below. Do not deploy against untrusted websites, multi-tenant servers, or sensitive desktops.

---

## 1. Audited Security & Reliability Status (`FIG-09`)

![FIG-09 Security and Reliability Findings](assets/benchmarks/fig-09-security-findings.svg)

- **TSX Source:** [`Fig09SecurityFindings.tsx`](../research_visuals/benchmark_report/src/figures/Fig09SecurityFindings.tsx) · **PNG Preview:** [`fig-09-security-findings.png`](assets/benchmarks/fig-09-security-findings.png) · **Policy:** [`SECURITY.md`](../SECURITY.md)

| ID | Finding | Severity | Evidence | Fix Status | Exact Code Pointer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | Cross-frame wrong-target click (`position:fixed` overlay over `iframe`) reports `ok:true, verified:true` | **Critical** | `CONFIRMED` | **NOT FIXED** | `src/computer_use_lite/browser_cdp.py:97,129-134` |
| **F-02** | Secret redaction regex misses `card`, `ccnum`, `ssn`, `autocomplete=cc-number` & hides `address_shipping`/`opinion`/`spinner` | **High** | `CONFIRMED` | **NOT FIXED** | `src/computer_use_lite/browser_cdp.py:1863,2150` |
| **F-03** | `show_cursor=True` creates Shadow DOM `<canvas>`, causing false `1280×720` `opaque_canvas` blind crop | **High** | `CONFIRMED` | **NOT FIXED** | `src/computer_use_lite/cursor_overlay.py:494,517`, `browser_cdp.py:1008-1020` |
| **F-04** | `validate_navigation_url` fails open on DNS errors (`.invalid` allowed); DNS-rebinding TOCTOU open | **Medium** | `CONFIRMED` / `NOT RUN` (TOCTOU) | **NOT FIXED** | `src/computer_use_lite/session_manager.py:141-145` |
| **F-05** | Direct loopback CDP WebSocket binds on localhost without token auth by default (`CUL_MCP_DIRECT_WS`) | **Medium** | `PARTIAL` (`NOT RUN` local exploit) | **NOT FIXED** | `src/computer_use_lite/browser_cdp.py:550-555,602-608` |
| **F-06** | Desktop `verify_fresh` hardcodes `occluded: False`; `invoke_pattern` executes across covered windows | **Medium** | `CONFIRMED` (`exebox`) | **NOT FIXED** | `src/computer_use_lite/desktop_uia.py:786` |
| **F-07** | File Explorer (`CabinetWClass`) background tab controls leak with `offscreen: false` (`71 -> 85`) | **Medium** | `CONFIRMED` (`exebox`) | **NOT FIXED** | `src/computer_use_lite/desktop_uia.py` (`FindAllBuildCache`) |
| **F-08** | Win32 `PrintWindow` horizontally mirrors `WS_EX_LAYOUTRTL` windows | **Medium** | `CONFIRMED` | **NOT FIXED** | `src/computer_use_lite/blind_gap.py` |
| **F-REF** | Claim that `src/engine/` holds a stale duplicate source copy | **Info** | `REFUTED` | **NO DEFECT** | `src/engine/*.py` (`16`-line `importlib` aliases) |

*Additional code-verified open limits (`NOT FIXED`):* `desktop_uia.py:379` omits `Alt+Tab`/`Alt+F4`/`Ctrl+Esc`/`Ctrl+Shift+Esc` from `_BLOCKED_KEY_TOKENS`; `open_desktop` has no process allowlist or confirmation gate; `api.py:106-111` omits checkbox/radio/slider/select/readonly AX metadata (`<input readonly>` reports `verified:true`, raw `date` input can corrupt ISO values); `desktop_uia.py`, `snapshot.py`, and `desktop_cursor_overlay.py` execute Windows-only `ctypes.WinDLL` / `WINFUNCTYPE` at module import time (preventing Linux/macOS import).

---

## 2. Clean Visual Audit Evidence (`0d19a9e`)

The synthetic local captures below are reproduced unaltered from `audit_2026-11-27` (zero user windows or personal paths):

### F-01: Cross-Origin `iframe` Covered by Transparent Fixed Overlay
![Synthetic iframe covered by fixed transparent overlay](assets/evidence/b5_cross_origin_iframe_under_fixed_overlay.png)
*Outcome observed on Windows 11 (`0d19a9e`): `discover()` exposed the inner iframe button; `act()` returned `ok:true` and `verified:true` while the overlay intercepted `coverClicks=1` and the target received `btnClicks=0`.*

### F-08: Win32 `PrintWindow` RTL Mirroring (`LTR` vs `WS_EX_LAYOUTRTL`)
| Normal LTR Test Window | `WS_EX_LAYOUTRTL` Mirrored Capture |
| :---: | :---: |
| ![LTR Win32 probe window](assets/evidence/b12_ltr_printwindow.png) | ![Mirrored RTL PrintWindow capture](assets/evidence/b12_rtl_printwindow.png) |

---

## 3. Open Benchmark & Platform Questions

- Desktop Native (`@oai/sky`) vs CUL head-to-head comparison and `CUL T2` (`Calculator` + `7006652.txt`) remain **uncompleted**.
- Interactive `WinSta0\Default` end-to-end validation of Calculator (`calc.exe` AppContainer) and multi-step SendInput sequences outside isolated `exebox` desktops remains pending.
- Live third-party cross-origin embeds (`youtube.com/embed`), exact provider BPE billing (especially for Arabic UIs), dependency CVE scans, and `MAX_SESSIONS=16` RAM ceilings remain unmeasured.

For architectural history and previous roadmaps, see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md), [OPTIMIZATION_ROADMAP.md](OPTIMIZATION_ROADMAP.md), and [`../SECURITY.md`](../SECURITY.md).

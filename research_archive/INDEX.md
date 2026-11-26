# Research Archive Index (`computer-use-lite`)

This directory preserves superseded plans, pre-fix audits, stale-process stress runs, skill validation dossiers, release-preparation snapshots, and pointers to anchored raw artifact bundles so the complete research and debugging history of **Computer Use Lite** remains auditable.

> [!IMPORTANT]
> Documents in `research_archive/` and linked raw folders are **historical snapshots**, NOT current user or security documentation. Always start with canonical docs in [`../docs/INDEX.md`](../docs/INDEX.md), [`../README.md`](../README.md), [`../SECURITY.md`](../SECURITY.md), and [`../docs/KNOWN_LIMITATIONS.md`](../docs/KNOWN_LIMITATIONS.md).

---

## 1. Archived Standalone Reports (Moved into `research_archive/`)

| Archive Path | Original Path | Snapshot Baseline | Provenance & Supersession Status | Current Canonical Counterpart |
| :--- | :--- | :--- | :--- | :--- |
| [`audits/2026-11-26-engine-audit-report.md`](audits/2026-11-26-engine-audit-report.md) | `AUDIT_REPORT.md` | `8744f98`..`6a2f0fb` | Full `M0–M6` audit cataloging `P-01..P-24`. Superseded on `P-01..P-10`, `P0-1..P0-5`, and Workstream A; `P1/P2` recommendations remain reference designs. | [OPTIMIZATION_ROADMAP.md](../docs/OPTIMIZATION_ROADMAP.md), [KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md) |
| [`audits/2026-11-26-fix-plan.md`](audits/2026-11-26-fix-plan.md) | `FIX_PLAN.md` | Pre-`47bea1b` | Locked `M0–M6` thresholds and fix backlog (`P-01..P-22`). Superseded by execution in `2026-11-26-fix-report.md` and `P0-1..P0-5`. | [OPTIMIZATION_ROADMAP.md](../docs/OPTIMIZATION_ROADMAP.md) |
| [`audits/2026-11-26-fix-report.md`](audits/2026-11-26-fix-report.md) | `FIX_REPORT.md` | `47bea1b..6a2f0fb` / `abebcff` | Completed `M0–M6` remediation log (`P-01, P-02-local, P-03, P-04, P-06, P-09, P-10, P-19b-initial`), `5/5` clean runs, and `P-19c` `NOT-REPRODUCED`. Pre-dates Workstream A & `P0-1..P0-5`. | [ARCHITECTURE.md](../docs/ARCHITECTURE.md), [BENCHMARKS.md](../docs/BENCHMARKS.md) |
| [`live_runs/2026-11-26-task-plan.md`](live_runs/2026-11-26-task-plan.md) | `TASK_PLAN.md` | `a922c3b` | Pre-execution `18`-task visibility-checked live test plan (`T01–T18`). Companion execution log is `2026-11-26-run-report-stale-pid-4076.md`. | [RESEARCH_FINDINGS.md](../docs/RESEARCH_FINDINGS.md) |
| [`live_runs/2026-11-26-run-report-stale-pid-4076.md`](live_runs/2026-11-26-run-report-stale-pid-4076.md) | `RUN_REPORT.md` | **Stale `PID 4076` (`10:06:13`)** | `T01–T18` (`8 PASS / 9 PARTIAL / 1 FAIL`, `284` calls). **Caveat:** Executed against pre-fix stale MCP `PID 4076`; superseded for code bugs, valuable for surface/widget discoveries (`T01`, `T06`, `T08`, `T12`, `T13`, `T15`, RTL mirroring). | [KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md), [RESEARCH_FINDINGS.md](../docs/RESEARCH_FINDINGS.md) |
| [`skill_updates/2026-11-26-skill-update-report-r1.md`](skill_updates/2026-11-26-skill-update-report-r1.md) | `SKILL_UPDATE_REPORT.md` | `b4ca9b5` | Round 1 skill update synthesis (`HT1–HT3`, `PID 18036` discovery). **Superseded** by Round 2 report below. | [`2026-11-26-skill-update-report-final.md`](skill_updates/2026-11-26-skill-update-report-final.md) |
| [`skill_updates/2026-11-26-skill-update-report-final.md`](skill_updates/2026-11-26-skill-update-report-final.md) | `FINAL_SKILL_UPDATE_REPORT.md` | `3e67e49` | Round 2 final skill update report (`F1–F3`, `8` `M1` live probes, report-vs-raw conflict corrections). Pre-dates Workstream A & `P0-1..P0-5`. | [RESEARCH_FINDINGS.md](../docs/RESEARCH_FINDINGS.md), [BENCHMARKS.md](../docs/BENCHMARKS.md) |
| [`release_prep/2026-11-26-copyright-attribution-audit.md`](release_prep/2026-11-26-copyright-attribution-audit.md) | `COPYRIGHT_ATTRIBUTION_AUDIT.md` | `698861d` baseline | Point-in-time license/SPDX audit (`66/66` eligible files prior to Workstream A & `P0`). Canonical license files stay at repo root. | [../NOTICE](../NOTICE), [../AUTHORS.md](../AUTHORS.md), [../CONTRIBUTING.md](../CONTRIBUTING.md) |
| [`release_prep/2026-11-26-baseline/INVENTORY.md`](release_prep/2026-11-26-baseline/INVENTORY.md) | `release_preparation/INVENTORY.md` | `3e67e49` | Point-in-time repo inventory pre-`698861d` / pre-Overlay / pre-P0. Superseded by the docs reorganization manifest. | [../DOCUMENTATION_REORGANIZATION_REPORT.md](../DOCUMENTATION_REORGANIZATION_REPORT.md) |
| [`release_prep/2026-11-26-baseline/SECURITY_REVIEW.md`](release_prep/2026-11-26-baseline/SECURITY_REVIEW.md) | `release_preparation/SECURITY_REVIEW.md` | `3e67e49` | Secret & path leak scan + pre-`P0-4`/`P0-5` threat review. | [../SECURITY.md](../SECURITY.md) |
| [`release_prep/2026-11-26-baseline/PUBLICATION_BOUNDARY.md`](release_prep/2026-11-26-baseline/PUBLICATION_BOUNDARY.md) | `release_preparation/PUBLICATION_BOUNDARY.md` | `3e67e49` | Public vs gitignored artifact boundary specification (`3e67e49`). | [../CONTRIBUTING.md](../CONTRIBUTING.md) |
| [`release_prep/2026-11-26-baseline/FINAL_RELEASE_READINESS.md`](release_prep/2026-11-26-baseline/FINAL_RELEASE_READINESS.md) | `release_preparation/FINAL_RELEASE_READINESS.md` | `3e67e49` | Pre-`P0`/pre-Overlay release readiness scorecard (superseded by current docs). | [../README.md](../README.md), [../docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md) |

---

## 2. Anchored Mixed-Artifact Historical & Empirical Collections

These Markdown files remain anchored alongside their immutable `.json`, `.png`, `.txt`, and `.py` evidence so raw data references and verification scripts remain unbroken:

### Legacy Rejected Experiments & Negative Results
- **[`archive/README.md`](../archive/README.md)** — Repository archive notes for historical screenshots & runtime states.
- **[`archive/stale_h2_grid/README.md`](../archive/stale_h2_grid/README.md)** & **[`h2_report.md`](../archive/stale_h2_grid/h2_report.md)** — Explicitly preserved **invalidated** `H2` desktop grid run (`(0, 87)` px browser-chrome offset bug; `h2_probes.json` companion).
- **[`results/experiments/h1_report.md`](../results/experiments/h1_report.md)** — Browser cursor probe (`29.46 s`, `81.8%`; rejected).
- **[`results/experiments/h1b_report.md`](../results/experiments/h1b_report.md)** — Corrected latency/pipelining sweep (`sync` `14.93 s`, `pipe_80` `34.4%` agreement; rejected).
- **[`results/experiments/h3_report.md`](../results/experiments/h3_report.md)** — `NOT RUN / SKIPPED` placeholder retaining stale H2 citation notice.

### Benchmark & Oracle Evidence Datasets
- **[`results/benchmarks/benchmarks_real.md`](../results/benchmarks/benchmarks_real.md)** (`benchmarks_real.json`) — Phase D `n=1` latency & `TOKENS_EST` snapshot dataset.
- **[`results/perf_study/BENCHMARK_REPORT.md`](../results/perf_study/BENCHMARK_REPORT.md)** (`all_results.json`, `exp1_4_uia.json`, `exp5_remote_ops.json`, `exp6_7_9_browser.json`, `exp8_freshness.json`) — 9-experiment optimization study (`Exp 8` confound disclosed in [RESEARCH_METHODOLOGY.md](../docs/RESEARCH_METHODOLOGY.md)).
- **[`results/agent_benchmark/HARNESS_VALIDATION.md`](../results/agent_benchmark/HARNESS_VALIDATION.md)** (`harness_validation.json`) — Deterministic `20/20` oracle check (`0` VLM inferences).

### Local Audit, Skill Update & Root-Cause Dossiers
- **``fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md`` (`fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md`, local-only)** *(gitignored local evidence bundle)* — Reproduction table paired with `38` `.txt`/`.json`/`.patch` raw logs (`M0–M6`).
- **``research_trace/2026-11-26/`` (`research_trace/2026-11-26/OPTIMIZATION_PLAN.md`, local-only)** *(gitignored local dossier)* — ``M0_ISSUE_MATRIX.md`` (`research_trace/2026-11-26/M0_ISSUE_MATRIX.md`, local-only), ``OPTIMIZATION_PLAN.md`` (`research_trace/2026-11-26/OPTIMIZATION_PLAN.md`, local-only), and ``RESEARCH_CITATIONS.md`` (`research_trace/2026-11-26/RESEARCH_CITATIONS.md`, local-only) captured at `3e67e49` alongside `verify_dossier.py` and `repro/`.
- **``skill_updates/2026-11-26/`` (`skill_updates/2026-11-26/DESIGN.md`, local-only)** & **``skill_updates/2026-11-26_final/`` (`skill_updates/2026-11-26_final/DESIGN.md`, local-only)** — Rounds 1 & 2 skill prompt optimization dossiers (`19` Markdown files paired with raw probe PNGs, `m5_summary.json`, `lint_skill.py`, and `verify_report_numbers.py`).

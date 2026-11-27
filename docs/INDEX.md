# Computer Use Lite — Documentation Index

This is the single canonical navigation entry point for **Computer Use Lite (`computer-use-lite`)**, authored by Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/)).

> **Maturity & Epistemic Rule:** Computer Use Lite is an **Experimental Public Research Preview** (`v0.2.0a0` Security, Reliability, Portability & Cursor Hardening Edition built atop preserved immutable baseline `v0.1.0a0` / `0d19a9e`). Documents distinguish verified code (`[VERIFIED-CODE]`), measured datasets (`[MEASURED]`), post-fix verification (`FIXED + VERIFIED`), unverified hardware hooks (`NOT VERIFIED`), and unrun live LLM benchmarks (`NOT_RUN`). See [BENCHMARK_METHODOLOGY.md](BENCHMARK_METHODOLOGY.md) and [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md).

---

## Release & Comparative Evaluation Dossier (`v0.2.0a0`)

| Document / Collection | Scope |
| :--- | :--- |
| [ENGINEERING_CHANGE_HISTORY.md](releases/v0.2.0a0/ENGINEERING_CHANGE_HISTORY.md) | Seven-part engineering lifecycle (`F-01`–`F-08`, `P0`–`P3`, Cursor A–G): defect, discovery, root cause, code fix, verification, benchmark delta, unresolved boundaries |
| [`../research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md`](../research/audits/post-fix-v0.2.0a0/POST_FIX_AUDIT_REPORT.md) | Independent line-verified post-fix audit on commit `a33a8f2`, including explicit `NOT VERIFIED` (`exebox`) & `NOT_RUN` (`Track B1`) boundaries |
| [`../research/benchmarks/post-fix-v1/REPORT.md`](../research/benchmarks/post-fix-v1/REPORT.md) | Frozen protocol (`c60498f`) comparative evaluation across Tracks A (`32/32` vs `2/32`), B1 (`NOT_RUN`), B2 (`18/18` vs `12/18`), C (`N=10` transport/hover/rAF/RSS), and D (`95/95` + WSL2 `Python 3.14.7`) |
| [BENCHMARK_COMPARISON.md](BENCHMARK_COMPARISON.md) | Historical `FIG-01`–`FIG-07` browser MCP results (`fdc92d9`), updated `FIG-06` cross-platform suite, and new `FIG-10` & `FIG-11` post-fix evaluations |
| [BENCHMARK_METHODOLOGY.md](BENCHMARK_METHODOLOGY.md) | Protocols (`fdc92d9` seed `2040777688` + `post-fix-v1`), `b11` prompt-contamination disclosure, `TOKENS_EST` vs BPE limits, and Wilson CI formulas |
| [SECURITY_AND_LIMITATIONS.md](SECURITY_AND_LIMITATIONS.md) | `FIG-09` post-fix security & reliability board (`F-01`–`F-08` remediations + `F-REF` refuted), historical baseline captures (`assets/evidence/`), and open limits |
| [`../research_archive/benchmark_publication/`](../research_archive/benchmark_publication/benchmark_data.json) | Canonical machine-readable JSON datasets (`benchmark_data.json`, `benchmark_sources.json`) |
| [`../research_visuals/benchmark_report/`](../research_visuals/benchmark_report/) | Isolated TypeScript/React/SVG package generating [`assets/benchmarks/`](assets/benchmarks/figures_manifest.json) (`FIG-01`–`FIG-11`) + `CulCover.tsx` |
| [`assets/brand/logo.svg`](assets/brand/logo.svg) | Official owner-supplied SVG mark preserved verbatim |

---

## Core Project & Governance Documents

| Document | Purpose |
| :--- | :--- |
| [README.md](../README.md) | Overview, installation, quickstart examples, test/benchmark commands, and high-level maturity summary |
| [WINDOWS_MCP_SETUP.md](WINDOWS_MCP_SETUP.md) | Windows installer and configuration guide for Codex, Antigravity, and Claude Code |
| [SECURITY.md](../SECURITY.md) | Supported trust scope (`single-user local workstation`), `v0.2.0a0` P0–P2 protections, open Chromium DNS TOCTOU / hook bounds, and vulnerability reporting |
| [CHANGELOG.md](../CHANGELOG.md) | Release log covering `[0.2.0a0]` engineering hardening plus preserved `[0.1.0a2]` / `[0.1.0a1]` / `[0.1.0a0]` (`0d19a9e`) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Development setup, environment flags, test markers, SPDX rules, and privacy/archive rules |
| [AUTHORS.md](../AUTHORS.md) · [LICENSE](../LICENSE) · [NOTICE](../NOTICE) · [CITATION.cff](../CITATION.cff) | Authorship, Apache-2.0 terms, third-party dependency licenses, and software citation metadata |

---

## Architecture & Engineering Decisions

| Document | Scope |
| :--- | :--- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current component architecture (`15` Python modules in `src/computer_use_lite/`): Browser CDP, Windows UIA, `Resolver`, `blind_gap`, `TaskState`, `15`-tool `FastMCP` server + `cul_reload` supervisor, Cursor Overlay, `TakeoverGuard`, and implemented-vs-open boundaries |
| [MCP_SUPERVISOR_RELOAD.md](architecture/MCP_SUPERVISOR_RELOAD.md) | Stdlib-only stdio MCP supervisor (`computer_use_lite.supervisor`), `cul_reload` zero-client-restart reload protocol, Win32 Job Object tree cleanup, non-destructive LKG rollback, and self-update boundaries |
| [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md) | Historical empirical decision scorecard (`H1`–`H3`, `M0`–`M5`, `benchmarks_real`, 9-Exp perf study) + ADRs for Workstream A Cursor Overlay and `P0-1..P0-5` |
| [OPTIMIZATION_ROADMAP.md](OPTIMIZATION_ROADMAP.md) | Complete engineering status across `P0` (`P-01..P-10`, `P0-1..P0-5`), Workstream A, and unimplemented `P1` / `P2` / `Rejected` items |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Verified boundaries and open issues across browser discovery, desktop UIA, Cursor Overlay desktop prerequisites, security, and unrun VLM benchmarks |

---

## Empirical Research, Benchmarks & History

| Document | Scope |
| :--- | :--- |
| [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md) | Epistemic tag definitions, `engine_hashes()` immutability, cold/warm stats, `TOKENS_EST` & `1,229` proxy disclosures, `Exp 8` & `vs_control` confounds |
| [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) | Structured empirical findings across cursor-grid rejection, UIA `MTA`/`AutoSetFocus=0`, 2-call `DOMSnapshot+AX` & `DirectCdpClient`, token studies, live stress-test failure taxonomy, and Cursor Overlay decoupling |
| [BENCHMARKS.md](BENCHMARKS.md) | Suite inventory (`698861d` `pytest`, E2E `8/8`, `benchmarks_real`, 9-Exp study, `20`-task oracle harness, `M5` skill token checks, plus post-`698861d` unit suites) |
| [RESEARCH_HISTORY.md](RESEARCH_HISTORY.md) | Chronological evolution from exploratory grid scripts (`H1`–`H3`) through the 9-experiment study, `P-01..P-22` audit, `3e67e49` trace, Workstream A Cursor Overlay, and Phase 1 `P0-1..P0-5` |

---

## Historical Research Archive & Reorganization Audit

- **[research_archive/INDEX.md](../research_archive/INDEX.md)** — Master index of superseded audits (`P-01..P-24`), stale-process stress runs (`PID 4076`), skill update reports (`R1` & `Final`), point-in-time `3e67e49` release-preparation snapshots, and anchored raw experiment/evidence folders ([archive/](../archive/), [results/](../results/), `fix_runs` *(local-only, excluded from public git)*, `skill_updates` *(local-only, excluded from public git)*, `research_trace` *(local-only, excluded from public git)*).
- **[DOCUMENTATION_REORGANIZATION_REPORT.md](../DOCUMENTATION_REORGANIZATION_REPORT.md)** — Full 62-file inventory, SHA-256 provenance ledger, conflict resolutions, and link-audit verification.

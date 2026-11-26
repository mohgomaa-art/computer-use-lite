# Computer Use Lite — Documentation Index

This is the single canonical navigation entry point for **Computer Use Lite (`computer-use-lite`)**, authored by Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/)).

> **Maturity & Epistemic Rule:** Computer Use Lite is an **Experimental Public Research Preview** (`HEAD` `d47b4e9`). Documents clearly distinguish implemented facts (`[VERIFIED-CODE]`), measured experiments (`[MEASURED]`), prior run reports (`[REPORTED]`), unimplemented plans (`[PROPOSAL]`), and unrun evaluations (`[UNVERIFIED]`). See [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md).

---

## Core Project & Governance Documents

| Document | Purpose |
| :--- | :--- |
| [README.md](../README.md) | Overview, installation, quickstart examples, test/benchmark commands, and high-level maturity summary |
| [SECURITY.md](../SECURITY.md) | Supported trust scope (`single-user local workstation`), `P0-4`/`P0-5` protections, open threats (DNS-rebinding TOCTOU, local DirectWS TCP exposure, `KillSwitch` init), and vulnerability reporting |
| [CHANGELOG.md](../CHANGELOG.md) | Release log preserving `[0.1.0-alpha]` (`698861d`) and post-release Workstream A Cursor Overlay + `P0-1..P0-5` changes (`d47b4e9`) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Development setup, environment flags, test markers, SPDX rules, and privacy/archive rules |
| [AUTHORS.md](../AUTHORS.md) · [LICENSE](../LICENSE) · [NOTICE](../NOTICE) · [CITATION.cff](../CITATION.cff) | Authorship, Apache-2.0 terms, third-party dependency licenses, and software citation metadata |

---

## Architecture & Engineering Decisions

| Document | Scope |
| :--- | :--- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full `HEAD` (`d47b4e9`) component architecture: Browser CDP, Windows UIA, `Resolver`, `blind_gap`, `TaskState`, 13-tool `FastMCP` server, Workstream A Cursor Overlay, `P0-1..P0-5`, and explicit implemented-vs-planned separation |
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

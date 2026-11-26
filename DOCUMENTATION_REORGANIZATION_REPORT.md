# Documentation Reorganization Report (`computer-use-lite`)

**Project:** Computer Use Lite (`computer-use-lite`)  
**Author:** Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/) · [AUTHORS.md](AUTHORS.md))  
**Repository State Audited:** `main` at `d47b4e9` (`698861d` release-prep baseline + Workstream A Cursor Overlay `7c7b9b4..d47b4e9` + Phase 1 `P0-1..P0-5` `77cd171..a3291b3`)  
**Reorganization Scope:** **DOCUMENTATION-ONLY (`.md` files only)** — zero modifications to source (`.py`), tests, benchmarks, JSON datasets, images, `LICENSE`, `NOTICE`, `CITATION.cff`, `pyproject.toml`, workflows, or `.git` history; zero test, server, or benchmark executions performed.

---

## 1. Initial Documentation Inventory & Pre-Reorganization Baseline

Before edits or moves, an exhaustive scan of the repository identified **62 Markdown files** (`61` project/research/skill Markdown files + `1` untracked pytest cache notice `.pytest_cache/README.md`).

- **Pre-reorganization breakdown:**
  - `49` git-tracked `.md` files (including `19` tracked files inside gitignored `skill_updates/`, `11` at root, `6` in `docs/`, `4` in `results/`, `3` in `.agents/skills/`, `3` in `.github/`, `3` in `archive/`)
  - `13` untracked `.md` files (`AUDIT_REPORT.md`, `RUN_REPORT.md`, `4` in `release_preparation/`, `3` in `research_trace/2026-11-26/`, `2` in `results/`, `1` in `fix_runs/2026-11-26/m0_baseline/`, `1` in `.pytest_cache/`)
- **Newly created Markdown documents during reorganization:** `5` (`docs/INDEX.md`, `docs/RESEARCH_FINDINGS.md`, `docs/OPTIMIZATION_ROADMAP.md`, `research_archive/INDEX.md`, and this `DOCUMENTATION_REORGANIZATION_REPORT.md`).
- **Post-reorganization repository total:** `66` project/archive/skill Markdown files (`+ 1` untouched `.pytest_cache/README.md`).

---

## 2. Classification of All 62 Initial Markdown Documents

*(Original SHA-256 digests recorded via `Get-FileHash -Algorithm SHA256` before any edit or move.)*

| # | Original Path | Original SHA-256 | Classification | Action / Post-Reorganization Path |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `README.md` | `C9BA14434A5DC7C61A0612324609DA9A17A40EBFAE8A1D245EFC3655586EBA73` | `CANONICAL` | **Modified in place** -> `README.md` |
| 2 | `CHANGELOG.md` | `E9F0AC569F17FDAF6BA54D5AF04ADC64A08CFEE280F075B80EC899EBF9F4B78D` | `CANONICAL` | **Modified in place** -> `CHANGELOG.md` |
| 3 | `SECURITY.md` | `C337C8438E7C7B499A6E40E89F8D9DFE402351D499CE620BE802872D1CB494C8` | `CANONICAL` | **Modified in place** -> `SECURITY.md` |
| 4 | `AUTHORS.md` | `FDBF6B341EECBFF18C0CC82EABCAC3E58A04BECF9A5BCBEADBC0A3964E043D0E` | `CANONICAL` | **Kept unchanged** -> `AUTHORS.md` |
| 5 | `CONTRIBUTING.md` | `64BC516BC2AC11937F3DB06F0D6023F771F3F5C3C8E8493BBACC9B63218AD252` | `CANONICAL` | **Modified in place** -> `CONTRIBUTING.md` |
| 6 | `.github/ISSUE_TEMPLATE/bug_report.md` | `533FFEC97DF7A70815BB4A17476D193344E7AAEC938A0243B29D148137461E37` | `CANONICAL` | **Kept unchanged** |
| 7 | `.github/ISSUE_TEMPLATE/research_question.md` | `25C6F4E6480FF74AFE4641A1CE49916E890D8EAC98887F0ABBB0434299DA9083` | `CANONICAL` | **Kept unchanged** |
| 8 | `.github/PULL_REQUEST_TEMPLATE.md` | `D5A33CBFA6B9B651CC2B23062F26760D6D11BBD73F6CAB1B24B67A8D5F7DA5C3` | `CANONICAL` | **Kept unchanged** |
| 9 | `docs/ARCHITECTURE.md` | `89CA5A63691413C81921914FCB18B930724AAAE014F16C72CE961D49A4A53824` | `CANONICAL` | **Modified in place** -> `docs/ARCHITECTURE.md` |
| 10 | `docs/ARCHITECTURE_DECISION.md` | `34633FB6B05CB7F5F108BDC3F4E853E3AEBC783D427B74D722D6755E1645A00D` | `CANONICAL` | **Modified in place** *(exact path retained for `src/computer_use_lite/__init__.py`)* |
| 11 | `docs/BENCHMARKS.md` | `A58A5D24B3AE8BB3AE6F1C8FBF8325275AA4B1C0391534BA363ED32CB6B33AB5` | `CANONICAL` | **Modified in place** -> `docs/BENCHMARKS.md` |
| 12 | `docs/KNOWN_LIMITATIONS.md` | `B87D1586F18D6E199A2BD4E13A58B545C8A4516A5C8C981E6591D8F9C229853D` | `CANONICAL` | **Modified in place** -> `docs/KNOWN_LIMITATIONS.md` |
| 13 | `docs/RESEARCH_HISTORY.md` | `42B5D9398CEFC37B9AAA4EA7F8642005AE752DFF70C18506D04DA99E9CB58262` | `CANONICAL` | **Modified in place** -> `docs/RESEARCH_HISTORY.md` |
| 14 | `docs/RESEARCH_METHODOLOGY.md` | `CABBF2C011E378F5F3952B90EB709F62B1190CFC81880DA7F7DC6159B3871632` | `CANONICAL` | **Modified in place** -> `docs/RESEARCH_METHODOLOGY.md` |
| 15 | `AUDIT_REPORT.md` | `3B073EAE6BA0366AE38BE49638B0A2A7959AEA657D4B480BBF3F4D138E5F7A96` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/audits/2026-11-26-engine-audit-report.md`](research_archive/audits/2026-11-26-engine-audit-report.md) *(distilled into `docs/RESEARCH_FINDINGS.md`, `docs/OPTIMIZATION_ROADMAP.md`)* |
| 16 | `FIX_PLAN.md` | `AF87B36F0067BFFDB6C61997DADF034B3D0CE97686736CF86AF1557277C744BF` | `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/audits/2026-11-26-fix-plan.md`](research_archive/audits/2026-11-26-fix-plan.md) |
| 17 | `FIX_REPORT.md` | `EB4F1D3641D41D4819DE8CD32A848B7FB7C165A0D79D9A55C94FAA2B8081D2A6` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/audits/2026-11-26-fix-report.md`](research_archive/audits/2026-11-26-fix-report.md) |
| 18 | `TASK_PLAN.md` | `E30D308C057C4623A9B11C233D8624961A139BE75C19A83C824B78B0AB1C69A7` | `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/live_runs/2026-11-26-task-plan.md`](research_archive/live_runs/2026-11-26-task-plan.md) |
| 19 | `RUN_REPORT.md` | `A8B608C434067899D61E7D30D444BCE78E582C73DC9951BDC833B8A4FD9F341B` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/live_runs/2026-11-26-run-report-stale-pid-4076.md`](research_archive/live_runs/2026-11-26-run-report-stale-pid-4076.md) |
| 20 | `SKILL_UPDATE_REPORT.md` | `AF84136021AE4DD266B32B6F33607A1A5BCB34DDE350C16C2D8F66348059225B` | `DUPLICATE` / `HISTORICAL ARCHIVE` *(superseded by Round 2)* | **Moved & archived** -> [`research_archive/skill_updates/2026-11-26-skill-update-report-r1.md`](research_archive/skill_updates/2026-11-26-skill-update-report-r1.md) |
| 21 | `FINAL_SKILL_UPDATE_REPORT.md` | `3A6CED85EC3505D6E8FC095BCF8E89CFA0D85DF135F88D91756FC1346DD968F0` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/skill_updates/2026-11-26-skill-update-report-final.md`](research_archive/skill_updates/2026-11-26-skill-update-report-final.md) |
| 22 | `COPYRIGHT_ATTRIBUTION_AUDIT.md` | `B07C9EAC136A512F34766209CBB4749218004BAE6AAF8D4B7D76765AE59D0A87` | `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/release_prep/2026-11-26-copyright-attribution-audit.md`](research_archive/release_prep/2026-11-26-copyright-attribution-audit.md) |
| 23 | `release_preparation/INVENTORY.md` | `2D6AE37E5D227D408B163206F7F421BF0FAC88A67EFD7B9B368A6849D146F444` | `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/release_prep/2026-11-26-baseline/INVENTORY.md`](research_archive/release_prep/2026-11-26-baseline/INVENTORY.md) |
| 24 | `release_preparation/SECURITY_REVIEW.md` | `CE80D0087343C62F59AC844B3101219E4B8ADC3016CB998F0CBE4FDEB22BB84C` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/release_prep/2026-11-26-baseline/SECURITY_REVIEW.md`](research_archive/release_prep/2026-11-26-baseline/SECURITY_REVIEW.md) |
| 25 | `release_preparation/PUBLICATION_BOUNDARY.md` | `905C16E57450B233D1BB283F81861955F9A11F657D7379B563BC44CB26A7A265` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/release_prep/2026-11-26-baseline/PUBLICATION_BOUNDARY.md`](research_archive/release_prep/2026-11-26-baseline/PUBLICATION_BOUNDARY.md) |
| 26 | `release_preparation/FINAL_RELEASE_READINESS.md` | `A2DC50326D5B59DB287E138070FBBA4C544417F94507FB9390C9E191D98E738B` | `CONSOLIDATE` / `HISTORICAL ARCHIVE` | **Moved & archived** -> [`research_archive/release_prep/2026-11-26-baseline/FINAL_RELEASE_READINESS.md`](research_archive/release_prep/2026-11-26-baseline/FINAL_RELEASE_READINESS.md) |
| 27–29 | `archive/README.md`, `archive/stale_h2_grid/{README,h2_report}.md` | `244F6B2E...`, `1950A64E...`, `344D5539...` | `HISTORICAL ARCHIVE` | **Anchored in place** beside `.json`/`.png` companions; indexed in [`research_archive/INDEX.md`](research_archive/INDEX.md) |
| 30–32 | `results/experiments/{h1_report,h1b_report,h3_report}.md` | `89CC5FEC...`, `00327CEA...`, `1B2DFA67...` | `REFERENCE` / `HISTORICAL ARCHIVE` | **Anchored in place** beside `h*.json`; indexed in [`research_archive/INDEX.md`](research_archive/INDEX.md) |
| 33 | `results/benchmarks/benchmarks_real.md` | `E7894A6E1D2C70401B5FD8E90BABA0DE5BA5E9BF32F2D8EC4599992865CA442A` | `REFERENCE` | **Anchored in place** beside `benchmarks_real.json` |
| 34 | `results/perf_study/BENCHMARK_REPORT.md` | `65A595AA3783DAAE0EBF06C9A6D90ABCC3BB3B9FE94276F0C7A201F0FE62BD59` | `REFERENCE` | **Anchored in place** (`[!NOTE]` caveat cross-link added) |
| 35 | `results/agent_benchmark/HARNESS_VALIDATION.md` | `5B304809A5D272BEDFA244E32A2C53E05FEDE75EFC6085BA0DEC98C7B065096E` | `REFERENCE` | **Anchored in place** beside `harness_validation.json` |
| 36 | `fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md` | `9FB2795B30F25FCD604026D98FA33DD97320143203EAE3ACA9F0E8075BD16D40` | `HISTORICAL ARCHIVE` | **Anchored in place** beside 38 raw logs (`11` `file:///` links fixed to relative) |
| 37–39 | `research_trace/2026-11-26/{M0_ISSUE_MATRIX,OPTIMIZATION_PLAN,RESEARCH_CITATIONS}.md` | `1E53BF29...`, `034F5E88...`, `6BC2D3EB...` | `CONSOLIDATE` / `REFERENCE` | **Anchored in place** beside `verify_dossier.py` & `repro/`; `P0->d47b4e9` status banners prepended on Matrix & Plan |
| 40–48 | `skill_updates/2026-11-26/*` (`9` files incl. `old_skill_snapshot/`) | `6AC3E13A...` etc. | `HISTORICAL ARCHIVE` *(superseded)* | **Anchored in place** beside `lint_skill.py` & `verify_report_numbers.py` |
| 49–58 | `skill_updates/2026-11-26_final/*` (`10` files incl. `prior_skill_snapshot/`) | `E01297B3...` etc. | `REFERENCE` | **Anchored in place** beside `.json`/`.png` captures (`8` image links repaired in `m1_gap_probes/RESULTS.md`) |
| 59–61 | `.agents/skills/computer-use-lite/{SKILL.md, references/mcp_tools.md, references/python_api_and_safety.md}` | `2A49D302...`, `4640F756...`, `A5313C20...` | `UNRESOLVED` *(intentional agent prompt baseline frozen at `3e67e49`)* | **Kept unchanged**; drift documented cleanly below |
| 62 | `.pytest_cache/README.md` | `73FD6FCCDD802C419A6B2D983D6C3173B7DA97558AC4B589EDEC2DFE443DB9AD` | *Excluded cache artifact* | **Untouched / ignored** |

---

## 3. Grouping Summary (Retained, Consolidated, Archived, Duplicates, Unresolved)

- **Retained as Canonical (`14` files + `3` newly created canonical hubs = `17` canonical documents):**
  - Root & `.github/`: `README.md`, `CHANGELOG.md`, `SECURITY.md`, `AUTHORS.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/research_question.md`, `.github/PULL_REQUEST_TEMPLATE.md`.
  - `docs/`: `docs/INDEX.md` *(new)*, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DECISION.md`, `docs/RESEARCH_FINDINGS.md` *(new)*, `docs/RESEARCH_METHODOLOGY.md`, `docs/BENCHMARKS.md`, `docs/OPTIMIZATION_ROADMAP.md` *(new)*, `docs/KNOWN_LIMITATIONS.md`, `docs/RESEARCH_HISTORY.md`.
- **Consolidated into Canonical Documentation:**
  - `AUDIT_REPORT.md` + `FIX_REPORT.md` -> findings/metrics consolidated into `docs/RESEARCH_FINDINGS.md`, `docs/BENCHMARKS.md`, `docs/OPTIMIZATION_ROADMAP.md`, `docs/RESEARCH_HISTORY.md`.
  - `RUN_REPORT.md` + `FINAL_SKILL_UPDATE_REPORT.md` + `skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md` -> surface discoveries consolidated into `docs/RESEARCH_FINDINGS.md`, `docs/KNOWN_LIMITATIONS.md`.
  - `research_trace/2026-11-26/{M0_ISSUE_MATRIX,OPTIMIZATION_PLAN}.md` + Workstream A / `P0-1..P0-5` commits -> architecture & `P0->P1->P2` roadmap consolidated across `README.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DECISION.md`, `docs/OPTIMIZATION_ROADMAP.md`, `SECURITY.md`, `CHANGELOG.md`.
  - `release_preparation/*` -> actionable security/test/path gates folded into `SECURITY.md`, `CONTRIBUTING.md`, `docs/KNOWN_LIMITATIONS.md`, and `docs/BENCHMARKS.md`.
- **Moved to `research_archive/` (`12` standalone documents + new `research_archive/INDEX.md`):**
  - `research_archive/audits/`: `2026-11-26-engine-audit-report.md`, `2026-11-26-fix-plan.md`, `2026-11-26-fix-report.md`
  - `research_archive/live_runs/`: `2026-11-26-task-plan.md`, `2026-11-26-run-report-stale-pid-4076.md`
  - `research_archive/skill_updates/`: `2026-11-26-skill-update-report-r1.md`, `2026-11-26-skill-update-report-final.md`
  - `research_archive/release_prep/`: `2026-11-26-copyright-attribution-audit.md` and `2026-11-26-baseline/{INVENTORY,SECURITY_REVIEW,PUBLICATION_BOUNDARY,FINAL_RELEASE_READINESS}.md`
  - Empty `release_preparation/` directory removed cleanly after moving all 4 files.
- **Anchored Reference / Mixed-Evidence Files Left Beside Companions:** `archive/*` (`3`), `results/*` (`6`), `fix_runs/.../M0_REPRODUCTION_TABLE.md` (`1`), `research_trace/2026-11-26/*` (`3`), `skill_updates/*` (`19`). All linked from `research_archive/INDEX.md`.
- **Duplicates Identified:**
  - `SKILL_UPDATE_REPORT.md` (Round 1) & `skill_updates/2026-11-26/*` were superseded by `FINAL_SKILL_UPDATE_REPORT.md` (Round 2) & `skill_updates/2026-11-26_final/*`; Round 1 artifacts were archived/marked superseded without deletion.
- **Unresolved / Held Outside Consolidated Public Docs (`3` files):**
  - `.agents/skills/computer-use-lite/{SKILL.md, references/mcp_tools.md, references/python_api_and_safety.md}`: Held intentionally at their validated `3e67e49` prompt baseline rather than modified in this pass; they lag Workstream A Cursor Overlay and `P0-2..P0-5`.

---

## 4. New Documentation Hierarchy

```text
/
├── README.md                                  # Concise public overview, install, quickstart, honest limits (@mohgomaa-art)
├── CHANGELOG.md                               # Unreleased post-0.1.0-alpha (Cursor Overlay + P0-1..P0-5) + [0.1.0-alpha]
├── SECURITY.md                                # Trust scope, P0-4 Fetch SSRF & P0-5 CDP safeguards, open TOCTOU/DirectWS risks
├── CONTRIBUTING.md                            # Dev setup, CUL_* env toggles, test markers, SPDX & privacy rules
├── AUTHORS.md                                 # Mohamed Gomaa
├── DOCUMENTATION_REORGANIZATION_REPORT.md     # This reorganization manifest & verification report
├── .github/                                   # PR template, bug report, research question templates
│
├── docs/
│   ├── INDEX.md                               # Single canonical navigation hub
│   ├── ARCHITECTURE.md                        # System modules (13), CDP, UIA, Cursor Overlay, P0-1..P0-5, implemented vs planned
│   ├── ARCHITECTURE_DECISION.md               # Historical empirical scorecard, KEEP/DROP, benchmarks_real, + Workstream A / P0 ADRs
│   ├── RESEARCH_FINDINGS.md                   # Core empirical findings (positive + negative + M1 live probe discoveries)
│   ├── RESEARCH_METHODOLOGY.md                # Epistemic tags, SHA-256 immutability, TOKENS_EST/Exp 8/vs_control confounds
│   ├── BENCHMARKS.md                          # Commit-pinned suite inventory, perf study, oracle harness, unrun gaps
│   ├── OPTIMIZATION_ROADMAP.md                # Completed P-01..P-10, Workstream A, P0-1..P0-5, and UNIMPLEMENTED P1/P2/Rejected
│   ├── KNOWN_LIMITATIONS.md                   # P0 mitigations vs open browser, desktop UIA, security & verification gaps
│   └── RESEARCH_HISTORY.md                    # Five-phase chronological evolution
│
└── research_archive/
    ├── INDEX.md                               # Master historical catalog & pointers to anchored archive/results/fix_runs/trace
    ├── audits/                                # Engine audit, M0-M6 fix plan, M0-M6 fix report
    ├── live_runs/                             # T01-T18 task plan & stale PID 4076 run report
    ├── skill_updates/                         # Round 1 & Round 2 skill update reports
    └── release_prep/                          # Point-in-time copyright audit & 3e67e49 release-prep baseline
```

---

## 5. Key Research Findings Preserved & Conflicts Resolved

1. **Pre-P0 Public Docs vs `HEAD` (`d47b4e9`) Code Drift Resolved:** `README.md`, `CHANGELOG.md`, `SECURITY.md`, `docs/ARCHITECTURE.md`, and `docs/KNOWN_LIMITATIONS.md` previously reflected `698861d` (`0.1.0-alpha`) and omitted Workstream A (`cursor_overlay.py`, `desktop_cursor_overlay.py`, `CUL_MCP_HEADFUL`, `_WDA_EXCLUDEFROMCAPTURE`, `HEADLESS:`/`CURSOR:`) and `P0-1..P0-5` (`77cd171..a3291b3`), while also using an outdated space-separated `line_map` example instead of the actual `eN|role|name|x,y,w,h|actions` wire format (`api.py:96`). All canonical docs now reflect `d47b4e9` accurately.
2. **Negative Experimental Results Preserved Explicitly:** Rejected cursor grids (`H1` `29.46 s`, `H1b` `14.93 s`/`34.4%` pipelined, `H2` `(0, 87)` px invalidated origin, `H3` `NOT BUILT`), `Exp 5 RemoteOperations`, `Exp 6 One-Call JS`, and `Exp 9 MutationObserver` stay preserved with full caveats across `docs/ARCHITECTURE_DECISION.md`, `docs/RESEARCH_FINDINGS.md`, `docs/OPTIMIZATION_ROADMAP.md`, `archive/`, and `results/experiments/`.
3. **Methodological Confounds & Oracle Boundaries Kept Intact:** `Exp 8` (`fsync=False` confound), `vs_control` real-site circular scoring, `TOKENS_EST = len/4` vs `1,229` proxy, and `bench_agent_20tasks.py`'s **`20/20` deterministic oracle only (`0` live VLM runs)** remain highlighted in both `README.md` and `docs/`.
4. **Stale Server `PID 4076` Separation:** `RUN_REPORT.md` (`8 PASS, 9 PARTIAL, 1 FAIL`) was archived clearly labeled **`2026-11-26-run-report-stale-pid-4076.md`** so its pre-fix failures are never conflated with `d47b4e9`.
5. **Implemented vs. `P1/P2` Proposals Separated:** Unimplemented proposals in `research_trace/2026-11-26/OPTIMIZATION_PLAN.md` (`P1` AX metadata enrichment, `_visible_click_point`, `WS_EX_LAYOUTRTL` un-mirroring, Explorer `CabinetWClass` scoping, `P2` Linux/macOS import guards, mouse drag, 20-task live VLM runs) carry explicit `[PROPOSAL / NOT IMPLEMENTED]` status.

### Remaining Unresolved Tensions / Open Items
1. **`.agents/skills/computer-use-lite/*.md` Currency:** Still documents `3e67e49` (missing `CUL_MCP_HEADFUL`, `navigate` tab actions, `#32770` Save As dialog handling, and Cursor Overlay toggles). Kept frozen to preserve existing `skill_updates/.../verify_report_numbers.py` validation checks.
2. **Post-`0.1.0-alpha` Full-Suite Test Verification (`d47b4e9`):** The historical `52 passed in 68.86s` metric applies only to `698861d`; `tests/test_cursor_overlay.py` contains uncommitted working-tree edits, and an interactive `WinSta0\Default` full `pytest` + restarted-MCP live sweep against public OOPIFs/Save As/multi-tab has not been executed yet.
3. **Legacy Verification Script Paths:** `skill_updates/2026-11-26/verify_report_numbers.py` and `skill_updates/2026-11-26_final/verify_report_numbers.py` hardcode root `SKILL_UPDATE_REPORT.md` and `FINAL_SKILL_UPDATE_REPORT.md` (`.py` files could not be edited in this docs-only assignment); archived banners note this explicitly.

---

## 6. Link, Path-Privacy & Integrity Verification (`Post-Reorganization`)

- **Broken Links Fixed:**
  - Normalized `100+` workstation `file:///<LOCAL_USER_HOME>/...` URIs across the `12` archived reports into portable repository-relative paths and `<LOCAL_AGENT_ARTIFACT_DIR>` placeholders, updating cross-references to moved documents (`AUDIT_REPORT.md`, `FIX_PLAN.md`, `FIX_REPORT.md`, `TASK_PLAN.md`, `RUN_REPORT.md`, `SKILL_UPDATE_REPORT.md`, `FINAL_SKILL_UPDATE_REPORT.md`).
  - Repaired `8` self-broken relative `.png` links inside ``skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md`` (`skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md`, local-only) (`m1_gap_probes/*.png` -> `*.png`).
  - Repaired `11` broken workstation `file:///` links inside ``fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md`` (`fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md`, local-only) into relative sibling links (`pytest_full.txt`, `repro_findings.txt`, etc.).
- **Path-Privacy Verification (`local OS user paths`):**
  - **Canonical docs (`README.md`, root `.md`, `.github/`, `docs/`, `research_archive/INDEX.md`, `DOCUMENTATION_REORGANIZATION_REPORT.md`):** `0` local workstation paths (`verified across 598 local links, 0 broken`). *(Archive policy docs under `research_archive/release_prep/2026-11-26-baseline/` retain literal historical check rules naming the local workstation account string; gitignored `skill_updates/` dossiers remain anchored untouched beside their verification scripts.)*
- **Non-`.md` Immutability:** `git status --porcelain` verified zero changes to any `.py`, `.json`, `.toml`, `.yml`, `.html`, `.png`, `LICENSE`, `NOTICE`, or `CITATION.cff` file (only the pre-existing uncommitted `benchmarks/`, `results/`, `tests/test_cursor_overlay.py` working-tree entries were already present before this task).

---

## 7. Complete Manifest of Created, Moved & Modified Markdown Files

| Action | Path(s) | Post-Edit SHA-256 |
| :--- | :--- | :--- |
| **Created** | `docs/INDEX.md` | `D61F979397D606CA0AC431EBBB64576CF1341DBF725A9DF26B32918FF10A419B` |
| **Created** | `docs/RESEARCH_FINDINGS.md` | `F68AE3896BDA5559B4D827F4846698985257AE4DA431992D13EA33F740AF9043` |
| **Created** | `docs/OPTIMIZATION_ROADMAP.md` | `53FF2AB1D3D4FF96E74ECC569D7AA7264C46E0A0125D99E747263B97D89E8764` |
| **Created** | `research_archive/INDEX.md` | `31AEA8F7DB7778A5CB8026BAE31E684362843E92D2E030FA587EE83DA98E6F9A` |
| **Created** | `DOCUMENTATION_REORGANIZATION_REPORT.md` | *(self; verified on disk)* |
| **Modified (Canonical)** | `README.md` | `B773828F35C07FC3D6EFD12AD2BADD51A2D809D416AA524071EFE207645C5C34` |
| **Modified (Canonical)** | `CHANGELOG.md` | `3EE0A757D71D69A20F9D0D6135785394CF366BE849C7AF8EE1638AD73E008702` |
| **Modified (Canonical)** | `SECURITY.md` | `C10A21A34BAF2859C3D92EB6878781926305365E8514A08E152F9F444368899B` |
| **Modified (Canonical)** | `CONTRIBUTING.md` | `4DC59EC48F5E3CAE74EC6357F9405E156D44FB333C36B08DBAFB1596DB690CB2` |
| **Modified (Canonical)** | `docs/ARCHITECTURE.md` | `9C3623763066E3A676E8D6340A507506B2720D6142EC53D12DAA077B6ADC1CD4` |
| **Modified (Canonical)** | `docs/ARCHITECTURE_DECISION.md` | `00170D91269715C1651246B5CDF7E96EF56BFD8723AC3971CD309454A6A913EA` |
| **Modified (Canonical)** | `docs/BENCHMARKS.md` | `2AE869623434A534A3613692D5EEC8D52EA45B033BBF74B437B1AD537ADD4BF3` |
| **Modified (Canonical)** | `docs/KNOWN_LIMITATIONS.md` | `3395F29446C6049893067839EBFC7A6EF431CDD7F22FA811BA75D9F69C4ACA31` |
| **Modified (Canonical)** | `docs/RESEARCH_HISTORY.md` | `64E40835ECF4ED5669C31BF02A216F23F5B5037EF70EEC271BEFF51CA103868C` |
| **Modified (Canonical)** | `docs/RESEARCH_METHODOLOGY.md` | `D7A6AC03CF766FE6DBD6E7AE3F3F413136974597B4B2BB3367A500F5A0D7D89B` |
| **Moved + Banner/Links** | `research_archive/audits/2026-11-26-engine-audit-report.md` (`<- AUDIT_REPORT.md`) | `42B5BCECE42992BBCD4DE23CD2014CE9EDE908C1523193F5241F8119D037B697` |
| **Moved + Banner/Links** | `research_archive/audits/2026-11-26-fix-plan.md` (`<- FIX_PLAN.md`) | `A386C1B3F94A6782A28E45B4001FE59DDEA562D3834CD360880097B4E38CADF5` |
| **Moved + Banner/Links** | `research_archive/audits/2026-11-26-fix-report.md` (`<- FIX_REPORT.md`) | `213E51FE641153C1922952FCBBF32E712397F86B8D3FEDB5591BF44DB81F3A8F` |
| **Moved + Banner/Links** | `research_archive/live_runs/2026-11-26-task-plan.md` (`<- TASK_PLAN.md`) | `EFE75532810B52038333F143AE785875CA484232E8A865088D5EC4FED08768B2` |
| **Moved + Banner/Links** | `research_archive/live_runs/2026-11-26-run-report-stale-pid-4076.md` (`<- RUN_REPORT.md`) | `43AAEFD6146373F5F88473964F6FFE9FD274065448B8110F28032951F7E395DB` |
| **Moved + Banner/Links** | `research_archive/skill_updates/2026-11-26-skill-update-report-r1.md` (`<- SKILL_UPDATE_REPORT.md`) | `CD630D8B83764B6046F4D2D67B8528A50391196B988A890DB6851C42AE06B09A` |
| **Moved + Banner/Links** | `research_archive/skill_updates/2026-11-26-skill-update-report-final.md` (`<- FINAL_SKILL_UPDATE_REPORT.md`) | `28EB44F23FDE730F452D0A71F50819675FD29D6FE16CD9D9EBA648F6515953D6` |
| **Moved + Banner/Links** | `research_archive/release_prep/2026-11-26-copyright-attribution-audit.md` (`<- COPYRIGHT_ATTRIBUTION_AUDIT.md`) | `B3A0B421082AB3EA983F4271753886A747D2586AC101995292C5298F70BA046C` |
| **Moved + Banner/Links** | `research_archive/release_prep/2026-11-26-baseline/INVENTORY.md` (`<- release_preparation/INVENTORY.md`) | `A30A06B0A65C280F46378C7CE14E79497EC67DF84A9E4903C156BD354A217B3A` |
| **Moved + Banner/Links** | `research_archive/release_prep/2026-11-26-baseline/SECURITY_REVIEW.md` (`<- release_preparation/SECURITY_REVIEW.md`) | `FBE49524857C8B68AA39E7B04FCA36D2C2F2C1BE9952E3BBEAA7AF0989729BF2` |
| **Moved + Banner/Links** | `research_archive/release_prep/2026-11-26-baseline/PUBLICATION_BOUNDARY.md` (`<- release_preparation/PUBLICATION_BOUNDARY.md`) | `EB1CACFE647C940DE3AD90B26C891ECE0425F145F95C5DA17B6F2EEA1814DE3A` |
| **Moved + Banner/Links** | `research_archive/release_prep/2026-11-26-baseline/FINAL_RELEASE_READINESS.md` (`<- release_preparation/FINAL_RELEASE_READINESS.md`) | `A6B7EE497B6F07E454FCCF9436E858655DB0F8F26460BFAE4095FC5B94B3C265` |
| **Modified (Anchored Link/Status)** | `research_trace/2026-11-26/M0_ISSUE_MATRIX.md` | `E10363F37B3B00C80A742678B3306D44CB02036286562B20EBAD950EE9096105` |
| **Modified (Anchored Status)** | `research_trace/2026-11-26/OPTIMIZATION_PLAN.md` | `00383CDACF33F5D9CD8B4A6DECC2414BA42B78379D75752E0AED6B36753A5F0A` |
| **Modified (Anchored Note)** | `results/perf_study/BENCHMARK_REPORT.md` | `388388DFB50883359B668DA28875DA422B1547AE9BC26F641826E5E84E8A0093` |
| **Modified (Anchored Links)** | `skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md` | `6DDC3634E37EB1122F680A2BF28744706FEF57FE697D875B51D1576F243DAA9C` |
| **Modified (Anchored Links)** | `fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md` | `6954D05AE7B9D6D5C174A5B1F63E50EDFC3713F668F6A7C27A36F52D43E1BC79` |

---

## 8. Final Verification Check (Reorganization Summary)

- **DONE:** Audited all `62` pre-existing Markdown files with SHA-256 digests; aligned canonical public docs (`README.md`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `docs/*`) with `HEAD` `d47b4e9` (Workstream A Cursor Overlay + `P0-1..P0-5`); created `docs/INDEX.md`, `docs/RESEARCH_FINDINGS.md`, `docs/OPTIMIZATION_ROADMAP.md`, `research_archive/INDEX.md`, and `DOCUMENTATION_REORGANIZATION_REPORT.md`; archived `12` standalone root/release-prep working reports cleanly under `research_archive/` with link repair and path privacy normalization.
- **IN PROGRESS:** None inside this documentation-only assignment.
- **UNRESOLVED:** `.agents/skills/computer-use-lite/*.md` intentionally remains at its validated `3e67e49` prompt baseline; full `d47b4e9` `pytest` re-run and `bench_agent_20tasks.py` live VLM benchmarks remain unexecuted outside this docs-only scope.
- **ARCHIVED:** `12` standalone reports moved into `research_archive/` (`audits/`, `live_runs/`, `skill_updates/`, `release_prep/`) plus `32` mixed-directory evidence Markdown files anchored beside raw `.json`/`.png`/`.txt`/`.py` datasets and indexed in `research_archive/INDEX.md`.
- **CANONICAL DOCUMENTS:** `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `AUTHORS.md`, `.github/{ISSUE_TEMPLATE/*,PULL_REQUEST_TEMPLATE.md}`, `docs/{INDEX,ARCHITECTURE,ARCHITECTURE_DECISION,RESEARCH_FINDINGS,RESEARCH_METHODOLOGY,BENCHMARKS,OPTIMIZATION_ROADMAP,KNOWN_LIMITATIONS,RESEARCH_HISTORY}.md`.
- **FILES CHANGED:** `32` Markdown files total (`5` newly created, `10` canonical modified in place, `12` moved/archived with provenance banners & relative links, `5` anchored research/run Markdown files patched for broken links or `d47b4e9` status banners).
- **FILES NOT TOUCHED:** Zero non-Markdown files modified (`src/`, `tests/`, `benchmarks/`, `experiments/`, `scripts/`, `results/*.json`, `LICENSE`, `NOTICE`, `CITATION.cff`, `pyproject.toml`, `.git`); untouched `.agents/skills/computer-use-lite/*.md`, `AUTHORS.md`, `.github/*.md`, `archive/*.md`, `results/{experiments,benchmarks,agent_benchmark}/*.md`, `research_trace/2026-11-26/RESEARCH_CITATIONS.md`, `skill_updates/2026-11-26/*.md`, and `.pytest_cache/README.md`.
- **NEXT RECOMMENDED ACTION:** Review git status/diff on `.md` files (`git status`), decide separately whether to stage/commit the curated `docs/` + `research_archive/` reorganization and whether to run a dedicated interactive `WinSta0\Default` `pytest` + live VLM evaluation pass + `.agents/` skill update cycle.

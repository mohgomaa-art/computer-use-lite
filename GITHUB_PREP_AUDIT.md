# GitHub Release Preparation Audit (`computer-use-lite`)

**Project:** Computer Use Lite (`computer-use-lite`)  
**Author:** Mohamed Gomaa ([`@mohgomaa-art`](https://github.com/mohgomaa-art/) · [AUTHORS.md](AUTHORS.md))  
**Audited Revision:** `main` at `d47b4e9` + consolidated `.md` working tree  
**Audit Mode:** **Read-Only Audit & Planning** — zero edits made to `.gitignore`, `.py`, `.json`, configuration, tests, or git history; zero staging, commits, remotes, pushes, tests, or benchmarks executed.

---

## Executive Verdict: `NOT READY` *(for immediate raw `git push` to a public GitHub repository)*

While copyright/SPDX headers passed statically across **`67/67`** eligible source/HTML files (`scripts/verify_copyright_headers.py`, exit `0`), **`0`** API keys/tokens were detected, and all `598` relative Markdown links resolve cleanly, **4 concrete release blockers** prevent pushing the current repository state cleanly to a public GitHub repository:

1. **Already-Committed Workstation Paths in Tracked `skill_updates/` History:** `45` files inside `skill_updates/` are already tracked on `main` (`f0fd6ba..3e67e49`), including `skill_updates/2026-11-26/m0_env_git.txt` (`62` lines containing `C:\Users\<USER>\...`), `skill_updates/2026-11-26/m5_runs/server_check.json` (`2` workstation path lines), `6` `.py` automation scripts hardcoding absolute local workspace paths, and `4` `.md` docs (`12` tracked files total). Untracking at `HEAD` alone will not purge them from git commit history prior to a public push.
2. **`.gitignore` Unanchored Pattern Collision:** Unanchored `live_runs/` and `skill_updates/` rules silently ignore `research_archive/live_runs/` (`2` files) and `research_archive/skill_updates/` (`2` files), breaking archive completeness while recording `D` deletions of their root predecessors.
3. **CI / Test Readiness Gaps:** `tests/test_audit_fixes.py::test_p0_3_win32_save_as_commit_and_dialog_alerts` (`L631`) omits `CUL_SKIP_DESKTOP == "1"` and `@pytest.mark.windows_desktop`, risking GUI dialog failure/hangs inside GitHub Actions `windows-latest` (`CUL_SKIP_DESKTOP: "1"`). Additionally, `tests/test_cursor_overlay.py` carries uncommitted edits and no full `d47b4e9` suite run has verified the consolidated tree.
4. **Remote & Repository Setup:** `git remote -v` is unconfigured, and [SECURITY.md](SECURITY.md) notes **GitHub Private Vulnerability Reporting** must be enabled upon repository creation.

Clearing those items converts status cleanly to **`READY`**.

---

## 1. Git Ignore Audit (`.gitignore`)

### Scope Inspected
- Found `2` ignore files: root [`.gitignore`](.gitignore) (`53` lines) and tool-generated `.pytest_cache/.gitignore` (`*`). Zero ignore files exist inside `src/`, `docs/`, `research_archive/`, `results/`, `benchmarks/`, or `tests/`.

### Exact `git check-ignore -v` Findings
| Path Checked | Matched `.gitignore` Rule | Effect / Defect |
| :--- | :--- | :--- |
| `research_archive/live_runs/2026-11-26-task-plan.md` | `.gitignore:44:live_runs/` | **UNINTENDED COLLISION:** hides archived doc while root `TASK_PLAN.md` shows `D` |
| `research_archive/live_runs/2026-11-26-run-report-stale-pid-4076.md` | `.gitignore:44:live_runs/` | **UNINTENDED COLLISION:** hides archived run report |
| `research_archive/skill_updates/2026-11-26-skill-update-report-r1.md` | `.gitignore:46:skill_updates/` | **UNINTENDED COLLISION:** hides archived Round 1 report while root `SKILL_UPDATE_REPORT.md` shows `D` |
| `research_archive/skill_updates/2026-11-26-skill-update-report-final.md` | `.gitignore:46:skill_updates/` | **UNINTENDED COLLISION:** hides archived Final report while root `FINAL_SKILL_UPDATE_REPORT.md` shows `D` |
| `live_runs/2026-11-26/evidence/T01.json` | `.gitignore:44:live_runs/` | Intended ignore (raw evidence) |
| `fix_runs/2026-11-26/m0_baseline/M0_REPRODUCTION_TABLE.md` | `.gitignore:45:fix_runs/` | Intended ignore (should still anchor `/fix_runs/`) |
| `research_trace/2026-11-26/OPTIMIZATION_PLAN.md` | `.gitignore:47:research_trace/` | Intended ignore (should still anchor `/research_trace/`) |
| `archive/screenshots/h1_overlay.png` | `.gitignore:48:archive/screenshots/` | Intended ignore (also matched by `*.png` at line 50) |
| `archive/runtime_state/task_state.json` | `.gitignore:49:archive/runtime_state/` | Intended ignore |

**Why it matters:** Without a leading `/`, Git matches directory patterns at **any depth**. Root-anchoring (`/outputs/`, `/results/...`, `/live_runs/`, `/fix_runs/`, `/skill_updates/`, `/research_trace/`, `/archive/screenshots/`, `/archive/runtime_state/`) isolates root working/artifact folders while allowing `research_archive/live_runs/` and `research_archive/skill_updates/` to be tracked normally without fragile `git add -f`.

> **Important Note on `skill_updates/`:** Because `45` files under `/skill_updates/` were previously force-added into git (`f0fd6ba..3e67e49`), `.gitignore` alone does **not** untrack already-committed files (`git rm --cached -r skill_updates` is required if removing them from the repo).

### Exact Proposed `.gitignore` Diff *(NOT Applied Yet)*

```diff
--- a/.gitignore
+++ b/.gitignore
@@ -33,17 +33,17 @@
 .freebuff/
 
 # Ephemeral runtime outputs, crops, and local screenshots (may contain local usernames or window edges)
-outputs/
-results/crops/
-results/crops_bench/
-results/runtime/
-results/bench_state.json
-results/**/task_state*.json
-results/agent_benchmark/crops/
-results/agent_benchmark/runtime/
-live_runs/
-fix_runs/
-skill_updates/
-research_trace/
-archive/screenshots/
-archive/runtime_state/
+/outputs/
+/results/crops/
+/results/crops_bench/
+/results/runtime/
+/results/bench_state.json
+/results/**/task_state*.json
+/results/agent_benchmark/crops/
+/results/agent_benchmark/runtime/
+/live_runs/
+/fix_runs/
+/skill_updates/
+/research_trace/
+/archive/screenshots/
+/archive/runtime_state/
 *.png
```

---

## 2. Research Archive & Workspace Publication Audit

**Cross-Repository Privacy/Secret Scan Summary:**
- **API Keys / Tokens / Private Keys:** `0` hits across all text/source/JSON/Markdown/config files.
- **Non-Example Emails:** `0` personal/real emails (`oopif@example.test` in `tests/test_audit_fixes.py` only).
- **Screenshots (`.png`):** `117` total PNGs (`archive/`: `10` / `1.8 MB`; `results/`: `3` / `0.88 MB`; `skill_updates/`: `43` / `11.15 MB`; `live_runs/`: `61` / `7.12 MB`). **All `117` PNGs currently have `git_tracked = 0`** due to `*.png` in `.gitignore`. Keep raw desktop screenshots (`live_runs/`, `skill_updates/`, `archive/screenshots/`) **local**, as full-desktop grabs can show window chrome, desktop wallpaper/taskbar, or localized user shell context.

### Archive & Historical Artifact Manifest

| Path / Collection | Files | Scan Observations | Classification | Recommended GitHub Handling |
| :--- | :---: | :--- | :---: | :--- |
| [`research_archive/INDEX.md`](research_archive/INDEX.md) | `1` `.md` | `0` paths/secrets; links all archived items | **`TRACK`** | Commit cleanly as archive hub |
| [`research_archive/audits/`](research_archive/audits/2026-11-26-engine-audit-report.md) (`engine-audit-report`, `fix-plan`, `fix-report`) | `3` `.md` | `0` user paths; `0` secrets; ephemeral `exebox-*` sandbox IDs noted in audit/fix headers | **`TRACK`** | Commit (`??` currently untracked) |
| [`research_archive/live_runs/`](research_archive/live_runs/2026-11-26-task-plan.md) (`task-plan`, `run-report-stale-pid-4076`) | `2` `.md` | `0` user paths; `0` secrets; ephemeral `exebox-*` ID; stale `PID 4076` warning banner | **`TRACK`** | Anchor `/live_runs/` in `.gitignore` first, then commit |
| [`research_archive/skill_updates/`](research_archive/skill_updates/2026-11-26-skill-update-report-final.md) (`skill-update-report-r1`, `skill-update-report-final`) | `2` `.md` | `0` user paths; `0` secrets; captures all `M5` metrics cleanly | **`TRACK`** | Anchor `/skill_updates/` in `.gitignore` first, then commit |
| [`research_archive/release_prep/2026-11-26-copyright-attribution-audit.md`](research_archive/release_prep/2026-11-26-copyright-attribution-audit.md) | `1` `.md` | `0` user paths; point-in-time `66/66` header snapshot | **`TRACK`** | Commit |
| `research_archive/release_prep/2026-11-26-baseline/{INVENTORY,SECURITY_REVIEW}.md` | `2` `.md` | `0` user paths; `0` secrets | **`TRACK`** | Commit |
| `research_archive/release_prep/2026-11-26-baseline/{PUBLICATION_BOUNDARY,FINAL_RELEASE_READINESS}.md` | `2` `.md` | `5` + `3` literal mentions of the local username string inside path-scrubbing rule descriptions (`0` actual file paths) | **`TRACK`** *(or scrub literal token)* | Commit (or replace literal rule string with `<LOCAL_USER>` for `0`-hit clean greps) |
| [`archive/README.md`](archive/README.md), [`archive/stale_h2_grid/`](archive/stale_h2_grid/h2_report.md) | `3` `.md`, `1` `.json` | Already tracked; negative H2 provenance; `0` secrets/paths | **`TRACK`** | Keep tracked unchanged |
| `archive/screenshots/` & `archive/runtime_state/` | `10` `.png`, `4` `.json` | Gitignored; raw captures & step logs | **`KEEP-LOCAL`** | Leave gitignored (anchor `/archive/...`) |
| `live_runs/` (`2026-11-26/`) | `61` `.png`, `22` `.json`, `2` `.py`/`.txt` | Gitignored; `m0_baseline_procs.json` has `62` local user-path lines; raw screenshots | **`KEEP-LOCAL`** | Keep gitignored (already summarized in `research_archive/live_runs/`) |
| `fix_runs/` (`2026-11-26/`) | `44` files (`.txt`, `.json`, `.patch`, `.py`, `1` `.md`) | Gitignored; `25`+ user-path hits across `run_*.txt`, `summary.json`, `pytest_full.txt` | **`TRACK-SUMMARIZED`** | Keep raw folder local (`research_archive/audits/2026-11-26-fix-report.md` publishes summary) |
| `research_trace/2026-11-26/` | `3` `.md`, `8` `.py`, `4` `.json` | Gitignored; `.md` files have `0` user paths (`<PYTHON312_EXE>`), while `7` `.py` scripts hardcode `C:\Users\<USER>` | **`TRACK-SUMMARIZED`** *(distilled in `docs/`)* / **`KEEP-LOCAL`** *(raw `repro/`)* | Keep gitignored (`.md` findings consolidated in `docs/OPTIMIZATION_ROADMAP.md` & `docs/RESEARCH_FINDINGS.md`) |
| `skill_updates/` (`2026-11-26/` & `2026-11-26_final/`) | `45` **tracked** (`.md`, `.json`, `.py`, `.txt`) + `43` untracked `.png`s | **BLOCKER:** `12` currently **tracked** files leak `C:\Users\<USER>` (`m0_env_git.txt` `62` lines, `server_check.json`, `6` `.py` scripts, `4` `.md` docs); `.png` captures `7–11 MB` gitignored | **`TRACK-SUMMARIZED`** *(keep report in `research_archive/skill_updates/`)*; **`KEEP-LOCAL`** *(raw logs/`m0_env_git.txt`/PNGs)* | **Untrack (`git rm --cached`) & remove from public commit history** (`m0_env_git.txt`, `server_check.json`, `.py` paths), OR redact before public release |
| `.pytest_cache/`, `**/__pycache__/`, `outputs/` | Cache / compiled bytecode | Generated environment artifacts | **`EXCLUDE`** | Remain gitignored |

---

## 3. Benchmarks & Results Publication Audit (`benchmarks/` & `results/`)

| Path / Artifact | Git State | Evidence Class | Observations & Reproducibility | Recommended Action |
| :--- | :---: | :--- | :--- | :--- |
| `benchmarks/{__init__,common,corpus,benchmark_real}.py` + `fixtures/` | Tracked (clean) | **Reproducible Methodology** | Clean SPDX/Apache-2.0 headers; deterministic local/corpus fixtures | **`TRACK`** (unchanged) |
| `benchmarks/bench_{action_freshness,browser,remote_ops,uia}.py` & `benchmarks/run_all.py` | Tracked (`M`) | **Reproducible Methodology** | Real bugfixes vs old commits (`SafeArrayCreateVector` double-free, `OP_NEW_UINT`, occlusion pruning, `_detect_box_kind`, updated `_keep_drop_hold`); **note** `run_all.py:207` embeds hardcoded hardware text (`Windows 11 10.0.26200-SP0, i5-11400F, 15.84 GB`) in report output (`CRLF -> LF` normalized on add) | **`TRACK`** (commit cleanly in Benchmark Methodology workstream; parameterize hardware string dynamically later) |
| `benchmarks/agent_tasks.py` & `benchmarks/bench_agent_20tasks.py` | Untracked (`??`) | **Reproducible Methodology** | Valid SPDX headers (`67/67`); defines 20-task harness & `--dry-run-oracle`; no API keys embedded (reads runtime provider SDKs) | **`TRACK`** (commit cleanly in 20-Task Agent Harness workstream) |
| `results/experiments/h1_*`, `h1b_*`, `h2_gate0*`, `h3_report.md` | Tracked (clean) | **Historical Experimental Output** | Rejected/negative empirical artifacts; `0` user paths/secrets; cited by `docs/` | **`TRACK`** (keep unchanged) |
| `results/benchmarks/benchmarks_real.{json,md}` | Tracked (`M`) | **Machine-Specific Point Snapshot** | Real websites (`GitHub`, `YouTube`, `Gmail`, `Maps`) + Notepad/Explorer vary by live web/OS; current `M` diffs (`140.2 ms`, `387.7 ms`, `215.5 ms`) match values cited in `docs/ARCHITECTURE_DECISION.md` & `docs/BENCHMARKS.md` | **`TRACK`** (sync working-tree `M` values with `docs/BENCHMARKS.md` & note `n=1`/live-variance caveats) |
| `results/e2e/e2e_results.json` | Tracked (`M`) | **Verified Benchmark Output** | Updated `8/8` passing fixture measurements matching `docs/BENCHMARKS.md` (`16.7 ms` browser, `73.3 ms` Notepad) | **`TRACK`** (commit updated values) |
| `results/agent_benchmark/HARNESS_VALIDATION.md` & `harness_validation.json` | Untracked (`??`) | **Verified Benchmark Output (Oracle Only)** | Reproducible deterministic `20/20` oracle telemetry (`0` LLM calls, `0` user paths); directly matches `benchmarks/bench_agent_20tasks.py` | **`TRACK`** (commit alongside `bench_agent_20tasks.py`) |
| `results/perf_study/` (`BENCHMARK_REPORT.md`, `all_results.json`, `exp1_4_uia.json`, `exp5_remote_ops.json`, `exp6_7_9_browser.json`, `exp8_freshness.json`) | Untracked (`??`) | **Machine-Specific Study (`~608 KB`)** | Hardware-tied Windows 11 `i5-11400F` (`2026-11-24`), `0` user paths/secrets, `"engine_untouched": true`; directly cited in `docs/BENCHMARKS.md` & `docs/RESEARCH_FINDINGS.md` | **`TRACK`** *(reproducible locally on Win11 via `python -m benchmarks.run_all --exp all`; real-site metrics cannot reproduce byte-for-byte externally — already disclosed)* |
| `results/crops/`, `results/crops_bench/`, `results/runtime/`, `results/agent_benchmark/{crops,runtime}/` | Ignored (`!!`) | **Temporary Logs & Crops** | Local PNG crops (`3` PNGs) + `19` per-task runtime JSONs | **`KEEP-LOCAL`** (gitignored by `/results/...`) |

---

## 4. Git Working-Tree Workstream & Commit-Boundary Proposal

Current `git status` mixes multiple independent workstreams. Never combine them into a single commit or revert another agent's work:

| Priority | Proposed Atomic Commit Scope | Included Files | Notes / Boundaries |
| :---: | :--- | :--- | :--- |
| **0** | **Repo Hygiene / `.gitignore` Anchoring** | `.gitignore` *(applying proposed diff above)* | Must land **before or first** so `/live_runs/` and `/skill_updates/` stop hiding `research_archive/live_runs/` and `research_archive/skill_updates/`. |
| **1** | **Workstream A — Cursor Overlay Test Update** | `tests/test_cursor_overlay.py` (`M`) | Isolates `bring_window_to_front` Z-order test refinement; verify with `pytest` before committing. |
| **2** | **Benchmark Suite Fixes (`9-Exp Study`)** | `benchmarks/bench_action_freshness.py`, `benchmarks/bench_browser.py`, `benchmarks/bench_remote_ops.py`, `benchmarks/bench_uia.py`, `benchmarks/run_all.py` (`M`) | Preserves all empirical bugfixes separately from results and docs. |
| **3** | **Verified Benchmark & Study Result Sync** | `results/benchmarks/benchmarks_real.{json,md}`, `results/e2e/e2e_results.json` (`M`), `results/perf_study/*` (`??`) | Pairs with `benchmarks/` methodology and existing `docs/BENCHMARKS.md` citations. |
| **4** | **20-Task Agent Harness & Oracle Baseline** | `benchmarks/agent_tasks.py`, `benchmarks/bench_agent_20tasks.py`, `results/agent_benchmark/HARNESS_VALIDATION.md`, `results/agent_benchmark/harness_validation.json` (`??`) | Self-contained agent harness (`0` LLM calls). |
| **5** | **Documentation Consolidation & Research Archive** | `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `DOCUMENTATION_REORGANIZATION_REPORT.md`, `GITHUB_PREP_AUDIT.md`, `docs/*`, `research_archive/*`, root `D` removals (`AUDIT_REPORT.md`/`FIX_*`/`TASK_PLAN.md`/`SKILL_UPDATE_REPORT*`/`COPYRIGHT_ATTRIBUTION_AUDIT.md`), `skill_updates/2026-11-26_final/m1_gap_probes/RESULTS.md` link repair | Wait for `.gitignore` commit (#0) so all `12` archived `.md` moves stage cleanly. |
| **6** | **Release Privacy Cleanup (`skill_updates/` Tracked History)** | Untrack leaking tracked files in `skill_updates/` (`m0_env_git.txt`, `server_check.json`, path-hardcoded `.py`/`.md`) + history rewrite decision | **Maintainer authorization required** (`git filter-repo` or fresh orphan release branch if pushing publicly so `f0fd6ba..3e67e49` paths don't persist in GitHub history). |
| *(None)* | **Engineering Roadmap (`P1`/`P2`)** | *No code files in working tree* | Strictly planned in `docs/OPTIMIZATION_ROADMAP.md`; zero `src/` edits pending. |

---

## 5. GitHub Readiness Inspection

| Surface | Inspected State | Gaps / Conflicts Identified |
| :--- | :--- | :--- |
| **CI Workflow (`.github/workflows/ci.yml`)** | Runs `windows-latest`, Python `3.12`, `CUL_SKIP_DESKTOP: "1"`, `pip install -e ".[dev,benchmarks]"`, `playwright install chromium`, `compileall`, `pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning` | **1. HIGH:** `tests/test_audit_fixes.py:631` (`test_p0_3_win32_save_as_commit_and_dialog_alerts`) checks only `sys.platform != "win32"` (missing `CUL_SKIP_DESKTOP == "1"` / `@pytest.mark.windows_desktop`), risking failure/hang on headless CI desktop (`asksaveasfilename` + `MessageBoxW`). **2.** `tests/test_cursor_overlay.py` desktop tests skip on `CUL_SKIP_DESKTOP == "1"`, but lack `@pytest.mark.windows_desktop` marker. **3.** CI does not run `python scripts/verify_copyright_headers.py`. **4.** No full `pytest` verification executed yet on `d47b4e9` + uncommitted overlay diff. |
| **License & Notices (`LICENSE`, `NOTICE`, `COPYRIGHT`)** | `LICENSE` = Apache-2.0 (`Copyright 2026 Mohamed Gomaa`); `NOTICE` verifies all 12 runtime/transitive packages compatible (zero GPL/AGPL); `scripts/verify_copyright_headers.py` passes **`67/67`** eligible files | Pre-P0 `2026-11-26-copyright-attribution-audit.md` mentioned `66/66`; new `67/67` run passes, cleanly preserved in archive. |
| **Authorship & Package Metadata (`AUTHORS.md`, `CITATION.cff`, `pyproject.toml`, `requirements.txt`)** | All consistently identify **Mohamed Gomaa** (`Apache-2.0`, `0.1.0-alpha` / `0.1.0a0`, Windows OS classifier, Python `>=3.10`). `requirements.txt` matches `pyproject.toml` core deps cleanly | `pyproject.toml` does not yet define `[project.urls]` (`Repository`, `Issues`). `README.md` uses `https://github.com/mohgomaa-art/computer-use-lite.git` (must match final GitHub slug). |
| **Security & Templates (`SECURITY.md`, `.github/`)** | `SECURITY.md` reflects `P0-4`/`P0-5` + open TOCTOU/`KillSwitch`/`DirectWS` limits cleanly; templates (`bug_report.md`, `research_question.md`, `PULL_REQUEST_TEMPLATE.md`) use valid relative links | `SECURITY.md` intentionally omits a personal email and directs researchers to **GitHub Private Vulnerability Reporting** (must be enabled in repo settings on GitHub after creation). |
| **Agent Prompt Skill (`.agents/skills/computer-use-lite/`)** | `5` tracked files (`SKILL.md`, `references/*`, `evals/*`) | Frozen at `3e67e49` (pre-Overlay & pre-`P0-2..P0-5`); clearly documented as un-synced outside this pass. |

---

## 6. Security & Privacy Blockers Summary

1. **Git-Tracked Local Paths in `skill_updates/` (`BLOCKER FOR PUBLIC PUSH`):** `12` tracked files under `skill_updates/` (especially `m0_env_git.txt` with `62` lines and `server_check.json` + `6` `.py` scripts) contain `C:\Users\<USER>\...` workstation paths inside `HEAD` and commits `f0fd6ba..3e67e49`. **Action:** Untrack/remove or sanitize them **and** squash/filter commits (or initialize a clean release branch) before pushing publicly.
2. **Literal Rule Token Mention in Archived Baseline (`LOW / OPTIONAL`):** `research_archive/release_prep/2026-11-26-baseline/{PUBLICATION_BOUNDARY,FINAL_RELEASE_READINESS}.md` quote the literal local username token inside example grep rules (`0` file paths exposed). Optionally generalize to `<LOCAL_USER>` if strict automated scanner parity (`0` keyword hits) is desired.
3. **Ephemeral Sandbox Desktop IDs (`INFO`):** `exebox-RQDBU...`, `exebox-ZZCPD...`, `exebox-REOZN...` appear in historical audit/run archives (random Win32 AppContainer/sandbox desktop names, non-secret).
4. **Open Engine Security Boundaries (`DOCUMENTED, NOT HIDDEN`):** Loopback `DirectCdpClient` TCP endpoint (`DirectWS=True`), OS-level DNS-rebinding TOCTOU (`P0-4`), unvalidated direct Python `BrowserSession` calls, and `KillSwitch` initial `GetCursorPos` fail-open remain openly documented in [SECURITY.md](SECURITY.md) — **ensure public repo README/About describes it as Experimental Research Preview**.

---

## 7. Pre-Push Checklist (`Action Sequence Upon Maintainer Approval`)

1. [ ] Apply the anchored `.gitignore` diff (Section 1) so `/live_runs/`, `/fix_runs/`, `/skill_updates/`, and `/research_trace/` stay ignored while `research_archive/{live_runs,skill_updates}/` track normally.
2. [ ] Decide & execute `skill_updates/` history hygiene: untrack leaking `skill_updates/` logs/scripts (`m0_env_git.txt`, `server_check.json`, hardcoded `.py` paths) and scrub/squash commits (`f0fd6ba..3e67e49`) before pushing to a public remote.
3. [ ] Gate `tests/test_audit_fixes.py::test_p0_3_win32_save_as_commit_and_dialog_alerts` (`@pytest.mark.windows_desktop` + `CUL_SKIP_DESKTOP == "1"`) and add `@pytest.mark.windows_desktop` to the 4 desktop overlay tests in `tests/test_cursor_overlay.py`. Optionally add `python scripts/verify_copyright_headers.py` to `.github/workflows/ci.yml`.
4. [ ] Run full verification after code/test changes (`CUL_SKIP_DESKTOP=1 pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning`, interactive Windows `pytest`, and `python scripts/verify_copyright_headers.py`).
5. [ ] Commit Workstreams 0–5 atomically (never bundling `tests/test_cursor_overlay.py`, `benchmarks/`, `results/`, `.gitignore`, and `docs/`+`research_archive/` into one commit).
6. [ ] Create GitHub repository under `https://github.com/mohgomaa-art/` matching `README.md` URL / `pyproject.toml`, configure **Private Vulnerability Reporting (Security Advisories)** before making repository public, verify `git ls-files` path scan returns `0` personal path leaks across `HEAD` and pushed commits, then push cleanly.

---

**Audit Status:** Complete (`GITHUB_PREP_AUDIT.md` written; awaiting explicit authorization before editing `.gitignore`/tests, staging, committing, or configuring a GitHub remote).

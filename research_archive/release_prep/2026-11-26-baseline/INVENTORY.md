> [!NOTE]
> **Archival Provenance:** Moved from `release_preparation/INVENTORY.md` (pre-move SHA-256: `2D6AE37E5D227D408B163206F7F421BF0FAC88A67EFD7B9B368A6849D146F444`). Archived Release Preparation Artifact Inventory captured at `HEAD=3e67e49` (pre-Workstream A & pre-P0). See [Documentation Reorganization Report](../../../DOCUMENTATION_REORGANIZATION_REPORT.md) and [docs/INDEX.md](../../../docs/INDEX.md) for current repository state. See also [Archive Index](../../INDEX.md) and [README](../../../README.md).
> *(Absolute local workstation URIs and relative paths were normalized for archival portability; original findings, figures, and scope claims below are preserved verbatim.)*

# Phase 0 — Repository Forensic Inventory (`computer-use-lite`)

> **Inspection Timestamp:** `2026-11-26` (`[MEASURED]` from local filesystem, Git CLI, Python `importlib.metadata`, and `pytest`).
> **Scope Note:** Non-destructive read-only forensic capture taken prior to release documentation updates.

---

## 1. Git Repository State

| Property | Measured Value |
| :--- | :--- |
| **Git Top-Level** | Nested repository directory `computer-use-lite/` (`[MEASURED]`) |
| **Current Branch** | `main` (`* main`, zero other branches) |
| **`HEAD` Commit** | `3e67e492947fc032f4a8914865d8638c41ecb2ec` (`docs(skill): record M5 held-out validation metrics and verified FINAL_SKILL_UPDATE_REPORT`) |
| **Remotes** | None (`[]`) |
| **Tags** | None (`[]`) |
| **Git `user.name` / `user.email`** | `TODO Copyright Holder` / `todo@example.invalid` (placeholder preparation config) |
| **Total History Commits (`HEAD`)** | `25` commits (`150` distinct historical blobs scanned) |
| **Tracked Files (`git ls-files`)** | `123` files across `22` top-level entries |
| **Untracked Files (`--exclude-standard`)** | `155` files (`AUDIT_REPORT.md`, `RUN_REPORT.md`, `benchmarks/agent_tasks.py`, `benchmarks/bench_agent_20tasks.py`, `fix_runs/`, `live_runs/`, `research_trace/`, `results/`) |
| **Ignored Files (`--ignored`)** | `175` files (`.pytest_cache/`, `__pycache__/`, `*.png` captures in `archive/screenshots/`, `live_runs/`, `results/`, `skill_updates/`) |
| **Pre-Existing Dirty Tracked Files (`8`)** | `benchmarks/bench_{action_freshness,browser,remote_ops,uia}.py`, `benchmarks/run_all.py`, `results/benchmarks/benchmarks_real.{json,md}`, `results/e2e/e2e_results.json` (`500` insertions, `264` deletions) |

---

## 2. Commit History Overview (`25` Commits)

| Commit Range | Scope & Purpose | Notes |
| :--- | :--- | :--- |
| `ab8e417`..`8744f98` (`4` commits, `2026-11-24`) | Initial repo organization (`src/computer_use_lite/`, `src/engine/`, `tests/`, `benchmarks/`, `experiments/`, `results/`, `archive/stale_h2_grid/`, `LICENSE`, `NOTICE`, `README.md`, `CONTRIBUTING.md`, `.github/workflows/ci.yml`, `docs/ARCHITECTURE_DECISION.md`) | Contains `[TODO: Copyright Holder]` placeholders. |
| `bc7b72f`..`2280fcc` (`12` commits, `2026-11-26`) | Audit thresholds (`FIX_PLAN.md`), pre-audit snapshot (`0e42dde`), failing-first tests (`test_audit_fixes.py`), targeted `src/`/`tests/` fixes (`47bea1b..6a2f0fb`, `2280fcc` covering `P-01`, `P-02` localhost fixture, `P-03`, `P-04`, `P-06`, `P-09`, `P-10`, `P-19b`) | Latest `src/` commit is `6a2f0fb` (`2026-11-26 12:09:59 +0200`). |
| `abebcff`..`a922c3b` (`3` commits, `2026-11-26`) | `M6` doc reconciliation, `FIX_REPORT.md`, and live testing plan (`TASK_PLAN.md`) | `abebcff` introduced a local machine `cwd` path in `README.md`. |
| `f0fd6ba`..`3e67e49` (`6` commits, `2026-11-26`) | Agent skill updates (`.agents/skills/computer-use-lite/`), working ledgers (`skill_updates/`), `SKILL_UPDATE_REPORT.md`, `FINAL_SKILL_UPDATE_REPORT.md` | Introduces `91` tracked local username path references inside `skill_updates/` & `FINAL_SKILL_UPDATE_REPORT.md`. |

---

## 3. Directory & Artifact Classification Inventory

| Path | Files | Bytes (`all`) | Tracking State | Category / Relationship to Current `HEAD` |
| :--- | ---: | ---: | :--- | :--- |
| `src/computer_use_lite/` | `11` `.py` (+pyc) | `401,829` (incl. `src/engine/`) | Tracked (`100%`) | Core production engine & MCP server (`6a2f0fb`). |
| `src/engine/` | `9` `.py` | *(above)* | Tracked (`100%`) | Thin `sys.modules[__name__] = importlib.import_module("computer_use_lite.*")` backwards-compatibility shims (`[VERIFIED-CODE]`, sync-verified). |
| `tests/` | `6` src (+pyc) | `568,343` | Tracked (`100%`) | Test suites (`test_engine_audit.py`, `test_audit_fixes.py`, `test_e2e.py`, `test_mcp_server.py`, `test_benchmarks_study.py`, `fixtures/form.html`). Current pre-release run: `52 passed in 68.86s` (`[MEASURED]`). |
| `.github/` | `1` `.yml` | `650` | Tracked (`100%`) | GitHub Actions `windows-latest` CI running headless (`CUL_SKIP_DESKTOP=1`) compile + `pytest -v -rs`. |
| `docs/` | `1` `.md` | `9,825` | Tracked (`100%`) | `ARCHITECTURE_DECISION.md` (`H1–H3` verdicts, `benchmarks_real` §3 summary, perf study KEEP/DROP/HOLD). |
| `benchmarks/` | `13` (`11` `.py`, `2` `.html`) | `512,509` | `11` Tracked (`5` dirty), `2` Untracked | Performance study suite (`run_all.py`, `bench_*.py`, `corpus.py`, `benchmark_real.py`) + `agent_tasks.py` / `bench_agent_20tasks.py` (untracked deterministic 20-task harness). |
| `experiments/` | `7` (`5` `.py`, `2` `.html`) | `212,353` | Tracked (`100%`) | Historical/diagnostic probes (`h1_canvas_probe.py`, `h1b_latency_cluster.py`, `h2_desktop_gate0.py`, `h2_desktop_grid.py`, `win32_probe.py`). |
| `archive/` | `18` (`4` tracked) | `1,933,687` | `4` Tracked (`stale_h2_grid/`, `README.md`), `14` Ignored | Explicit negative historical evidence (`stale_h2_grid`) + gitignored local screenshots/runtime state. |
| `results/` | `45` (`11` tracked, `27` untracked, `7` ignored) | `1,961,478` | Mixed (`3` tracked dirty) | Curated experiment reports (`h1*`, `h2_gate0*`, `h3*`), real benchmarks (`benchmarks_real.*`), updated perf study (`results/perf_study/`), `20`-task oracle harness validation (`results/agent_benchmark/`), E2E JSON (`e2e_results.json`), plus ignored crops/runtime logs. |
| `.agents/` | `5` (`3` `.md`, `2` `.json`) | `39,768` | Tracked (`100%`) | Local IDE agent skill definition & evals (leave untouched during release doc prep per boundary rules). |
| Root governance/docs | `5` tracked (`LICENSE`, `NOTICE`, `README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`) | `29,422` | Tracked | Project manifests & license notices; contains `[TODO: Copyright Holder]` and `README.md:73` personal path. |
| Root audit/session reports & working folders | `AUDIT_REPORT.md`, `RUN_REPORT.md`, `FIX_PLAN.md`, `FIX_REPORT.md`, `TASK_PLAN.md`, `SKILL_UPDATE_REPORT.md`, `FINAL_SKILL_UPDATE_REPORT.md`, `fix_runs/`, `live_runs/`, `research_trace/`, `skill_updates/` | `> 20 MB` (`233+` files) | Mixed tracked (`skill_updates`, `*FIX*`, `TASK_PLAN`, `*SKILL*`) + untracked | Internal engineering, live-run captures, skill validation transcripts, and research trace dossiers containing machine-specific paths/desktops. |

---

## 4. Package Structure & Dependency License Verification

Verified directly from `pyproject.toml`, `requirements.txt`, and `importlib.metadata` in the active Python `3.12` environment (`[MEASURED]`):

| Dependency | Spec (`pyproject.toml`) | Installed | Verified License | Role |
| :--- | :--- | :--- | :--- | :--- |
| `playwright` | `>=1.40` | `1.64.0` | `Apache-2.0` | Browser launch, lifecycle, DOM/CDP host |
| `pillow` | `>=10.0` | `12.3.0` | `MIT-CMU` | Cropped PNG export & pixel utilities |
| `websockets` | `>=14.0` | `17.2` | `BSD-3-Clause` | Direct persistent CDP WebSocket client (`DirectCdpClient`) |
| `mcp` | `>=1.25.0` | `1.30.0` | `MIT` | FastMCP stdio server & MCP protocol types |
| `uiautomation` | `>=2.0.29; sys_platform == 'win32'` | `2.0.29` | `Apache 2.0` | Optional / auxiliary Windows UIA |
| `comtypes` | `>=1.5.0; sys_platform == 'win32'` | `1.5.0` | `MIT` | Native COM/UIA client (`CUIAutomation8`) |
| `pytest` (optional `dev`) | `>=7.0` | `9.1.1` | `MIT` | Test runner |
| `psutil` (optional `benchmarks`) | `>=6.0` | `7.2.2` | `BSD-3-Clause` | Subprocess/orphan telemetry (`tests/` & `benchmarks/`) |
| Transitive (`anyio`, `pyee`, `greenlet`, `typing-extensions`) | — | `4.15.1`, `14.0.0`, `3.5.6`, `4.16.0` | `MIT`, `MIT`, `MIT AND PSF-2.0`, `PSF-2.0` | Runtime/async transitive packages |

**License Compatibility Verdict:** All verified direct and transitive licenses are permissive (`Apache-2.0`, `MIT`, `MIT-CMU`, `BSD-3-Clause`, `PSF-2.0`) and compatible with **Apache-2.0**. *(Note: `mcp` and `anyio` should be added to `NOTICE`'s third-party dependency inventory alongside existing entries.)*

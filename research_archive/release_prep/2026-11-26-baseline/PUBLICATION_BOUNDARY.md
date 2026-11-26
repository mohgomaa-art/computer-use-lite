> [!NOTE]
> **Archival Provenance:** Moved from `release_preparation/PUBLICATION_BOUNDARY.md` (pre-move SHA-256: `905C16E57450B233D1BB283F81861955F9A11F657D7379B563BC44CB26A7A265`). Archived Publication Boundary Policy drafted during `3e67e49` release preparation. See [README.md](../../../README.md) and [research_archive/INDEX.md](../../INDEX.md) for current public/local separation. See also [Archive Index](../../INDEX.md) and [README](../../../README.md).
> *(Absolute local workstation URIs and relative paths were normalized for archival portability; original findings, figures, and scope claims below are preserved verbatim.)*

# Phase 2 — Curated Public Release Publication Boundary (`v0.1.0-alpha`)

> **Classification Key:**
> - **`PUBLIC`** — Include verbatim in public GitHub release (`clean, reproducible, attribution-verified, 0 personal paths/secrets`).
> - **`PUBLIC-SUMMARIZED`** — Distill technical methods, verified tables, and negative findings into curated `docs/` (`RESEARCH_METHODOLOGY.md`, `BENCHMARKS.md`, `RESEARCH_HISTORY.md`, `KNOWN_LIMITATIONS.md`) while keeping verbose/noisy working artifacts out of public release trees.
> - **`PRIVATE`** — Keep on owner's workstation only (contains local usernames/paths `<LOCAL_USER>`, raw OS desktop screenshots, full LLM transcripts, IDE/host session artifacts).
> - **`REMOVE-FROM-RELEASE`** — Exclude from curated public release branch/tag (pre-release planning checklists, internal working scripts, scratch outputs, gitignored caches).

---

## 1. Complete Repository Classification Matrix

| Path / Directory | Current Git Status | Classification | Rationale & Action |
| :--- | :--- | :---: | :--- |
| `src/computer_use_lite/` (`11` `.py` files) | Tracked | **`PUBLIC`** | Core library, MCP server, tests/security modules. Zero personal paths/secrets verified (`[MEASURED]`). |
| `src/engine/` (`9` `.py` compatibility shims) | Tracked | **`PUBLIC`** | Clean thin alias package re-exporting `computer_use_lite` modules (`[VERIFIED-CODE]`). |
| `tests/` (`5` `.py` suites + `fixtures/form.html`) | Tracked | **`PUBLIC`** | Reproducible unit, audit-fix, MCP stdio, benchmark-contract, and E2E suites. Zero personal paths/secrets verified. |
| `benchmarks/` (`11` `.py` tracked + `agent_tasks.py`, `bench_agent_20tasks.py` + `fixtures/`) | `11` Tracked (`5` dirty), `2` Untracked | **`PUBLIC`** | Reproducible benchmark harnesses + dual-origin OOPIF/shadow corpus (`benchmarks/agent_tasks.py` and `bench_agent_20tasks.py` should be included cleanly with honest `oracle_harness_validation_only` labeling). Zero personal paths/secrets verified (`[MEASURED]`). |
| `experiments/` (`5` `.py`, `2` `.html`) | Tracked | **`PUBLIC`** | Essential negative/exploratory hypothesis scripts (`H1`, `H1b`, `H2`, `win32_probe.py`) enabling independent inspection of rejected paths. |
| `archive/README.md` & `archive/stale_h2_grid/` | Tracked | **`PUBLIC`** | Explicitly labeled negative historical archive (documents `(0, 87)` px browser-chrome offset bug). |
| `archive/screenshots/` & `archive/runtime_state/` | Ignored | **`PRIVATE`** | Raw PNG window/screen captures (`address bars may show local file paths`) & old runtime states; keep gitignored. |
| `docs/` (`ARCHITECTURE_DECISION.md` + new `RESEARCH_METHODOLOGY.md`, `KNOWN_LIMITATIONS.md`, `ARCHITECTURE.md`, `BENCHMARKS.md`, `RESEARCH_HISTORY.md`) | Tracked / New | **`PUBLIC`** | Canonical public engineering, epistemic methodology, verified benchmarks, and limitations documentation. |
| Root Open-Source Files (`LICENSE`, `NOTICE`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `AUTHORS.md`, `CITATION.cff`, `CHANGELOG.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`, `.gitattributes`, `.github/`) | Tracked / Updated / New | **`PUBLIC`** | Attribution fixed (`Mohamed Gomaa`), personal `cwd` removed from `README.md`, standard community/security templates added. |
| `results/benchmarks/benchmarks_real.{json,md}` | Tracked (updated) | **`PUBLIC`** | Curated multi-target latency/token measurements (contextualized honestly in `docs/BENCHMARKS.md` as `n=1` pre-Step 5 reference + live caveats). |
| `results/perf_study/` (`all_results.json`, `exp*.json`, `BENCHMARK_REPORT.md`) | Untracked (clean JSON/MD) | **`PUBLIC-SUMMARIZED`** | Commit `results/perf_study/` OR keep summarized cleanly in `docs/BENCHMARKS.md` with explicit disclosure of `Exp 8` confound (`os.fsync` mismatch) and pre-Step 5 corpus scores. Zero personal paths verified (`[MEASURED]`). |
| `results/experiments/` (`h1*`, `h1b*`, `h2_gate0*`, `h3_report.md`) | Tracked | **`PUBLIC`** | Core empirical record of `H1`/`H1b`/`H2`/`H3` hypotheses (`0` secrets/paths). |
| `results/agent_benchmark/` (`HARNESS_VALIDATION.md`, `harness_validation.json`, `runtime/*.json`, excluding `crops/*.png`) | Untracked (`crops/` ignored) | **`PUBLIC-SUMMARIZED`** | Keep `HARNESS_VALIDATION.md` / `harness_validation.json` documented honestly as `oracle_harness_validation_only` (`0` LLM calls); exclude `crops/` PNGs (`PRIVATE`/ignored). |
| `results/e2e/e2e_results.json` | Tracked (updated) | **`PUBLIC`** | Latest clean `8/8` fixture E2E output (`0` personal paths; check whether desktop timing matches clean baseline). |
| `results/crops/`, `results/crops_bench/`, `results/runtime/` | Ignored | **`PRIVATE`** | Ephemeral local captures & task state logs; keep gitignored. |
| `.agents/` (`5` skill/eval files) | Tracked | **`PUBLIC` or `REMOVE-FROM-RELEASE`** | **Owner choice:** No personal paths verified (`0` matches `[MEASURED]`), clean skill packaging (`lint_skill.py` `0` flags); keep if demonstrating agent skill integration or exclude if keeping repo pure library/MCP. Do NOT edit during engine prep. |
| `skill_updates/` (`45` tracked files + `43` PNGs) | Tracked / Ignored PNGs | **`PRIVATE` / `REMOVE-FROM-RELEASE`** | **CRITICAL:** Contains **`77` local username path occurrences** (`<LOCAL_USER>`), IDE workspace IDs, Antigravity script references, and desktop window captures (`Preflight`, `M1`, `M5`). Summarize M5 methodology/conclusions in `docs/BENCHMARKS.md` + `docs/RESEARCH_HISTORY.md` (`PUBLIC-SUMMARIZED`). |
| `FINAL_SKILL_UPDATE_REPORT.md`, `SKILL_UPDATE_REPORT.md` | Tracked | **`REMOVE-FROM-RELEASE`** | Contains `15` `<USER_HOME>` links + internal agent run logs (`PID`, conversation hashes). |
| `AUDIT_REPORT.md`, `RUN_REPORT.md`, `FIX_PLAN.md`, `FIX_REPORT.md`, `TASK_PLAN.md` | Tracked (`FIX_*`, `TASK_PLAN`) & Untracked (`AUDIT_*`, `RUN_*`) | **`PUBLIC-SUMMARIZED` / `REMOVE-FROM-RELEASE`** | Contain `170+` local `<LOCAL_USER>` path refs (untracked) & internal session step numbers (`step 2258`, `exebox-*`). Distill ALL technical findings, verified defect evidence, and pre/post comparisons honestly into `docs/BENCHMARKS.md`, `docs/KNOWN_LIMITATIONS.md`, and `docs/RESEARCH_HISTORY.md`. |
| `live_runs/`, `fix_runs/`, `research_trace/` | Untracked (`fix_runs`, `live_runs` PNGs ignored) | **`PRIVATE` / `REMOVE-FROM-RELEASE`** | Raw desktop captures and window lists from the owner's personal desktop session + local machine username paths (`<LOCAL_USER>`). **Never publish publicly.** |
| `release_preparation/` (`INVENTORY.md`, `SECURITY_REVIEW.md`, `PUBLICATION_BOUNDARY.md`, `FINAL_RELEASE_READINESS.md`) | New local working dossier | **`REMOVE-FROM-RELEASE`** | Internal release engineering gate & pre-publication checklist for Mohamed Gomaa. Exclude from the final clean public tag once reviewed (or keep private). |

---

## 2. Git History Hygiene Note

Because `abebcff` and `f0fd6ba..3e67e49` already committed `92` occurrences of `<LOCAL_USER>` (inside `README.md`, `FINAL_SKILL_UPDATE_REPORT.md`, and `skill_updates/`) into existing local `main` history:
- Per audit policy, **local `main` history has NOT been deleted or rewritten** during preparation.
- For public GitHub publication, Mohamed Gomaa should create a clean release branch/initial public snapshot from the `PUBLIC`-classified files only (detailed step-by-step in `FINAL_RELEASE_READINESS.md`), keeping `main` locally as the full private research archive.

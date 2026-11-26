> [!NOTE]
> **Archival Provenance:** Moved from `release_preparation/FINAL_RELEASE_READINESS.md` (pre-move SHA-256: `A2DC50326D5B59DB287E138070FBBA4C544417F94507FB9390C9E191D98E738B`). Archived Release Readiness Scorecard captured at `HEAD=3e67e49` prior to Workstream A Cursor Overlay & `P0-1..P0-5`. Superseded by [docs/KNOWN_LIMITATIONS.md](../../../docs/KNOWN_LIMITATIONS.md), [docs/BENCHMARKS.md](../../../docs/BENCHMARKS.md), and [SECURITY.md](../../../SECURITY.md). See also [Archive Index](../../INDEX.md) and [README](../../../README.md).
> *(Absolute local workstation URIs and relative paths were normalized for archival portability; original findings, figures, and scope claims below are preserved verbatim.)*

# Final Release Readiness Report — Computer Use Lite (`v0.1.0-alpha`)

**Project:** Computer Use Lite (`CUL`)  
**Target Version:** `v0.1.0-alpha` (`pyproject.toml`: `0.1.0a0`)  
**Release Classification:** `Public Research Preview — Experimental — Not Production Ready`  
**Creator & Lead Developer:** **Mohamed Gomaa**  
**Assessment Date:** `2026-11-26`  
**Committed Baseline `HEAD`:** `3e67e492947fc032f4a8914865d8638c41ecb2ec` (`main`, `0` remotes, `0` tags)

---

## A. Executive Verdict

**Release Verdict: `CONDITIONALLY READY` (Curated Orphan Release Export Only — `NOT READY` for Raw `main` Push or Direct Export From Current Dirty Working Tree)**

All public documentation, licensing (`Apache-2.0`, `Mohamed Gomaa`), citation metadata, dependency notices, reproducibility docs, issue/PR templates, `.gitignore`/`.gitattributes`, and CI workflow hardening are complete and verified clean (`0` `[TODO:]` tags, `0` secrets, `0` broken links, `0` personal paths across all newly authored/updated public release files, `compileall rc=0`).

However, pushing raw `main` or cutting a tag directly from the current working tree is **blocked** until the four explicit owner gates below are resolved.

---

## B. Explicit Release Blockers & Owner Action Gates

### 1. CRITICAL BLOCKER — Uncommitted `src/` & `tests/` Edits in Shared Working Tree (`1` Test Failure Observed)
- **Observed Fact (`[MEASURED]`):** During release documentation preparation (`2026-11-26 16:37–16:45`), concurrent upstream `P0` development left uncommitted edits directly in the working tree:
  - Modified tracked files: `src/computer_use_lite/browser_cdp.py` (`DirectCdpClient` multiplexed `Target.setAutoAttach` flattened OOPIF + `cursor_overlay` hooks), `src/computer_use_lite/session_manager.py` (`show_cursor` / `_with_busy_cursor`), `tests/test_audit_fixes.py` (`test_p0_1_site_per_process_oopif_discovery_gt_and_actions`).
  - Untracked new files: `src/computer_use_lite/cursor_overlay.py`, `tests/test_cursor_overlay.py`.
- **Current Test Measurement on Live Working Tree:**  
  `pytest tests -v -rs -W error::pytest.PytestReturnNotNoneWarning` (`57` tests collected) -> **`56 passed, 1 failed in 81.97s`**:
  - `test_p0_1_site_per_process_oopif_discovery_gt_and_actions`: `PASSED`
  - `tests/test_cursor_overlay.py` (`4/4`): `PASSED`
  - **`tests/test_audit_fixes.py::test_m2_p01_dense_dom_python_latency_and_occlusion_parity`:** **`FAILED`** (`AssertionError: Dense-DOM local Python p50=32.87ms >= 30.0ms`, threshold `< 30.0ms`).
- **Baseline Comparison:** Prior to those `16:37–16:45` `src/` edits, committed `HEAD` (`3e67e49`) passed **`52/52` in `68.86s`**.
- **Required Owner Choice:**
  - **Option A (Recommended for clean `v0.1.0-alpha`):** Commit or stash the in-progress OOPIF + `cursor_overlay` work onto a separate `feat/p0-oopif-cursor` branch, export `v0.1.0-alpha` cleanly from committed `HEAD` (`3e67e49`) + release docs/packaging, and verify `52/52` clean green on that exact release worktree.
  - **Option B (Include OOPIF + `cursor_overlay` in `v0.1.0-alpha`):** Investigate/resolve the `32.87 ms` `p50` latency regression on `test_m2_p01` (without lowering `< 30.0 ms`), achieve `57/57` clean pass, and update `README.md`, `CHANGELOG.md`, `docs/ARCHITECTURE.md`, and `docs/KNOWN_LIMITATIONS.md` to document the newly added OOPIF attachment and `cursor_overlay.py` API.

### 2. CRITICAL BLOCKER — Personal Filesystem Paths Inside Local `main` History
- **Observed Fact (`[MEASURED]`):** Committed `main` history (`25` commits, `150` unique blobs) holds `92` local OS username/path occurrences across `12` tracked files (`README.md:73`, `FINAL_SKILL_UPDATE_REPORT.md`, and `10` files in `skill_updates/`), plus `510+` occurrences in untracked/ignored local artifacts (`AUDIT_REPORT.md`, `RUN_REPORT.md`, `live_runs/`, `fix_runs/`, `research_trace/`). Commits `abebcff` and `f0fd6ba..3e67e49` are already baked into local `main` history.
- **Required Owner Action:** **NEVER push local `main` history directly to GitHub.** Export a clean single-commit / orphan public branch (`release/v0.1.0-alpha`) strictly from `PUBLIC`-classified files (commands in Section F), keeping full `main` history untouched on the owner's local machine.

### 3. HIGH RISK — Verified Open Security Limitations (`v0.1.0-alpha` Preview Scope)
- **Observed Facts (`[MEASURED]` in `sec_probes.py` on `HEAD`):**
  1. **HTTP `302` Redirect SSRF (`OPEN`):** `validate_navigation_url()` validates initial entry URLs only; Chromium follows external `HTTP 302 Location: http://127.0.0.1:<port>/...` directly (`secret_hits: 1`).
  2. **DNS-Rebinding TOCTOU (`OPEN`):** Python `socket.getaddrinfo()` check executes separately from Chromium socket resolution; offline `socket.gaierror` falls through.
  3. **Unauthenticated Local CDP Socket (`OPEN` on host):** `--remote-debugging-port` serves unauthenticated `/json/version` and origin-less WebSocket control to local processes (browser-tab `Origin:` CSWSH upgrades return `HTTP 403` on Chromium `1.64`).
  4. **`KillSwitch` Fail-Open Init (`OPEN`):** First-sample `GetCursorPos()` `OSError` is swallowed inside `move_mouse()`.
- **Release Gate:** All four items are explicitly disclosed in [`SECURITY.md`](../../../SECURITY.md) and [`docs/KNOWN_LIMITATIONS.md`](../../../docs/KNOWN_LIMITATIONS.md). Decide whether to ship `v0.1.0-alpha` strictly labeled single-user trusted host preview OR authorize a pre-tag `src/` security patch (`context.route()` redirect hop guard + `KillSwitch` fail-closed init) before publishing.

### 4. MEDIUM BLOCKER — Unconfirmed Owner Public Metadata (Never Fabricated)
Fill in confirmed values prior to pushing public GitHub tags:
- Repository URL (`https://github.com/<org>/computer-use-lite`): update `git clone <repository-url>` in [`README.md`](../../../README.md), `[project.urls]` in [`pyproject.toml`](../../../pyproject.toml), and `repository-code` in [`CITATION.cff`](../../../CITATION.cff).
- Vulnerability reporting / maintainer contact: enable **GitHub Security Advisories** and/or set a verified contact email in [`SECURITY.md`](../../../SECURITY.md) and [`pyproject.toml`](../../../pyproject.toml).
- Local Git identity: replace placeholder `TODO Copyright Holder <todo@example.invalid>` in local `.git/config` before authoring public release commits (`git config user.name "Mohamed Gomaa"` + confirmed email).
- Pre-existing label in tracked `docs/ARCHITECTURE_DECISION.md:29`: contains literal string `exebox-` (an internal sandbox desktop identifier `GetThreadDesktop = exebox-...`). Clarify or scrub wording if internal runner naming should not appear publicly.

---

## C. Public Artifact Verification Matrix (`phase8_verify.py` Results)

Every item below was checked deterministically on disk (`compileall_rc = 0`, `broken_links = []`, `private_links = []`):

| Artifact | Status | Verification Summary |
| :--- | :--- | :--- |
| [`LICENSE`](../../../LICENSE) | Ready | Full Apache-2.0 (`189` lines) verbatim with `Copyright 2026 Mohamed Gomaa` at line 177. |
| [`NOTICE`](../../../NOTICE) | Ready | `Mohamed Gomaa` attribution + full permissive dependency inventory (`playwright`, `pillow`, `websockets`, `mcp`, `uiautomation`, `comtypes`, `pytest`, `psutil`, `anyio`). |
| [`pyproject.toml`](../../../pyproject.toml) | Ready | Valid TOML (`tomllib`): `name="computer-use-lite"`, `version="0.1.0a0"`, `authors=[{"name": "Mohamed Gomaa"}]`, `3 - Alpha` classifier, zero placeholder `[TODO:]`. |
| [`AUTHORS.md`](../../../AUTHORS.md) & [`CITATION.cff`](../../../CITATION.cff) | Ready | Solely attributes **Mohamed Gomaa** (`0.1.0-alpha`, `Apache-2.0`, `2026-11-26`). |
| [`CHANGELOG.md`](../../../CHANGELOG.md) | Ready | Matches committed `HEAD` (`3e67e49`) fixes, architecture, rejected paths, and unresolved limits. |
| [`README.md`](../../../README.md) | Ready | Matches `HEAD` (`3e67e49`) signatures/architecture, zero `<LOCAL_USER>` paths, zero `[TODO:]`, clear trust warnings & test instructions. *(Update if Option B merges `cursor_overlay` + OOPIF before tag.)* |
| [`docs/RESEARCH_METHODOLOGY.md`](../../../docs/RESEARCH_METHODOLOGY.md) | Ready | Epistemic tags, control-vs-ablation methodology, `TOKENS_EST`/`Exp 8`/`M5`/oracle disclosures. |
| [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) | Ready | Complete component map & Mermaid flow matching committed `HEAD` (`3e67e49`) and verified `13` MCP tools. |
| [`docs/BENCHMARKS.md`](../../../docs/BENCHMARKS.md) | Ready | Verified `E2E 8/8`, `benchmarks_real`, `9-Exp` study verdicts, `P-01`/`P-04`/`P-06`, and `20/20` `oracle_harness_validation_only` warning. |
| [`docs/KNOWN_LIMITATIONS.md`](../../../docs/KNOWN_LIMITATIONS.md) | Ready | Exhaustive honest inventory (`OOPIF`, multi-tab, `#32770` Save As, RTL `PrintWindow`, `KillSwitch`, `302` SSRF, unrun VLMs). |
| [`docs/RESEARCH_HISTORY.md`](../../../docs/RESEARCH_HISTORY.md) | Ready | Preserves negative findings (`H1`–`H3`, `archive/stale_h2_grid/` `(0,87)` px bug, `PID 4076` stale run warning, `P-19(c)` `NOT-REPRODUCED`). |
| [`SECURITY.md`](../../../SECURITY.md) | Ready | Trust boundaries, verified controls, disclosed `OPEN` issues, advisory warning without invented email. |
| [`.gitignore`](../../../.gitignore) & [`.gitattributes`](../../../.gitattributes) | Ready | Protects future captures/traces (`live_runs/`, `fix_runs/`, `skill_updates/`, `research_trace/`, `results/agent_benchmark/crops/`, `*.tmp`, `*.bak`) & LF/CRLF rules. |
| [`.github/`](../../../.github/workflows/ci.yml) | Ready | `ci.yml` adds `-W error::pytest.PytestReturnNotNoneWarning`; added clean `bug_report.md`, `research_question.md`, `PULL_REQUEST_TEMPLATE.md`. |

---

## D. Publication Boundary Summary (Public vs. Excluded)

Refer to [`PUBLICATION_BOUNDARY.md`](PUBLICATION_BOUNDARY.md) for the full table:
- **`PUBLIC` (Include in `release/v0.1.0-alpha`):** `src/` (committed `HEAD` clean `computer_use_lite/` + `engine/`), `tests/` (committed `HEAD`), `benchmarks/`, `experiments/`, `archive/README.md`, `archive/stale_h2_grid/`, `results/{benchmarks,e2e,experiments,perf_study}/` + sanitized `results/agent_benchmark/{HARNESS_VALIDATION.md,harness_validation.json,runtime/*.json}`, `docs/`, root packaging/governance files, `.gitignore`, `.gitattributes`, `.github/`. *(Note: `.agents/` has `0` leaks and can optionally be kept or excluded per owner preference.)*
- **`EXCLUDE / KEEP PRIVATE`:** `skill_updates/`, `FINAL_SKILL_UPDATE_REPORT.md`, `SKILL_UPDATE_REPORT.md`, `AUDIT_REPORT.md`, `RUN_REPORT.md`, `FIX_PLAN.md`, `FIX_REPORT.md`, `TASK_PLAN.md`, `live_runs/`, `fix_runs/`, `research_trace/`, `release_preparation/`, all `*.png` screenshot/crop outputs (`results/crops/`, `results/agent_benchmark/crops/`, `archive/screenshots/`, `archive/runtime_state/`).

---

## E. Exact Verification Metrics Observed in This Session

1. **Baseline `HEAD` `3e67e49` (pre-16:37 working-tree edits):** `pytest tests -q -rs -W error::pytest.PytestReturnNotNoneWarning` -> **`52 passed in 68.86s`**.
2. **Live Working Tree (with concurrent `16:37–16:45` uncommitted OOPIF/`cursor_overlay` files):** `pytest tests -v -rs -W error::pytest.PytestReturnNotNoneWarning` -> **`56 passed, 1 failed in 81.97s`** (`test_m2_p01_dense_dom_python_latency_and_occlusion_parity` failed at `p50=32.87ms >= 30.0ms`).
3. **Static & Compile Checks (`phase8_verify.py`):**
   - `python -m compileall -q src experiments benchmarks tests`: `exit code 0`.
   - `22` public release files checked: `0` `[TODO:`, `0` `<LOCAL_USER>`, `0` `AppData`, `0` `antigravity`, `0` `broken_links`, `0` `private_links` (`docs/ARCHITECTURE_DECISION.md` has pre-existing literal `"exebox-"`).
   - `mcp_server.build_server()` registers exact `13` tools matching documentation.
   - `python -m pip check`: `3` pre-existing unrelated global environment protobuf conflicts (`googleapis-common-protos`, `google-api-core`, `proto-plus`), `0` dependency conflicts among CUL requirements.

---

## F. Safe Non-Destructive Public Export Steps (For Owner Execution — Do Not Run Automatically)

When ready to publish `v0.1.0-alpha` cleanly **without mutating local `main` history or shipping private files**:

```powershell
# 1. Inspect and stash/branch any uncommitted P0 work first if choosing Option A:
git status
# e.g., git stash push -m "wip-p0-oopif-cursor" -- src/ tests/

# 2. Configure clean public commit author identity:
git config user.name "Mohamed Gomaa"
git config user.email "<your-confirmed-email>"

# 3. Create an isolated clean orphan branch for public history:
git worktree add --orphan -b release/v0.1.0-alpha ..\cul-public-release

# 4. Copy ONLY PUBLIC-classified files from computer-use-lite into ..\cul-public-release
#    (Explicitly omit: skill_updates/, live_runs/, fix_runs/, research_trace/, release_preparation/,
#     AUDIT_REPORT.md, RUN_REPORT.md, FIX_PLAN.md, FIX_REPORT.md, TASK_PLAN.md,
#     SKILL_UPDATE_REPORT.md, FINAL_SKILL_UPDATE_REPORT.md, *.png, results/crops*, results/runtime*)

# 5. Inside ..\cul-public-release:
#    - Add confirmed repo URL & security contact to README.md, pyproject.toml, CITATION.cff, SECURITY.md
#    - Run verification gate cleanly inside ..\cul-public-release:
#        python -m compileall -q src experiments benchmarks tests
#        pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning
#        git grep -i "<LOCAL_USER>"   # must return zero hits across entire tree & orphan commit
#    - git add -A && git commit -m "chore(release): initial public research preview v0.1.0-alpha"
#    - git tag -a v0.1.0-alpha -m "Computer Use Lite v0.1.0-alpha (Public Research Preview)"
#    - git remote add origin https://github.com/<owner>/computer-use-lite.git
#    - git push -u origin release/v0.1.0-alpha --tags
```

---

## G. Post-`v0.1.0-alpha` Roadmap

1. Merge & stabilize Option B `OOPIF` (`Target.setAutoAttach`) + `cursor_overlay` with passing `p50 < 30 ms` `test_m2_p01` regression check (`v0.1.1-alpha` / `v0.2.0-alpha`).
2. Add `context.route()` SSRF validation on HTTP redirects and fail-closed `KillSwitch` initialization.
3. Decouple Win32 `ctypes.WinDLL("user32")` imports for Linux/macOS browser-only compatibility.
4. Execute and publish live VLM runs on [`benchmarks/bench_agent_20tasks.py`](../../../benchmarks/bench_agent_20tasks.py).

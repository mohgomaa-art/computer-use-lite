# Evidence Index (Pre-Fix Baseline)

All evidence pre-dating repairs is frozen under `C:\Users\mnile\Desktop\Computer-use-lite\EVIDENCE\PRE_FIX_2026-11-27\` with a verified `SHA256_MANIFEST.txt` (`496` files).

| Category | Frozen Evidence Path (`EVIDENCE/PRE_FIX_2026-11-27/...`) | Description |
| :--- | :--- | :--- |
| **Git Repository Bundle & Tags** | `git/computer-use-lite-public-release-pre-fix.bundle`, `git/bundle_verify.txt`, `git/git_refs_and_tags.txt`, `git/github_releases.txt` | Complete pre-fix repository history (`0d19a9e`, `566f08d`, `de27b49`), tag `baseline-pre-fix-2026-11-27`, GitHub Release state (`v0.1.0a0`, `v0.1.0a2`). |
| **Secondary Checkout Preservation** | `git/secondary_checkout_status.txt`, `git/secondary_checkout_diff.patch` | Unmodified preservation record of sibling `computer-use-lite` (`d47b4e9`) uncommitted docs/scripts/test state. |
| **Verified Source Archives** | `archives/computer-use-lite-v0.1.0a0-0d19a9e.zip`, `archives/computer-use-lite-v0.1.0a2-de27b49.zip`, `archives/archive_equivalence.json` | Blob-by-blob SHA-256 verified ZIP exports (`118/118` and `179/179` matched). |
| **Arabic Review PDFs** | `audits/computer-use-lite_ المميزات والعيوب (2026-11-27).pdf`, `audits/computer-use-lite_ تقرير الهجوم الشامل (2026-11-27).pdf` | Original 5-page Pros/Cons & 10-page Comprehensive Attack reports. |
| **Linux Audit Package** | `audits/AUDIT_REPORT (1).md` | Independent Ubuntu sandbox audit of `0d19a9e` (`18,210 B`). |
| **Windows 11 + Merged Audits** | `audits/audit_2026-11-27/AUDIT_REPORT.md`, `audits/audit_2026-11-27/final_package/pkg/{AUDIT_REPORT_FINAL,OPEN_QUESTIONS_FINAL,REPRO_COMMANDS_FINAL,CHANGES_VS_INPUTS}.md`, `audits/audit_2026-11-27/evidence/*`, `audits/audit_2026-11-27/run_*.py` | Real Windows 11 reproductions, screenshots (`b5_*`, `b9_*`, `b10_*`, `b12_*`), JSON probe logs, and merged cross-OS report. |
| **Cursor Reference Patch** | `audits/cursor-audit-fix.patch.txt`, `audits/CUL_cursor_strict_prompt-919dc90a.txt` | AI-authored cursor fix diff (491 lines; audited & corrected before use) and cursor engineering spec. |
| **Historical Browser Benchmarks** | `benchmarks/runs_20261126_195128/*` | `72`-run Playwright MCP vs CUL raw JSONL, protocol, preflight logs, and `REPORT.md` (`fdc92d9`). |
| **Desktop Pilot & Readiness** | `pilot/DESKTOP_NATIVE_VS_CUL_PILOT.md`, `pilot/NATIVE_COMPUTER_USE_PREFLIGHT.md`, `pilot/desktop-pilot-evidence/*` | Supervised `@oai/sky` Calculator smoke check and `T1`/`T2` harness preparation manifests (`BLOCKED` prior to scored trials). |

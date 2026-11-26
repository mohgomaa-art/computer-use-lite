## Summary
Describe the motivation and exact scope of this change. If modifying performance or discovery behavior, cite before/after numbers measured on clean `HEAD`.

## Type of Change
- [ ] Bug fix (`src/computer_use_lite/`)
- [ ] New benchmark / experiment (`benchmarks/`, `experiments/`)
- [ ] Documentation / research clarity (`README.md`, `docs/`)
- [ ] Tests / CI / packaging

## Quality & Attribution Checklist
- [ ] Preserves Apache-2.0 (`SPDX-License-Identifier: Apache-2.0` on new `.py` files) and authorship metadata
- [ ] Contains **zero** personal usernames, home-directory paths, API tokens, or raw desktop screenshots
- [ ] Preserves negative evidence and exact caveats (no omitted failures or weakened test assertions)
- [ ] Matches actual function/tool signatures

## Verification Performed
State exact commands executed and exact pass/skip counts (do not mark tests passed unless actually run after your final edit):

- Non-desktop suite (`CUL_SKIP_DESKTOP=1 pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning`):
- Full Windows desktop suite (`pytest -v -rs -W error::pytest.PytestReturnNotNoneWarning`):
- Compile check (`python -m compileall -q src experiments benchmarks tests`):

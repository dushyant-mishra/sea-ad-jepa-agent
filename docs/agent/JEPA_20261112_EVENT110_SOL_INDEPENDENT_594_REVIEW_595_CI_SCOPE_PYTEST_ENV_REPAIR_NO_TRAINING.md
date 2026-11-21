# Event110 — Independent Sol review of Macha #594 and scoped #595 repair

**Date: 2026-11-12 UTC.** This is **non-training safety engineering**, not biological validation, restart qualification or independent approval of the author's repair. All 109 earlier chronology events, 74 no-repeat keys, Event90 scientific source/data/results, Event102 WSL incident, Events104–109 and prior negative experiments remain intact. Do not repeat Stage81, TD19/57B/59, R5, corrected real replay #314, Full104/Level4, V79/V80 or synthetic experiments.

## New confirmed RED findings on #594 (head a3d35716d1eacb24b3fc4cf6c99fe758e0619d56)

1. The non-training workflow guard skipped every workflow with a `branches:` filter. Harmless synthetic automatic push-to-main and PR-to-main examples using `pytest -q tests/test_*.py` were not rejected; the historical exception was too broad.
2. The explicit-list pytest runner inherited `PYTEST_ADDOPTS` and `PYTEST_PLUGINS`. In a harmless scratch example, PYTEST_ADDOPTS collected **2 tests instead of the 1 named test**. A synthetic plugin also loaded through PYTEST_PLUGINS despite disabled automatic plugin discovery. No neural model, optimizer, backward, EMA or real data was involved.

## Repair on stacked [draft #595](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/595)

**Exact repaired head:** `37dc2469f05d83a6dcfc38cedc54e4f9325bd10c`, based on unchanged draft #594. Only the historical `d1-independent-closure-ci.yml` Git blob `a0e3fb2622992630ce705467bfcb3aad7aa1001e` is exempt from automatic workflow glob scanning; its old branch/manual D1 route is **not approved for dispatch**. Any changed copy loses the exception, and automatic main-branch workflows are scanned. PYTEST_ADDOPTS and PYTEST_PLUGINS are cleared before the already literal, guarded pytest arguments. Five new static/stdlib mocked tests cover those risks. New tests use no torch, pytest collection, model or training.

**Exact Git source blobs:**
- `scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py`: `ca7cf7ac867d13494e7e2fdb861f4025a07370d6`
- `tests/test_ci_sol_594_scope_and_pytest_env_static_red.py`: `78d7caf16cf762d137e29d46d72a11fa05e85277`
- `.github/workflows/jepa-v5-macha-review-590-593-static-no-training.yml`: `5d399e1584f3792d80596f3b29d54228d91f7fab`

**Exact-head author CI: 5/5 workflows GREEN**, runs [43316634301](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/43316634301), [43316634333](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/43316634333), [43316634396](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/43316634396), [43316634295](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/43316634295), [43316634606](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/43316634606). Python 3.11.9 and 3.12.7 static-only test steps both green. These CI outcomes are not an independent Macha review; #595 remains draft, unmerged and **Macha reciprocal acceptance pending**. AST checking does not prove no indirect/transitive optimizer execution from arbitrary helpers; do not overclaim repo-wide zero-step safety.

## Custody / scientific boundary

Event109 already reported Macha's four original #590–#593 defects and #594; Event110 is strictly the two additional #594 findings and #595. No real SEA-AD data, protected V80 controller, GPU, optimizer step, backward, EMA, qualified physical probe or trained V5 representation was used. Stage4, D1, real-data rights and training remain unauthorised.

Canonical #322: append Event110 (110 total), no-repeat key 75. Mirror this original human document and machine map byte-for-byte on #460, prepend Event110 and repin to current #322 head. Future verified work uses Event111+; no rewriting old records.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test/contract head before this qualification update:
`20d6a1246e48cde4d9d8993c19b8cd2d20cf4c87`

## Qualified pure helpers

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`
- `scripts/v5/td_target_tournament_precision.py`
- `scripts/v5/td_target_tournament_prefreeze.py`

No helper implements a biological target statistic, matrix reader, neural model, or authorization path.

## Preserved TDD sequence

1. Initial three modules absent -> 3 collection errors.
2. Minimal implementation -> 18 passed.
3. Truncated authority-map tests -> 2 failed / 8 passed; repaired -> 21 passed.
4. Candidate-specific gate expansion -> 7 failed / 7 passed; repaired -> 25 passed.
5. Precision helper absent -> collection RED; implementation -> 32 combined passed.
6. Prefreeze-manifest helper absent -> collection RED; implementation -> 39 combined passed.
7. Historical token-identity/support mechanism audit showed the old architecture could expose source/operator through gene-identity support patterns even without explicit operator embeddings. Tests were expanded with `Q5_Q_ADDRESS_ONLY_DEFEAT` and `L6_IDENTITY_SUPPORT_BASELINE_DEFEAT`; the old frozen contract failed broadly (`13 failed / 3 passed` in the local adjudicator RED cycle).
8. Minimal contract/adjudicator repair -> current combined focused suite:

`41 passed in 0.05s`

## Candidate-specific gates

- **C1 relational shared:** scale-free recurrence; fine locality not primary; matched wrong-cell defeat.
- **C2 measured query target:** q scalar absent from student; q-excluded teacher ablation; q-free target normalization; q-count-only defeat; **q-address-only defeat**.
- **C3 learned shared state:** learned-teacher disjoint-view continuity; conditional technology-imprint control; evidence response; separate depth/measurement response; collapse/shortcut defeat; **identity+support-only baseline defeat**.
- **C4 structured composite:** increment over constituents plus learned-state/query protections, including q-address-only and identity+support-only baseline defeat.
- **C5 regulatory/chromatin specialist:** circularity control; independent provenance; no causal-truth claim; support/abstention.

No aggregate score can override a failed common or candidate-specific gate.

## Null, leakage, precision, and prefreeze guarantees

- matched wrong-cell reassignment preserves donor/operator/support/depth-bin/detection-bin and changes identity;
- singleton strata are `NOT_ESTIMABLE`, never silently crossed;
- direct/transitive q-scalar ancestry into student or target normalization is rejected;
- q-address conditioning and separately recorded teacher-only q auxiliary evidence remain distinguishable;
- a supplied predeclared `alpha_eff` determines exact donor-sign and permutation-resolution floors;
- helpers do not choose alpha from outcomes;
- the prefreeze manifest freezes the complete decision family before outcomes and leaves biological results `NOT_OPENED`;
- donor upper bounds may prove a case incapable of resolving a planned gate but never prove actual biological estimability.

## Historical design/shortcut audits bound to this scaffold

- `docs/agent/TD_HISTORICAL_QUANTITATIVE_DESIGN_CALIBRATION_20261011.md`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json`
- `docs/agent/TD_84_CELL_TRUTH_TABLE_ROLE_AUDIT_20261011.md`
- `docs/agent/TD_HISTORICAL_TOKEN_IDENTITY_SHORTCUT_MECHANISM_AUDIT_20261011.md`

These establish source/donor/support asymmetry, objective precision rules, the 84-cell set's structural-only role, and the need to defeat identity/support shortcuts explicitly.

## Static no-value/no-training audit

Production helpers contain no `h5py`, `anndata`, `scanpy`, `torch`, corrected-value reader, `read_h5ad`, `h5py.File`, `numpy.load`, `open_memmap`, optimizer, or model-fit call. Only Python standard-library utilities are used.

## Exact SHA-256 identities for changed shortcut-gate artifacts

- `scripts/v5/td_target_tournament_scaffold.py` — `f2dd398e437d6a014a820e7430feadfc70d4c4ef21f361f7f3255a882f69d209`
- `tests/v5/test_td_target_tournament_scaffold.py` — `2635438920990941c442f321c541e7be469c4bff833b7535f7792ba1e9a8f237`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1.json` — `e3594769db122362c0c824046bf1bf6cce199f531bf454c13953188286cd999a`

Previously qualified helper hashes remain unchanged and are recorded in machine state.

## Limitation

Repository-wide pytest has not run in the reconstructed local harness. Draft PR #275 had no GitHub Actions run at the last check. This is focused synthetic qualification only.

## Authority boundary

No corrected values, G6/G7, corrected replay, real tournament, target selection, representation selection, TD60, Stage4, pathology, or training are authorized. The scaffold remains fixture-only.

Terminal:
`SYNTHETIC_SCAFFOLD_QUALIFIED__IDENTITY_SUPPORT_SHORTCUT_GATES_BOUND__41_FOCUSED_TESTS_GREEN__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

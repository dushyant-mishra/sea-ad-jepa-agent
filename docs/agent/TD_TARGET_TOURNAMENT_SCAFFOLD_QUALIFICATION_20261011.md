# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test head before qualification artifacts:
`248a483550da651442b7d1d709850a9e0613fda5`

The controlling audit branch has independently added representation/shortcut crosswalks. Those sharpen constraints but grant no value or training authority.

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
5. Precision helper absent -> collection RED; implementation -> 7/7 green and 32 combined.
6. Prefreeze-manifest helper absent -> collection RED; implementation -> 7/7 green.
7. Current combined focused suite:

`39 passed in 0.05s`

## Candidate-specific gates

- C1: scale-free relational recurrence; fine locality not primary; matched wrong-cell defeat.
- C2: q scalar absent from student; q-excluded teacher ablation; q-free target normalization; q-count-only defeat.
- C3: learned-teacher disjoint-view continuity; conditional technology-imprint control; evidence response; separate depth/measurement response; collapse/shortcut defeat.
- C4: increment over constituents plus learned-state and query-leakage protections.
- C5: circularity control; independent provenance; no causal-truth claim; support/abstention.

No aggregate score can override a failed common or candidate-specific gate.

## Null, leakage, precision, and prefreeze guarantees

- matched wrong-cell reassignment preserves donor/operator/support/depth-bin/detection-bin and changes identity;
- singleton strata are `NOT_ESTIMABLE`, never silently crossed;
- direct/transitive q-scalar ancestry into student or target normalization is rejected;
- q-address conditioning and separately recorded teacher-only q auxiliary evidence remain distinguishable;
- a supplied predeclared `alpha_eff` determines exact donor-sign and permutation-resolution floors;
- the helper never chooses alpha from outcomes;
- a prefreeze config declares the complete decision family before outcomes;
- Bonferroni `alpha_eff = family_alpha / M` is derived from that frozen family;
- donor upper bounds can prove a decision case mathematically incapable of resolving the planned sign gate before outcomes;
- a sufficient donor upper bound does **not** claim actual estimability because support/ties may still reduce usable donors;
- generated manifests retain biological result `NOT_OPENED` and all authority flags false.

At family alpha 0.05 with 20 frozen cases, the fixture test derives alpha_eff 0.0025, minimum 10 non-tied donors for two-sided sign-test resolution, and 399 null draws merely for exact p-value resolution.

## Historical quantitative calibration now frozen

`docs/agent/TD_HISTORICAL_QUANTITATIVE_DESIGN_CALIBRATION_20261011.md` and `TD_TARGET_TOURNAMENT_DESIGN_CALIBRATION_V1.json` bind metadata-only design facts including source imbalance, donor/operator inequality, support asymmetry, held-out source gaps, shortcut strength, rare-event donor counts, and the rule that historical null replicate counts/performance values are not future thresholds.

## Static no-value/no-training audit

Production helpers contain no `h5py`, `anndata`, `scanpy`, `torch`, corrected-value reader, `read_h5ad`, `h5py.File`, `numpy.load`, `open_memmap`, optimizer, or model-fit call. Only Python standard-library utilities are used.

## Exact new helper identities

- `scripts/v5/td_target_tournament_prefreeze.py` — `69da225f5138bce13028304f47c6802ade2a53d892aab168cd8542c6ab6508d4`
- `tests/v5/test_td_target_tournament_prefreeze.py` — `f1584beb0c8818e6f714d6b6047e5f451794cd95a72ae1136e49a5fe77fa8e84`
- `scripts/v5/td_target_tournament_precision.py` — `519b0b607b7365e005d42f2360a738381e94e1a4e5b13efdd0362e56df278eeb`
- `tests/v5/test_td_target_tournament_precision.py` — `40582508948f0a7e7e8d3be6e760574c477dc4ce6f5fbbe5cb8553099ee2345e`

Earlier qualified helper hashes remain recorded in machine state.

## Limitation

Repository-wide pytest has not run in the local reconstructed harness. Draft PR #275 currently has no GitHub Actions run, so this is focused synthetic qualification only.

## Authority boundary

No corrected values, G6/G7, corrected replay, real tournament, target selection, representation selection, TD60, Stage4 or training are authorized. Current scaffold remains fixture-only.

Terminal:
`SYNTHETIC_SCAFFOLD_QUALIFIED__PREFREEZE_AND_PRECISION_INFRASTRUCTURE_READY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

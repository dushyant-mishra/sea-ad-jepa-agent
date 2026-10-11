# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test/contract/precision head before qualification artifacts:
`a9d7f45b0598fbb1a4bf3ecb1d037b9d1b904e1c`

Original base scientific-audit head:
`318e6badb38a879f0109bdc318b75340bb230f81`

The controlling audit branch subsequently advanced through documentation-only representation crosswalk commits, including explicit learned-representation shortcut evidence. Those crosswalks sharpened this scaffold but did not grant value or training authority.

## Scope

Qualified pure helper modules:

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`
- `scripts/v5/td_target_tournament_precision.py`

They implement no biological target statistic, matrix reader, neural model or authorization mechanism.

## TDD evidence

1. **RED 1:** 3 collection errors because all three initial production modules were absent.
2. **GREEN 1:** 18 passed after minimal implementation.
3. **RED 2:** 2 failed / 8 passed when self-audit showed truncated authority maps were accepted.
4. **GREEN 2:** 21 passed after exact authority-key enforcement.
5. **RED 3:** 7 failed / 7 passed when candidate-specific scientific gates were added to tests and the coarse adjudicator could not represent them.
6. **GREEN 3:** 25 passed after exact candidate-specific gate enforcement.
7. **RED 4:** precision tests failed at collection because the precision module did not exist.
8. **GREEN 4:** precision helper 7/7 passed; combined scaffold suite now reports:

`32 passed in 0.05s`

## Candidate-specific gate surface

- **C1 relational shared:** scale-free recurrence; fine/deep locality not primary; matched wrong-cell defeat.
- **C2 measured query target:** q scalar absent from student; q-excluded teacher ablation; q-free target normalization; q-count-only defeat.
- **C3 learned shared state:** learned-teacher disjoint-view continuity; conditional technology-imprint control; evidence-response behavior; separate measurement-depth response; collapse/shortcut defeat.
- **C4 structured composite:** increment over constituents plus learned-state and query-leakage protections.
- **C5 regulatory/chromatin specialist:** circularity control; independent provenance; no causal-truth claim; support/abstention.

No favorable aggregate score can override a failed common or candidate-specific gate.

## Matched-null and query-lineage guarantees

Tests establish that matched wrong-cell reassignment changes identity while preserving donor/operator/support/depth-bin/detection-bin; singleton strata are `NOT_ESTIMABLE`; q-address conditioning is allowed; direct or transitive q-scalar ancestry into student/target normalization is rejected; cycles fail closed; teacher-only q auxiliary evidence remains separable.

## Outcome-blind precision/estimability helper

The precision module chooses no alpha and sees no biological outcome. Given a prospectively frozen `alpha_eff`, it derives:

- minimum non-tied donors required for an exact two-sided sign gate to have enough p-value resolution;
- exact two-sided donor sign p-values;
- whether donor-direction recurrence is mathematically resolvable;
- minimum permutation draws needed merely to attain `alpha_eff` resolution under `(1 + extreme)/(B + 1)`.

At alpha 0.05, the donor-sign resolution floor is 6 non-tied donors and the permutation-resolution floor is 19 draws. These are resolution floors, not recommended effect thresholds or high-precision Monte-Carlo budgets.

## Static no-value / no-training audit

AST inspection found no `h5py`, `anndata`, `scanpy`, `torch`, corrected-value reader, `read_h5ad`, `h5py.File`, `numpy.load`, `open_memmap`, optimizer or model-fit call. The helpers use only Python standard-library facilities.

## Exact local SHA-256 identities

- `scripts/v5/td_target_tournament_scaffold.py` — `68af489178dffa7bdad67e01e4acd806906067893da686845a63441130e1505c`
- `scripts/v5/td_target_tournament_nulls.py` — `f57a878ff466d15f232c964d50d643baa0660ff24486513f99116247ae255b8f`
- `scripts/v5/td_query_information_guard.py` — `55a87fbeb6a8825af941b36abc0ebc3ab14366b751357dc0fc5d37ec14438a41`
- `scripts/v5/td_target_tournament_precision.py` — `519b0b607b7365e005d42f2360a738381e94e1a4e5b13efdd0362e56df278eeb`
- `tests/v5/test_td_target_tournament_scaffold.py` — `fa8411ec42ab66970e01d43959cc9adcb758e7fc5bf991398660f80bb6824abb`
- `tests/v5/test_td_target_tournament_nulls.py` — `1b95fd21396394e1d1fcaf342cb7955406698e0434ece20084d050e8c6b94386`
- `tests/v5/test_td_query_information_guard.py` — `9c33caa62c5f473d2586a40ab3fd3fe2edd73827f048722b06c209b3a10260a6`
- `tests/v5/test_td_target_tournament_precision.py` — `40582508948f0a7e7e8d3be6e760574c477dc4ce6f5fbbe5cb8553099ee2345e`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1.json` — `a335f92026132cf7a5a4b161864e3728ae85da0f400b8f970113fe7438e5d4ac`

## Important limitation

Repository-wide pytest was not run in the local reconstructed harness. Draft PR #275 currently has no GitHub Actions workflow runs for its branch head. This is therefore a focused synthetic qualification, not a claim that every repository test passes.

## Authority boundary

No corrected value reads, G6/G7, corrected replay, real tournament execution, target selection, representation selection, TD60, Stage4 or training are authorized. The scaffold remains `fixture_only=true`.

Terminal:

`SYNTHETIC_SCAFFOLD_QUALIFIED__CANDIDATE_SPECIFIC_GATES_AND_PRECISION_RULES_FROZEN__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

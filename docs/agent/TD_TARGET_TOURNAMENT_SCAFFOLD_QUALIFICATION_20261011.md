# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test/contract head before this qualification update:
`7a8a681476d81b3e4d84c20986bebd790c213dba`

Original base scientific-audit head:
`318e6badb38a879f0109bdc318b75340bb230f81`

The controlling audit branch subsequently advanced through documentation-only target/representation crosswalk commits, including explicit learned-representation shortcut evidence. Those crosswalks sharpened the scaffold by requiring a candidate-specific conditional technology-imprint gate; they did not grant value or training authority.

## Scope

This qualification covers only three synthetic/metadata-only helper modules:

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`

They implement no target statistic, no matrix reader, no neural model and no authorization mechanism.

## TDD evidence

### RED 1 — modules absent
Before production modules existed, the three focused test files were executed together. Pytest stopped during collection with exactly three `FileNotFoundError` errors, one for each absent module.

### GREEN 1
After minimal implementation, the focused files reported `18 passed`.

### RED 2 — authority completeness
A self-audit added tests requiring complete frozen authority-key sets. The inherited implementation failed exactly those tests: `2 failed, 8 passed`. A truncated authority mapping could otherwise omit a forbidden key.

### GREEN 2
The validator was repaired to require exact authority-key sets for both contract and candidate receipts. Combined focused result: `21 passed`.

### RED 3 — candidate-specific scientific gates
After the audit branch added explicit representation-shortcut/technology-imprint constraints, tests were expanded so each candidate family has its own frozen gates. The old coarse adjudicator failed this expansion: `7 failed, 7 passed` in the adjudicator file. It did not understand candidate-specific gate sets.

### GREEN 3
The contract/adjudicator now require the exact candidate-specific gate list for each candidate. Combined focused result:

`25 passed in 0.05s`

## Candidate-specific gate surface now frozen in the scaffold

- **C1 relational shared:** scale-free recurrence; deepest/fine locality not primary; matched wrong-cell defeat.
- **C2 measured query target:** q scalar absent from student; q-excluded teacher ablation; q-free target normalization; q-count-only defeat.
- **C3 learned shared state:** learned-teacher disjoint-view continuity; conditional technology-imprint control; evidence-response behavior; separate measurement-depth response; collapse/shortcut defeat.
- **C4 structured composite:** must add information over constituents, retain learned-view continuity/technology control, and retain query leakage protections.
- **C5 regulatory/chromatin specialist:** circularity control; independent provenance; no causal-truth claim; support/abstention.

A favorable aggregate score cannot override failure of any common or candidate-specific gate.

## Matched-null and query-lineage guarantees

The tests additionally establish that:

- matched wrong-cell reassignment changes cell identity while preserving donor/operator/support/depth-bin/detection-bin;
- singleton strata are `NOT_ESTIMABLE`, never reassigned across strata;
- reassignment is deterministic for fixed seed/input;
- q-address conditioning is allowed;
- direct or transitive q-scalar ancestry into the student or target normalization is rejected;
- dependency cycles fail closed;
- a separately recorded teacher-only q auxiliary covariate is permitted.

## Static no-value / no-training audit

AST inspection of all three production modules found no `h5py`, `anndata`, `scanpy`, `torch`, corrected-value reader, `read_h5ad`, `h5py.File`, `numpy.load`, `open_memmap`, optimizer, or model-fit call. Observed imports are only Python standard-library `collections` and `hashlib` in the null constructor.

These modules therefore cannot themselves open the corrected expression substrate or launch training.

## Exact local SHA-256 identities for qualified bytes

- `scripts/v5/td_target_tournament_scaffold.py`
  `68af489178dffa7bdad67e01e4acd806906067893da686845a63441130e1505c`
- `scripts/v5/td_target_tournament_nulls.py`
  `f57a878ff466d15f232c964d50d643baa0660ff24486513f99116247ae255b8f`
- `scripts/v5/td_query_information_guard.py`
  `55a87fbeb6a8825af941b36abc0ebc3ab14366b751357dc0fc5d37ec14438a41`
- `tests/v5/test_td_target_tournament_scaffold.py`
  `fa8411ec42ab66970e01d43959cc9adcb758e7fc5bf991398660f80bb6824abb`
- `tests/v5/test_td_target_tournament_nulls.py`
  `1b95fd21396394e1d1fcaf342cb7955406698e0434ece20084d050e8c6b94386`
- `tests/v5/test_td_query_information_guard.py`
  `9c33caa62c5f473d2586a40ab3fd3fe2edd73827f048722b06c209b3a10260a6`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1.json`
  `a335f92026132cf7a5a4b161864e3728ae85da0f400b8f970113fe7438e5d4ac`

## Important limitation

This local qualification did **not** run the repository-wide pytest suite because the execution harness used an isolated reconstructed subset containing only the new modules/tests. Draft PR #275 exists specifically to obtain repository CI if configured. Until repository CI reports, this is a focused synthetic qualification, not a claim that every repository test passes.

## Authority boundary

This qualification does not authorize corrected value reads, G6/G7, corrected biological replay, real-data tournament execution, target selection, representation selection, TD60, Stage4 or training. The scaffold contract remains `fixture_only=true`.

Terminal:

`SYNTHETIC_SCAFFOLD_QUALIFIED__CANDIDATE_SPECIFIC_GATES_FROZEN__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

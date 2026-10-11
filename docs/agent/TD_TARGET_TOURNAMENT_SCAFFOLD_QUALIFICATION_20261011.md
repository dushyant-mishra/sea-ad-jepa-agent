# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test head before this qualification note:
`7ef08e44bdee698115617213a59c71362bebe9a7`

Base scientific-audit head:
`318e6badb38a879f0109bdc318b75340bb230f81`

## Scope

This qualification covers only three synthetic/metadata-only helper modules:

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`

They implement no target statistic, no matrix reader, no neural model and no authorization mechanism.

## TDD evidence

### RED 1 — modules absent

Before production modules existed, the three focused test files were executed together. Pytest stopped during collection with exactly three `FileNotFoundError` errors, one for each absent module. This established that the tests were exercising new behavior rather than inherited code.

### GREEN 1

After minimal implementation, the three focused files reported:

`18 passed in 0.04–0.06s`

### RED 2 — self-audit of authority completeness

A self-audit then added tests requiring the complete frozen authority-key sets. The inherited implementation failed exactly those tests:

`2 failed, 8 passed`

The failure was substantive: an authority mapping could omit a forbidden key and still pass because only supplied values were checked for `false`.

### GREEN 2

The validator was repaired to require exact authority-key sets for both contract and candidate receipts. Combined focused result:

`21 passed in 0.04s`

## What the tests establish

The scaffold now proves, on synthetic fixtures only:

1. a candidate with a mandatory gate failure is rejected even if its aggregate score is arbitrarily high;
2. C5 regulatory/chromatin can only become an optional-specialist candidate, never a foundation-target candidate;
3. no candidate receipt selects a target or representation or authorizes Stage4/training/value reads;
4. truncated or truthy authority objects fail closed;
5. duplicate candidate receipts fail closed;
6. the matched wrong-cell null always changes cell identity while preserving donor/operator/support/depth-bin/detection-bin;
7. singleton strata are `NOT_ESTIMABLE` rather than reassigned across strata;
8. matched reassignment is deterministic for the same seed and input set;
9. q-address conditioning is permitted;
10. direct q-scalar student input is rejected;
11. indirect q leakage through normalization/QC ancestry is rejected;
12. q-bearing target normalization is rejected;
13. a separately recorded teacher-only q auxiliary covariate is permitted;
14. dependency cycles fail closed.

## Static no-value / no-training audit

AST inspection of all three production modules found:

- no `h5py` import;
- no `anndata` import;
- no `scanpy` import;
- no `torch` import;
- no project corrected-value/read-path import;
- no `read_h5ad`, `h5py.File`, `numpy.load`, `open_memmap`, model-fit or optimizer call.

Observed imports are only Python standard library `collections` and `hashlib` in the null constructor.

Therefore these modules cannot themselves open the corrected expression substrate or launch training.

## Exact local SHA-256 identities for qualified bytes

- `scripts/v5/td_target_tournament_scaffold.py`
  `a7b45804be5eb2d94a919b5e63a110968e45a46d6dd58cdde9346777ff967f4b`
- `scripts/v5/td_target_tournament_nulls.py`
  `f57a878ff466d15f232c964d50d643baa0660ff24486513f99116247ae255b8f`
- `scripts/v5/td_query_information_guard.py`
  `55a87fbeb6a8825af941b36abc0ebc3ab14366b751357dc0fc5d37ec14438a41`
- `tests/v5/test_td_target_tournament_scaffold.py`
  `b4f0ef85b4905706caa575cf926a144296155bcb2c8fdfe02794b380d1684cce`
- `tests/v5/test_td_target_tournament_nulls.py`
  `1b95fd21396394e1d1fcaf342cb7955406698e0434ece20084d050e8c6b94386`
- `tests/v5/test_td_query_information_guard.py`
  `9c33caa62c5f473d2586a40ab3fd3fe2edd73827f048722b06c209b3a10260a6`
- `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1.json`
  `1a673b28a9293f23b53dbe3d68a65d26e387ef8bdb93182f706f9aac46ff90d7`

## Important limitation

This local qualification did **not** run the repository-wide pytest suite because the execution harness used an isolated reconstructed subset containing only the new modules/tests. A draft PR should be used to obtain repository CI if configured. Until then, this is a focused synthetic qualification, not a claim that every repository test passes.

## Authority boundary

This qualification does not authorize:

- corrected value reads;
- G6 or G7;
- corrected biological replay;
- the target tournament on real data;
- target selection;
- representation selection;
- TD60;
- Stage4;
- training.

The scaffold contract remains `fixture_only=true`.

Terminal:

`SYNTHETIC_SCAFFOLD_QUALIFIED__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

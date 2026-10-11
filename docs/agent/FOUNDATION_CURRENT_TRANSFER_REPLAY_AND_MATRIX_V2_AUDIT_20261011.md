# Foundation current-transfer replay + matrix-identifiability V2 audit — 2026-10-11

Scope: synthetic/foundation representation lane only. No target-discovery work is performed here.

## New executable replay surface

PR #269 now carries a dependency-light bounded current-transfer implementation:
- `src/sea_ad_jepa/v4/foundation_current_transfer_v1.py`
- `scripts/v4/run_foundation_current_transfer_v1.py`
- focused tests for held-group nearest-centroid transfer, conditional nuisance decoding, matrix-identifiability summaries, and fail-closed authority.

TDD evidence:
- first RED run `38156315568`: 4 failed / 14 passed, all four failures the intentionally absent current-transfer module;
- second RED run `38156416415`: exposed one bad synthetic fixture plus the intentionally absent CLI; the fixture was repaired rather than changing the algorithm;
- GREEN run `38156521672`, job `114520523294`: **19 passed in 0.52 s**.

The implementation has no outcome-tuned acceptance thresholds and always keeps `representation_freeze_authorized=false`, `factorial_execution_authorized=false`, and `training_authorized=false`.

## Bounded u205 state-chunk replay

The exact u205 41K encoder was evaluated on the authenticated 84-cell / 42-matrix truth table in restartable chunks. The chunk rows were verified against metadata `stable_key` order before scoring.

On the three canonical broad classes (68 scorable cells), a fixed nearest-centroid decoder produced:
- held-out donor broad-biology BA: `0.4934640523`;
- held-out matrix broad-biology BA: `0.4775910364`.

On the same 68 HVS/SEA-AD cells, after subtracting training-fold broad-class centroids, source remained strongly decodable:
- held-out donor conditional source BA: `0.96875`;
- held-out matrix conditional source BA: `0.96875`.

This is an independent bounded cross-check of PR #276's stronger residual-source finding. It is not a production transfer PASS/FAIL because the 84-cell truth table contains only two cells per matrix and no prospective pass threshold was frozen before u205 outcomes. NPH52 is excluded from this conditional source test because it lacks canonical broad labels under the frozen ontology.

## Matrix-identifiability V2 reconciliation

The current PR #276 implementation already defines canonical broad labels as exactly:
- `Neuronal: GABAergic`;
- `Neuronal: Glutamatergic`;
- `Non-neuronal and Non-neural`.

The older committed V1 CSV predated that stricter serialization. Re-running the current `matrix_label_identifiability()` rule on the exact 50K sample-freeze metadata (`SHA-256 79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`) reproduces the mounted V2 CSV **byte-for-byte**:

`FOUNDATION_MATRIX_LABEL_IDENTIFIABILITY_V2.csv` SHA-256 `9938144a00f7bad209506c809ff3fa54747dde10c34373358df7a89defe3f3e3`.

V2 ruling:
- total matrices: `42`;
- canonical-broad `AVAILABLE`: `34`;
- `UNAVAILABLE`: `8`;
- all 7 NPH52 matrices are unavailable;
- SEA-AD caudate is also unavailable for canonical broad-class transfer because its 17 populated broad labels are subclass strings rather than one of the frozen three canonical classes.

This does not make the caudate matrix unusable generally. It means it cannot be included in a canonical broad-class transfer score without constructing a new ontology, which is forbidden post hoc.

## Independent CPU resource confirmation

Fresh CPU measurements in the current environment, 2 PyTorch threads:
- 1 cell: model `1.300 s`, process wall `3.32 s`, peak RSS `770252 KiB`;
- 4 cells: model `6.659 s`, process wall `8.57 s`, peak RSS `1626632 KiB`.

These differ somewhat from PR #276's earlier machine measurements but support the same operational ruling: **CPU diagnostic batch ceiling <=4**. They are not a final production-GPU benchmark.

## Scientific ruling

The new work strengthens, rather than relaxes, the existing terminal:

`FOUNDATION_RESIDUAL_GATES_MEASURED__SUCCESSOR_ACCEPTANCE_RULES_FROZEN__LEARNED_T1_INVARIANCE_NOT_QUALIFIED__CANONICAL_MATRIX_IDENTIFIABILITY_34_OF_42__FINAL_GPU_AND_FULL104_PHYSICAL_GATES_PENDING__REPRESENTATION_FREEZE_BLOCKED__TRAINING_OFF`

No TEST/Morabito, pathology, target-discovery corrected values, representation winner, Stage4, factorial execution, or JEPA training authority is created by this audit.

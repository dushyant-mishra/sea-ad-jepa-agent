# Foundation current-transfer replay + canonical matrix V2 handoff — 2026-10-11

This handoff is for the synthetic/foundation representation lane only. Target discovery is a separate lane.

## Latest verified implementation work

PR #269 now includes a replayable current-transfer diagnostic module and CLI at implementation head `f0044c8b37991375aeeee56e1e47bfbaff7af528`.

Verification history:
- RED `38156315568`: 4 failed / 14 passed, expected missing module;
- RED `38156416415`: 2 failed / 17 passed, one synthetic-fixture defect plus expected missing CLI;
- GREEN `38156521672`, job `114520523294`: **19 passed in 0.52 s**.

The new path computes held-group broad-biology transfer and biology-conditioned source imprint from compact state chunks. It is non-authorizing and has no outcome-tuned thresholds.

## Current u205 bounded replay

Authenticated 84-cell / 42-matrix truth table, exact u205 41K encoder:
- broad-biology held-out donor BA `0.4934640523`;
- broad-biology held-out matrix BA `0.4775910364`;
- source BA after training-fold broad-class residualization, held-out donor `0.96875`;
- source BA after training-fold broad-class residualization, held-out matrix `0.96875`.

Interpretation: the learned state remains strongly source/acquisition informative after coarse biological conditioning. This agrees with PR #276's stronger fit-pop residual-source result and does not qualify technology invariance.

## Canonical matrix identifiability is now 34/42

PR #276's current code defines only three canonical broad classes. Re-execution against the exact 50K sample-freeze metadata reproduces `FOUNDATION_MATRIX_LABEL_IDENTIFIABILITY_V2.csv` byte-for-byte, SHA-256 `9938144a00f7bad209506c809ff3fa54747dde10c34373358df7a89defe3f3e3`.

Canonical-broad transfer coverage:
- 34 matrices AVAILABLE;
- 8 UNAVAILABLE;
- 7/7 NPH52 unavailable;
- SEA-AD caudate unavailable for this specific broad-class endpoint because its populated labels are subclass strings outside the frozen three-class ontology.

Do not revert to the older 35/42 count for canonical broad-class transfer. Do not invent a mapping after seeing outcomes.

## Resource confirmation

Fresh CPU run, 2 threads:
- 1 cell: `1.300 s` model time, `770252 KiB` peak RSS;
- 4 cells: `6.659 s` model time, `1626632 KiB` peak RSS.

This independently supports the existing laptop diagnostic ceiling `<=4` cells per CPU batch. Final production-GPU qualification remains external.

## Current authority boundary

Use PR #276's prospective successor acceptance contract for any future representation first evaluated after that contract. u0000/u0205 remain excluded from prospective promotion.

Current terminal:
`FOUNDATION_RESIDUAL_GATES_MEASURED__SUCCESSOR_ACCEPTANCE_RULES_FROZEN__LEARNED_T1_INVARIANCE_NOT_QUALIFIED__CANONICAL_MATRIX_IDENTIFIABILITY_34_OF_42__FINAL_GPU_AND_FULL104_PHYSICAL_GATES_PENDING__REPRESENTATION_FREEZE_BLOCKED__TRAINING_OFF`

No representation freeze, scientific factorial execution, Stage4, TEST/Morabito/pathology, or JEPA training is authorized.

# JEPA parallel premise-prefreeze lane checkpoint 03 — 2026-10-06

Takeover record only. No Stage-A or training authority.

Working branch:

`design/premise-qualification-contract-v3-20261006`

Current V3 branch progression:

1. `b149de6e60aa2b068453dd7926217af5e107667a` — V3 premise design anchored to current main and prior V2 governance.
2. `47739d86b2c7cb50809436386062d2f2d0d5ade5` — representation-family tournament; no winner/default.
3. `b17f5016242894ef0190539e29ba61af55942e16` — observation-operator contract.
4. `7018edea1ca58e9cfd42a5e83b625fddb5b15ad1` — external-validation asset matrix using existing audited evidence rather than redoing PRs #188–#199.
5. `9713231e4c71c11535182ae98ec2f49d2c4636dc` — foundation-population estimand prefreeze; `selected_estimand=UNSET_REQUIRES_APPROVAL`.
6. `6a46e0dfd489a0e9c6380eb917f1231cdb2d1d9a` — representation stability protocol.
7. `de948511463b14f22339191ffb98b2070afa81b1` — biological-evidence versus measurement-depth convergence protocol.

Newly frozen scientific distinctions:

- technology/assay is handled as a constrained observation operator, not unrestricted dataset identity;
- representation-family comparison remains neutral among `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, and `STRUCTURED_COMBINED_STATE`;
- stable subspace does not imply stable individual coordinates;
- coordinate-level biological interpretation is prohibited when only subspace stability is demonstrated;
- donor-balanced resampling, principal angles, canonical correlations, alignment diagnostics and degeneracy/eigenvalue-gap checks are required before coordinate claims;
- biological-evidence convergence and measurement-depth convergence are separate uncertainty axes;
- donor/operator/study/technology transport remain separate evidence axes;
- biological OOD and measurement OOD must not be collapsed;
- external != independent; access != exposure; same-nucleus pairing != donor-level separate-nucleus evidence; cell count cannot rescue low donor n;
- Morabito remains protected and unavailable for target selection;
- observational multimodal support cannot establish causality;
- unresolved external-asset facts remain explicit unknowns rather than guessed values;
- estimand candidates include `CELL_WEIGHTED_EMPIRICAL`, `DONOR_WEIGHTED`, `SOURCE_BALANCED_DONOR_WEIGHTED`, and `HIERARCHICAL_TEMPERED`; none is selected;
- any later hierarchical tempering exponent is a scientific estimand parameter and may not be tuned post hoc on biological outcomes.

Current authority boundaries:

- `TRAINING=OFF`;
- Stage A is prefreeze only, not execution authority;
- encoder optimizer updates = 0 during target/representation discrimination;
- EMA updates = 0;
- no target winner;
- no representation winner;
- no estimand selected;
- no deciding numeric threshold selected in this lane;
- TEST sealed;
- Morabito protected.

Next work:

1. publish machine-readable V3 contracts for representation stability, observation operator, evidence/depth convergence, external assets and estimand choices;
2. add fail-closed governance tests/validator against semantic drift;
3. reconcile any current-main movement before opening/merging a PR;
4. independent whole-branch review before merge.

Parallel-lane boundary: do not duplicate runtime optimizer/EMA/checkpoint reconciliation or Macha V77 generator work.

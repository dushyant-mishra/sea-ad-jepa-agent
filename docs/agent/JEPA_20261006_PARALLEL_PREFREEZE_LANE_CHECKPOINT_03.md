# JEPA parallel premise-prefreeze lane checkpoint 03 — 2026-10-06

Takeover record only. No Stage-A or training authority.

Working branch:

`design/premise-qualification-contract-v3-20261006`

Draft PR:

`#220 — Premise qualification V3: stability, observation operator, and uncertainty prefreeze`

Current scientific branch head:

`e7fecec4f15cb70439ce0df1971601e64a2c6a0a`

Current V3 branch progression:

1. `b149de6e60aa2b068453dd7926217af5e107667a` — V3 premise design anchored to current main and prior V2 governance.
2. `47739d86b2c7cb50809436386062d2f2d0d5ade5` — representation-family tournament; no winner/default.
3. `b17f5016242894ef0190539e29ba61af55942e16` — observation-operator contract.
4. `7018edea1ca58e9cfd42a5e83b625fddb5b15ad1` — external-validation asset matrix using existing audited evidence rather than redoing PRs #188–#199.
5. `9713231e4c71c11535182ae98ec2f49d2c4636dc` — foundation-population estimand prefreeze; `selected_estimand=UNSET_REQUIRES_APPROVAL`.
6. `6a46e0dfd489a0e9c6380eb917f1231cdb2d1d9a` — representation stability protocol.
7. `de948511463b14f22339191ffb98b2070afa81b1` — biological-evidence versus measurement-depth convergence protocol.
8. `a793b18ca0f7dbd0c7843d26a5c67a162b5ebe74` — machine-readable V3 prefreeze state.
9. `7c7de0931587b0d86b37f67a9de948a517639313` — first RED governance assertions.
10. `bd3d04147de5fa9628aeaab9bd7071e78a31fbbf` — PR guard workflow introduced; first run exposed a harness defect because pytest was absent.
11. `b6f5766e5ca62d307798bacfa509667a9b500966` — workflow harness repaired by explicitly installing pytest. Run #2 reached the tests and produced the intended RED state: 7 validator-dependent tests failed because the validator file did not yet exist.
12. `3168a7f8931142a160a135786dd35b4f5efb6211` — minimal validator implemented; PR guard run #3 GREEN.
13. `c2baf462fb6f5cd546594dc2b8b6bbb75e7fdb91` — second RED layer added for recoverability semantics, four transfer axes, biological-vs-measurement OOD separation, claim ladder, Stage-A claim ceiling, protected-asset selection, donor-vs-cell count, and observational-to-causal promotion. PR guard run #4: 8 passed / 8 failed exactly on the newly unimplemented invariants.
14. `e7fecec4f15cb70439ce0df1971601e64a2c6a0a` — validator extended only for those named invariants. PR guard run #5 GREEN.

Current governance/CI evidence:

- RED was observed before validator implementation.
- Initial CI harness failure (`pytest` missing) was not misreported as scientific RED; harness was repaired and rerun first.
- First real RED: validator absent, 1 passed / 7 failed with FileNotFoundError at the intended validator path.
- First GREEN: focused V3 surface guard passed.
- Second real RED: 8 existing tests passed / 8 new adversarial mutations failed exactly because those invariants were not yet enforced.
- Second GREEN: run `37499863322`, job `112393795775`, conclusion `success` on `e7fecec4...`.

Newly frozen scientific distinctions:

- technology/assay is handled as a constrained observation operator, not unrestricted dataset identity;
- representation-family comparison remains neutral among `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, and `STRUCTURED_COMBINED_STATE`;
- stable subspace does not imply stable individual coordinates;
- coordinate-level biological interpretation is prohibited when only subspace stability is demonstrated;
- donor-balanced resampling, principal angles, canonical correlations, alignment diagnostics and degeneracy/eigenvalue-gap checks are required before coordinate claims;
- biological-evidence convergence and measurement-depth convergence are separate uncertainty axes;
- donor/operator/study/technology transport remain separate evidence axes;
- biological OOD and measurement OOD must not be collapsed;
- target-object recoverability cannot be promoted to biological-truth recoverability;
- claim ladder remains `RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION`, with no automatic promotion;
- Stage A maximum claim remains `RNA_REPRESENTATION`;
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

1. broaden governance tests to ensure all referenced source documents exist and the CLI validator rejects corrupted canonical state;
2. compare PR #220 against live main and reconcile any new main movement;
3. independent whole-branch scientific review focused on hidden flexibility, representation favoritism, observation-operator shortcut channels, external-asset overclaim, and estimand leakage;
4. keep PR draft and do not merge until review is clean.

Parallel-lane boundary: do not duplicate runtime optimizer/EMA/checkpoint reconciliation or Macha V77 generator work.

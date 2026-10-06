# JEPA parallel premise-prefreeze lane checkpoint 03 — 2026-10-06

Takeover record only. No Stage-A or training authority.

Working branch: `design/premise-qualification-contract-v3-20261006`
Draft PR: `#220 — Premise qualification V3: stability, observation operator, and uncertainty prefreeze`
Current scientific branch head: `660af8147afd7c71b6f71a01c4ceb4c714c62b74`

## Durable scientific package

- `b149de6e60aa2b068453dd7926217af5e107667a` — V3 premise design on current-main baseline.
- `47739d86b2c7cb50809436386062d2f2d0d5ade5` — neutral four-family representation tournament.
- `b17f5016242894ef0190539e29ba61af55942e16` — observation-operator contract.
- `7018edea1ca58e9cfd42a5e83b625fddb5b15ad1` — external-validation asset matrix, reusing prior audits rather than repeating them.
- `9713231e4c71c11535182ae98ec2f49d2c4636dc` — foundation-population estimand prefreeze; none selected.
- `6a46e0dfd489a0e9c6380eb917f1231cdb2d1d9a` — representation-stability protocol.
- `de948511463b14f22339191ffb98b2070afa81b1` — biological-evidence versus measurement-depth convergence protocol.
- `a793b18ca0f7dbd0c7843d26a5c67a162b5ebe74` — machine-readable V3 prefreeze state.

## TDD / CI history

The governance guard was developed through observed RED→GREEN cycles rather than written after the fact.

1. `7c7de093...` + `bd3d0414...`: first RED tests/workflow. Initial CI failure was a harness defect (`pytest` absent), not counted as scientific RED.
2. `b6f5766e...`: harness fixed by explicitly installing pytest. Real RED: 1 passed / 7 failed because validator was deliberately absent.
3. `3168a7f8...`: minimal validator. GREEN.
4. `c2baf462...`: second RED layer. 8 passed / 8 failed on newly named scientific invariants.
5. `e7fecec4...`: validator extended only for those invariants. GREEN, run `37499863322`, job `112393795775`.
6. Whole-branch audit found a real provenance defect: machine state named four source-document paths that did not exist.
7. `efcee040...`: source-document linkage RED. 16 passed / 1 failed and listed exactly the four stale paths.
8. `0ca9f4e5...`: corrected only those four paths. GREEN, run `37500238823`, job `112395059998`.
9. `082483c3...`: third RED layer for remaining observation/asset/estimand invariants. 17 passed / 8 failed exactly on missing checks: donor-ID shortcut; blanket technology-invariance rule; estimand-roster drift; post-hoc tempering; external=independent; access=exposure; pairing-class collapse; unknown-field guessing.
10. `660af8147afd7c71b6f71a01c4ceb4c714c62b74`: validator extended only for those eight invariants. GREEN, run `37500945561`, job `112397471487`.

## Frozen scientific distinctions

- Technology/assay is a constrained observation operator, not unrestricted dataset identity.
- Free donor ID, unrestricted dataset ID and arbitrary matrix ID are forbidden model shortcuts.
- Universal technology unpredictability is not itself the biological qualification objective.
- Representation comparison stays neutral among `GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, `STRUCTURED_COMBINED_STATE`.
- Stable subspace does not imply stable coordinates; coordinate semantics require coordinate stability after lawful alignment.
- Biological-evidence convergence and measurement-depth convergence are separate uncertainty axes.
- Donor/operator/study/technology transport are separate evidence axes.
- Biological-support OOD and measurement-regime OOD stay separate.
- `TARGET_OBJECT_RECOVERABILITY` is not `BIOLOGICAL_TRUTH_RECOVERABILITY`.
- Claim ladder remains `RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION`; no automatic promotion.
- Stage A maximum claim remains `RNA_REPRESENTATION`.
- External != independent; access != prior exposure.
- Same-nucleus pairing and separate-nucleus donor-level evidence are distinct.
- Cell count cannot replace donor count.
- Unknown external-asset fields fail closed rather than being guessed.
- Morabito remains protected and unavailable for target selection.
- Observational multimodal support is not causal evidence.
- Estimand candidates remain `CELL_WEIGHTED_EMPIRICAL`, `DONOR_WEIGHTED`, `SOURCE_BALANCED_DONOR_WEIGHTED`, `HIERARCHICAL_TEMPERED`; none selected.
- Hierarchical tempering is a scientific estimand parameter and cannot be tuned post hoc on biological outcomes.

## Current boundaries

`TRAINING=OFF`; Stage A prefreeze only; optimizer updates=0 and EMA updates=0 during target/representation discrimination; no target winner; no representation winner; no estimand selected; no deciding numeric margin selected; TEST sealed; Morabito protected.

## Next work

1. Re-fetch live `main` and compare PR #220 before any readiness claim.
2. Complete final whole-branch scientific/governance review for hidden flexibility, representation favoritism, observation-channel shortcuts, external-asset overclaim and estimand leakage.
3. Update PR #220 body with final RED/GREEN history and review findings.
4. Keep PR draft; do not merge without independent review/owner direction.

Do not duplicate the runtime optimizer/EMA/checkpoint lane or Macha V77 simulator lane.

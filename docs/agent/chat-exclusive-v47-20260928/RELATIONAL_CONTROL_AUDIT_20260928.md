# JEPA relational-target control audit — 2026-09-28

Status: **CONTROL FAILURE IDENTIFIED; RELATIONAL TARGET NOT YET SCIENTIFICALLY QUALIFIED FOR TRAINING.**

No protected biological readout was opened. This audit uses repository history, historical NPH52 A-sample technical metadata, an exact NPH52 TD57B Panel-0 replay, and synthetic/pseudo-gene adversarial controls.

## Bottom line

The TD56/TD57/TD58/TD59 matched wrong-cell null is useful but **not a sufficient biological negative control**. It preserves donor/operator and coarsely matches library size/detected-gene count, then permutes Y-cell identity. That operation breaks biology **and any remaining same-cell technical state**. Therefore a technical factor imperfectly represented by those matching variables can make the correct-cell arm look biological.

A technical-only pseudo-view constructed from actual NPH52 donor/operator/library/detected geometry passes the historical TD57B-style gate. The gate is therefore not suitable, as currently written, to authorize scientific training.

## Historical audit

### What survives

- TD57B was genuinely prospective, used independent disjoint panels, donor halves, source-by-source reporting, and a matched Y-cell null.
- The gate is not vacuous: TD57C's nearest-third locality test failed on real data, and the clean independent-null synthetic arm in this audit also fails.
- TD58 demonstrated partial-evidence recoverability under a fixed shared mask; this is a useful identifiability result, not biological specificity.
- TD59 demonstrated broader mesoscale recurrence under its frozen p95 rule, but 2/24 cases did not beat null max and it still uses the same wrong-cell null family.
- Donor-primary aggregation and source separation remain good design patterns.

### What does not survive as biological control authority

1. **The wrong-cell null does not preserve latent or residual same-cell technical state.** Matching donor/operator/depth/detection is not enough to establish that only biology was removed.
2. **TD19 had already shown technical geometry can recur across sources.** Its depth-only pseudo-states reproduced HVS↔SEA-AD relational geometry at approximately r=0.98, and QC adjustment materially reduced the historical relational geometry.
3. **Historical HVS/SEA-AD gene identities in the 50k discovery expression were later shown defective.** Label-free within-source numerical geometry may still be real structure, but the claim that the same intended gene panels carried it across sources is not intact. Corrected decoded replay is required for production authority.
4. **There was no decisive technical-only negative control that the final relational gate was required to reject.** Donor halves, fresh panels, and wrong-cell permutations do not substitute for that test.

## Exact NPH52 replay

The historical NPH52 feature axis is independently verified sound. The 1,310 A_NATURAL_MIXTURE NPH52 rows were reconstructed from supplied freeze/operator metadata, historical sparse discovery expression was loaded, and TD57B Panel-0 gene/pair hashing, triplet sampler, donor halves and 64-null construction were reproduced exactly to displayed precision:

| split | half | observed | null p95 | margin |
|---|---|---:|---:|---:|
| 0 | 0 | 0.669772 | 0.575605 | +0.094167 |
| 0 | 1 | 0.676178 | 0.561820 | +0.114358 |
| 1 | 0 | 0.697368 | 0.575949 | +0.121419 |
| 1 | 1 | 0.656250 | 0.562500 | +0.093750 |

This validates the local reimplementation used for red-team. It does **not** validate the biological interpretation of the null.

## Adversarial control using actual NPH52 technical geometry

RNA was replaced with two independent 512-dimensional pseudo-gene views constructed **only** from measured log library size and detected-gene count, plus independent gene-specific coefficients/noise. There is no biological latent variable in this arm. Donor IDs, operators, rows, technical covariates, triplet sampler, donor halves and historical depth/detection-matched Y-cell null are retained.

Four independently seeded runs in the packaged exact-redteam script all passed all four donor-half cases:

- technical-only: **4/4 runs fully qualify**;
- clean independent null: **0/4 runs fully qualify**;
- planted shared-state positive: **4/4 runs fully qualify**.

An extended interactive repetition over eight seeds gave the same qualitative result.

Thus the gate has sensitivity and can reject an unstructured null, but it cannot distinguish biological shared state from measured technical shared state. That is the control failure relevant to training.

## Post-hoc QC balancing does not rescue the historical claim

As an exploratory diagnostic only, the exact NPH52 Panel-0 triplets were restricted so comparison cells had similar measured QC distance to the anchor. The real RNA result was not robust across tolerances (3/4, 4/4, then 2/4 donor-half passes for three tested tolerances), and the technical-only pseudo-view still passed. These post-outcome experiments are not authority and should not be tuned further.

## Required successor gate before scientific training

Freeze a new control gate **before inspecting corrected FULL104 relational outcomes**. It should include:

1. **NEG-0 clean independent views** — must fail.
2. **NEG-1 measured technical-only pseudo-views** from exact source-specific QC variables and donor/operator geometry — must fail.
3. **NEG-2 latent technical nuisance synthetic arm** where observed QC is an imperfect proxy for a same-cell hidden capture factor — must fail.
4. **POS-1 planted shared-state arm** — must pass.
5. **Source-specific corrected decoder replay** — HVS, NPH52 and SEA-AD separately estimable/reported.
6. **No new relational outcome tuning.** Develop control/statistic only on negative/planted-positive arms; then run corrected real relational test once.
7. **Independent-modality confirmation.** A surviving RNA relational target should still be challenged by the donor-level ATAC route.

If no statistic can reject NEG-1/NEG-2 while retaining POS-1, record **INSUFFICIENTLY_SPECIFIC_AGAINST_TECHNICAL_STATE** and do not use it to authorize scientific training.

## Training consequence

Mechanical GPU smoke training can test gradients, EMA, checkpointing and memory. **Scientific teacher training remains OFF until a target control gate can reject technical-only structure while retaining planted shared-state sensitivity.**

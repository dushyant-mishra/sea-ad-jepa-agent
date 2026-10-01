# V65 privileged-factor recoverability precision and decision contract V2

**Date:** 2026-09-30  
**Status:** PROSPECTIVE DECISION CONTRACT V2 — no paired RNA↔ATAC recoverability outcome opened

**Supersedes:** `docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md` for geometry-gate semantics only. All other frozen decisions are carried forward unchanged.

## 1. Scope

This contract completes the decision layer for:

`docs/agent/V65_FIRST_PRIVILEGED_FACTOR_RECOVERABILITY_EXECUTION_CONTRACT_20260930.md`

It freezes how the first real NIH-CARD ATAC-only privileged factor may be classified before any recoverability outcome is inspected.

It does not authorize execution by itself.

## 2. Authority

Privileged factor:

`Z_priv_ATAC_V1`

constructed from ATAC only, rank 16, using TRAIN donors only for fitted transforms and basis estimation.

Canonical donor split:

`results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`

- TRAIN: 16 donors
- VALIDATION: 4 donors
- TEST: 4 donors

The different donor membership embedded in the earlier recoverability preflight is superseded for execution.

TEST may not influence:
- factor construction;
- factor normalization;
- ridge alpha;
- RNA feature handling;
- candidate shared rank;
- projection rotation;
- thresholds;
- classification logic.

## 3. Why no ordinary TEST bootstrap confidence interval

TEST contains only four independent donors.

The project therefore will NOT report a donor-bootstrap interval over four TEST donors as if it were a precise population interval.

Nuclei are not substituted for donors as independent N.

Final classification instead requires prospective replication across:
1. donor-held-out VALIDATION, used for rank selection under the fixed rule below;
2. untouched donor-held-out TEST, used once for confirmation.

This is intentionally conservative. Failure to satisfy it means UNQUALIFIED under this design, not evidence that the privileged factor is biologically false.

## 4. Predictor and tuning

Primary RNA predictor:

ridge regression from lawful log1p-CP10K RNA to the fixed 16-dimensional ATAC privileged state.

Ridge alpha grid is frozen as:

`[0.01, 0.1, 1.0, 10.0, 100.0]`.

Alpha is selected using leave-one-donor-out cross-validation inside TRAIN only.

No VALIDATION or TEST donor may choose alpha.

## 5. Baselines

For every held-out donor compare the candidate against both:

### B1 technical baseline

Linear prediction of the privileged state from:
- log RNA library size;
- detected-gene count.

### B2 global-RNA baseline

Linear prediction of the privileged state from the first 16 RNA PCA coordinates.

RNA PCA is fit on TRAIN only.

The comparison baseline for a donor is the better of B1 and B2 on that donor.

An evidence-availability flag is never an input to the candidate predictor; it is reported only as a shortcut diagnostic.

## 6. Primary recoverability metric

For each held-out donor separately compute multivariate explained variance over the fixed privileged target:

`R2_multi = 1 - sum ||Z_true - Z_pred||^2 / sum ||Z_true - mean_TRAIN(Z)||^2`

where the TRAIN privileged-state mean is used as the reference and is fixed before evaluation.

Primary improvement:

`DELTA_R2 = R2_multi(candidate) - max(R2_multi(B1), R2_multi(B2))`.

Do not pool nuclei across donors before computing donor-level values.

## 7. Materiality threshold

A recoverability claim requires more than statistical separation from a shortcut baseline.

The prospective materiality margin is:

`DELTA_R2 >= 0.05`

at the median donor level.

This is a project decision margin: five percentage points of additional privileged-state variance explained beyond the strongest simple baseline. It is not claimed to be a universal biological threshold.

The margin is frozen now and may not be lowered after results are visible.

## 8. Pairing-specific negative control

For each held-out donor, keep the candidate predictions fixed and permute the nucleus-to-privileged-state pairing within that donor.

Each donor has **one canonical permutation schedule**, shared by the R2 pairing gate and the geometry gates for every aggregate rank and incremental shell.

Construct it exactly as follows:

1. `digest = sha256("V65_RECOVERABILITY_PERMUTATION|<donor_id>".encode("utf-8")).digest()`;
2. `seed_uint64 = int.from_bytes(digest[:8], byteorder="big", signed=False)`;
3. initialize `numpy.random.Generator(numpy.random.PCG64(seed_uint64))`;
4. generate exactly 10,000 sequential `rng.permutation(n_donor_nuclei)` permutations.

For the R2 gate:

- apply each permutation to the rows of the true projected privileged state;
- keep the candidate prediction and TRAIN-frozen reference mean fixed;
- recompute `R2_multi` for every permutation;
- define the null threshold as `numpy.quantile(null, 0.99, method="higher")`;
- require the observed donor-level `R2_multi` to be **strictly greater** than that threshold.

The same permutation indices are reused for G1 and G2 in Section 10, for every aggregate projector and incremental shell. No rank, shell or metric gets an independently resampled null.

This is a pairing-specific anti-shortcut diagnostic, not a substitute for donor replication.

## 9. Shared-rank construction

Candidate shared ranks are fixed:

`0, 2, 4, 8, 16`.

The full 16-D privileged factor remains immutable.

For a candidate nonzero shared rank `k`:

1. fit the full ridge predictor on TRAIN;
2. center TRAIN true privileged states and TRAIN predictions using TRAIN means only;
3. define the oriented cross-covariance exactly as
   `C = Z_true_train^T Z_pred_train`;
4. compute the deterministic SVD `C = U S V^T`, with singular values sorted descending;
5. define the **privileged target-space projector**
   `P_k = U[:, :k] U[:, :k]^T`;
6. apply the SAME frozen target-space projector to true and predicted privileged states:
   `Z_true_shared = Z_true P_k`,
   `Z_pred_shared = Z_pred P_k`;
7. freeze `P_k` and its digest before VALIDATION scoring.

Sign flips of individual singular vectors do not change `P_k`. If a singular-value tie makes the rank-`k` projector non-unique at the selection boundary, that rank is `UNQUALIFIED_FOR_SELECTION` rather than resolved by an arbitrary rotation.

No projection is fit or rotated on VALIDATION or TEST.

Rank 0 means no privileged subspace is currently qualified for compulsory RNA supervision.

### Incremental nested shells

All candidate projectors come from the **same TRAIN-only SVD** and are nested.

Define:

- `P_0 = 0`
- `S_2 = P_2`
- `S_4 = P_4 - P_2`
- `S_8 = P_8 - P_4`
- `S_16 = P_16 - P_8`

The expected intrinsic ranks are:

- aggregate `P_k`: `2, 4, 8, 16`
- incremental shells `S_k`: `2, 2, 4, 8`

A higher aggregate rank may not qualify merely because it inherits signal from an already-qualified lower rank.

For every candidate rank `k`, compute the full recoverability gate twice:

1. on the aggregate projected state `P_k`;
2. on the newly added shell `S_k`.

The same lawful RNA predictor, technical baseline, global-RNA baseline, donor-level `R2_multi`, `DELTA_R2`, pairing-permutation gate and geometry gate are applied to both objects.

If a singular-value tie makes `P_k` non-unique at a selection boundary, selection stops below that boundary. No higher rank may be selected by skipping the ambiguous boundary.

## 10. Geometry gate

A synthetic mathematical audit found that the V1 geometry gate was redundant:

- centered canonical correlations between two multivariate states are the singular values of `Q_true^T Q_pred`;
- the cosines of the principal angles between those same centered column spaces are the same singular values.

Therefore canonical correlation and principal-angle cosine may both be **reported**, but they may not be counted as two independent qualification gates.

The independent audit is:

`scripts/v64/audit_recoverability_geometry_gate_redundancy_v1.py`

and is synthetic only; no real paired NIH-CARD outcome was opened.

For every nonzero candidate shared rank and every held-out donor compute two distinct quantities:

### G1 — subspace alignment

Compute canonical correlations between centered:

- `Z_true_shared`
- `Z_pred_shared`

after application of the frozen TRAIN-only target-space projector `P_k`.

The donor summary is the **median canonical correlation**.

Principal-angle cosines may be emitted as an audit alias of this same subspace-alignment object, but they do not create an additional gate.

### G2 — relational geometry

Compute all upper-triangle pairwise Euclidean distances among nuclei within the donor separately for:

- `Z_true_shared`
- `Z_pred_shared`

Then compute the **Pearson correlation** between those two pairwise-distance vectors.

This statistic is translation-invariant and evaluates whether the predicted state preserves the donor's within-state relational geometry rather than only spanning a linearly aligned subspace.

The pairwise distances are not treated as independent observations. No p-value or effective N is derived from the number of nucleus pairs.

### Pairing-permutation null

For each donor:

1. keep `Z_pred_shared` fixed;
2. compute `digest = sha256("V65_RECOVERABILITY_PERMUTATION|<donor_id>".encode("utf-8")).digest()`;
3. convert `digest[:8]` to an unsigned 64-bit integer using **big-endian** byte order;
4. initialize exactly `numpy.random.Generator(numpy.random.PCG64(seed_uint64))`;
5. generate exactly **10,000** sequential `rng.permutation(n_donor_nuclei)` row permutations;
6. reuse that identical 10,000-permutation sequence for every candidate rank in that donor;
7. apply each permutation to the rows of `Z_true_shared`;
8. recompute G1 and G2 for every permutation;
9. define each 99th-percentile threshold using:
   `numpy.quantile(null, 0.99, method="higher")`;
10. the observed metric must be **strictly greater** than its own threshold.

A donor passes the geometry gate only if BOTH:

1. observed median canonical correlation > its G1 99th-percentile permutation threshold;
2. observed relational-geometry correlation > its G2 99th-percentile permutation threshold.

The geometry implementation must evaluate the **intrinsic projected rank**, not the 16-D ambient storage width.

For aggregate `P_k`, the expected intrinsic rank is `k`.

For shell `S_k`, the expected intrinsic rank is the shell width:
- `S_2: 2`
- `S_4: 2`
- `S_8: 4`
- `S_16: 8`

Canonical-correlation bases are therefore obtained from the nonzero left-singular subspace of each centered projected state at the declared intrinsic rank. The ambient 16-D projected matrix is not required or expected to have rank 16.

Fail closed if:

- either projected state has rank below its declared intrinsic rank;
- the pairwise-distance vector has zero variance;
- any metric is non-finite;
- the deterministic permutation sequence cannot be reproduced.

The old requirement for a separate principal-angle threshold is **SUPERSEDED BEFORE REAL EXECUTION** because it duplicated G1 mathematically.

## 11. VALIDATION rank-selection rule

Evaluate candidate ranks in ascending order:

`2 -> 4 -> 8 -> 16`.

A rank is VALIDATION-eligible only if **both** its aggregate `P_k` and its incremental shell `S_k` independently satisfy all of the following:

1. `DELTA_R2 > 0` in all 4 VALIDATION donors;
2. median VALIDATION `DELTA_R2 >= 0.05`;
3. candidate `R2_multi > 0` in all 4 VALIDATION donors;
4. pairing-permutation gate passes in all 4 VALIDATION donors;
5. geometry gate passes in all 4 VALIDATION donors;
6. technical baseline is not within 0.01 `R2_multi` of the candidate in any VALIDATION donor.

This **aggregate-and-shell requirement** prevents lower-rank signal from carrying a weak or unrecoverable newly added shell across the threshold.

Apply a **contiguous nested-rank rule** over `2 -> 4 -> 8 -> 16`.

Starting at rank 2, advance only while every rank encountered remains VALIDATION-eligible. Select the **largest contiguous eligible rank**.

Examples:
- if 2 passes and 4 fails, select 2 even if 8 or 16 happen to pass;
- if 2 and 4 pass and 8 fails, select 4;
- if 2, 4, 8 and 16 all pass, select 16;
- if rank 2 fails, lock rank 0 even if a higher rank happens to pass.

This rule is required because the candidate subspaces are nested. Skipping over a failed lower-rank projection to claim a higher recoverable rank would indicate unstable geometry rather than a coherent recoverable hierarchy.

If no nonzero contiguous rank is eligible, lock rank 0 and classify the factor `UNQUALIFIED` under this experiment without opening TEST for model rescue.

The previous smallest-eligible rule is superseded prospectively before any paired recoverability outcome was opened. A synthetic monotone fixture showed that it would systematically select rank 2 even when all ranks through 16 were recoverable, making `RNA_RECOVERABLE` practically unreachable under a nested factor.

## 12. TEST confirmation rule

TEST is opened only after:
- ridge alpha is locked;
- privileged basis is locked;
- shared projection/rank is locked;
- every threshold above is locked;
- all VALIDATION decisions are written to a receipt.

The locked nonzero rank `k` is confirmed on TEST only if:

### Aggregate confirmation

Its aggregate `P_k` satisfies all of the following:

1. `DELTA_R2 > 0` in all 4 TEST donors;
2. median TEST `DELTA_R2 >= 0.05`;
3. candidate `R2_multi > 0` in all 4 TEST donors;
4. pairing-permutation gate passes in all 4 TEST donors;
5. geometry gate passes in all 4 TEST donors;
6. median TEST `DELTA_R2` is at least 50% of median VALIDATION `DELTA_R2`.

### Shell confirmation

Every incremental shell from `S_2` through `S_k` must independently satisfy the same TEST requirements 1–6 against that shell's own VALIDATION values.

TEST does **not** add the VALIDATION-only per-donor 0.01 technical-baseline margin; it confirms the already-locked rank using the frozen TEST requirements above.

If any required shell fails, the locked rank is not confirmed. TEST may not fall back to a smaller rank.

The 50% replication rule prevents a barely positive TEST result from being described as transport of a much stronger VALIDATION effect.

No TEST failure may be repaired by:
- changing rank;
- changing alpha;
- changing normalization;
- changing factor basis;
- changing thresholds;
- dropping a TEST donor.

## 13. Classification

### RNA_RECOVERABLE

Assign only if rank 16 is selected on VALIDATION and passes the TEST confirmation rule.

Interpretation:
the full frozen 16-D privileged factor has current RNA-recoverability authority under this design.

### PARTIALLY_RNA_RECOVERABLE

Assign only if rank 2, 4 or 8 is selected on VALIDATION and passes the TEST confirmation rule.

Only that locked projection is eligible for future compulsory universal RNA supervision.

The remaining privileged residual is preserved.

### UNQUALIFIED

Assign if:
- no nonzero VALIDATION rank is eligible; or
- the locked VALIDATION rank fails TEST confirmation; or
- technical/global-RNA baselines explain the apparent recoverability under the gates above.

UNQUALIFIED means the factor is not established as a lawful universal RNA-student target under this experiment.

### PRIVILEGED_PRIVATE

This experiment cannot assign PRIVILEGED_PRIVATE.

That label requires independent biological support for the privileged factor/residual from evidence not used merely to establish RNA non-recoverability.

Poor RNA prediction alone is insufficient.

## 14. Shortcut reporting

Regardless of classification report, for every donor:

- candidate `R2_multi`;
- technical-baseline `R2_multi`;
- global-RNA-baseline `R2_multi`;
- `DELTA_R2`;
- RNA library depth;
- detected genes;
- ATAC library depth;
- permutation-null percentile;
- geometry metrics.

High candidate recovery accompanied by equally high technical-baseline recovery is not biological qualification.

## 15. Multiplicity

There is one privileged factor family in this first experiment and a fixed nested rank set.

No factor-family multiplicity correction is needed.

Rank selection is controlled by:
- fixed nested ranks;
- largest-contiguous-eligible-rank rule;
- no skipping over a failed lower rank;
- all-donor VALIDATION gates;
- one locked TEST confirmation.

No edge/gene-level significance hunting is authorized.

## 16. Required execution receipts

Before TEST can open, write a VALIDATION lock receipt containing:
- input digests;
- canonical donor membership;
- TRAIN-fitted ATAC transform/basis digest;
- TRAIN-fitted RNA transform/PCA digest;
- ridge alpha;
- candidate-rank metrics;
- selected rank;
- selected projection digest;
- all thresholds;
- statement that TEST was unopened.

After TEST, write a separate immutable TEST receipt.

## 17. Governance

This contract does NOT authorize:
- Phase B;
- Stage 4;
- Morabito;
- disease/protected outcomes;
- multimodal teacher implementation;
- JEPA training.

Paired recoverability execution itself remains blocked until the project explicitly authorizes opening this Stage-4-like cross-modal experiment.

TRAINING OFF.


## V2 repair note

This V2 carries forward the repaired contiguous-rank policy and makes its incremental-shell requirement explicit alongside the geometry repair. It does not change the donor split, privileged factor construction, ridge alpha grid, R2 materiality margin, classification labels, or governance. The repair was made before any paired recoverability outcome was opened.

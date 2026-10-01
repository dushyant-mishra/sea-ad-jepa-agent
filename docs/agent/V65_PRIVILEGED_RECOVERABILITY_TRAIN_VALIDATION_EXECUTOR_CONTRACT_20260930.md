# V65 privileged recoverability TRAIN+VALIDATION executor contract

**Date:** 2026-09-30  
**Status:** EXECUTOR INTERFACE FROZEN — REAL EXECUTION NOT AUTHORIZED

## 1. Purpose

This contract defines the only lawful state transition for the first real `Z_priv_ATAC_V1` recoverability experiment before TEST.

It does not authorize real fitting.

The permitted future sequence is:

`STRUCTURAL_PREFLIGHT -> EXPLICIT_AUTHORIZATION -> TRAIN_FIT -> VALIDATION_EVALUATION -> VALIDATION_LOCK -> STOP`

There is deliberately no TEST transition in this executor.

TEST confirmation requires a separate successor executor that consumes an immutable VALIDATION lock receipt.

## 2. Canonical authority

The executor must bind:

- paired subset SHA-256 `6dca0d35ed7fd6cc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6`;
- canonical donor split `V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`;
- V2 precision/decision contract;
- execution-mechanics contract;
- outcome-blind structural preflight receipt;
- producer Git blob and SHA-256.

If any digest differs from authority, STOP.

## 3. Explicit authorization artifact

Real TRAIN+VALIDATION fitting may begin only if an explicit machine-readable authorization artifact exists and contains exactly:

- `experiment = Z_PRIV_ATAC_V1_RECOVERABILITY`;
- `scope = TRAIN_AND_VALIDATION_ONLY`;
- `test_access = FORBIDDEN`;
- the canonical source digest;
- the canonical split digest;
- the V2 decision-contract digest;
- the mechanics-contract digest;
- `authorized = true`.

Absence of this artifact is a STOP.

A prose instruction or branch name is not authorization.

## 4. TEST isolation

The TRAIN+VALIDATION executor must not:

- load TEST numeric rows;
- construct TEST matrices;
- serialize TEST row indices;
- compute TEST factor values;
- compute TEST predictions;
- compute TEST baseline values;
- compute TEST permutations;
- compute TEST geometry.

It may know only the declared TEST donor count and donor IDs from the frozen split receipt for exclusion checks.

TEST numeric access remains sealed.

## 5. TRAIN construction

Only TRAIN donors may fit:

- ATAC IDF;
- privileged SVD16 basis;
- privileged TRAIN mean/SD;
- RNA normalization/standardization parameters;
- RNA PCA16 basis;
- candidate ridge alpha;
- technical-baseline alpha;
- global-RNA-baseline alpha;
- candidate/baseline full-state fits;
- recoverable cross-covariance SVD;
- all `P_k` and `S_k`.

VALIDATION may not alter any of these objects.

## 6. TRAIN artifact freeze before VALIDATION

Before any VALIDATION recoverability metric is computed, persist and hash-bind:

- source/split/contract digests;
- TRAIN donor IDs;
- ATAC IDF;
- privileged SVD16 basis and singular values;
- privileged TRAIN mean/SD;
- RNA TRAIN mean/SD and zero-SD mask;
- RNA PCA16 basis and singular values;
- three selected alphas plus complete TRAIN donor-CV score tables;
- full-state candidate/technical/PCA coefficients and intercepts;
- recoverable cross-covariance SVD;
- `P2/P4/P8/P16`;
- `S2/S4/S8/S16`;
- any boundary-tie status;
- producer identity.

The resulting `TRAIN_FIT_RECEIPT` digest is immutable input to VALIDATION.

If these objects are revised after VALIDATION is seen, the experiment is invalid and must restart from a new prospective authority.

## 7. VALIDATION execution

VALIDATION may compute only the metrics already frozen in V2:

- donor-level full/aggregate/shell candidate R2;
- technical and global-RNA baseline R2;
- DELTA_R2;
- deterministic pairing-permutation threshold/pass;
- G1 canonical-alignment threshold/pass;
- G2 relational-geometry threshold/pass.

The same canonical 10,000 permutation schedule is reused exactly as V2 requires.

No additional metric may influence rank selection.

## 8. VALIDATION rank decision

Apply the V2 contiguous nested-rank rule exactly:

`2 -> 4 -> 8 -> 16`.

For each rank, both aggregate `P_k` and incremental shell `S_k` must pass.

Select the largest contiguous eligible rank.

If rank 2 fails, lock rank 0.

No skipping failed ranks.

No fallback based on an outcome-favorable alternate metric.

## 9. VALIDATION lock receipt

Before any TEST successor can exist, commit an immutable receipt containing:

- TRAIN fit receipt digest;
- every VALIDATION donor metric for every aggregate and shell;
- permutation thresholds and pass/fail;
- G1/G2 thresholds and pass/fail;
- candidate-rank eligibility table;
- selected rank;
- selected projector digest;
- classification state `LOCKED_PENDING_TEST` or `UNQUALIFIED_WITHOUT_TEST_RESCUE`;
- statement `TEST_NUMERIC_VALUES_UNOPENED = true`;
- exact producer/contract/source digests.

If selected rank is 0, TEST must remain unopened under the current contract.

## 10. No biological relabeling

A VALIDATION failure establishes only:

`UNQUALIFIED_FOR_UNIVERSAL_RNA_SUPERVISION_UNDER_THIS_DESIGN`.

It does not establish:

- regulatory-private biology;
- biological falsity;
- absence of ATAC information.

A later private-state claim requires separate biological evidence.

## 11. Relation to the multimodal student

The VALIDATION-selected shared projection, if nonzero and later TEST-confirmed, is the first candidate authority for the shared regulatory interface between:

- universal RNA student;
- future multimodal student.

Before TEST confirmation it remains provisional and may not supervise either production model.

No multimodal training is authorized by a VALIDATION lock.

## 12. Fail-closed conditions

STOP if:

- authorization artifact absent or false;
- any authoritative digest differs;
- TEST numeric access is attempted;
- donor split differs;
- a TRAIN-fitted object depends on VALIDATION values;
- a model/baseline is refit per rank or shell;
- a candidate rank uses a different alpha;
- a projector is fit on VALIDATION;
- a boundary singular-value tie is resolved by arbitrary rotation;
- a permutation schedule differs from V2;
- any non-frozen metric changes rank selection;
- a TRAIN artifact changes after VALIDATION begins.

## 13. Governance

Current state:

`recoverability_execution_authorized = false`

`TEST = SEALED`

`MULTIMODAL_TRAINING = OFF`

`JEPA_TRAINING = OFF`

`STAGE4 = NOT_AUTHORIZED`

Measurement-only Phase B remains a separate Claude-lane authority and is unaffected by this contract.

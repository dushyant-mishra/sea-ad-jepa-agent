# V5 representation-firewall V2 review — 2026-09-10

Status: `PROSPECTIVE_HARDENING_AND_REAL_DATA_SMOKE_ONLY__NO_TRAINING_AUTHORITY`

## Scope

This review is confined to V5 anti-cheat mechanics. It does not modify T0 V20, does not execute V21, does not close FULL104 expression binding, and does not authorize production training.

## V1 gaps found by adversarial review

### 1. Blacklist routing was bypassable by aliases and unregistered objectives

`representation_firewall_v1.py` rejected a small exact-name blacklist for direct `z_bio` inputs, but a semantically equivalent alias such as `dataset_id`, `study_id`, `batch_id`, `operator_id`, or `stable_key` was not structurally classified. The V1 manifest also did not reject arbitrary additional learned objectives. A new auxiliary objective could therefore consume an observation/identity channel without violating any registered V1 biological-objective check.

### 2. Observation/reconstruction gradients could train the shared biology input

`biology_observation_adapter_v1.py` formed `z_obs` from the live `student_native_state`. An observation-only loss therefore produced gradient in that shared state. Because the same upstream state also feeds `z_bio`, an observation or reconstruction objective could actively teach the shared representation technical identity even when observation descriptors were not direct inputs to the `z_bio` head.

A second-pass review found a related bypass: input routing alone is insufficient if `GENE_LEDGER_RECONSTRUCTION` consumes `z_bio` and its measurement-bearing reconstruction loss is allowed to update `z_bio`. The reconstruction path therefore also needs an explicit gradient boundary.

## V2 closure

`representation_firewall_v2.py` changes the routing contract from blacklist-first to fail-closed registration:

- direct `z_bio` and `z_obs` descriptors must come from explicit allowlists;
- known donor/source/matrix/operator/dataset/study/batch/sample/cell/stable-key/pathology/protected aliases are forbidden as direct learned-state fields;
- categorical identity embeddings are explicitly forbidden;
- the objective registry is exact: unknown auxiliary objectives fail closed;
- the canonical same-cell intervention family is exact: unknown or missing interventions fail closed;
- biological objectives consume `z_bio` only;
- ledger reconstruction consumes exactly `(z_bio, z_obs)`, with no side channel;
- per-objective gradient destinations are explicit;
- ledger reconstruction may train `z_obs`/decoder but may not update `z_bio`;
- checkpoint selection and downstream biology readout are evaluation-only gradient destinations;
- source-adversarial erasure remains non-default because source can be confounded with legitimate biology.

`biology_observation_adapter_v2.py` makes the executable gradient boundary concrete:

- the observation head conditions on detached biology context and detached fixed observation descriptors;
- observation-only losses cannot update the upstream biology state or biology predictor;
- the helper `gene_ledger_reconstruction_inputs_v2()` returns detached `z_bio` context plus trainable `z_obs`, preventing a measurement-bearing reconstruction loss from writing into `z_bio` through the reconstruction input;
- same-cell intervention and independent held-out biology qualification remain mandatory because this structural firewall does not prove that observed RNA itself contains no measurement imprint.

Local adversarial/unit result before publication: `29 passed`.

## Hash-locked real-data smoke

A tiny deterministic smoke was executed under the pre-existing `REAL_DATA_SMOKE_NON_AUTHORITY` permission using only hash-verified assets. The quarantined standalone operator-address NPZ was not used; the operator-address state was read from the hash-verified calibration bundle and verified against its internal bundle manifest.

Result terminal:

`PASS_REAL_DATA_SMOKE_NON_AUTHORITY_MECHANICS_ONLY`

Key mechanics findings:

- all 50,000 frozen discovery rows matched the authoritative full reader-fit metadata identity;
- `stable_key` was unique and signed-int64 compatible;
- `sample_row` was **not** globally unique because both frozen 25K discovery samples reuse `0..24999`; `(sample, sample_row)` is unique. This is an explicit identity-alias trap and `sample_row` must not be promoted to a global cell key;
- the real 50K expression payload was CSR `[50000, 41238]` with 246,702,069 stored nonzeros;
- on the deterministic four-cell operator-homogeneous smoke subset, every stored nonzero landed in the authoritative `MEASURED_SCALAR` support state and none landed in structurally-unmeasured or collision-unresolved addresses;
- canonical packing survived reverse-order replay exactly;
- the V2 firewall validated the intended routing and gradient registry;
- the adapter forward path remained finite under a one-address-per-cell mechanics-only mask perturbation;
- runtime was CPU-only, so no production-GPU or protected-gradient authority was created.

The one-hidden-address perturbation is deliberately a mechanics probe, not a production mask rate or threshold.

## Explicit non-closures

This work does **not** close any of the following:

- `STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`;
- `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
- production `D_shared`, `D_private`, `D_total`, `D_obs`, or `d_gene`;
- production masking, QC, collapse, shortcut-superiority, or power thresholds;
- real proposal-weight invariance;
- real packing/order/restart invariance at production geometry;
- V5 production CUDA Gate-2;
- learned-checkpoint same-cell/shortcut/collapse qualification;
- postqualification;
- independent review;
- training authority.

`training_authorized: false`

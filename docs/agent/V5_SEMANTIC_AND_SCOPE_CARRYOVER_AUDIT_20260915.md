# V5 semantic and authority-scope carryover audit

Date: 2026-09-15
Status: `ACTIVE_DESIGN_AUDIT_NOT_FROZEN`

Purpose: prevent current V5 from inheriting not only historical numbers/code paths, but also historical *meanings* and authority scope.

No training authority is created.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## 1. Semantic carryover: `biology` labels exceed current evidence

Current evidence establishes recurrent within-donor cross-view molecular information beyond the measured Q_DEPTH/Q_DETECT family, but explicitly does **not** establish that the unexplained component is biological or nontechnical.

Therefore identifiers such as:

- `z_bio`;
- `biology_state`;
- `biology_anchor`;
- `student_biology_state`;
- `biology_anchor_alignment_loss`;

must not be interpreted as scientific authority that the represented state is biological.

### Current code finding

`src/sea_ad_jepa/v5/biology_observation_adapter_v1.py` describes a same-cell common-core teacher state as a "biology anchor" and names its primary output `z_bio_prediction` / `z_bio_anchor`.

`biology_observation_adapter_v2.py` correctly repairs an important gradient defect by detaching the primary state and observation features before the observation head, but it retains the same biological naming.

### Classification

- V2 gradient firewall: `REUSABLE_MECHANIC`.
- biological naming/semantic claim: `PROVISIONAL_LABEL_ONLY__NOT_SCIENTIFIC_AUTHORITY`.

### Required future production terminology

Until biological identity is independently established, production-facing contracts should use neutral terminology such as:

- `z_primary`;
- `z_molecular`;
- `shared_molecular_state`;
- `primary_state_anchor`;
- `observation_state`.

A later authority may rename a qualified component biological only if the qualification actually supports that claim.

### Rule

`NAMES_DO_NOT_CREATE_CAUSAL_OR_BIOLOGICAL_AUTHORITY`

No checkpoint, receipt, loss, or downstream report may treat a variable as biological solely because a historical implementation calls it `z_bio`.

## 2. Common-core does not equal biology

The 17,186-address common core is a **comparability/support construct**. It is not automatically the biological part of the transcriptome.

A same-cell teacher state computed on common-core support may be useful as:

- a cross-source comparable anchor;
- a consistency target;
- a calibration object;
- a shared-support qualification object.

It must not become `BIOLOGICAL_TRUTH_TARGET` merely because it is measurable across sources.

Current V5 `data_contract_v2.EvidenceAuthorityV2` already supports this separation by giving comparable support an explicit non-objective role drawn from:

- `CALIBRATION_ONLY`;
- `CONSISTENCY_DIAGNOSTIC_ONLY`;
- `DISABLED`.

This separation should be retained and widened only through explicit authority.

## 3. Native support does not equal private biology

Operator/source-native measured addresses can contain real biological information, technology-specific observation structure, or both.

Therefore:

`native_support != automatically D_private biology`

and:

`common_core != automatically D_shared biology`.

Support family and latent semantic role are distinct authorities.

The target design must not infer one from the other.

## 4. Dimension-qualification estimand is not training estimand

`src/sea_ad_jepa/v5/full104_dimension_interface_v1.py` projects the FULL104 dimension input with:

`estimand = EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR`.

That estimand is currently scoped to the dimension/rank qualification chain.

The base-training scientific estimand remains unresolved, with empirical/FULL104, source-uniform, and donor-primary/operator-balanced views deliberately separated after the Layer-2 sensitivity analysis.

### Required firewall

`DIMENSION_ESTIMAND_AUTHORITY != BASE_TRAINING_ESTIMAND_AUTHORITY`

A future training receipt must contain its own training-estimand authority ID and scientific-weight root. It may not infer training weights from the D_shared/dimension authority simply because the latter is already frozen.

## 5. Rank envelope `1..512` requires scope discipline

`d_shared_authority_v2.py` freezes a rank envelope of 1..512 and allocates error across 10 × 512 quantity/rank combinations.

This is **not yet classified as accidental carryover**.

Possible lawful interpretation: 512 is the dimensional ceiling of the authenticated upstream feature representation being qualified, not a chosen V5 model width.

Required rule:

`QUALIFICATION_RANK_CEILING != PRODUCTION_MODEL_WIDTH`

Before final model geometry is frozen, provenance must show why the D_shared rank envelope is 512 and bind that ceiling to the feature substrate or qualification interface that generated it. The production encoder width must remain separately authorized.

## 6. Observation-state firewall is mechanical, not semantic proof

`biology_observation_adapter_v2.py` prevents observation/reconstruction losses from writing gradients into the primary state by detaching the primary state and observation descriptors before the observation head.

This establishes a useful gradient boundary.

It does **not** prove:

- the primary state is biological;
- the observation state contains only technical effects;
- indirect measurement information is absent from the primary state;
- common-core teacher state is causally technology-invariant.

Same-cell interventions, source/donor transport checks, and objective-aligned shortcut tests remain necessary.

## 7. Carryover checklist added by this audit

Future current-V5 implementation should fail review if it:

- treats `z_bio` naming as evidence of biology;
- treats common-core support as automatically biological/shared latent truth;
- treats native support as automatically private biology;
- imports equal-donor dimension-qualification weights into training without a separate training-estimand authority;
- equates the D_shared rank ceiling of 512 with production encoder width;
- treats the observation gradient firewall as proof that the primary state is free of measurement information.

## 8. Current terminals

`SEMANTIC_CARRYOVER_AUDIT_ACTIVE`

`BIOLOGY_LABELS_ARE_PROVISIONAL_NOT_AUTHORITY`

`COMMON_CORE_SUPPORT_IS_COMPARABILITY_NOT_BIOLOGY_AUTHORITY`

`DIMENSION_ESTIMAND_MUST_NOT_WIDEN_TO_TRAINING`

`D_SHARED_512_RANK_CEILING_REQUIRES_PROVENANCE_SCOPE_CHECK`

`TRAINING_OFF`

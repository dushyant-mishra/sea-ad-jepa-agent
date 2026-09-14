# V5 CLOSED SUBSTRATE INVARIANT REGISTRY — 2026-09-14

## Purpose

This registry distinguishes **closed substrate invariants** from quantities that must be recomputed when the representation changes. It exists to prevent agents from spending heavy-machine time rediscovering facts that were already authenticated and closed.

Governing rule:

`INHERIT_CLOSED_INVARIANTS__RECOMPUTE_ONLY_REPRESENTATION_DEPENDENT_QUANTITIES__REOPEN_ONLY_IF_PARENT_BYTES_OR_SEMANTICS_CHANGE`

Nothing in this registry authorizes D_shared, training, protected/pathology access, TD60, or relational activation.

## A. Closed invariants — do not rerun as scientific discovery

These properties are already established for the current authenticated FULL104 substrate and should be inherited by successor feature rebuilds that explicitly bind to the same parents.

### Population / identity

- FULL104 population count: **4,553,407 cells**.
- Donors: **104**.
- Operators/matrices: **42**.
- Expression blocks: **8,915**.
- Molecular Ledger addresses: **41,238**.
- Sources: **SEA-AD + HVS + NPH52**.
- Heavy block manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
- Sealed FULL104 dimension-input artifact SHA-256: `eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad`.

### Row coverage / exactly-once assembly

Historical assembly already established the complete 4,553,407-row population and exactly-once row coverage. A successor rebuild over the unchanged selection-row universe does **not** need to rediscover population coverage as a scientific result.

`ASSEMBLY_SEEN_V5.npy` being all ones and byte-identical to the historical `ASSEMBLY_SEEN.npy` is useful **lineage corroboration**, not a new discovery result.

For successor rebuilds, the required action is:

1. bind to the authenticated historical row universe / selection-row contract;
2. verify the new writer did not omit/duplicate rows;
3. record the receipt;
4. do not promote the repeated all-ones result as a new scientific finding.

If the row-selection parent, ordering semantics, or population definition changes, this invariant must be reopened.

### Address/support structure

- Universal common measured core: **17,186 addresses** across all 42 operators.
- Distinct operator support patterns: **9**.
- Support-measurability is redundant with operator under the current observation-state parent.
- Q_DEPTH and Q_DETECT are losslessly recoverable to discrete generating counts over all 4,553,407 rows.

These remain inherited unless the observation-state artifact, operator set, address registry, or measurement semantics change.

### Source nesting

Under the authenticated FULL104 metadata:

- donors spanning more than one source: **0 / 104**;
- operators spanning more than one source: **0 / 42**;
- support patterns are nested within source;
- donor counts by source: HVS 41, NPH52 17, SEA_AD 46.

This is a metadata invariant. It need not be recomputed for every feature representation unless the metadata parent changes.

### Historical normalization semantics

Recovered transform:

`log1p(raw_count * 10000 / full_source_library)`

applied exactly once.

A new feature builder should verify that it implements the frozen transform against its bound parent bytes. It should not treat rediscovery of this formula as a new result.

## B. Closed historical findings — inherit as constraints, not current biological authority

- Historical A/B used the same 41,238-address molecular universe and therefore are not genuinely disjoint molecular views.
- Historical 4-view / 60%-visible masking is provenance/mechanics and a useful measurement-robustness challenge, not current independent-view authority.
- Historical covariance was singular/highly redundant; nominal rank 512 is not automatically successor rank authority.
- Source/support information was strongly readable before training; this is a substrate property, not merely a learned shortcut.
- Random cell-level CV is not donor-generalization evidence.
- Donor-block resampling/generalization and support-only falsification were already required by historical discovery.
- T0 terminal remains `T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`.
- Historical QID warning remains: `matched-null state intervention != demonstrated paired-wrong-query intervention`.

## C. Representation-dependent quantities — MUST be recomputed after a new feature rebuild

These cannot be inherited from historical A/B or from another K-way molecular partition:

- output feature-array hashes and exact dtype/shape;
- deterministic molecular-view disjointness/union for the new partition;
- per-view covariance spectrum;
- effective rank / spectral entropy / conditioning;
- per-view Q_DEPTH/Q_DETECT correlations;
- cross-fitted source/operator/QC predictability in the rebuilt representation;
- cell/donor geometry preservation across disjoint views;
- view balance / sparsity / nonzero support;
- rank-support evidence;
- nuisance-adjustment structure-preservation tradeoff;
- same-cell representation response under thinning/masking;
- whole-procedure positive/negative-control calibration;
- final V3 null calibration and power.

## D. Metadata-dependent null mechanics — compute once per metadata/exchangeability definition, not once per feature array

These depend primarily on donor/source/operator metadata and candidate randomization rules:

- cross-source donor permutation legality;
- within-source donor mobility;
- donor operator-exposure profiles;
- within-operator cell mobility;
- donor-disjoint train/validation/test integrity;
- exact matching-stratum occupancy.

If the candidate null definition changes, rerun the corresponding mobility/calibration audit. A feature rebuild alone does not require repeating metadata facts unless the test statistic or eligibility population changes.

## E. Reopen conditions

A closed invariant may be reopened only if one of the following changes:

- authenticated parent bytes/hash;
- row-selection/population definition;
- address registry;
- operator/source/donor metadata;
- observation-state semantics;
- normalization semantics;
- eligibility population relevant to the invariant.

A different projection, molecular partition, rank, model, or latent representation **does not** by itself reopen population/metadata invariants.

## F. Required agent behavior

Before adding a heavy-machine task, classify it as one of:

1. `CLOSED_INVARIANT_LINEAGE_CHECK` — cheap verification/receipt only;
2. `REPRESENTATION_DEPENDENT_RECOMPUTATION` — scientifically required after rebuild;
3. `NEW_UNRESOLVED_PARAMETER` — derive/narrow locally first;
4. `FULL104_ONLY_RESIDUAL_QUESTION` — heavy execution justified.

Do not schedule category 1 as a discovery task.

`CLOSED_INVARIANTS_REGISTERED__NO_D_SHARED_OUTCOME_ACCESS__NO_TRAINING_AUTHORITY`

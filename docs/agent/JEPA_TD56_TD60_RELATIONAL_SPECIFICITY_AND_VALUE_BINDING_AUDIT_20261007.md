# JEPA TD56–TD60 relational specificity and value-binding audit — 2026-10-07

Status: `AUDIT_CHECKPOINT__NO_EXECUTION_AUTHORITY`

## Executive classification

The strongest surviving historical Target Discovery line should currently be classified as:

`REPRODUCIBLE_RELATIONAL_RNA_STRUCTURE__PARTIAL_EVIDENCE_RECOVERABILITY_SUPPORTED__BIOLOGICAL_SPECIFICITY_UNRESOLVED_AGAINST_UNOBSERVED_SAME_ASSAY_TECHNICAL_STATE__NPH52_VALUE_BINDING_NOT_PHYSICALLY_REQUALIFIED__NO_TARGET_AUTHORITY`

This is stronger than “nothing survived,” but materially weaker than “qualified biological target.”

## What survives from TD56–TD59

Historical evidence remains substantial:

- TD56: two disjoint 512-address RNA views showed concordant within-donor relational geometry in HVS, NPH52 and SEA-AD;
- TD57B: two additional independent panel pairs, deterministic donor splits and halves, 24/24 PASS;
- TD58: ~60% partial molecular evidence reproduced the relational target 24/24;
- TD57C: nearest-third fine locality failed prospectively, demonstrating the gate could fail;
- TD59: nearest-half mesoscale recurrence survived 24/24, but nearest-half remains a pilot bracket rather than production locality authority.

The surviving object is ordinal/relational rather than a fixed coordinate:

`q(i;j,k) = sign(d(i,j)-d(i,k))`.

These results support reproducibility and partial-view recoverability of a relational RNA object.

## S149-aware panel-selection classification

The panel-selection mechanism is not a pooled source/cohort covariance selector.

Actual TD56/TD57 code recovered from `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip` constructs the common address set from the 42-operator observation-state matrix and ranks canonical integer address indices by deterministic SHA-256 preimages.

TD56 uses the first two 512-address slices of:

`sort(common, key = SHA256("TD56S|gene|<canonical_address_index>"))`.

TD57B prospectively uses later disjoint slices:

- Panel 0: X positions 1024:1536, Y 1536:2048;
- Panel 1: X 2048:2560, Y 2560:3072.

Thus panel membership does not depend on RNA expression covariance, source topology, disease outcome, pathology, or pooled study composition.

Classification:

`TD56_TD57B_PANEL_SELECTION__S149_SAFE__SUPPORT_AND_HASH_DERIVED`

This does **not** validate the expression values subsequently attached to those addresses.

## Known row-alias defect is not the active TD57B failure

The recovered TD57B executor uses `global_row`, verifies rows are unique, requires rows in the A natural-mixture range, and rejects invalid global-row binding. It does not use the historically corrupted post-reset block-local row alias that caused earlier false HVS↔SEA-AD dependencies.

Therefore:

`TD57B_GLOBAL_ROW_BINDING__KNOWN_RESET_INDEX_ALIAS_NOT_ACTIVE`

This does not close feature-axis / column-to-address identity.

## Exact feature/value assumption in TD56/TD57

The recovered executors load the frozen 50K CSR arrays:

- `data.npy`
- `indices.npy`
- `indptr.npy`
- `shape.npy`

They build a lookup with canonical address indices and directly interpret each CSR `indices` entry as a canonical molecular-address index.

The scientific calculation therefore depends on the semantic invariant:

`CSR column index == canonical molecular_address_index`.

The executors hash the CSR bytes, support matrix and source metadata, so they prove repeatability on those bytes. They do **not**, by themselves, prove the semantic column binding.

A column permutation made upstream could reproduce all historical result hashes while attaching the wrong gene/address identity to RNA values.

## Discovery expression materialization — source-specific audit

The historical discovery materializer is stronger than a naive positional concatenation.

### HVS and SEA-AD

For non-NPH52 HDF5-backed matrices, the Python materializer:

1. reads source sparse feature indices from the authenticated source matrix;
2. uses the provenance table `source_feature_index -> molecular_address_index`;
3. excludes collision-blocked source features;
4. requires the mapping to be injective;
5. checks selected source row cell/donor identity;
6. writes each source count explicitly into the canonical 41,238-address output column.

This gives HVS and SEA-AD materially stronger historical evidence for feature-to-address placement.

Current classification:

`HVS_SEA_DISCOVERY_COLUMN_BINDING__EXPLICIT_PROVENANCE_REMAP_PRESENT__NO_NEW_DEFECT_FOUND_IN_THIS_AUDIT`

This is not a fresh raw-file requalification and should not be overstated beyond the recovered materializer/provenance lineage.

### NPH52

The R materializer similarly *intends* to map:

`source_counts[source_feature_index + 1, selected_cell] -> molecular_address_index`.

However V48 PR #187 later explicitly qualifies the NPH52 physical closure:

- feature-axis position was independently verified;
- no `.qs` count was compared to a Level-4 value;
- the R materializer was not pinned by the then-current contract;
- value-level fidelity / column-to-address identity remained open physical-reader qualification tasks.

PR #187 body likewise records that `.qs` value-level fidelity and column-to-address identity remain unverified.

Therefore the older broad `identity_exact` / `normalized_payload_exact_in_final` labels must not be interpreted as complete physical proof of NPH52 source-feature-to-value identity.

Classification:

`NPH52_DISCOVERY_COLUMN_TO_ADDRESS_VALUE_BINDING__NOT_PHYSICALLY_REQUALIFIED`

This is directly relevant to the user's historical warning about gene/address identifiers becoming jumbled relative to RNA values.

## Biological-specificity failure of the old relational gate

The old TD56–TD59 qualification relied on a matched wrong-cell null that preserved donor/operator/depth/detection strata while breaking same-cell correspondence.

V47 demonstrated that this control destroys both:

1. true same-cell biology; and
2. unmeasured same-cell technical/capture state.

A measured technical shared state could pass the old relational gate, showing that the gate had sensitivity but insufficient biological specificity.

V48 then tested measured-QC residualization. On the real NPH52 scaffold, measured technical correspondence (`NEG-1`) could be largely removed while planted biology remained. But latent capture (`NEG-2`) remained highly similar to planted biology when recorded QC was only an imperfect proxy.

The decisive V48 logical witness constructs two worlds with byte-identical observed RNA views and metadata:

- `PLANTED_SHARED_BIOLOGICAL_STATE`;
- `UNMEASURED_SHARED_TECHNICAL_CAPTURE_STATE`.

Because the observable arrays are identical, no same-RNA statistic restricted to those observables can be required to distinguish the semantic labels.

Frozen terminal:

`INSUFFICIENTLY_SPECIFIC_AGAINST_UNOBSERVED_TECHNICAL_STATE__SAME_ASSAY_OBSERVABLES_NONIDENTIFIABLE`

Important interpretation:

- this does **not** prove the real TD56–TD59 signal is technical;
- it proves same-assay RNA evidence alone cannot prove that it is biological under an unrestricted latent technical nuisance class.

## TD60 successor status

TD60 V2 correctly incorporates this supersession.

Status:

`DESIGNED_NOT_EXECUTABLE__RELATIONAL_SPECIFICITY_GATE_FAILED__NO_TRAINING_AUTHORITY`

Historical TD57B/TD59 panels, triplets, source separation, no-new-panel/no-new-locality rules and learned-teacher continuity concept remain reusable, but the old wrong-cell null cannot establish specificity alone.

Before any corrected FULL104 relational outcome or learned-teacher TD60 outcome may be opened, a separate frozen relational technical-state specificity authority must PASS.

Current resolution paths are prospectively limited to:

1. an additional independent measurement modality; or
2. an explicitly restricted nuisance class with claims bounded to that restriction.

Training remains OFF.

## Interaction with current V3 premise qualification

This historical line maps naturally onto current V3 semantics:

- reproducibility / recurrence: supported historically;
- partial-view recoverability: supported historically;
- biological target meaning: not identified from same-RNA evidence;
- observation-process / technical confounding: unresolved under unrestricted hidden nuisance;
- external biological evidence: not yet qualified;
- production learned-teacher continuity: not executed.

Accordingly TD56–TD59 should be retained as a strong **candidate relational representation/evaluation family**, not promoted to a biological target winner.

## Required next audits

Before using historical TD56–TD59 numerics as conclusion-bearing target evidence:

1. physically requalify NPH52 `.qs` feature/value identity on the machine holding the source files;
2. preserve HVS, NPH52 and SEA-AD as separate source/domain strata;
3. do not use pooled source topology as biology;
4. do not revive the wrong-cell null as sole biological-specificity proof;
5. finish the prospective cross-modal technical-specificity gate before biological promotion;
6. keep any external assay endpoints independent of target/panel/threshold selection;
7. do not execute TD60 or training under this checkpoint.

## Boundaries

- target winner: none;
- representation winner: none;
- TD56–TD59 not biologically qualified;
- TD60 has no result and remains non-executable;
- TRAINING=OFF;
- STAGE_A_EXECUTION=OFF;
- MULTIMODAL_TRAINING=OFF;
- TEST sealed;
- Morabito protected;
- 500K / Stage4 not authorized.

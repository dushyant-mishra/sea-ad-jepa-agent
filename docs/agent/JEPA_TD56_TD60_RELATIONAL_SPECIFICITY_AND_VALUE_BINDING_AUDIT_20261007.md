# JEPA TD56–TD60 relational specificity and value-binding audit — 2026-10-07

Status: `AUDIT_CHECKPOINT__NO_EXECUTION_AUTHORITY__CORRECTED_AFTER_V46_AXIS_TRACE`

## Executive classification

The current classification is:

`PANEL_SELECTION_GENEALOGY_SAFE__HISTORICAL_RELATIONAL_STATISTICS_REPRODUCIBLE_ON_DEFECTIVE_OR_UNREQUALIFIED_EXPRESSION_BYTES__BIOLOGICAL_SPECIFICITY_UNRESOLVED__NUMERICAL_BIOLOGY_NOT_CURRENT_AUTHORITY__TD60_NOT_EXECUTABLE`

This file supersedes its own earlier, too-permissive HVS/SEA-AD column-binding assessment. A later V46/Sept-27 source trace proves that the historical 50K discovery materializer used a semantically defective HVS/SEA-AD feature index.

## What remains valid from TD56–TD59

The historical executions remain useful as **forensic/reproducibility evidence**:

- TD56: two disjoint 512-address views;
- TD57B: two additional independent panel pairs; historical 24/24 PASS;
- TD58: historical ~60% partial-evidence recurrence; 24/24 PASS;
- TD57C: nearest-third locality prospectively failed HVS Panel0 2/4, showing the gate could fail;
- TD59: nearest-half mesoscale recurrence historically passed 24/24.

The historical relational object was ordinal:

`q(i;j,k) = sign(d(i,j)-d(i,k))`.

However, because the expression-address binding used by those executions is not current semantic authority, these historical numeric PASS results must **not** be treated as current evidence that the intended molecular addresses carry the reported relational geometry.

## Panel selection remains S149-safe

Recovered TD56/TD57 code constructs panels from the 42-operator observation-state support matrix and deterministic SHA-256 ordering of canonical address indices.

TD56 uses the first two 512-address slices of a deterministic hash ranking. TD57B uses later disjoint slices (positions 1024–3071), avoiding the earlier panels.

Panel membership does not depend on pooled RNA covariance, source topology, disease outcome, pathology or later TD results.

Classification:

`TD56_TD57B_PANEL_SELECTION__S149_SAFE__SUPPORT_AND_HASH_DERIVED`

This means the **choice of address labels** is genealogically clean. It does not prove that the RNA values attached to those labels were correct.

## Known global-row alias is not the active TD57B defect

Recovered TD57B code uses `global_row`, checks uniqueness/range, and does not use the old post-reset block-local row alias that caused earlier false HVS↔SEA-AD dependencies.

Classification:

`TD57B_GLOBAL_ROW_BINDING__KNOWN_RESET_INDEX_ALIAS_NOT_ACTIVE`

The active issue is the **feature axis**, not the row axis.

## Exact dependency of the historical TD executors

TD56/TD57 load the historical 50K CSR expression arrays and interpret CSR column indices as canonical molecular-address indices.

Therefore the scientific calculation requires:

`CSR column index == canonical molecular_address_index`.

Reproducing the same CSR bytes only proves repeatability on those bytes; it does not prove the upstream source gene/value binding.

## Historical 50K producer path

The recovered producer `foundation_materialize_discovery_expression.py` built non-NPH52 shards as follows:

1. read the physical H5 sparse matrix column integers from `node['indices']`;
2. load `stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`;
3. construct `source_feature_index -> molecular_address_index`;
4. use the H5 sparse column integer directly as the key into that mapping;
5. write the source count to the returned canonical 41,238-address column.

Thus correctness depends on `source_feature_index` being the **physical matrix column index**.

## HVS / SEA-AD: historical 50K feature axis is affected

The Sept-27 V46 handoff and Oct-5/6 retrospective establish a real historical defect:

- old `HVS_COMMON` and `SEA_AD_COMMON source_feature_index` represented an **Ensembl-harmonized rank**, not the physical H5AD column index;
- the **historical 50K discovery materializer is explicitly named as affected**;
- original Level-4 HVS/SEA-AD materializers were also affected;
- old named-gene R7/R8 results depending on that axis were invalid;
- V44 used the same defective 50K NPZ.

A later physical SEA-AD MTG spot-check independently demonstrates the defect against the same provenance table: four of four sampled `source_feature_index` values landed on unrelated H5AD genes. One documented example is canonical address `ENSG00000207751` mapping through index `32126`, while physical H5AD column 32126 is `CEACAM5 / ENSG00000105388`.

Therefore the earlier interpretation that the 50K HVS/SEA shards had a trustworthy explicit remap is withdrawn.

Current classification:

`HVS_SEA_HISTORICAL_50K_COLUMN_TO_ADDRESS_BINDING__KNOWN_DEFECTIVE`

This is the exact class of gene/address-ID ↔ RNA-value jumbling the user warned about.

## NPH52: separate unresolved value-level authority

The NPH52 R producer uses:

`source_counts[source_feature_index + 1, selected_cell] -> molecular_address_index`.

V48/PR #187 later established feature-axis position evidence but explicitly left `.qs` value-level fidelity / column-to-address identity unverified under the then-current physical-reader contract.

Classification:

`NPH52_DISCOVERY_COLUMN_TO_ADDRESS_VALUE_BINDING__NOT_PHYSICALLY_REQUALIFIED`

So the historical TD56–TD59 three-source result currently has:

- HVS: known defective 50K source-feature binding lineage;
- SEA-AD: known defective 50K source-feature binding lineage;
- NPH52: value-level/column-to-address physical requalification incomplete.

## Consequence for TD56–TD59 numerics

The correct current status is not “historical biology replicated across three sources.” It is:

`HISTORICAL_RELATIONAL_STATISTICS_REPRODUCIBLE_ON_THEIR_EMITTED_BYTES__INTENDED_MOLECULAR_ADDRESS_SEMANTICS_NOT_QUALIFIED`

The old numerical effects, 24/24 counts and partial-evidence recurrence may be retained for forensic chronology and for testing future corrected executors against old behavior. They cannot currently authorize:

- target meaning;
- source replication of intended gene/address biology;
- partial-evidence biological recoverability;
- TD60 learned-teacher continuation;
- production target selection.

A corrected replay is required before those claims can be reconsidered.

## Same-assay biological-specificity blocker remains independently valid

Even if the feature axis is repaired, the old relational qualification still has a second independent problem.

V47 showed the matched wrong-cell null breaks both true same-cell biology and unmeasured same-cell technical/capture state.

V48 then showed measured-QC residualization can remove a measured technical factor but cannot, in general, distinguish planted biology from an unobserved technical capture latent when the observables are identical.

The decisive semantic twin contains byte-identical observed RNA/metadata under labels:

- `PLANTED_SHARED_BIOLOGICAL_STATE`;
- `UNMEASURED_SHARED_TECHNICAL_CAPTURE_STATE`.

Frozen terminal:

`INSUFFICIENTLY_SPECIFIC_AGAINST_UNOBSERVED_TECHNICAL_STATE__SAME_ASSAY_OBSERVABLES_NONIDENTIFIABLE`

This does not prove the historical TD signal was technical. It proves same-assay RNA alone cannot establish biological specificity under an unrestricted latent technical nuisance class.

## TD60 successor status

TD60 V2 correctly refuses execution until a separate relational technical-state specificity authority passes.

Status:

`DESIGNED_NOT_EXECUTABLE__RELATIONAL_SPECIFICITY_GATE_FAILED__NO_TRAINING_AUTHORITY`

The old panel/triplet/no-new-panel/no-new-locality design logic may be reusable after corrected expression replay. The old wrong-cell null cannot become sole biological-specificity authority.

## Required repair sequence before any TD56→TD60 promotion

1. Rebuild or independently verify HVS and SEA-AD discovery expression using **physical source matrix columns**, not the historical harmonized-rank field.
2. Physically requalify NPH52 `.qs` feature/value identity.
3. Bind `registry identity -> frozen ordering -> tokenizer/index mapping -> physical matrix column -> reader output` end to end.
4. Replay the frozen TD56/TD57B panel definitions and historical triplet designs on corrected bytes without reselection.
5. Preserve sources as separate domains; do not use pooled source topology as biology.
6. Re-evaluate TD58 partial-evidence and TD59 locality only after corrected full-evidence recurrence is established.
7. Require a separately frozen cross-modal or explicitly restricted-nuisance specificity gate before biological target promotion.
8. Keep TD60 and all training OFF until all upstream gates pass.

## Interaction with V3 premise qualification

At present the historical relational family can support only:

- a useful candidate **mathematical form** for relational/ordinal representation;
- a clean prospective panel-selection genealogy;
- reusable test designs and negative-control lessons.

It does **not** currently support a qualified empirical claim about intended molecular-address biology because the input semantics are not closed.

## Boundaries

- target winner: none;
- representation winner: none;
- TD56–TD59 historical numeric biology: not current authority;
- TD60: no result and non-executable;
- TRAINING=OFF;
- STAGE_A_EXECUTION=OFF;
- MULTIMODAL_TRAINING=OFF;
- TEST sealed;
- Morabito protected;
- 500K / Stage4 not authorized.

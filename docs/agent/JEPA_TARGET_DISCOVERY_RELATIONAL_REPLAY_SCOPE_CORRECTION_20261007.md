# JEPA target-discovery relational replay scope correction — 2026-10-07

Status: `AUDIT_CORRECTION__NO_REAL_RNA_EXECUTION_AUTHORITY`

## Purpose

Correct the current interpretation of the historical TD56–TD59 relational lineage after the HVS/SEA-AD physical-feature-axis defect and the later V77/S174 cache repair work.

This document preserves historical outcomes as historical records, but distinguishes them from current scientific authority.

## Main correction

The HVS/SEA-AD 50K target-discovery expression substrate used by TD56–TD59 was generated through the invalid canonical-ordinal -> physical-column assumption. Therefore any TD56–TD59 terminal that numerically depends on HVS or SEA-AD expression values is `REPLAY_REQUIRED` before it can be used as current biological evidence.

This includes historical PASS results and historical FAIL results.

In particular:

- TD56 historical PASS remains preserved but is `REPLAY_REQUIRED` for HVS/SEA-AD-dependent scientific interpretation.
- TD57A historical PASS remains preserved but is `REPLAY_REQUIRED`.
- TD58 historical PASS remains preserved but is `REPLAY_REQUIRED`.
- TD57B historical 24/24 PASS remains preserved but is `REPLAY_REQUIRED`.
- TD57C historical HVS 2/4 FAIL remains preserved as the historical terminal, but its current scientific status is `REPLAY_REQUIRED__DO_NOT_TREAT_AS_CURRENT_LOCALITY_FALSIFICATION` because the deciding HVS values came from the contaminated substrate.
- TD59 historical 24/24 PASS remains preserved but is `REPLAY_REQUIRED`.

A corrected replay may reproduce or change the old decisions. It may not tune their rules after seeing corrected outcomes.

## What remains reusable without expression replay

The following design objects are outcome-blind / metadata-only and may be preserved if their exact historical bytes/provenance are recovered:

- the historical 17,186-address common-core membership object;
- SHA256 gene-ranking rule `SHA256("TD56S|gene|<address>")`;
- deterministic gene-position allocations;
- pair-hash rules;
- donor/operator metadata and frozen cell identities, subject to custody verification;
- deterministic donor splits;
- triplet sampling rules;
- matched-null hash rules;
- TD57C metadata-only locality feasibility choice of nearest one-third;
- TD59 prospectively fixed nearest-half successor design;
- all historical pass/fail thresholds and sequential stopping rules.

Expression-derived values, distances, pair signs, neighborhood identities, triplet relations, observed statistics and expression-dependent measurability must be recomputed from correctly bound values.

## Exact historical gene-position allocation

All of the surviving relational lineage is generated from the same historical 17,186-address list ranked by:

`SHA256("TD56S|gene|<address>")`

The relevant position allocation is contiguous:

| Historical screen | Ranked positions | Number of genes |
|---|---:|---:|
| TD56 / TD57A / TD58 | 0..1023 | 1,024 |
| TD57B Panel 0/1 | 1024..3071 | 2,048 |
| TD57C Panel 0/1 | 3072..6143 | 3,072 |
| TD59 Panel 0/1 | 6144..9215 | 3,072 |
| **Union** | **0..9215** | **9,216** |

Therefore the minimal molecular replay universe for the complete TD56–TD59 relational history is the first **9,216 historical ranked addresses**, not all 41,238 Molecular Ledger addresses.

This is a replay/minimal-custody fact only. It does not make 9,216 a production vocabulary or target dimension.

## Exact historical cell scope

These screens use `A_NATURAL_MIXTURE`, global rows `0..24,999` from the 50K falsification archive.

Historical source row counts:

- HVS: 1,129
- NPH52: 1,310
- SEA_AD: 22,561
- total: 25,000

The exact historical cell identities/order and donor/operator metadata must be preserved. A replay on a different cell sample would answer a different question.

## Do not regenerate the panels from a new common core

The historical hypotheses are defined by the exact original 17,186-address membership followed by the frozen hash ranking.

Required sequence:

1. recover the original 17,186-address membership object from its historical authority;
2. verify its exact bytes/hash against the recorded authority (derived CSV historical SHA-256 `8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`; support-state authority historical SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`);
3. regenerate the historical SHA ranking from that exact membership;
4. take positions 0..9215 exactly;
5. validate every selected historical address against corrected matrix-native physical feature identity for each source/operator where the historical contract requires common measurement;
6. if a selected address is not actually physically measurable under corrected identity, fail closed and record the historical screen as not exactly replayable under its frozen support premise; do **not** substitute a replacement gene.

A newly recomputed corrected common-core list may be useful for a future prospective experiment, but it cannot replace the historical membership in a replay and still be called the same TD56–TD59 experiment.

## Relation to Macha/S174

Macha's S174 G1/G1b work provides strong corrected identity-binding and rebuilt-cache evidence for the V77 cache scope. Reuse its identity/decoder logic and receipts where applicable.

However the S174 rebuilt cache is not a substitute for the TD56–TD59 replay substrate:

- TD56–TD59 require the exact historical 25,000 A_NATURAL_MIXTURE rows and frozen row identities;
- the V77 cache is a different calibration/cache product;
- therefore target-discovery values must be rematerialized for the historical A rows under the corrected identity chain.

Do not duplicate already-qualified matrix-native identity logic merely to create a separate target-discovery decoder implementation.

## NPH52

NPH52 does not share the specific HVS/SEA-AD canonical-ordinal -> physical-column defect. Historical NPH52 results therefore have a stronger status for that defect.

Nevertheless, for a clean three-source replay it is preferable to read the exact historical NPH52 A rows through the authenticated NPH52 row/feature binding rather than silently mix corrected HVS/SEA-AD values with an old 50K NPH52 payload. This also closes the separate historical NPH52 materialization/availability caveats.

This preference does not imply that historical NPH52 values are invalidated by the HVS/SEA-AD defect.

## Replay order

Preserve the historical scientific chronology and stopping rules. A practical dependency order is:

1. recover and hash-verify exact 17,186 historical membership;
2. generate and freeze the exact 9,216 historical replay-address manifest;
3. verify physical measurability/identity for those addresses against exact source matrices;
4. rematerialize exact A_NATURAL_MIXTURE rows to a fresh immutable corrected artifact;
5. replay TD56;
6. replay TD57A and TD58 under their original rules;
7. replay TD57B under its original two-panel sequential rules;
8. replay TD57C under its original sequential rule;
9. replay TD59 only with its original prospectively frozen rule and fresh historical panel positions;
10. classify each result as `SURVIVES_UNCHANGED`, `DECISION_CHANGED`, `NOT_ESTIMABLE`, or `NOT_EXACTLY_REPLAYABLE`.

No new locality fraction, pair width, threshold, panel replacement or rescue analysis may be introduced into the deciding replay.

## Important locality correction

The earlier Oct-7 shorthand that "TD57C failure remains a failure" was too strong after discovery of the HVS/SEA-AD feature-axis defect.

Correct statement:

> TD57C remains a preserved historical FAIL and cannot be post-hoc rescued by changing its frozen one-third rule. But because its deciding HVS expression values came from the contaminated substrate, it must be replayed on corrected values before the one-third locality falsification can be used as current scientific evidence.

The same principle applies symmetrically to historical PASS results.

## What this does not authorize

This document does not authorize:

- real-RNA rematerialization or replay execution;
- Stage A execution;
- JEPA training or EMA updates;
- target or representation selection;
- TEST/Morabito/reader_validation/oracle opening;
- pathology/outcome access;
- production vocabulary or neighborhood selection.

`TARGET_WINNER = NONE`
`REPRESENTATION_WINNER = NONE`
`TRAINING = OFF`

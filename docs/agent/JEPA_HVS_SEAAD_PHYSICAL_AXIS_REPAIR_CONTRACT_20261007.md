# JEPA HVS/SEA-AD physical-axis repair implementation contract — 2026-10-07

Status: `DESIGN_FROZEN__NO_REAL_RNA_EXECUTION_AUTHORITY`

## Purpose

This document fills one missing layer only: the **pre-execution implementation contract** for repairing HVS/SEA-AD physical feature binding.

It does not replace or repeat:

- `JEPA_FULL104_HVS_SEAAD_FEATURE_AXIS_SEMANTIC_INVALIDATION_20261007.md`;
- `JEPA_HVS_SEAAD_FEATURE_AXIS_CONTAMINATION_BOUNDARY_AND_REPLAY_PLAN_20261007.md`;
- `JEPA_HVS_SEAAD_REPLAY_PLAN_MACHA_SCOPE_CORRECTION_20261007.md`.

Those documents already define the defect, contamination boundary, replay scope and work that must not be repeated.

This contract defines what a future repair implementation must prove **before** any corrected real-RNA values are allowed to influence Stage A or target-discovery readjudication.

## Hard boundary

This file authorizes design only.

It does **not** authorize:

- opening or reading real HVS/SEA-AD expression values;
- rematerialization;
- cache rebuild;
- S149 rerun;
- target-discovery replay;
- Stage-A execution;
- reader_validation/oracle access;
- TEST/Morabito/pathology access;
- training, Stage 4 or 500K.

## Defect being repaired

Forbidden historical shortcut:

`canonical/harmonized source_feature_index == sparse physical matrix column`

Required chain:

`matrix-native feature identity`
`-> exact physical column`
`-> raw count slot`
`-> intended canonical molecular address`
`-> canonical output column`

Numeric ordinal equality is never accepted as proof of identity.

## Source-family physical identity authorities

### HVS

For each exact HVS matrix in replay scope, the repair must authenticate the matrix bytes/source lineage and recover the ordered physical feature vector directly from the matrix-native feature datasets used by that matrix family.

The audited Stage81A2 lineage identifies HVS native feature authority as:

- stable/native ID axis: `raw/var/_index`;
- paired symbol axis: `raw/var/feature_name`;
- expected width for the audited family: `18,736`;
- previously recorded order hash for the audited shared HVS family: `4c1e94c02df22d936270bd82e5229efa81af156c4666ad95849eeabea2e21788`.

The hash is a cross-check, not a substitute for reconstructing the actual ordered feature vector from the authenticated matrix.

If more than one HVS matrix/object is in replay scope, every distinct physical feature vector must be independently authenticated. The known local all-matrix decoder validation of one HVS object does not silently authorize another HVS object.

### SEA-AD

For every exact SEA-AD matrix/region in replay scope, recover the matrix-native ordered feature vector from:

- stable/native ID axis: `var/gene_ids`;
- paired symbol/name axis: `var/index`;
- expected width for the audited family: `36,601`.

Historical references to an `a7391464...` ordered-feature family are leads only. The repair must reconstruct the full ordered vector from the exact authenticated matrix and then compare hashes/sidecars; it may not infer physical order from a filename or partial hash.

All SEA-AD matrices in replay scope must be checked individually even when they are expected to share one order.

## Canonical join rule

For each matrix:

1. normalize the matrix-native stable feature identifier only by a prospectively documented identifier-normalization rule needed for exact identity comparison (for example, Ensembl version stripping only if the canonical ledger authority itself uses the corresponding unversioned identity);
2. join matrix-native stable identity to the frozen canonical molecular-address provenance by identity, never by ordinal;
3. preserve the exact physical column index from the matrix-native ordered vector;
4. require one unambiguous physical feature identity for every consumed scalar canonical address;
5. write output only to that address's frozen canonical output column;
6. record both the physical identity and canonical identity in the repair receipt.

No symbol-only fallback is allowed for deciding values when a stable identifier is expected.

## Fail-closed rules

A value is unavailable rather than guessed when any of the following occurs:

- source stable ID is unresolved;
- normalized identity maps to multiple physical columns;
- canonical address maps to multiple unresolved source features;
- feature vector width differs from authenticated matrix width;
- reconstructed feature-order hash disagrees with the matrix/source authority;
- stable ID and paired symbol provide contradictory identity evidence requiring adjudication;
- expected count/raw slot is absent or its semantics are not provenance-bound;
- collision status is unresolved;
- decoder and identity-join disagree on an unambiguous sentinel and the disagreement cannot be explained by the decoder's documented conservative collision policy.

There is no positional/rank fallback.

## Raw-slot contract

Before consuming any value, the future implementation must record for each matrix:

- exact source file/object identity and SHA/hash authority;
- sparse/dense storage location;
- exact raw/count slot or dataset path;
- integer-count status where applicable;
- matrix dimensions;
- feature-axis dimensions;
- cell-axis identity authority;
- normalization rule applied after extraction.

The repair must not silently change historical normalization while repairing feature identity. Feature-axis repair and normalization changes are separate scientific changes.

## Decoder role

The Sept-27 decoder lineage and later local all-matrix decoder run are **validation oracles**, not the primary production binding.

Primary repair binding:

`matrix-native stable ID -> physical column -> canonical address`

Decoder use:

- independently cross-check physical-column identity/value extraction;
- report agreement for all decoder-covered matrices;
- explicitly report decoder-uncovered matrices;
- preserve the decoder's documented 682 SEA-AD conservatively dropped multi-gene/summed columns as a separate comparison class rather than forcing production repair to drop them automatically.

The production repair may retain a uniquely resolvable physical column that the conservative decoder declined, but it must report that difference explicitly.

## Sentinel suite — required before any bulk rematerialization

The repair implementation must define a deterministic sentinel set **before opening bulk corrected outputs**.

Sentinels must include, per source family and where supported:

1. addresses used in the historical 29-address corrected artifact;
2. several ordinary unambiguous genes selected deterministically from the address universe without expression outcomes;
3. at least one low physical-column index and one high physical-column index;
4. at least one historical case where harmonized rank and physical column differ substantially;
5. collision/unresolved examples that must fail closed;
6. any matrix-specific identity edge case discovered during feature-vector authentication.

For each unambiguous sentinel, record:

- matrix ID/source file;
- cell ID used for value cross-check;
- canonical molecular address;
- matrix-native stable feature ID;
- physical column;
- old historical `source_feature_index` if applicable;
- direct source value;
- repaired extractor value;
- decoder value if decoder-covered;
- exact equality verdict for integer raw counts;
- classification of any mismatch.

A sentinel failure blocks bulk rematerialization.

## Exhaustive mapping proof — required after sentinels, before scientific replay

Sentinels are necessary but insufficient.

For every matrix in replay scope, emit a machine-readable table covering every candidate physical feature / canonical address consumed by the rematerializer, containing at minimum:

- matrix identity;
- physical column;
- matrix-native stable feature ID;
- matrix-native symbol/name;
- normalized identity used for join;
- canonical molecular address/index;
- mapping status;
- collision status;
- decoder cross-check status when available.

Acceptance requires:

- exact matrix width match;
- no duplicate physical column consumed for two scalar canonical addresses unless explicitly adjudicated by frozen collision semantics;
- no unresolved address silently assigned a value;
- no rank-based fallback;
- complete accounting of mapped/unmapped/collision-blocked features.

## Immutable output policy

Historical contaminated substrates remain untouched.

Every future repaired artifact must be written under a new root and bind:

- source matrix identities/hashes;
- ordered native feature-vector hashes;
- canonical registry/provenance hash;
- repair code commit/hash;
- mapping-table hash;
- sentinel receipt hash;
- output shard hashes;
- merged-output hash;
- normalization specification.

No overwrite-in-place of historical 50K, Level-4 or Stage81A3R/V77 real-RNA caches is allowed.

## Required pre-rematerialization verdict

A future implementation may advance to bulk corrected rematerialization only if all matrices receive:

`PHYSICAL_AXIS_IDENTITY_QUALIFIED_FOR_REPAIR`

Otherwise classify each matrix as one of:

- `BLOCKED__FEATURE_VECTOR_NOT_AUTHENTICATED`
- `BLOCKED__RAW_SLOT_NOT_AUTHENTICATED`
- `BLOCKED__AMBIGUOUS_IDENTITY_MAPPING`
- `BLOCKED__DECODER_SENTINEL_DISAGREEMENT`
- `BLOCKED__OTHER_PROVENANCE_FAILURE`

Partial qualification of one matrix/source does not authorize another.

## After a future authorized rematerialization

The existing replay plan remains controlling:

1. preserve old artifacts;
2. compute old-vs-corrected deltas first;
3. identify which historical panels/features were actually changed;
4. selectively replay only decision-bearing analyses whose numerical inputs changed;
5. preserve original prospectively frozen hypotheses/nulls/thresholds where applicable;
6. do not rescue historical failures post hoc.

## Current terminal state

`REPAIR_DESIGN = FROZEN`

`REAL_RNA_REPAIR_EXECUTION = NOT_AUTHORIZED`

`STAGE_A_EXECUTION = NOT_AUTHORIZED`

`TRAINING = OFF`

`TARGET_WINNER = NONE`

`REPRESENTATION_WINNER = NONE`

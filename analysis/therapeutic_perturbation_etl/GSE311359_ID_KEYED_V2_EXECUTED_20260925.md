# GSE311359 — ID-keyed V2 executed; phantom rows eliminated (audit P1-7)

Date: 2026-09-25
Producer: `scripts/build_gse311359_id_keyed_effects_v2.py`
Physically executed on the authenticated `GSE311359_RAW.tar` across all 7 samples.

```
feature identity source        deposited features.tsv column 1
keyed on                       feature ROW index carrying the feature ID
phantom units in V2            0
non-BIN1 units reproduced      2,434 / 2,434 exactly
BIN1 cis elements              3, kept separate, each carrying real counts
V1 artifacts                   untouched; V1 BIN1 outcomes not reused
```

## The defect, and its exact scope

V1 keyed pseudobulk on the feature **display name**. Three capture features
share the name `BIN1`, so their counts collapsed into one unit while three
`ncells` entries reported cells.

Measured directly against the V1 artifact:

```
V1 rows claiming cells while holding zero counts : 14
those rows' guide_id                             : BIN1 only
V2 equivalent                                    : 0
```

Fourteen phantom rows, all BIN1, exactly as predicted from the 7 samples × 2
surplus features. No other target produced one.

## Non-BIN1 reproduction — the condition PR #92 left open

PR #92 allowed the other 82 targets "scoped validity only if independent tests
confirm they were unaffected". Run over every unit:

```
non-BIN1 units    V1 2,434    V2 2,434    common 2,434
V1-only 0    V2-only 0
n_cells mismatches       0
total_counts mismatches  0
distinct guide IDs reproduced  365
```

Exact reproduction, not approximate agreement. The keying change moves nothing
outside BIN1, which is what the exhaustive feature-table check predicted: 381
guide features, 381 distinct IDs, exactly one shared display name.

## The three BIN1 elements under ID keying

```
BIN1_enh_1      7 units   74 cells   337,458 counts
BIN1_enh_2      7 units   81 cells   398,453 counts
BIN1_enh_2_AS   7 units   84 cells   357,222 counts
```

Each now carries its own cells and its own counts across all seven samples.
Under V1 these three shared a single 37-cell counter per sample with only one
holding counts.

They are kept **separate**. Summing them would average three different
cis-regulatory interventions — a second error, independent of the phantom-row
defect, and one that a naive "fix" would have introduced.

## Guards in the producer

* fails closed if the seven feature tables are not identical in ID, name, type
  and order, since pooled aggregation depends on it;
* fails closed on duplicate feature IDs;
* **asserts no unit may report cells while holding zero counts** — the V1
  phantom signature — so the defect cannot silently recur;
* refuses an occupied output directory;
* non-targeting role is determined from the **feature ID** prefix, verified
  against the deposit as 17 controls, not from a V1-derived label.

## What this does NOT establish

Kept explicit so the identity fix is not over-read:

* **No protospacer sequence is proven.** The deposit carries no guide sequence
  table for GSE311359. Sequence identity for these three features remains an
  open limit, and a sequence source is still wanted.
* **No perturbation efficiency is measured** for any element.
* **No cis causality.** `BIN1` is the depositors' own nominated label on the
  feature ID. That the element regulates BIN1 is their assertion, carried
  forward as such and not verified here.

## Status

```
was  STOP_AUTHOR_SOURCE_MISSING_FOR_BIN1   (PR #92)
then STOP_PENDING_PHYSICAL_V2_REBUILD      (identity resolved from the deposit)
now  PASS_DEVELOPMENT_ETL_ID_KEYED         (rebuild executed and verified)
     with SEQUENCE_IDENTITY_UNPROVEN as a standing, separate limit
```

The other 82 targets are no longer merely "confirmed unaffected by the
collision" — they are reproduced exactly under the corrected keying.

Outputs on the external disk, referenced by digest in
`GSE311359_ID_KEYED_RECEIPT_V2.json`. V1 artifacts are preserved byte-for-byte
and no V1 BIN1 outcome is reused anywhere.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```

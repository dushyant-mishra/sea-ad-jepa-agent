# GSE311359 — BIN1 guide collapse: **CONFIRMED**, with phantom pseudobulk rows

Date: 2026-09-24
Raised by: PR #92 (independent review lane)
Status: **defect confirmed and characterised**; remediation requires an
authenticated feature-ID to protospacer map that does not yet exist.

```
duplicate guide_id in identity table    CONFIRMED   BIN1 x3 of 381 rows
guide UMI counting                      CORRECT     row-indexed, not name-keyed
per-cell guide assignment               CORRECT     row-indexed
pseudobulk aggregation                  DEFECTIVE   3 features -> 1 unit
phantom rows in guide_sample_meta       14          claim 37 cells, hold 0 counts
BIN1 target engagement                  INVALID
other 82 targets                        UNAFFECTED
```

## What PR #92 reported, verified independently

`GSE311359_perturbation_identity.csv` holds 381 feature rows but only 379 unique
`guide_id` values. `BIN1` appears three times:

```
380:BIN1,BIN1,other,,False
381:BIN1,BIN1,other,,False
382:BIN1,BIN1,other,,False
```

Every other feature follows a `<target>_tss_g<n>` or `non-targeting_<nnnnn>`
convention. These three are bare `BIN1` with no guide index, so the source
deposit did not distinguish them by name. Duplication of `target_id` is by
design — multiple guides per target — but `guide_id` is the feature identity and
must be unique.

## What the review did not state: the failure mode is phantom rows, not merging

The counting layer is **not** affected. Guide UMIs are accumulated by feature row
index, and the dominance rule selects a row index:

```python
if r in guide_pos:
    guide_counts[c][r] = val           # r is the feature row, not the name
best_row, best_umi = max(d.items(), key=lambda kv: kv[1])
single[c] = best_row
```

So a cell dominated by BIN1-feature-1 versus BIN1-feature-2 is resolved
correctly at the physical level. The defect enters one line later, where the row
index is converted back to a name to build the pseudobulk key:

```python
g = ref_names[r]                        # "BIN1" for all three rows
col_key[c] = kindex[f"{g}||{s}"]        # resolves to ONE position
ncells[f"{g}||{s}"] += 1                # ONE shared counter
```

`keys` received three `BIN1||S1` entries from the identity list, so three
positions exist in the pseudobulk matrix, but `kindex` maps the name to only one
of them. The consequence is visible in the emitted artifact:

```
sample=S1  n_cells=37  total_counts=0          <- phantom
sample=S1  n_cells=37  total_counts=0          <- phantom
sample=S1  n_cells=37  total_counts=146841     <- carries all the counts
```

All three rows report the same 37 cells because they share one counter, while
only one holds expression. The retention filter is `ncells[k] > 0`, which is 37
for all three, so **both phantoms survive into the result**: 14 rows across the
seven samples that claim cells they do not contain.

## Why this invalidates BIN1

`GSE311359_target_engagement.csv` reports `n_guides = 3` for BIN1 and marks it
`engagement_measurable = True`. The three contributing rows are one real
pseudobulk and two all-zero vectors. After CPM and `log2(x + 1)` an all-zero row
becomes a vector of zeros, so BIN1's engagement is an average over one real
measurement and two artefacts of the indexing bug.

Its across-sample values are
`-0.36, -2.51, -0.65, -1.57, -2.27, -1.94, -2.04`.

The instability is not by itself proof of the defect — the across-sample range of
2.16 is actually *below* the median range of 2.96 across the nine targets with
measurable engagement — but no value computed from phantom rows can be used
regardless of how it looks.

## Scope

Exactly one target is affected. `guide_id` has one duplicated value across the
whole table, and it is BIN1. The remaining 82 targets and all non-targeting
controls key uniquely and are unaffected by this defect.

BIN1 is an Alzheimer disease risk gene and one of the reasons this study was
prioritised, so "one target of 83" understates its importance to the collection
even though it overstates the computational blast radius.

## What remediation requires, and why it cannot be done locally

The three features must be told apart before they can be aggregated correctly,
and the deposit does not distinguish them by name. That needs either:

1. an authenticated feature-ID to protospacer map for the GSE311359 library, so
   each capture feature carries its own identity; or
2. the library table from the source publication, in the way Supplementary
   Table 5 supplied the 81 protospacers for GSE178317.

Neither exists in the acquired assets. Until one does, the correct treatment is:

* **exclude BIN1 from any benchmark or effect table** rather than report a value
  computed from phantom rows;
* key pseudobulk on the **feature row index**, never the guide name, so a
  duplicate label cannot silently create shared counters again;
* fail closed on any duplicate `guide_id` at load, which PR #92 adds.

No BIN1 value should be repaired by choosing one of the three rows: which
capture feature the real counts landed in is an artifact of dict insertion order,
not a biological fact.

## Standing instruction this reinforces

A name is not an identity. GSE311359 keyed a physical unit on a label that the
depositors did not guarantee unique, and the failure was silent and produced a
plausible number. The same rule that makes `selection_row` the cell identity in
FULL104 applies here: the identity of a capture feature is its row in the
authenticated feature census, never its display name.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```

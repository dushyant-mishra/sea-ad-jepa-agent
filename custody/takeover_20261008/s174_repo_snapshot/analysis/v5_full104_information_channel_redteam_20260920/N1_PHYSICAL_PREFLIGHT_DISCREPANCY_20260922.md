# N1 read-only physical preflight — **STOP: discrepancy in the frozen heavy artifact**

Date: 2026-09-22
Branch: `gpu/v5-n1-physical-preflight-exec-20260922-claude`
Parent: `8348c7308156a23df08a83897027e55260e3c203` (PR #62 head, verified unmoved)

```
RESULT   PREFLIGHT_FAILED
CAUSE    the heavy artifact carries TWO mutually inconsistent source encodings
ACTION   reported; no frozen input was replaced, repaired or regenerated
```

**Good news first, because the failure reads worse than it is.** Nothing here
invalidates a measured number, and the donor-level source encoding that all the
science actually uses is correct and agrees across four independent artifacts.
The defect is in a *label array* inside the heavy NPZ, and **PR #62's preflight
caught it on its first real run**. That is the gate working exactly as designed.

**N1 was not executed.** No burden computed, no mask generated, no target
selected, no precision evaluated.

---

## What happened

```
$ python scripts/agent/preflight_full104_audit_b_n1_physical_v1_20260922.py \
    --heavy-artifact  .../core_sufficient_statistics_v1.npz \
    --independent-qualification .../DONOR_UMI_INDEPENDENT_QUALIFICATION_V1.json \
    --split-receipt   .../full104_split_receipt_v1.json \
    --out             .../AUDIT_B_N1_PHYSICAL_PREFLIGHT_V1.json

ValueError: source-name ordering differs from frozen HVS/NPH52/SEA_AD
```

All three inputs authenticated before the run:

| input | digest | state |
|---|---|---|
| heavy NPZ | `f77dff47…`, 242,087,519 B | matches bound |
| `donor_umi` qualification (PR #59) | `bbd2b95b…` | `DONOR_UMI_INDEPENDENTLY_QUALIFIED` |
| outer split receipt | canonical `5d616c9c…`, 4 folds, 104 donors | matches bound |

## Ground truth, recomputed from authenticated Level-4 metadata

| source | donors | cells |
|---|---:|---:|
| HVS | **41** | 198,718 |
| NPH52 | **17** | 236,476 |
| SEA_AD | **46** | 4,118,213 |
| total | 104 | 4,553,407 |

Donor sets are disjoint across sources (all pairwise overlaps 0).

So PR #62's frozen `SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")` with
`EXPECTED_SOURCE_COUNTS = (41, 17, 46)` is **correct**.

## The defect: two source encodings inside one file

The heavy NPZ stores `source_names = ['HVS', 'SEA_AD', 'NPH52']` — codes 1 and 2
transposed relative to ground truth. Worse, the file's own two source vectors then
disagree with each other:

| array | code 0 | code 1 | code 2 | follows |
|---|---|---|---|---|
| `donor_src` | HVS (41) | **NPH52 (17)** | **SEA_AD (46)** | canonical sorted order |
| `src_of_cell` | HVS | **SEA_AD** | **NPH52** | the stored (transposed) `source_names` |

```
src_of_cell == donor_src[cell_donor]  ->  FALSE
```

Two arrays in the same frozen, `HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE` file encode
the same fact incompatibly.

### Root cause

`full104_physical_shakedown_v1.py:295` defines the canonical rule:

```python
source_names = tuple(sorted({str(row["source"]) for row in manifest}))
```

Sorted, that is `('HVS', 'NPH52', 'SEA_AD')`. The heavy-NPZ producer instead
recorded **first-appearance order in the manifest**, which is HVS, SEA_AD, NPH52 —
then encoded `src_of_cell` under that order, while `donor_src` was built under the
canonical one.

## What is NOT affected

Four artifacts agree on the **donor-level** encoding, which is the one the science
consumes:

| artifact | 0 | 1 | 2 | agrees |
|---|---|---|---|---|
| split receipt `donor_source_code` (+ its own `source_names` = HVS/NPH52/SEA_AD) | HVS 41 | NPH52 17 | SEA_AD 46 | ✅ |
| target-qualification sample `donor_source_code_i64.npy` | HVS 41 | NPH52 17 | SEA_AD 46 | ✅ |
| heavy NPZ `donor_src` | HVS 41 | NPH52 17 | SEA_AD 46 | ✅ |
| ground truth from Level-4 metadata | HVS 41 | NPH52 17 | SEA_AD 46 | — |

`sample donor_source_code == NPZ donor_src` → **True**.

**My earlier rare-tail structural report is therefore correct.** It labelled the
twelve source × fold cases `0=HVS, 1=NPH52, 2=SEA_AD` from the sample's
`donor_source_code`, which is the canonical convention. The NPH52 zero-margin
finding (folds 1, 2, 3 at exactly 4 eligible donors) stands as reported.

## A gap in my own earlier work, stated plainly

My V2 heavy qualification receipt asserts `per_cell_source_vector_agrees: true`.
That assertion is *literally* true — `src_of_cell` does match the mapping built
from the stored `source_names` — but it validated a **mislabeled** encoding and
never cross-checked `src_of_cell` against `donor_src`. A one-line check
(`src_of_cell == donor_src[cell_donor]`) would have caught this a session earlier.
The check I wrote confirmed internal consistency with the wrong reference and
reported it as agreement.

## Adversarial controls — the binder itself is sound

Run in memory against `validate_bound_arrays`; the frozen artifact was never
modified. With canonical `source_names` supplied, the binder **accepts** the real
arrays — so `source_names` is the sole blocker.

| control | rejection |
|---|---|
| donor permutation, source counts preserved (within-source) | `donor identity/order is not the sorted unique FULL104 registry` |
| `donor_src` permuted, 41/17/46 multiset preserved | `donor_source_vector_sha256 differs from independently qualified physical array` |
| stored NPZ `source_names` | `source-name ordering differs from frozen HVS/NPH52/SEA_AD` |
| strict-core order transposed | `strict-core order/range is invalid` |
| `donor_umi` as float64 (precision loss) | `donor_umi must be exact frozen int64 geometry (104, 17186)` |
| `donor_umi < donor_nnz` at one cell | `detected/UMI counts must be nonnegative with raw UMI >= detected` |
| negative `donor_nnz` | same guard |
| qualification verdict weakened | `independent qualification receipt does not assert qualification` |
| qualification bound to a different artifact | `independent qualification binds the wrong heavy artifact` |
| split canonical digest altered | `outer split has the wrong frozen canonical digest` |

**All ten rejected.** The two donor-permutation controls matter most: they are the
B2 concern made concrete — counts alone authenticate nothing — and PR #62 catches
them by binding `donor_source_vector_sha256` to the independently qualified array
rather than to a histogram. Integer precision is enforced by exact `int64` dtype,
so a float64 copy is refused outright.

## What must happen before N1

This is the owner's call; I have not chosen between these.

1. **Correct `source_names` and `src_of_cell` in the heavy artifact** to the
   canonical sorted order and re-qualify. This changes the artifact SHA, so every
   receipt binding `f77dff47…` must be re-issued. Cleanest, most expensive.
2. **Leave the artifact byte-identical and add a successor qualification** that
   declares `donor_src` the authoritative source vector, records `source_names`
   and `src_of_cell` as **defective and forbidden for weighting**, and has the
   N1 runtime consume only `donor_src`. Cheapest, but leaves two wrong arrays in
   a qualified file where a future caller can still reach them.
3. Whichever is chosen, add the missing cross-check
   `src_of_cell == donor_src[cell_donor]` to the qualification so this class of
   defect cannot recur silently.

I did not adopt option 2 unilaterally, because deciding that a frozen array is
"present but forbidden" is a scientific-governance call, not a mechanical repair —
and doing it quietly is exactly how a mislabeled array survives into a result.

```
AUDIT_B_N1         = UNOPENED
BURDEN CALCULATION = NOT RUN
MASKS GENERATED    = NONE
TARGETS SELECTED   = NONE
PRECISION          = NOT CALCULATED
TRAINING           = OFF
```

# Audit A — hidden normalization-denominator information

Date: 2026-09-20
Status: **`NEW_FINDING` / `OPEN`. No authority is changed. No biological claim.**

Produced by `scripts/audit_a_normalization_denominator_20260920.py` over all
8,915 authenticated blocks and all 4,553,407 cells, 39.4 minutes.
Evidence: `evidence/audit_a/`.

Label discipline, held throughout: this measures
**`OUTSIDE_LEDGER_DENOMINATOR_INFLUENCE`**. That is *not* the same channel as
**`DIRECT_HIDDEN_TARGET_LEAKAGE`**, which Audit F13 addresses separately. Neither
is evidence for the other. Evidence class:
`SUPPORTING_SHORTCUT_RECONNAISSANCE`.

---

## 1. The mechanism, verified in source rather than assumed

Both authenticated materializers compute `source_library` from the **raw source
expression, before** mapping and filtering to the 41,238-address ledger.

Python/H5 materializer, SHA `575d02a4…`, verbatim:

```python
libraries.append(int(np.rint(values).sum()))      # ALL raw source counts
in_range = indices < len(source_to_address)
targets  = np.full(len(indices), -1, dtype=np.int32)
targets[in_range] = source_to_address[indices[in_range]]
keep = targets >= 0                               # only mapped addresses
value_parts.append(np.rint(values[keep]).astype(np.int32))
```

NPH52 R materializer, SHA `ca595536…`, verbatim:

```r
mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
libraries <- as.numeric(Matrix::colSums(counts[,columns,drop=FALSE]))   # FULL
local <- t(counts[mapping$source_feature_index+1L, columns[take], drop=FALSE])
```

(R stores genes × cells, so `colSums` is the per-cell total over all genes; line
42 explicitly removes collision-blocked features from the mapping while line 45
sums everything.)

So RNA that never enters the ledger — unmapped features, collision-blocked
features, out-of-range source indices — still divides **every visible normalized
feature** through `log1p(raw · 10000 / source_library)`.

## 2. Magnitude

Over all 4,553,407 cells:

| quantity | value |
|---|---|
| total source library | 122,517,308,792 |
| total ledger mass | 117,838,742,268 |
| **total outside-ledger mass** | **4,678,566,524** |
| **pooled fraction outside ledger** | **0.0381869841** |
| pooled fraction reaching the strict core | 0.5735088987 |
| cells with any outside-ledger mass | 4,354,643 (**95.63%**) |

Per-cell `fraction_outside_ledger`: mean 0.036775, median 0.039514,
p95 0.046468, p99 0.050374, **max 0.25**.

So for a typical cell about 3.9% of the denominator is RNA the model never sees,
and for the worst cells a quarter of it is.

## 3. The channel is strongly source-dependent

| source | cells | outside-ledger mean | outside-ledger max | fraction reaching core (mean) |
|---|---|---|---|---|
| **HVS** | 198,718 | **0.000000** | **0.000000** | 0.950307 |
| **NPH52** | 236,476 | 0.014000 | 0.039530 | 0.896396 |
| **SEA_AD** | 4,118,213 | **0.039857** | **0.250000** | 0.545215 |

HVS is **exactly** zero — every count in an HVS cell's library reaches the
ledger. SEA_AD cells carry ~4% outside, and only 54.5% of a SEA_AD cell's
library reaches the strict core at all.

Two cells with identical ledger counts therefore normalize differently depending
on which source they came from. The denominator carries source identity into
every feature.

## 4. The denominator identifies the source perfectly

Donor-honest leave-one-donor-out nearest-centroid classification, using **only**
the three denominator fractions averaged per donor, unconditional over all 104
donors (no donor contributes to its own prediction):

| label | accuracy | majority-class baseline | classes |
|---|---|---|---|
| **source** | **1.0000** | 0.4423 | 3 |
| operator | 0.3173 | 0.2596 | 12 |

**104 of 104 donors classified correctly.** The normalization denominator alone
is a perfect out-of-donor source label.

A cell-level diagnostic — what share of cells fall nearest their own donor's mean
denominator vector — gives 0.0343 against a 0.0096 chance rate. Above chance but
weak, and it is a separability measure rather than an out-of-donor claim, so it
is reported as supporting only.

## 5. Why this matters, and what makes it consequential

A perfectly source-identifying scale factor sits inside every feature the model
reads. On its own that is a nuisance-variable finding. What makes it
consequential is Audit D:

> The primary attacker's score is a **within-donor centred** correlation. Donor-
> and source-level structure is removed before the correlation is taken, in
> **every** standardization regime tested — it is a property of the score, not of
> the standardization.

So this channel is, by construction, **invisible to the current attacker and to
any capacity-matched successor that inherits the same estimand**, while remaining
fully available to a production JEPA that reads absolute normalized values across
donors and sources.

That is the `A → D → G3` chain, and it is now quantified at both ends: the
channel perfectly identifies source (§4), and the estimand cannot express it
(Audit D, measured affine-invariance of exactly 0.000e+00).

## 6. Verification

All fail-closed invariants passed over all 4,553,407 cells:

```
source_library_positive                          true
ledger_mass_never_exceeds_source_library         true
outside_ledger_mass_never_negative               true
core_mass_never_exceeds_ledger_mass              true
all_fractions_finite                             true
independent_ledger_sum_routes_agree              true
core_nonzero_count_matches_authenticated_pass1   true
identity_space_closed                            true
```

Two independent corroborations, neither a second call to the same helper:

1. `L_ledger` accumulated both by `csr.sum(axis=1)` and by `np.add.reduceat` over
   the raw `data`/`indptr` arrays — agreement required per block.
2. The observed per-cell core nonzero count compared against `cell_nnz_core` in
   the authenticated pass1 NPZ, produced by a **different script in a different
   session**. Exact agreement across all 4,553,407 cells.

Test suite: 31 tests, 0 skipped — including a positive control recovering a
*known* outside-ledger mass exactly, a complementary control requiring zero to be
reported as zero, five negative controls each pinned to its specific abort
reason, and an int32-overflow regression.

## 7. What is not concluded

- **No biological claim.** This is reconnaissance.
- **No authority is changed.** Nothing about pass1, the census, eligibility, the
  burden ladder or the masking policy is modified.
- This is **not** direct hidden-target leakage. The F13 counterfactual separately
  established that changing a stored target value while holding the authenticated
  `source_library` fixed moves no feature. That test constrains the
  *implementation*; it does not address this channel, which lives in the data.

## 8. Proposed repair — required, not applied

```
PROPOSED_REPAIR_REQUIRED
```

At least three responses exist, and they are **different scientific positions**,
not variants of one bug fix:

1. **Re-derive the denominator from ledger mass.** Makes every feature a function
   only of modelled RNA and removes the channel. But it changes what
   normalization *means* — it is no longer library-size normalization against the
   cell's actual sequencing depth.
2. **Keep the biological library and model the channel explicitly**, carrying
   `fraction_outside_ledger` as a declared covariate. Preserves the biological
   meaning, at the cost of an extra modelled nuisance dimension.
3. **Change the estimand** so the attacker can see between-donor structure,
   making the channel measurable rather than removed.

Choosing among these is a design decision with consequences for what the
representation means. **It is deliberately not made here**, and it should not be
made by whichever option produces a preferred masking outcome.

```
OUTSIDE_LEDGER_DENOMINATOR_INFLUENCE = NEW_FINDING / OPEN
BIOLOGICAL_CLAIM = NONE
AUTHORITY_CHANGED = NONE
TRAINING_OFF
```

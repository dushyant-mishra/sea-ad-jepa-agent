# Audit G — calibration-cache tail coverage

Date: 2026-09-20
Status: **`NO_ISSUE_FOUND`. The cache behaves exactly as designed.**
The cache was not rebuilt and its role is unchanged.

Produced by `scripts/audit_g_cache_coverage_20260920.py`.
Evidence: `evidence/audit_g/`.

> **Correction notice.** An earlier revision of this report concluded that the
> cache over-represented HVS by 9.1× and was biased toward high-complexity cells,
> and marked both as `NEW_FINDING`. **Both conclusions were wrong.** They measured
> the cache against the *population marginal*, which the design explicitly
> rejects. Measured against the baseline the design actually targets, the cache
> matches to within 0.05%. The corrected analysis is below; the error and its
> cause are recorded in §5 rather than quietly removed.

---

## 1. The design target

From `FULL104_MASKING_NONLINEAR_CHALLENGE_20260918.md`:

> "Sampling is deterministic within donor, and **each donor receives equal total
> fit weight so large donors cannot dominate merely because they contain more
> cells.**"

So the cache is **equal-donor-weighted by construction**: 1,024 cells per donor,
104 donors. The population marginal — in which SEA_AD holds 90.4% of cells — is
precisely what that design is built to avoid. It is the wrong reference.

Within-donor selection uses `row_priority(full104_manifest_sha256, donor_code,
selection_row)`, a hash of the cell's **scientific identity**. It never sees
expression content, so it cannot preferentially retain complex cells.

## 2. The cache is exactly equal-donor-weighted

| source | donors | expected (`donors × 1024`) | observed | difference |
|---|---|---|---|---|
| HVS | 41 | 41,984 | **41,984** | **0** |
| NPH52 | 17 | 17,408 | 16,465 | −943 |
| SEA_AD | 46 | 47,104 | **47,104** | **0** |
| **total** | 104 | 106,496 | 105,553 | −943 |

The single shortfall is donor code 96 (NPH52), which has only 81 cells in total —
fewer than the cap. Every other donor is at exactly 1,024.

Source shares:

| source | population | **equal-donor-weight target** | cache observed |
|---|---|---|---|
| HVS | 4.3642% | **39.4231%** | **39.7753%** |
| NPH52 | 5.1934% | 16.3462% | 15.5988% |
| SEA_AD | 90.4425% | **44.2308%** | **44.6259%** |

The cache tracks its design target to within 0.75 percentage points, the residual
being that one short donor.

## 3. The complexity "shift" is the same thing

| measure | population | **equal-donor-weight expectation** | cache observed | deviation |
|---|---|---|---|---|
| mean core nonzeros per cell | 2,870.4 | **3,370.1** | **3,371.6** | **+0.05%** |

The marginal moves because the up-weighted donors genuinely carry more detected
core genes:

| source | population mean core nonzeros | donors |
|---|---|---|
| HVS | 4,055.2 | 41 |
| NPH52 | 3,573.8 | 17 |
| SEA_AD | 2,772.8 | 46 |

Equal-donor weighting promotes HVS and NPH52 from 9.6% of cells to 55.8% of the
cache, and those donors have higher complexity. The entire shift follows, with a
residual of 0.05%.

## 4. The low tail is retained as expected

| | cells |
|---|---|
| low tail (≤ 438 core nonzeros) in population | 45,655 |
| **expected in cache under equal-donor hash sampling** | **420** |
| observed in cache | **403** |
| observed / expected | **0.959** |

There is no sparse-cell filter and no low-tail suppression. The cache retains
2.3% of cells, so the very rarest extremes — the single cell with one detected
core gene — are simply unlikely to be drawn. The cache minimum of 30 against a
population minimum of 1 is sampling, not exclusion.

## 5. What I got wrong, and why

The earlier revision compared the cache's marginals against the **population**
and read every deviation as bias. That reference is only correct if the design is
trying to be population-representative, and this one explicitly is not.

Two checks would have prevented it, and neither was expensive:

1. **Read the design intent in the project history.** One sentence in
   `FULL104_MASKING_NONLINEAR_CHALLENGE_20260918.md` states the equal-donor-weight
   rule outright.
2. **Check whether the mechanism could produce the claimed bias at all.** The
   within-donor selector is a hash of donor and selection row — content-blind.
   Reading it would have settled the complexity claim in one step.

The same failure produced both false findings, because both compared against the
same wrong baseline.

## 6. Verdict

```
G_CACHE_EQUAL_DONOR_WEIGHTED_AS_DESIGNED         = CONFIRMED (deviation +0.05%)
G_CACHE_BIASED_TOWARD_HIGH_COMPLEXITY_CELLS      = WITHDRAWN (was measured against the wrong baseline)
G_PER_DONOR_CAP_REORGANIZES_SOURCE_COMPOSITION   = WITHDRAWN AS A FINDING (it is the design intent)
G_LOW_TAIL_SUPPRESSED                            = WITHDRAWN (observed/expected 0.959)
G_CACHE_CURRENT_ROLE                             = UNCHANGED
AUDIT_G_OUTCOME                                  = NO_ISSUE_FOUND
```

## 7. The one question that remains genuinely open

Not a defect, and not answered here: **is equal-donor weighting the right
weighting for capacity calibration specifically?**

It is clearly right for a source-balanced estimand, which is what the masking
score uses. Whether capacity — how much model is needed before a shortcut becomes
exploitable — should be calibrated under equal-donor weighting or under the
population the model will actually meet is a separate design question that
belongs with G3. This audit does not answer it and does not need to.

## 8. Not measured

`source_library` depth and outside-ledger-fraction coverage were reported
`NOT_MEASURABLE` in the earlier revision because the Audit A per-cell artifact
did not yet exist. It now does, and the comparison is a rerun via
`--audit-a-cells`. Given §2–§4, the expectation is that those marginals will also
match their equal-donor-weight predictions; that expectation has **not** been
verified, and is flagged rather than assumed.

No pathology or protected label was introduced or read.

```
TRAINING_OFF
```

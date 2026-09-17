# V5 masking V2 — interpretation ruling on the primary qualification metric

Recorded 2026-09-16, **while the frozen ladder is still executing**. Nothing in the running
ladder is altered by this document. No threshold, metric, contract term or analysis path is
changed. Levels 2 and 3 run exactly as preregistered.

## 1. The Level-1 headline is a metric-design failure, not noise

The ladder printed `reduction 297.7%` for Level 1. That number must not be read as a pass.

The frozen primary statistic is partial R² = `(R²_full − R²_base) / (1 − R²_base)`, "lower
is better", with a ≥30% relative reduction threshold. Partial R² is **unbounded below**.
When a freshly refit attacker predicts catastrophically worse than its own baseline it
reaches extreme values:

| condition | mean | median | min |
|---|---|---|---|
| U | −6.9649 | −0.1304 | **−2276.78** |
| V1 | −2.0678 | −0.1265 | −148.87 |
| V2 | −27.6982 | −0.1198 | **−15256.45** |

Once values like −15,256 enter, a relative-reduction threshold stops meaning anything:
**−15,000 is not thousands of times better shortcut suppression than −0.1.**

### Ruling

Level 1 is recorded as:

> **frozen primary mean executed as specified, but the primary aggregate is
> numerically/pathologically non-interpretable.**

The median and the distribution are **diagnostics**, not a retroactive replacement
qualification metric. This run is not rescued by switching to the median after seeing
results, and it is not declared a pass on the strength of a large negative mean.

## 2. A design defect in the comparison, visible in the decomposition

| subset | n | U mean / median | V2 mean / median |
|---|---|---|---|
| shortcut set non-empty (V2 genuinely targeted) | 22 | 0.042 / 0.0457 | 0.038 / 0.0296 |
| no shortcut (**V2 ≡ U by construction**) | 578 | −7.232 / −0.1438 | −28.754 / −0.1461 |

For the 578 no-shortcut cases V2 reduces to ordinary uniform masking, so there is **no
treatment difference at all**. Yet the means differ by 21.5. The cause is that U and V2 draw
**different random masks from the same distribution**, under different seeds. The entire gap
is Monte Carlo variation amplified by the pathological tail.

### Required in a prospective successor, NOT applied to this ladder

Use **common random numbers**:

- if no shortcut set exists, the V2 mask must be **exactly** the U mask;
- if a shortcut set exists, start from the same U mask and deterministically swap in the
  targeted shortcut addresses while preserving total burden.

Then every untreated case cancels exactly and the comparison isolates only what targeted
masking changed. Paired per-target-fold effects should be reported alongside any aggregate.

## 3. Corrected reading of cap saturation

Level-1 shortcut-set size histogram: `{0: 578, 3: 1, 5: 3, 6: 3, 8: 15}` — 22 of 600
non-empty, 15 of those at the cap of 8.

An earlier reading of mine — that cap saturation indicates several diffuse real partners —
was **wrong and is withdrawn**. Under the frozen rule, hitting the cap means:

> the procedure could not achieve the required 50% reduction before exhausting its allowed
> targeted capacity.

That is a statement about the **procedure**, not evidence of diffuse biological dependence.

## 4. Two separate conclusions are possible at ladder close

1. **Scientific** — whether V2 finds enough reproducible shortcuts to justify targeted masking.
2. **Measurement** — whether the frozen qualification statistic is fit for purpose.

These are independent. A run can fail the second without settling the first. If Levels 2
and 3 reproduce the Level-1 pathology, the expected close is:

`V2_PRIMARY_QUALIFICATION_METRIC_NOT_INTERPRETABLE__NO_MASKING_AUTHORITY`

— neither "V2 failed" (the threshold was not meaningfully evaluable) nor "V2 passed" (a
large negative mean is not suppression). All distributional evidence is preserved.

## 5. Successor design requirements (prospective)

- common/identical random base masks for U and V2 wherever no treatment applies;
- a nonnegative or otherwise bounded/robust shortcut-strength estimand;
- paired target-fold effects as the unit of analysis;
- a preregistered robust aggregate chosen before execution.

## 6. What is NOT being done

No frozen threshold, metric, contract term or fold assignment is altered. Levels 2 and 3
complete untouched, and each will be reported with the same decomposition: aggregate,
median, distribution, shortcut-set size histogram, non-empty count, and the
treated-versus-untreated split.

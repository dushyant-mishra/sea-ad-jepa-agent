# V5 masking V2 — authoritative corrected ladder, close

Branch `authority/v5-masking-shortcut-predictability-v2-20260916`.
Run executed from `90707075` (all four defects repaired, reporting complete).
Contract `0c3e89cf` unchanged; cap clarification `UNION_WITH_SUPPORT_THEN_DETERMINISTIC_GLOBAL_CAP_V1`
frozen before any corrected result was read. Wall time **614.1 min**, read-only FULL104.
No training. No `D_shared`. No protected outcome.

## Disposition

### `V2_PRIMARY_QUALIFICATION_METRIC_NOT_INTERPRETABLE__NO_MASKING_AUTHORITY`

This is neither "V2 failed" nor "V2 passed". The frozen threshold was executed exactly as
specified and could not be meaningfully evaluated. All distributional evidence is preserved.

---

## 1. The frozen aggregate is unusable — proven, not asserted

| level | blocks/op | cells | donors | U mean | V1 mean | V2 mean | **frozen reduction** |
|---|---|---|---|---|---|---|---|
| 1 | 3 | 56,503 | 76 | −6.9649 | −2.0678 | −27.6982 | **+297.7%** |
| 2 | 8 | 140,733 | 93 | −1.6889 | −1.0077 | −1.3766 | **−18.5%** |
| 3 | 20 | 250,000 | 99 | −1.2693 | −1.7200 | −3.5744 | **+181.6%** |

The frozen aggregate swings **+298% → −18.5% → +182%**, flipping sign twice across adjacent
power levels, while the medians barely move:

| level | U median | V1 median | V2 median | worst value |
|---|---|---|---|---|
| 1 | −0.1304 | −0.1265 | −0.1198 | −15,256.45 |
| 2 | −0.0562 | −0.0529 | −0.0554 | −348.66 |
| 3 | −0.0397 | −0.0429 | −0.0439 | −1,525.86 |

### The untreated subset is the decisive proof

For target-folds with no shortcut set, V2 reduces to uniform masking — **the same procedure,
differing only by RNG seed**. The paired difference must be ~0.

| level | n untreated | **median** diff | **mean** diff |
|---|---|---|---|
| 1 | 578 | **+0.00023** | **−21.52** |
| 2 | 555 | **+0.00015** | **+0.34** |
| 3 | 574 | **−0.00007** | **−2.41** |

The median correctly returns ≈0 at every level, exactly as it must. The mean returns −21.5,
+0.34 and −2.41 for a null contrast. **The experiment is sound; the aggregate statistic is
not.** Partial R² is unbounded below, so a relative-reduction threshold on its mean is
dominated by whichever condition happened to draw the worse tail.

---

## 2. Scientific result, reported separately

Paired per-target-fold effect on the **treated** subset only (V2 − U; negative = V2 better):

| level | n | median diff | mean diff | **fraction V2 < U** |
|---|---|---|---|---|
| 1 | 22 | −0.00490 | −0.00429 | **0.636** |
| 2 | 45 | −0.00213 | −0.01170 | **0.689** |
| 3 | 26 | −0.00539 | −0.01311 | **0.731** |

Where a shortcut set is actually found, targeted co-masking helps **consistently and in the
right direction at every level**, and the fraction improved **rises monotonically with
power** (0.636 → 0.689 → 0.731).

But the effect is **tiny** — a median difference of ~0.005 against typical values of −0.04
to −0.13 — and **rare**: 22, 45 and 26 of 600 target-folds. Every level is below the frozen
`minimum_evaluated_targets: 50`, and the contract's `spectacular_small_n_rule` bars
qualifying on a handful regardless.

**This is a real but small directional signal that cannot qualify under the frozen terms,
and must not be promoted by switching metrics after the fact.**

---

## 3. Shortcut discovery and cap behaviour

| level | non-empty | histogram | mean size when non-empty | discovery ≥0.05 floor |
|---|---|---|---|---|
| 1 | 22/600 | {0:578, 3:1, 5:3, 6:3, 8:15} | 7.09 | 0.0367 |
| 2 | 45/600 | {0:555, 1:3, 2:5, 3:1, 4:1, 5:4, 6:1, 7:3, 8:27} | 6.29 | 0.0750 |
| 3 | 26/600 | {0:574, 3:1, 5:1, 6:1, 7:1, 8:22} | 7.58 | 0.0433 |

Discovery is **not monotone** in power (22 → 45 → 26), and the fraction clearing the floor
peaks at Level 2 (0.075) rather than at maximum power. Cap saturation dominates throughout
(mean set size 6.3–7.6 of a cap of 8), which under the corrected reading means **the
procedure could not reach its required 50% reduction before exhausting allowed capacity** —
a statement about the procedure, not about diffuse biological dependence.

---

## 4. Two independent conclusions

1. **Measurement.** The frozen primary statistic — the mean of an unbounded-below partial R²
   — is unfit for a relative-improvement threshold. Demonstrated by a null contrast
   returning −21.5.
2. **Scientific.** Targeted co-masking shows a small, consistent, correctly-signed benefit
   where shortcuts are found, strengthening with power, but on far too few targets and at
   far too small an effect to qualify. **Unresolved, not refuted.**

---

## 5. Successor requirements (prospective)

- **common random numbers**: identical masks where no treatment applies; a deterministic
  burden-preserving swap where it does, so untreated cases cancel exactly;
- a **nonnegative or otherwise bounded** shortcut-strength estimand;
- **paired per-target-fold effects** as the unit of analysis, not condition means;
- a **preregistered robust aggregate**;
- enough targets to clear the minimum-n rule, given only 4–8% clear the discovery floor.

## 6. Test accounting

| category | count |
|---|---|
| PASSED | 33 shortcut-predictability (incl. 4 defect regressions, cap suite, permutation, full-chain integration) · 61 masking-policy authority · 19 V1 estimator (byte-identical to V1 branch) · 4 masking authority V1 · 5 audit metrics |
| FAILED | 0 at HEAD |
| SKIPPED / DESELECTED | 0 / 0 |
| NOT ESTIMABLE | source/operator leakage probe, per-source heterogeneity — no policy qualified |
| NOT EXECUTED | native/non-common-core targets |
| HEAVY/DATA-DEPENDENT | three ladder levels executed read-only, 614.1 min |

**Status:** V1 valid negative evidence · V2 design viable · V2 implementation sound ·
V2 primary metric unfit · masking unresolved · **training off**.

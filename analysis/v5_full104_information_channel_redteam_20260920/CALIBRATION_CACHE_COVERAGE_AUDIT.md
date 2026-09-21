# Audit G — calibration-cache tail coverage

Date: 2026-09-20
Status: **characterization only. The cache was not rebuilt and its role is
unchanged.**

Produced by `scripts/audit_g_cache_coverage_20260920.py`.
Evidence: `evidence/audit_g/CALIBRATION_CACHE_COVERAGE_SUMMARY.json`,
`CALIBRATION_CACHE_COVERAGE_SUMMARY.csv`,
`CALIBRATION_CACHE_SOURCE_COMPOSITION.csv`.

```
cache_role = CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1
cache_role_unchanged_by_this_audit = true
cache_rebuilt = false
```

---

## 1. Question

Not "is the cache correct" — it is, and its current role stands. The question is:
**if it were later used for capacity calibration, would it have seen the
extremes the real population contains?**

A subset that silently concentrates in the middle would calibrate capacity
against a population that does not exist.

## 2. Scale

| | |
|---|---|
| population cells | 4,553,407 |
| cached cells | 105,553 |
| cached fraction | **2.318%** |
| donors | 104 |
| per-donor cap | 1,024 |
| donors at the cap | 103 |
| donors below the cap | 1 |
| retained per donor | 81 to 1,024 |
| per-donor retention rate | **0.588% to 100%** |

Tail thresholds were fixed at the 1st and 99th percentiles of the full
population **before** any comparison, so "the cache covers the tail" could not be
defined after seeing which tail it covers.

## 3. Finding G-1 — the cache is biased toward high-complexity cells

Core nonzero count per cell:

| statistic | full population | cache | direction |
|---|---|---|---|
| n | 4,553,407 | 105,553 | |
| **min** | **1** | **30** | cache never sees the sparsest cells |
| p01 | 438 | 638 | |
| p05 | 887 | 1,055 | |
| p25 | 1,840 | 2,057 | |
| **median** | **2,822** | **3,146** | +11.5% |
| p75 | 3,773 | 4,406 | |
| p95 | 5,020 | 6,597 | |
| p99 | 6,547 | 7,998 | |
| max | 11,181 | 11,022 | |
| **mean** | **2,870** | **3,372** | **+17.5%** |

Tail retention, against a 2.318% baseline:

| tail | cells in population | cells in cache | retention | vs baseline |
|---|---|---|---|---|
| low (≤ 438) | 45,655 | **403** | **0.883%** | **0.38×** |
| high (≥ 6,547) | 45,552 | **5,514** | **12.105%** | **5.22×** |

The low-complexity tail is retained at about **a third** of the baseline rate and
the high-complexity tail at **five times** it — a roughly **14-fold** relative
difference across the range. The cache's minimum of 30 against a population
minimum of 1 means the very sparsest cells are absent outright, not merely
under-sampled.

## 4. Finding G-2 — the per-donor cap reorganizes source composition

This is the larger effect.

| source | cells (population) | share | cells (cache) | share | retention rate |
|---|---|---|---|---|---|
| HVS | 198,718 | 4.36% | 41,984 | **39.78%** | **21.13%** |
| NPH52 | 236,476 | 5.19% | 16,465 | 15.60% | 6.96% |
| SEA_AD | 4,118,213 | **90.44%** | 47,104 | **44.63%** | **1.14%** |

SEA_AD falls from 90.4% of the population to 44.6% of the cache; HVS rises from
4.4% to 39.8%, a **9.1× over-representation**. Retention differs by **18.5×**
between HVS and SEA_AD.

This is an arithmetic consequence of a fixed per-donor cap over donors with very
unequal cell counts, and it is not an error: source-balanced scoring is the
intended estimand, and a per-donor cap is a deliberate balancing device. But it
means **the cache's marginal distributions are not the population's**, and that
has to be stated wherever the cache is used for anything other than
source-balanced control calibration.

G-1 and G-2 are not independent. Because sources differ in depth and complexity,
part of the complexity bias in §3 is the composition shift in §4 expressing
itself through the marginal.

## 5. Suitability

| use | suitable? | why |
|---|---|---|
| control calibration (current role) | **yes** | what it was built for; unchanged by this audit |
| source-balanced diagnostics | **yes** | the cap is what produces the balance |
| capacity calibration on population-representative marginals | **no** | HVS 9.1× over-represented, SEA_AD retained at 1.14% |
| calibrating behaviour in the low-complexity tail | **no** | 0.88% retention, and the sparsest cells are absent (min 30 vs 1) |

If the cache is later proposed for capacity calibration — which is where G3's
requirements point — this distributional mismatch must be addressed first, either
by re-weighting to population marginals with the weights declared in advance, or
by building a separate subset under a retention rule designed for that purpose.
**Neither is done here**, and choosing between them is a design decision that
belongs with G3, not with this audit.

## 6. Not measured

`source_library` depth quantiles and outside-ledger-fraction quantiles require
the Audit A per-cell artifact, which was still being produced when this ran.
They are reported

```
NOT_MEASURABLE — the Audit A per-cell artifact was not supplied;
                 this comparison was not performed
```

rather than quietly omitted, so a partial run cannot be mistaken for a complete
one. The script consumes that artifact via `--audit-a-cells` once available and
the comparison is then a rerun, not new code.

No pathology or protected label was introduced or read.

## 7. Status

```
G_CACHE_BIASED_TOWARD_HIGH_COMPLEXITY_CELLS            = NEW_FINDING
G_PER_DONOR_CAP_REORGANIZES_SOURCE_COMPOSITION         = NEW_FINDING
G_CACHE_SUITABLE_FOR_POPULATION_CAPACITY_CALIBRATION   = NO
G_CACHE_CURRENT_ROLE                                   = UNCHANGED
DEPTH_AND_OUTSIDE_LEDGER_COVERAGE                      = NOT_MEASURABLE (pending Audit A)
TRAINING_OFF
```

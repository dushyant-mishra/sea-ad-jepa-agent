# JEPA Macha/V77 — S149 weighting wording correction

Date: 2026-10-06
Parent observed before write: `b6b17ee189b19dee47746e343ab3685ab45ef2ed`
Working Macha head: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Status: `DOCUMENTATION_ONLY__S149_DIRECTION_UNCHANGED`

## Correction

Historical commit `fd21f649a7671dd345160e60079d0fac8d01418f` has the commit-title wording:

`the cache is donor-weighted`

That wording is too strong.

The committed receipt shows:

- calibration cache cells: HVS 3072, NPH52 246, SEA_AD 1408;
- cache donors: HVS 62, NPH52 19, SEA_AD 68;
- production FULL104 cells: HVS 198718, NPH52 236476, SEA_AD 4118213;
- production donors: HVS 41, NPH52 17, SEA_AD 46.

The cache's **cell composition happens to be much closer to donor proportions** than the full production cell composition. That is not the same thing as a donor-weighted statistical estimand.

The primary pooled S149 topology and its no-within-stratum null are computed across cells directly. Therefore they remain cell-weighted statistics.

Correct wording:

`THE_CALIBRATION_CACHE_CELL_MIX_IS_DONOR-LIKE_RELATIVE_TO_FULL104_CELL_MIX__THE_S149_STATISTIC_ITSELF_IS_NOT_DONOR-WEIGHTED`

## 3,292 clarification

The same historical validation contains:

- 3,292 **cells** from production donors;
- all 3,292 inferred coverage strata agreed with the study recorded by the production authority;
- no production donor in that subset was measured by more than one study.

Therefore any phrase such as `3,292 production-donor subset` should be read as `3,292 cells belonging to production donors`, not 3,292 donors.

## Biological meaning

This correction does not weaken the core S149 conclusion: pooled RNA topology is strongly entangled with study/measurement composition.

It does limit the numerical claim. The approximately 89% composition-null result is not yet a donor-population effect estimate.

## Authority unchanged

No selected estimand; no target winner; no representation winner; training OFF; Stage 4 closed; TEST sealed; Morabito protected.

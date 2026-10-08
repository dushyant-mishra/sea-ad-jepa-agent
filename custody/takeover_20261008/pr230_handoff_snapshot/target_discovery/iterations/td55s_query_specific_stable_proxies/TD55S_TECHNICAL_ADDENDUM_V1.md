# TD55S technical addendum v1

Status: PROSPECTIVE_TECHNICAL_BINDING__NO_OUTCOME_INSPECTED
Parent: `TD55S_PROSPECTIVE_SCREEN.md`

This addendum resolves execution details without changing the scientific hypothesis, proxy rule, K=16, train/test split, or gates.

## Separate family-specific ridge selection

Select one shared ridge multiplier for the shortcut family and one shared multiplier for the molecular family, each from `{1e-3,1e-2,1e-1,1,10}`.

For the molecular family, proxy selection is recomputed independently inside each inner-fit donor set before model fitting.

## Inner-fold query scoring

For each inner fold and model family:
- target SD and predictor standardization are computed from inner-fit donors only;
- a query contributes to that fold's validation MSE only if its target SD >1e-8;
- for the molecular family it must additionally have >=16 positive stable proxy scores in that inner-fit set;
- if fewer than 48 queries are measurable in any inner fold, TD55S is NOT_MEASURABLE and stops.

For each multiplier, average equal-donor validation MSE first across measurable queries within each fold, then equally across the two folds.
Tie-break multipliers by the same convention as TD48-TD52: round score to 12 decimals, then choose the larger multiplier on an exact rounded tie.

## Final model

After choosing multipliers, recompute final proxy identities from all pooled HVS+SEA_AD TRAIN donors. Final measurable queries require target SD>1e-8 and >=16 positive stable proxy scores. Require >=48/64.

Final shortcut and molecular comparisons use the exact same final measurable query set and the exact same TRAIN-derived target centering/scaling per query.

## Correlation numerical rule

Within each source and fit donor set, weighted residual correlation is NOT_MEASURABLE for a query/reference pair if either residual weighted variance <=1e-12. Otherwise use weighted Pearson correlation. Same-sign requires strict product `rho_HVS * rho_SEA_AD > 0`; zero or nonfinite correlations receive score 0.

No NPH52 outcome is inspected before this addendum is committed.
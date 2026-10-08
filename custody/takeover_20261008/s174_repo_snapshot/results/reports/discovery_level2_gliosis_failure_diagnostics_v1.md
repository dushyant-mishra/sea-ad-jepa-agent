# Level-2 Gliosis Failure Diagnostics v1

## Summary of why Level 2 failed

- Tier-1 genes diagnosed: 41
- Failed gliosis only: 40
- Other or multi-axis failures: 1
- Mean GFAP-positive donor fraction: 0.2804
- Mean Iba1-positive donor fraction: 0.3157
- Larger positive-fraction contributor: `Iba1`

## Failure-pattern counts

- `passes_non_gliosis_axes_fails_gliosis_only`: 40
- `fails_neuron_axis`: 1

## GFAP versus Iba1 contribution summary

Positive fractions are descriptive donor-level frequencies. The official gliosis penalty remains `max(GFAP_delta, 0) + max(Iba1_delta, 0)`.

- GFAP mean delta across gene-level donor means: -0.0170869
- Iba1 mean delta across gene-level donor means: -0.00916703

## Donor-outlier summary

- Genes where one donor contributes at least 50% of total positive gliosis penalty: 2
- Outlier-concentrated genes: BTBD9, CAMK2G
- Maximum top-donor contribution share across genes: 0.6221

## Sensitivity analysis summary

- Genes threshold-dependent between epsilon 0.001 and 0.01: 14
- Genes reaching >=0.80 gliosis stability at epsilon 0.001 / 0.005 / 0.01: 1 / 7 / 15
- Sensitivity results are labeled `sensitivity_only_not_evidence_promotion`.
- Official Level-2 statuses remain unchanged and not passed.

## Recommendation

Keep the official strict rule. Any future tolerance must be pre-registered and independently justified.

Do not change current evidence levels in this run. A future nonzero tolerance should be pre-registered before examining candidate outcomes and validated independently.

## Claim boundary

- Level-1 candidates remain model-implied and manifold-safe.
- Level-2 internal robustness is not established.
- No biological validation, causal mechanism, spatial support, or therapeutic efficacy is implied.

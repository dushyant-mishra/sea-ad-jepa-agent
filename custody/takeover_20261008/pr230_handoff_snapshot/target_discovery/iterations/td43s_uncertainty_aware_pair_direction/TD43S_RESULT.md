# TD43S result — uncertainty-aware pair-direction measurement reliability

Status: `TD43S_PAIR_DIRECTION_MEASUREMENT_RELIABILITY_SURVIVES__NO_TARGET_AUTHORITY`

Prospective freeze commit:
`26b7c4238b92049e50c398f635d9a196a622de81`

TD43 separates biological pair direction from measurement resolution:
- RESOLVED_POSITIVE
- RESOLVED_NEGATIVE
- UNRESOLVED_TIE

A half-depth tie is measurement uncertainty and is not scored as biological equality or reversal.

The frozen rule required both half-depth measurements to beat their donor/operator/depth/detection matched wrong-cell null for all four panels in all three sources: 24/24 half-panel tests.

All previously completed HVS and NPH52 half-panel tests passed. SEA_AD panels 0-2 also passed. The final missing SEA_AD panel-3 cases were independently reconstructed from raw counts and passed:

- half 1 coverage: 0.69655
- half 1 directional precision: 0.993284
- half 1 matched-null median: 0.892435
- half 1 matched-null p95: 0.893071
- PASS

- half 2 coverage: 0.69572
- half 2 directional precision: 0.993193
- half 2 matched-null median: 0.891935
- half 2 matched-null p95: 0.892569
- PASS

Therefore the frozen TD43 source/panel/half criterion is complete at 24/24 PASS.

This establishes only measurement reliability conditional on resolution. It does NOT establish complementary-evidence identifiability, donor-generalizable trainability, target authority, production pair selection/weighting, or JEPA training authorization.

The next gate must score cell-specific information as excess over pair-specific prior/matched-null performance; raw pair-order accuracy is not a valid qualification metric.

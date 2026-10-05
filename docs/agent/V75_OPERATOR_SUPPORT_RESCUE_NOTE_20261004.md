# V75 operator-support rescue

Purpose: restore the V73 stress-twin zero-quota operator-support rescue that was lost in V74 calibration closure, without changing calibrated observation semantics.

TDD sequence:
1. RED: require the 2,000-cell smoke population to retain all 42 authenticated observation operators with minimum operator count >= 1.
2. GREEN: make the smallest change in `scripts/v64/v73_full104_population_geometry.py` needed to satisfy that invariant.
3. Regression: verify 10K, 100K, 500K and exact FULL104 behavior, plus the existing V74 RNA-QC consumption/calibration lane.

No training authority is created by this repair.

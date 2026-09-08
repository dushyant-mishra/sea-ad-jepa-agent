# TD41S result — tie-aware pair-order geometry

Status: `TD41S_PAIR_ORDER_GEOMETRY_SURVIVES__NO_TARGET_AUTHORITY`

Prospective freeze commit:
`a1bfebf3ecbc55d9594058f182202e5a90a882ff`

The candidate was fully defined before label validation. No pair was selected from labels or outcomes.

## Primary GLUT results

| panel | RAW r | RAW null p95 | residual r | residual null p95 |
|---:|---:|---:|---:|---:|
|0|0.795418|0.446724|0.863849|0.608323|
|1|0.798383|0.462715|0.877319|0.585901|
|2|0.823760|0.481623|0.914965|0.607673|
|3|0.809855|0.479237|0.830679|0.555986|

RAW_PAIR_ORDER: 4/4 pass.
STATE_DEPTH_DET_RESID_PAIR_ORDER: 4/4 pass.

Median RAW GLUT r: ~0.8041.
Median residualized GLUT r: ~0.8706.

## Secondary observations

Residualized GABA graph r:
- panel0 0.862360
- panel1 0.881486
- panel2 0.854327
- panel3 0.818650

All exceed their own permutation null p95.

All19 residualized pair-order geometry is also positive and above null in every panel (~0.635-0.705).

## Interpretation

The fixed tie-aware within-cell pair-order representation reproduces the corrected TD34 state-relational scaffold across HVS and SEA_AD while:
- using exact Molecular Ledger gene identity correspondence;
- requiring no learned cross-source axes/loadings;
- requiring no state matching during construction;
- requiring no clustering or graph alignment;
- using no same-gene cross-cell dependency geometry;
- preserving measured-zero ties explicitly.

This is validation evidence only. It does not yet establish per-cell measurement reliability, donor recurrence, complementary-evidence identifiability, or full-reader authority.

Next required gate: label-free count-split measurement reliability and donor-block recurrence.

# JEPA Target Discovery — G6/G7 corrected-value prefreeze

Date: 2026-10-07
Status: `PREFROZEN_CHECKS_ONLY__NO_REAL_VALUE_READ_OR_MATERIALIZATION_AUTHORITY`

## Purpose
Define the first value-level checks that would follow a PASS of the value-blind G4/G5 mapping preflight. This document does **not** authorize opening count arrays.

## Historical TD50 sentinel authority
The preserved TD50 source artifacts are hash-bound historical records:

- HVS `td50_HVS.npz` SHA-256 `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`, 1,129 rows
- NPH52 `td50_NPH52.npz` SHA-256 `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`, 1,310 rows
- SEA-AD `td50_SEA_AD.npz` SHA-256 `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`, 22,561 rows

Historical `source_library` array byte hashes:
- HVS `3ec61d2e884a87a2d4a6f22088ea7605ffc6b6e1b52885a2c702b0801d634699`
- NPH52 `1ac67a825490efb55641eec00cc7f7a21221a69644192a7a37e9e7322c7dc689`
- SEA-AD `c66ce152b63afac28026e78a105c0af1861fa8dc2d78e44439efb7b50afac42d`

Historical `detected` array byte hashes, retained for diagnostics only:
- HVS `6e89b003367f91f101fe10947d2781911a1c12b17169564809fd03cc65a98d13`
- NPH52 `2ef463f7ad67fff578402b4016ad1f99129e1a0ef5de21d24bd98dabc2de5f1a`
- SEA-AD `370d81f2e6649ad55c63b395ec809607739fa70a0585c8bebca467b7b5a5d355`

## Important correction: historical `detected` is not an invariant gate
The original `compute_td50_source.py` defined:

`detected_genes = indptr[global_row + 1] - indptr[global_row]`

on the historical 50K canonical CSR matrix.

Therefore `detected` is the nnz count **after the historical feature mapping/materialization**. The corrected SEA-AD identifier join preserves the frozen collision policy but can exclude a different physical set than the defective positional mapping. Corrected per-cell nnz can therefore legitimately differ.

Consequences:
- exact `detected` equality is **not** a G6 PASS criterion;
- historical and corrected detected/nnz counts must be reported side by side as a diagnostic;
- a detected-count difference must not be used to alter the frozen gene panel, collision policy, or cell set.

## G6 — exact whole-cell raw library-total gate
For every one of the exact 25,000 Sample-A cells:

1. resolve the exact raw matrix row already authenticated by G5;
2. sum **every raw count in the physical row before address filtering/collision exclusion**;
3. require exact integer equality to the preserved TD50 `source_library` value for that same frozen row;
4. no tolerance, rescaling, or repaired-library estimate is permitted.

This is appropriate because feature permutation/remapping does not change the total raw molecule count.

Terminal:
- PASS only if all 25,000 rows agree exactly;
- otherwise `STOP_TD_G6_SOURCE_LIBRARY_MISMATCH`.

Normalization after G6, if separately authorized, remains exactly:

`log1p(raw_count * 10000 / source_library)`

where `source_library` is the verified whole-cell raw total, never the sum of the 9,216 replay genes.

## G7 — cross-lane S174 corroboration
Use the **final G1b authority**, not the earlier failed frozen G1 result.

Binding authority:
- branch `claude/s174-train-cache-rebuild-20261007`
- commit `4ab8e2101f2e595d9a97df05517d6e672768ecec`
- result `results/v77/S174_REBUILD_G1B_RESULT_V1.json`
- G1b freeze SHA-256 recorded inside that result: `0513421e45865f290bddf8b0be56d64c7d9c5297bf0150ea6b9df286514b5f8f`
- recorded result: `G1b_pass = true`, zero unexplained discrepancies; rebuilt cache authorized for the planned V77 replays.

Prospective TD cross-check rule:
1. determine the **natural cell-ID intersection** between Sample-A and the already-frozen S174 cache cells; do not select or add cells after seeing values;
2. for every naturally overlapping HVS/SEA-AD cell and every frozen replay address that is present in the S174 checked entry set, require exact integer raw-count equality between the new TD physical-ID read and the S174 G1b-authorized value;
3. use every available overlap; do not subsample based on outcomes;
4. tolerance is exactly zero for integer raw counts;
5. no replacement address/cell is allowed.

If natural overlap exists, any mismatch is terminal:
`STOP_TD_G7_S174_CROSSCHECK_MISMATCH`.

If the natural cell intersection is empty, record:
`NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`.

Zero natural overlap is not permission to manufacture an overlap. In that case G1b remains cross-lane implementation/source authority but there is no cell-level TD corroboration.

## 353 historical-ID / current-symbol identity flags
Macha's S174 lane records 353 mappings in which the frozen historical Ensembl-ID identity maps to a different current symbol. Those mappings remain frozen and are not tuned.

Before biological interpretation of corrected TD replay results:
- intersect the exact 9,216 replay addresses with the 353 identity-flag set when that identity-lane artifact is available;
- carry a semantic-warning flag for any overlap;
- do not change address identity or substitute a gene based on symbol preference.

This identity warning is separate from the physical mapping gate. Stable molecular address/Ensembl identity remains binding for replay.

## Boundary
This prefreeze does not authorize:
- reading real count arrays;
- writing `data/cache/td_relational_corrected_sampleA_9216_v1`;
- replaying TD56-TD59;
- Stage-A target selection;
- TD60;
- training or EMA updates;
- TEST, DEV/SEALED, pathology, Morabito, or external biology.

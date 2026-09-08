# TD59 replay-closure repair — independent successor implementation

Status: `PASS_TD59_REPLAY_CLOSURE_BY_INDEPENDENT_RECONSTRUCTION__ORIGINAL_EXECUTOR_BYTES_NOT_RECOVERED`
Date: 2026-09-08

## Why this repair exists

The frozen TD59 result binds the original local executor SHA-256:

`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`

but the exact executor bytes and six original result JSON bytes were not preserved in the current GitHub TD59 directory, and the uploaded historical working archive ends at TD58. A hash without bytes is insufficient for future executable replay.

This repair does **not** claim recovery of those missing original bytes. Instead it independently reconstructs the executor from:

- the prospectively frozen TD59 contract at commit `864651fbe56b973f6645866624513e827c2c54da`;
- the frozen pre-outcome binding at `f3eb86d26a306fe99ae2848dca89e9f2e9e25207`;
- the preserved TD57C predecessor mechanics;
- the immutable 50k expression-member arrays and calibration support.

## Successor replay executor

`td59_replay_closure_executor_v1.py`

SHA-256:
`870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`

This is a **successor replay implementation**, not the missing original executor.

## Input re-verification

The reconstructed immutable expression archive reproduced:

- outer ZIP SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- `data.npy` `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`;
- `indices.npy` `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`;
- `indptr.npy` `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`;
- `shape.npy` `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`;
- observation-state support `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`.

The three preserved source metadata NPZs retain their frozen TD57 hashes and detected-gene counts equal the sparse-row nonzero support exactly.

## Scientific-statistic replay result

The reconstructed implementation reran both panels in HVS, NPH52, and SEA_AD.

**All 24/24 committed case rows match exactly** for all three decision-bearing values:

- observed median donor local-triplet agreement;
- matched-null p95;
- matched-null maximum.

All 24 PASS booleans therefore reproduce exactly.

The reconstructed implementation also reproduces all six frozen TD59 pair-address SHA-256 values and the structural/measurable donor counts:

- HVS: 29/29;
- NPH52: 16/16;
- SEA_AD: 46/46.

Exact row-level equality is recorded in `TD59_REPLAY_CLOSURE_CASE_MATCH.csv`.

## Boundary of the repair

This closes the **scientific-statistic replay** gap, but not byte provenance of the missing original local files. Therefore:

- do not replace the historical original executor SHA with the successor executor SHA;
- do not claim the reconstructed JSONs have the original first-run JSON hashes;
- preserve the original result terminal and original hashes as historical bindings;
- use this successor implementation for future reproducible reconstruction of the frozen TD59 statistic.

The TD59 scientific terminal remains unchanged because its complete 24-case statistic is independently reproduced from immutable inputs and the prospective contract.

No training or production locality is authorized.

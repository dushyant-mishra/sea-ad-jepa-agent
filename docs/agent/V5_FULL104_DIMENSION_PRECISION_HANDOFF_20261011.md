# V5 FULL104 Dimension Precision — Canonical Handoff

Date: 2026-10-11

Implementation: PR #270.
Independent audit: PR #273.

## Closed prospectively

- Monte Carlo replicate counts are derived from an explicit familywise precision budget; historical replicate constants are not authority.
- Future returned FULL104 dimension-metric rows must be cryptographically bound to the exact physical FULL104 byte-closure receipt and the exact precision-authority receipt.
- Metric rows must be full-stream, non-fixture, non-synthetic, use full-refit matched nulls, and include held-donor and held-operator mechanics.
- Rank sweeps must be consecutive from rank 1 and use the exact prospectively derived replicate count.
- The metric-receipt validator cannot select a dimension or authorize training.
- The frozen downstream D_shared/D_private/D_obs selector already exists and remains separate.

Fresh implementation verification:
- GitHub Actions run `38149052609` — SUCCESS.

## What remains physical

The project-mounted files contain the authentic 50K auxiliary expression archive and calibration metadata, but **not** the >30 GB / 8,915-block FULL104 expression store. Therefore the following cannot be honestly completed in this environment:

1. current-byte physical FULL104 closure on 4,553,407 cells / 104 donors / 42 operators / 8,915 blocks / 41,238 addresses;
2. actual real full-stream dimension metric computation;
3. authenticated return of those metric rows;
4. numerical D_shared/D_private/D_obs selection and independent outcome audit.

The exact physical binder remains the existing `bind_full104_expression_blocks_v4.py` workflow; after its PASS, compute metrics under PR #270's precision authority, validate the compact returned receipt, then apply the frozen dimension-family selector.

## Terminal

`FULL104_STATISTICAL_AND_RETURN_RECEIPT_ENGINEERING_CLOSED__PHYSICAL_FULL_STREAM_EXECUTION_PENDING__D_SHARED_D_PRIVATE_D_OBS_UNSET__TRAINING_OFF`

`training_authorized=false`

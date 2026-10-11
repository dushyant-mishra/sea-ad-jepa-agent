# Target-discovery G6/G7 design update — 2026-10-10

Status: `DESIGN_UPDATED__NO_EXECUTION_AUTHORITY`

The standalone G6/G7 V2 design on PR #251 has been amended to bind only the repaired PR #255 V3 G4/G5 receipt contract.

Controlling audit documents:
- `docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-design.md` (historical base design)
- `docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-v3-preflight-amendment.md` (controlling amendment)
- `docs/superpowers/plans/2026-10-10-td-g6-g7-standalone-v2-v3-preflight.md` (implementation plan)

Future standalone V2 must reject old V1/V2 preflight receipts and accept only:
- `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3`;
- `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`;
- frozen `A_NATURAL_MIXTURE` 25,000-cell Sample A;
- exact 34/34 Sample-A H5 mapping/cell geometry;
- exact 35/35 S174 source-byte custody;
- all #255 required value-blind checks true.

The implementation may be prepared while #255 is being qualified, but remains unqualified and non-executable. No runtime value authorization exists. Even a future G6+G7 PASS stops before corrected TD biological replay.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

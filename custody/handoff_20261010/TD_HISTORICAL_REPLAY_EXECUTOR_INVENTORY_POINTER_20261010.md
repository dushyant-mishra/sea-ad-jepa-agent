# Historical corrected-replay executor inventory pointer

Date: 2026-10-10

Current audit authority:
`review/td-g6g7-preauthorization-hardening-20261009/custody/target_discovery/TD_HISTORICAL_REPLAY_EXECUTOR_INVENTORY_STATUS_20261010.json`

Status:
`PARTIAL_INVENTORY_COMPLETE__EXECUTOR_RECOVERY_REQUIRED_BEFORE_ADAPTER_IMPLEMENTATION`

Key custody ruling:
- TD57B exact executor/wrapper code is recoverable and hash-bound in historical repository state.
- TD56, TD57C and TD59 iteration roots preserve decision-bearing freezes/results/bindings, but a complete exact executor lineage still must be recovered from repository/archive/execution history before any corrected-replay adapter is implemented.
- Never reconstruct a decision-bearing historical executor from prose when exact code or an execution binding is recoverable.
- TD57C adapter qualification must reproduce the historical prospective FAIL before corrected data are touched.

This is inventory/custody only. It does not authorize adapter execution, corrected replay, target selection, TD60 or training.

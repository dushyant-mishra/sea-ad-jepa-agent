# T0 real B2 acceptance checklist — 2026-09-09

This checklist is deliberately strict. It prevents a preflight, a spot check, or a synthetic fixture run from being mistaken for population authority closure.

## A. Pre-run requirements

- [ ] Runner is committed under `scripts/v4/`.
- [ ] Replay verifier is committed under `scripts/v4/`.
- [ ] Expected source H5AD SHA is passed explicitly.
- [ ] Expected source byte count is passed explicitly.
- [ ] Expected logical root is passed explicitly.
- [ ] Expected row count `20804` is passed explicitly.
- [ ] Output directory is outside temp scratchpad and is empty before run.
- [ ] Permitted obs fields are limited to cell identity and donor ID.

## B. Raw-source population run requirements

- [ ] H5AD source is opened through the production path.
- [ ] Same file object is hashed and consumed by HDF5.
- [ ] Rows attempted = `20804`.
- [ ] Rows proven = `20804`.
- [ ] Skipped rows = `0`.
- [ ] Duplicate logical indices = `0`.
- [ ] Cell mismatches = `0`.
- [ ] Donor mismatches = `0`.
- [ ] Expression-row mismatches = `0`.
- [ ] Source-library mismatches = `0`.
- [ ] Population raw-source root emitted.
- [ ] Every emitted file has byte count and SHA-256.

## C. Replay requirements

- [ ] Replay reads emitted disk artifacts, not the in-memory object from the run.
- [ ] Stored population root recomputes from proof rows.
- [ ] Stored root == recomputed root == externally expected root.
- [ ] Package root recomputes from emitted files.
- [ ] Every proof row matches logical authority row identity.
- [ ] Source SHA matches expected.
- [ ] Source byte count matches expected.
- [ ] Row count matches `20804`.
- [ ] No pathology fields are present in artifacts.
- [ ] `real_execution_ready` remains false.

## D. Technical completeness requirements after raw-source replay

- [ ] Technical completeness consumes the replayed raw-source population authority.
- [ ] B2 closure root is externally bound.
- [ ] Physical read plan root is externally bound.
- [ ] B1 projection root is externally bound.
- [ ] Projection contains exactly `35076` unique positions.
- [ ] Every counts payload digest matches the logical row's bound digest.
- [ ] Every consumed block rows/nnz match closure geometry.
- [ ] Q_DEPTH derives from proven raw-source libraries.
- [ ] Q_DETECT derives from 35,076-position projection nonzero counts.
- [ ] Technical-completeness package root replays.

## E. Downstream hold

- [ ] No eligible donor construction.
- [ ] No numeric AT8 confirmation access.
- [ ] Donor role gate remains shut.
- [ ] Teacher/student productionization remains design-only until T0 authorities replay.

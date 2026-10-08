# FULL104 V014 Phase-0 preflight

Date: 2026-08-26

Status: **STOP_PROVENANCE_CONTRACT_NAME_MISMATCH**

## Verified

- Source ZIP: `C:/Users/dushy/Downloads/JEPA_CODEX_ADAPTIVE_HANDOFF_V014_20260826.zip`
- ZIP SHA-256: `cd880219bbefcc91950bd6c1d48567a9a26d0b584d82ab63ab73f1dd3d059d5b`
- `SHA256_MANIFEST_V014.csv`: 92 of 92 listed files match both byte length and SHA-256.
- Included contract read completely: `prior_v013/full104/FULL104_ADAPTIVE_CALIBRATION_CONTRACT_V1.md`
- Included contract SHA-256: `83f7a1912c857d14d20fbe6d1ebeefbf8e2b6b0786e82c2f0536a44a2442231b`
- Included donor split SHA-256 matches the current repository authority exactly: `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`.
- The included contract preserves the canonical three observation states and measured-zero semantics.

## Stop condition

The controlling user instruction names `JEPA_FULL_DATASET_ADAPTIVE_CALIBRATION_CONTRACT_V1.md`. No file with that name exists in the ZIP, and no manifest, README, or contract declares it to be an alias of `FULL104_ADAPTIVE_CALIBRATION_CONTRACT_V1.md`.

The included FULL104 contract is internally coherent and authenticated, but silently treating a differently named contract as the requested controlling document would violate the explicit fail-closed provenance requirement.

## Actions not performed

- No environment-discovery script was executed beyond package/repository read-only inspection.
- No 104-fit dataset-dependent value was derived.
- No expression was opened for reader-fit, reader-validation, reader-oracle, DEV, or SEALED donors.
- No checkpoints were loaded and no optimizer or EMA updates occurred.
- No Phase 1 or later action was started.

## Required resolution

Provide the named contract, or explicitly confirm in writing that the authenticated
`prior_v013/full104/FULL104_ADAPTIVE_CALIBRATION_CONTRACT_V1.md` at SHA-256
`83f7a1912c857d14d20fbe6d1ebeefbf8e2b6b0786e82c2f0536a44a2442231b`
is the intended controlling contract.

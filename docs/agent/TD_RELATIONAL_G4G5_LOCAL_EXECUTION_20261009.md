# TD relational corrected-replay preflight: local execution (2026-10-09)

**Terminal:** `FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

**G4/G5:** not executed. The driver stopped at its manifest file-hash check, before the mapping audit started.

Failure preserved exactly. No code change, no rerun, no file normalization, no value read. Stopped as instructed. The machine-readable record is `docs/agent/TD_RELATIONAL_G4G5_LOCAL_EXECUTION_20261009.json`.

## What ran

- **Code:** PR #243 head `a6c57e4e92b23756f5c49183eaa15d55f39cc325`, run from a separate clean worktree on branch `exec/td-relational-g4g5-local-20261009`.
- **Command:** `python scripts/v5/run_td_relational_replay_preflight.py`, run from the worktree root.
- **Environment:** canonical local Windows workstation, Python 3.9.7 (Anaconda), numpy 1.24.2, pandas 1.5.3, h5py 3.2.1.
- **Run time:** 2026-10-09, ending 22:00:49Z, exit code 1.
- **Executor blobs:**

| file | git blob |
|---|---|
| driver | `4f0a18f3` |
| manifest builder | `03dc4949` |
| mapping audit | `ed2d6274` |

  Full SHA-256 values are in the JSON record.
- **PR #243's own preflight tests,** run locally before execution: 8 passed, 1 skipped. The skipped test is the external-authority manifest rebuild, which needs environment variables; the driver performs the same rebuild.

## Inputs (all verified before the run)

| input | bytes | SHA-256 | status |
|---|---|---|---|
| `exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` | 14,700,106 | `79eb005c…` | matches frozen |
| `results/v4/stage81a2r_…_provenance_candidate.csv.gz` | 5,764,358 | `df0cb60f…` | matches frozen |
| `D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_…_collision_ledger.csv.gz` | 1,101,503 | `f6909f81…` | matches frozen |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5b…` | matches authority |
| `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip` | 92,478,083 | `c84849f5…` | matches authority |
| 35 HVS/SEA-AD H5ADs named by the S174 freeze | 323,643,986,614 in total | all 35 re-hashed | match the freeze in bytes and SHA-256 |

The S174 freeze resolved through the local branch ref to the frozen `240b2b71…`.

The two archives were not at the canonical project-root paths the driver reads. Each was copied byte for byte from where it was found on this machine and SHA-verified after copying:
- the calibration bundle from `D:/jepa_v5_outputs_20260925/calib_reassembled/`;
- the TD archive from `C:/Users/dushy/Downloads/`.

A different file with the same name, `D:/Jepa project/exports/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` (1,093,202,356 bytes), is not the authority and was not used.

## Why it failed

- **The content is right.** The manifest builder finished `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`: 9,216 addresses, all 31 internal checks true. The hash it computed in memory is exactly the frozen `4bde5f80…`.
- **The file on disk is not.** The builder writes the file with `Path.write_text`, which on Windows turns each newline into CRLF. All 9,217 line endings became CRLF, so the file on disk hashes to `923475ae…`.
- **The driver fails closed on that.** It re-hashes the file on disk. With LF endings restored, the bytes hash exactly to `4bde5f80…`.

So the 9,216-address content is the frozen content. The defect is platform-dependent serialization in the frozen code, not a scientific mismatch.

The generated files are committed unmodified in the frozen namespace `results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1/`:
- the CRLF manifest, exactly as written;
- the builder receipt;
- the extracted S174 freeze.

No `PREFLIGHT_RESULT.json` was written.

**Warning:** the driver's freshness guard checks only `PREFLIGHT_RESULT.json`. A rerun into this namespace would silently overwrite these files.

## No value read

No expression arrays were opened. The builder read only:
- `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` and `FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv` (support and identity metadata) from the calibration bundle;
- `td57b_p0_hvs.json`, `td57b_p1_hvs.json` and `td57c_p0_hvs.json` (address views) from the TD archive.

The mapping audit, which would read only H5AD `var`/`obs`, never started.

## Options for the target-discovery lane (not taken here)

1. Fix the frozen builder to write the manifest with explicit LF, for example `open(path, "w", newline="\n")` or `write_bytes`. Review it, then rerun into a fresh or explicitly superseding namespace.
2. Or approve running the unchanged frozen code on Linux/WSL, where text mode writes LF, and record the environment change.

In either case, do not edit the CRLF file to make the hash pass.

## Boundaries

G6/G7 are not executed and not authorized, and no runtime authorization artifact was created.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

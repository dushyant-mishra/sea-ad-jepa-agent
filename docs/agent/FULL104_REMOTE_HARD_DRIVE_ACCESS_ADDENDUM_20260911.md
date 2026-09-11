# FULL104 Remote Hard-Drive Access Addendum

Date: 2026-09-11
Status: `FULL104_DATA_NOT_UPLOADABLE_HERE__CLAUDE_GPU_LAPTOP_ACCESS_REQUIRED__NO_TRAINING_AUTHORITY`

## Purpose

This addendum records an operational boundary for the next Claude/Codex worker.

The full FULL104 / Phase2 production expression substrate is too large to be made available inside the ChatGPT environment. It is reported to be more than 30 GB and is accessible to Claude on the user's separate GPU-enabled laptop through the attached hard drive.

Do not ask the user to upload the full dataset here. Do not treat absence of the full data in `/mnt/data` as evidence that the substrate does not exist.

## Current environment boundary

The ChatGPT environment can handle:

- small and medium handoff artifacts;
- corrected TRAIN-cache ZIPs;
- split discovery-expression archives that fit this environment;
- hash manifests, receipts, and metadata summaries;
- GitHub governance/handoff files.

The ChatGPT environment should not be used to host or fully materialize the >30GB FULL104 production expression substrate.

## Correct task framing for Claude

The FULL104/B2 task is not "find or upload the dataset from scratch."

The correct task is receipt/verifier closure on the GPU laptop / hard-drive environment:

1. Locate the existing FULL104 / Phase2 production expression substrate on the attached hard drive.
2. Locate any already-produced terminal receipt for the closure marker:
   - `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`
3. If a receipt exists, audit and report:
   - 4,553,407 reader-fit cells;
   - 104 donors;
   - 42 operators / matrices;
   - 41,238 molecular addresses;
   - 8,915 Level-4 blocks;
   - historical manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`;
   - block-local/source coordinates;
   - row/cell identity closure;
   - donor identity closure;
   - anti-splice provenance.
4. If no receipt exists, run the already-built FULL104/B2 verifier against the hard-drive substrate and return only the receipt, manifest, hashes, counts, and failure/pass status.

## Negative controls

The following are useful but do not satisfy FULL104/B2 closure:

- `stage81a3r_corrected_real_train.zip`;
- corrected TRAIN-cache shard pairs;
- 4,726-row TRAIN cache;
- 50K subset;
- synthetic fixture;
- validation/oracle source;
- DEV/SEALED source;
- different-byte substitute.

The corrected TRAIN cache remains useful for loader/mechanics and anti-cheat smoke tests only.

## Prohibitions

This addendum does not authorize:

- S0-S4 production execution;
- AT8 opening;
- protected partition opening;
- `reader_validation` opening;
- oracle opening;
- T0 V21 freeze claim;
- V5 production training;
- optimizer steps or training checkpoints;
- pathology-guided tuning.

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## Terminal classification

`FULL104_REMOTE_HARD_DRIVE_ACCESS_REQUIRED_FOR_RECEIPT_OR_VERIFIER_RUN`

The next Claude worker should use the GPU laptop/hard-drive environment for FULL104/B2 receipt closure while using this GitHub branch for the T0 v2/V21-T1 repaired-candidate verification work order.

Training remains OFF.

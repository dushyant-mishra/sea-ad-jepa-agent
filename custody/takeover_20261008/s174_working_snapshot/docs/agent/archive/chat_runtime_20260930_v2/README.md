# Chat-runtime exclusive asset custody — 2026-09-30 V2

This directory preserves artifacts that were available **only in this chat runtime** and were not already repository files.

## What is physically in Git

The small text artifacts are copied into this directory. Their original chat-upload SHA-256 values are recorded in `CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V2.json`.

## What is not physically in Git

The GitHub write connector available to this chat can write UTF-8 text but cannot attach arbitrary local binary files. Therefore the large ZIP/NPZ/XLSX files are **not falsely claimed to be committed**.

For every such file the manifest records:

- exact filename;
- byte count;
- SHA-256;
- known provenance;
- internal structure where inspected;
- public recovery URL or reconstruction route where available;
- whether the artifact is current authority, historical, or superseded.

A future agent must check `bytes_in_git` before assuming a filename means the binary exists in the repository.

## Important chat-only binaries

### Dong/Roussos Supplementary Data 8 and 10

The user manually supplied the two XLSX files that automated Spring Nature requests returned as a JavaScript client-challenge page.

Exact hashes:

- Data 8 / MOESM10: `eb3c2e0eaf055bac3954802497cbdd07ccc65638ae361e1cf9af10668f224a74`
- Data 10 / MOESM12: `c2005fb8947b4352450a9a86f297673cce5350aab1b2ac69fe3949317c4f1f59`

Their validated scientific structure and GENCODE bridge are recorded in:

`results/v64/V64_DONG_ROUSSOS_PROMOTER_RESOURCE_CUSTODY_AND_BRIDGE_AUDIT_V1.json`

Do not substitute a 3,038-byte client-challenge response for either workbook.

### FULL104 discovery subset

The exact `full104_discovery_subset.npz` became physically available in this runtime and matched Claude's expected SHA-256:

`615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`

It contains 6,000 cells and a 17,186-address backbone. **Address is not asserted to be gene.**

### Foundation discovery expression split archive

The two uploaded parts concatenate byte-for-byte to the reconstructed ZIP:

```bash
cat FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001 \
    FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002 \
  > FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip
```

Verified reconstructed SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

## Superseded chat-generated artifacts

The partial promoter ledger receipt and raw promoter structural summary are preserved only for custody/history. They were generated before later corrections, including chromosome-aware handling of repeated Dong ENST IDs. Use the current V64 bridge/ledger artifacts instead.

## Governance

This custody package changes no scientific gate.

- TRAINING = OFF
- Phase B = STOPPED
- Stage 4 = NOT AUTHORIZED
- Morabito = PROTECTED

# JEPA provenance mirror

This directory records how decision-bearing artifacts connect to the public source datasets, local canonical working tree, frozen hashes, and reproducible reconstruction steps.

## What GitHub should store

Prefer small, durable provenance objects:

- source dataset identifiers and download references;
- exact file/object hashes;
- donor/operator/population manifests;
- split/firewall authorities;
- adapter/reader provenance;
- reconstruction commands or deterministic procedures;
- mappings from large local artifacts to their exact hashes;
- manifests binding review packets and conclusion-bearing source.

## Large/public data policy

The project uses publicly available source data. Public donor-level material may be mirrored when it materially improves reproducibility or auditability.

GitHub should nevertheless avoid unnecessary duplication of very large artifacts. Raw matrices, caches, model checkpoints, and regenerable intermediates should normally remain local when exact source identity + hash + deterministic reconstruction is sufficient.

Large data is included when at least one of these is true:

1. the exact bytes are required to reproduce a scientific conclusion and cannot be deterministically reconstructed;
2. the artifact is a compact frozen authority despite containing donor-level records;
3. remote preservation materially improves disaster recovery of a unique authoritative artifact.

## Exclusions

Never commit secrets, credentials, access tokens, private keys, or machine-specific authentication material.

## Chronology

Recovered historical bytes must be labelled with the recovery chronology class and linked to `docs/history/JEPA_HISTORICAL_LEDGER.md`. Git backfill date is not historical scientific proof.

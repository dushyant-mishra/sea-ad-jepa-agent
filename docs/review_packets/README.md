# Review packets

This directory is for **compact, decision-bearing review packages** that support independent audit of a JEPA gate.

## Include

A review packet should contain only the pieces needed to reproduce or challenge the gate:

- prospective contract;
- conclusion-bearing source snapshot;
- exact input/output manifest;
- schemas and compact CSV/JSON summaries;
- terminal status/report;
- independent validator/review;
- exact SHA-256 bindings.

## Exclude by default

Do not archive:

- pytest-generated output trees;
- `_staging` directories;
- caches or repeated extraction copies;
- temporary tensors;
- redundant raw data copies;
- repeated identical manifests from multiple test runs;
- failed/retry copies unless the failure itself is historically decision-bearing.

## Path convention

Use stage-specific paths so distinct historical versions cannot collide:

`docs/review_packets/<stage-family>/<gate-or-version>/...`

Examples:

- `docs/review_packets/contextual_teacher/f0/...`
- `docs/review_packets/f1/query_design_v2/...`
- `docs/review_packets/f1/hc3_15b/...`
- `docs/review_packets/f1/hc3_15c/...`

If two files have different hashes, they must never be flattened onto one destination path merely because their basenames match.

## Review status

Each packet should state one of:

- `AWAITING_EXTERNAL_REVIEW`
- `PASS_EXTERNAL_REVIEW`
- `STOP_EXTERNAL_REVIEW`
- `SUPERSEDED_AFTER_REPAIR`

Review prose is useful, but structured/hash-bound status is preferred for conclusion-bearing promotion.

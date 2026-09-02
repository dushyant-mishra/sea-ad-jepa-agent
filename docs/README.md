# JEPA repository documentation map

This repository is organized as a **reproducibility and provenance mirror**, not a raw-data dump.

## Where to look first

- [`agent/ACTIVE_STATE.md`](agent/ACTIVE_STATE.md) — current scientific/execution state and next legal gate.
- [`authority/`](authority/) — current frozen contracts, decision authorities, and immutable scientific definitions.
- [`history/JEPA_HISTORICAL_LEDGER.md`](history/JEPA_HISTORICAL_LEDGER.md) — chronological recovery ledger, including superseded and closed branches.
- [`review_packets/`](review_packets/) — compact gate-review packages and external-review records.
- [`../provenance/`](../provenance/) — data/source/hash/reconstruction provenance and large-artifact policy.
- [`../scripts/v4/`](../scripts/v4/) — current conclusion-bearing v4 code when mirrored from the canonical working tree.
- [`../tests/`](../tests/) — source tests; generated pytest output must not be archived as historical authority.

## Repository roles

### Current authority
Files that define what may be concluded or executed now. Historical copies never supersede current authority merely because they are newer Git objects.

### Historical recovery
Recovered historical bytes are preserved under version/stage-specific paths. A Git commit made during recovery proves only that the bytes were backfilled at that time; it does **not** prove that the artifact was committed historically.

### Review packets
Small, decision-bearing bundles: contracts, manifests, source snapshots, schemas, terminal reports, and external reviews. Repeated caches, staging trees, and test-output copies are excluded by default.

### Large/public data
Public source data may be mirrored when materially required for reproducibility. Otherwise GitHub stores source identifiers, exact hashes, manifests, and reconstruction instructions rather than redundant large matrices/caches.

## Non-negotiable organization rules

1. Frozen scientific bytes are not edited merely for repository aesthetics.
2. Distinct historical byte versions must have distinct repository paths.
3. No two different blobs may be mapped to the same proposed historical destination.
4. Generated pytest/output/staging copies are not history unless they are the only recovered copy of a frozen authority.
5. Current state and chronology are maintained incrementally after every decision gate.

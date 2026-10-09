# Recovered Sept. 7 target-discovery custody package

Status: `RECOVERED_CHAT_LOCAL__HASH_VERIFIED__TD34_PRIMARY_BYTES_AND_UPSTREAM_SUPPORT_BOUND`

Recovery date: 2026-10-08  
TD34 upstream closure date: 2026-10-09

This directory records recovery of the historical target-discovery package that later audits knew only by filename/hash.

## Original package identity

- filename: `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
- recovered chat-local path at recovery: `/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
- ZIP bytes: `1664383`
- ZIP SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- expected historical ZIP SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- identity verdict: `EXACT_MATCH`
- extracted file count: `97`

The binary ZIP itself is not duplicated into ordinary Git history. Its exact authenticated identity is preserved here, while authority-critical recovered text bytes and a package-wide checksum inventory are committed under this directory.

## Recovered primary identities

### Embedded handoff

- archive path: `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.md`
- bytes: `25939`
- SHA-256: `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`
- expected historical SHA-256: `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`
- verdict: `EXACT_MATCH`

The historical repository also preserves the Sept. 7 target-discovery handoff at `target_discovery/HANDOFF_CURRENT_20260907.md`; use the archive checksum plus historical Git rather than assuming a prose reconstruction.

### Original TD34 producer

- archive path: `scripts/td_iteration34_state_geometry_globalrow.py`
- committed recovery copy: `custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`
- bytes: `6740`
- SHA-256: `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`
- historical audit-recorded producer SHA-256: `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`
- verdict: `PRIMARY_PRODUCER_BYTES_RECOVERED__EXACT_HASH_MATCH`

The authentic producer establishes the TD34 panel rule directly:

1. load `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` and select addresses with `(states == 1).all(0)`;
2. sort those common-support addresses by `SHA256("TD25|<integer-address>")`;
3. take four consecutive blocks of 512 addresses.

The producer therefore does not rank panel membership by outcome, pathology, covariance, expression magnitude, topology, or observed cross-source result.

## TD34 upstream support binding — CLOSED 2026-10-09

The exact upstream support substrate consumed by the recovered producer has now been physically recovered from the canonical Aug-24 calibration bundle.

Canonical archive:

- filename: `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- bytes: `410278055`
- SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Exact producer-consumed member after extraction:

`FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

- bytes: `227532`
- SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- `states` shape/dtype: `(42, 41238)` / `uint8`

Applying the authentic producer to this canonical NPZ yields exactly `17186` all-operator common-support addresses.

Vector identities over raw `numpy.int32` bytes:

- sorted common support: `a4095c0e70141cacbcb940a2455480e9666452de4d41875360e9b4573c05a4f4`
- TD25-hash-ordered 17,186 vector: `48b311c8abe1c25912277c2c4aaafb595035649ab7e3929bed5655167bd8a310`
- first 2,048 ordered addresses: `13616d28a3e0c1e517b8b465e19e4ce7d209fc9e796391c041519fdcf1542b12`

Exact 512-address panel hashes:

- P0 `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- P1 `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- P2 `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- P3 `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

These exactly match the independently reconstructed candidate panel hashes from the authenticated TD21B common-support evidence.

Primary closure receipt:

`custody/target_discovery_20260907_recovered/TD34_EXACT_PANEL_BINDING_RECEIPT_20261009.md`

Current TD34 custody classification:

`TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__SELECTION_RULE_HASH_BOUND__NO_TARGET_AUTHORITY`

The former status `UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING` is superseded.

## Archive manifest facts

The recovered package's own `PACKAGE_MANIFEST.csv` records the archive contents and hashes. A fresh package-wide checksum inventory is preserved beside this README as `RECOVERED_PACKAGE_SHA256_MANIFEST.csv` so future agents can distinguish recovered bytes from historical references.

Notable archive files include the TD23–TD36 producer scripts, TD23–TD36 evidence, the prospective target-discovery contract, project-history decision context, and the Sept. 7 handoff. This custody branch commits only authority-critical missing primary bytes rather than duplicating all historical evidence already present in Git.

## Supersession rule

When older documents say any of the following, read them as historical state at the time of that audit rather than current custody truth:

- Sept. 7 ZIP `REFERENCE_ONLY_NOT_RECOVERED`;
- original TD34 producer bytes `NOT RECOVERED`;
- TD34 genealogy indeterminate solely because producer bytes were absent;
- TD34 `UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`;
- TD34 `EXACT_HISTORICAL_PANEL_BINDING_STILL_OPEN`.

Those custody gaps are now closed for TD34 exact panel membership. This does **not** create production target authority, training authority, Stage 4 authority, TEST access, Morabito access, representation freeze, or production promotion.

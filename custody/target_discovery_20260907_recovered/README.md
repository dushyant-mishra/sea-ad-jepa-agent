# Recovered Sept. 7 target-discovery custody package

Status: `RECOVERED_CHAT_LOCAL__HASH_VERIFIED__KEY_PRIMARY_BYTES_COMMITTED`

Recovery date: 2026-10-08

This directory records recovery of the historical target-discovery package that later audits knew only by filename/hash.

## Original package identity

- filename: `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
- recovered chat-local path: `/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
- ZIP bytes: `1664383`
- ZIP SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- expected historical ZIP SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- identity verdict: `EXACT_MATCH`
- extracted file count: `97`

The GitHub connector used for this custody update accepts UTF-8 text files but not an arbitrary binary ZIP upload. Therefore the binary ZIP itself is not copied into Git. Its exact authenticated identity is preserved here, while the highest-value recovered primary text bytes and a package-wide checksum inventory are committed under this directory.

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

## Remaining TD34 custody question

This recovery supersedes the old statement that the original TD34 producer bytes were not recovered. It does **not yet** establish a fully self-contained byte-for-byte reproduction of the four 512-address membership vectors because the producer's upstream support input

`FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

was not found inside this ZIP, and no standalone four-panel membership manifests were found by filename inspection.

Current TD34 custody classification:

`PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`

The next archaeology step is to recover/hash-bind the exact upstream observation-state NPZ or another authenticated artifact that contains the same common-support address set, then deterministically reconstruct and hash the four membership vectors.

## Archive manifest facts

The recovered package's own `PACKAGE_MANIFEST.csv` records the archive contents and hashes. A fresh package-wide checksum inventory should be kept beside this README as `RECOVERED_PACKAGE_SHA256_MANIFEST.csv` so future agents can distinguish recovered bytes from historical references.

Notable archive files include the TD23–TD36 producer scripts, TD23–TD36 evidence, the prospective target-discovery contract, project-history decision context, and the Sept. 7 handoff. This custody update commits only the most authority-critical missing primary bytes rather than duplicating all historical evidence already present in Git.

## Supersession rule

When older documents say any of the following, read them as historical state at the time of that audit rather than current custody truth:

- Sept. 7 ZIP `REFERENCE_ONLY_NOT_RECOVERED`;
- original TD34 producer bytes `NOT RECOVERED`;
- TD34 genealogy indeterminate solely because producer bytes were absent.

The remaining genealogy uncertainty is now narrower: authenticated upstream common-support state / exact membership-vector reconstruction.

This recovery is custody/documentation only. It confers no target authority, training authority, Stage 4 authority, TEST access, Morabito access, representation freeze, or production promotion.
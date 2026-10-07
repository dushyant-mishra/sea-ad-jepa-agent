# Chat-runtime target-recovery custody — 2026-10-07

This directory is a durable GitHub custody layer for the files and conclusions recovered during the 2026-10-07 target-discovery audit.

## What is stored directly

- `JEPA_CHAT_RUNTIME_CUSTODY_SHA256_20261007.csv`: exact byte size + SHA-256 for every top-level runtime file.
- `foundation_materialize_discovery_expression.py`: byte-exact recovered source. Original SHA-256 `ede646be8030ef1644d27496a98eb4661e1c95e4043bc44a6d520e81b7d0228f`.
- `foundation_materialize_nph_discovery_sample.R`: byte-exact recovered source. Original SHA-256 `c463688e87cbac14ad0ebd07716d160256ff1347731896e7945963f3a3d2f611`.
- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`: human-readable custody copy of the recovered audit; authoritative original-byte identity remains SHA-256 `c0f1f68fd3af9b95479fdc05536533481bd42710bc67a94a1c4996d4e4fe3b39` in the top-level SHA manifest.
- the controlling scientific/supersession interpretation is in `docs/agent/JEPA_TARGET_RECOVERY_CUSTODY_AND_SUPERSESSION_20261007.md`.

## Large binaries deliberately not duplicated into ordinary Git history

The following local bytes are cryptographically custodied by exact size/SHA rather than copied into normal Git blobs:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — 410,278,055 bytes — `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` — 303,979,881 bytes — `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` — 303,979,880 bytes — `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip` — 92,478,083 bytes — `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`
- `checkpoints.zip` — 71,356,460 bytes — `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `NIHMS1066836-supplement-Table_S5.xlsx` — 36,876,140 bytes — `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`

All other top-level files are enumerated in the SHA manifest as well.

## Archive inventory summary

Central-directory inspection of the local ZIPs established:

- calibration bundle: 50 files; ~2.78 GB uncompressed; includes code, support/namespace contracts, metadata SQLite, calibration outputs, sampler/split authorities and truth table;
- Sept-7 target-discovery handoff: 97 files; includes the original `scripts/td_iteration34_state_geometry_globalrow.py` plus TD23–TD36 evidence and scripts;
- Sept-8 light handoff: 48 files; includes TD56/TD57 artifacts and nested Sept-7 target-discovery ZIP;
- TD41–TD58 working archive: 155 files; includes TD41 reconstruction/audit code, TD43 cases, TD44–TD58 scripts and NPZ/NPY results;
- eligible-donor estimator candidate: 25 files; code/tests/contracts/ledgers;
- `expression.zip`: 45 files; recovered discovery audit, 50K sample freeze, and 42 operator metadata tables;
- `checkpoints.zip`: checkpoint manifest + u0000/u0205 checkpoints;
- `t1_checkpoint_u0200.zip`: u0010/u0025/u0050/u0100/u0200 checkpoint series;
- V77 JUnit ZIP: XML + log;
- chat-exclusive final-sources ZIP: two source/handoff texts + internal SHA file.

## Critical supersession warning

The recovered HVS/SEA-AD discovery producer is itself evidence of the physical-column problem: it constructs a map from provenance `source_feature_index` and indexes that map with HDF5 sparse `indices`. A later historical audit establishes that HVS/SEA-AD `source_feature_index` was a harmonized feature rank rather than the physical H5AD column. Therefore neither downstream positional consistency nor the historical discovery audit SHA is sufficient to establish correct gene→value semantics for HVS/SEA-AD.

Do not revive the earlier `DISCOVERY_EXPRESSION_ADDRESS_AXIS_PRIMARY_SOURCE_VERIFIED` label for HVS/SEA-AD. NPH52 is a separate path and requires its own semantic verification.

## Recovery rule

If any large local binary must be reacquired, require exact byte-size + SHA-256 equality to this custody manifest before treating it as the same artifact. Do not substitute a newly generated equivalent without a new lineage classification.

# External-review handoff

Terminal candidate: `PASS_F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT_REPAIR_AWAITING_EXTERNAL_REVIEW`

This package authenticates only the repaired real-reader, query-safe forward, resource-selection, resume, and sufficient-statistic mechanics. It does not authorize or contain the real F1 biological sweep, biological outcomes, final qualification gates, training, backward, optimizer, or EMA activity.

## Bound authorities

- pre-review candidate/base: `76fe7d63efe81451ef0fae3ef3eaf116be14f6be`
- implementation commit: `a3c4452d48cedc8650ba9de4a9d6737cc926544c`
- root commit: `2f33a8a1662e98de03cbb28604d8bfbb2d9477bb`
- permanent verifier governance commit: `f5b749819dd6b5fae9bb1f9af8c38c47b53e4655`
- QID-v2 contract SHA-256: `15d873871787e0820f63aaead8f27a6f1057541e16640d8492053144a9c69423`
- physical membership SHA-256: `edc6cf3f3774f23da63f57a55774d5703b89da087bc8efe970a80e316c89a2aa`
- superseded package root: `2d9bb25e0fb248251a184d5711ef1be95d4a53b3f41536262f2322f3503b725b`

## Result

- fixture: 51 unique `(cell,q)` records; 38 donors; 42 operators; three sources; five evidence levels; all three roles;
- selected mechanics: batch 4, reader block 4, workers 4, prefetch 4, pinned memory off;
- query-safe parity, resume parity, sufficient-statistic parity, and independent validation: PASS;
- full plan: 44,496 assignments, 43,108 unique `(cell,q)`, 474,188 expensive forwards, 222,480 effect rows, 1,400 logical shards;
- physical plan: 2,781 unique rows, 1,148 authenticated blocks, 6,221,329,590 bytes;
- projected runtime: 38,892.124971 seconds (10.803368 hours), engineering projection only;
- firewall: PASS. Real reader-fit expression was computationally opened only for the bounded technical check; protected data and biological outcomes were not opened or computed;
- permanent implementation verifier: PASS after one preserved veto and narrow repair.

Required next action: fresh external review of this repaired package. Real F1 remains forbidden until separately authorized.

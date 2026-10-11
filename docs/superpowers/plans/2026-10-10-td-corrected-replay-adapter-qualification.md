# TD corrected replay adapter qualification plan

Date: 2026-10-10

Status: `PLAN_ONLY__NO_VALUE_READ_AUTHORITY__NO_REPLAY_AUTHORITY`

Controlling science spec:
`docs/superpowers/specs/2026-10-10-td-corrected-biological-replay-prefreeze.md`

Machine prefreeze:
`custody/target_discovery/TD_CORRECTED_BIOLOGICAL_REPLAY_PREFREEZE_20261010.json`

Executor-provenance ledger:
`custody/target_discovery/TD_CORRECTED_REPLAY_EXECUTOR_PROVENANCE_LEDGER_20261010.json`

TD57C recovery receipt:
`custody/target_discovery/TD57C_EXECUTOR_RECOVERY_RECEIPT_20261010.json`

TD59 provenance addendum:
`docs/superpowers/specs/2026-10-10-td59-replay-provenance-addendum.md`

## Goal

Build a minimal compatibility layer that lets the frozen historical TD56/TD57B/TD57C/TD59 computations consume the future immutable G6 V2 Sample-A cache without changing any historical scientific rule.

The adapter is not allowed to define new panels, thresholds, nulls, donor splits, locality fractions or terminals.

## Core strategy

The future G6 V2 cache is expected to expose a 25,000-row Sample-A sparse matrix in the canonical 41,238-address coordinate system, with nonzero values materialized only for the exact frozen 9,216 replay addresses.

The historical target-discovery executors only need the A_NATURAL_MIXTURE rows and the addresses allocated to their own frozen panels. Therefore the compatibility layer should provide the historical executor with the same logical row/address access it previously received, while sourcing HVS/SEA-AD values from G6 and NPH52 values from the explicitly authenticated historical pass-through already embedded in G6.

Do not rebuild or infer values outside the G6 cache.

## Task 1 — executor provenance is now resolved stage by stage

The authenticated Project-Library archive:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

has exact frozen SHA-256:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

and size 92,478,083 bytes.

A 2026-10-10 exhaustive Project-Library audit recovered and independently SHA-verified these historical executors from that archive:

- TD56 HVS primary: `run_td56_hvs.py` → `a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43`
- TD56 NPH52 primary: `run_td56_nph.py` → `090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162`
- TD56 SEA_AD exact-fast primary: `run_td56_sea_fast.py` → `c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866`
- TD57B local decision executor: `td57b_fixed_relational_recurrence.py` → `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`
- TD57B fast wrapper: `td57b_fast_wrapper.py` → `808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70`
- TD57C local decision executor: `td57c_three_view_local_geometry.py` → `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

TD57C package recovery is therefore **closed**. Do not reconstruct TD57C from prose.

TD59 is the sole exception: the project already established that its original executor bytes were not recovered. Use the already-qualified replay-closure successor SHA-256 `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085` as the executable historical-statistic reference, while preserving original executor SHA `3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0` as historical provenance only.

No adapter code may be written for a stage except against its admissible executable reference above.

## Task 2 — define one read-only adapter API

The adapter should expose only:
- Sample-A row metadata in exact row order 0..24,999;
- sparse normalized value lookup by canonical molecular address;
- source library and detected-count diagnostics already carried by G6 metadata;
- exact source/donor/operator/cell identifiers required by the historical executors.

It must not expose:
- other 50K rows;
- addresses outside the frozen G6 replay set;
- pathology/biological labels;
- DEV/SEALED/external data.

## Task 3 — authenticated historical-fixture equivalence

Before corrected values are allowed, qualify the adapter using authenticated historical inputs only.

Construct a historical-fixture G6-shaped cache from the exact historical Sample-A 50K CSR and the exact frozen 9,216-address manifest. This fixture is for adapter equivalence only and does not create corrected evidence.

For every historical stage:
1. run the stage's admissible historical executable reference from the provenance ledger on authenticated historical input;
2. run the adapter-fed version of that same admissible reference on the authenticated historical fixture;
3. compare all decision-bearing outputs exactly or at the historically documented deterministic numeric tolerance where exact floating-point identity is impossible;
4. require identical case PASS/FAIL decisions and identical stage terminal;
5. require identical donor/sample/panel support counts;
6. require exact null sampling identities and deterministic split identities.

For TD59, “admissible historical executable reference” means the validated replay-closure successor, not the missing original bytes.

Qualification must include the historically decision-bearing primary screens, not only helper tests.

## Task 4 — TD56 equivalence

Use the exact recovered primary executors above. The decision-bearing corrected TD56 object remains the prospectively frozen primary screen.

Require identity on authenticated historical values for:
- selected gene views and fixed pair identities;
- source-specific sampled cell pairs;
- donor×operator strata;
- matched null identities;
- observed/null statistics;
- source PASS decisions;
- terminal.

Historical adversarial/robustness reruns remain audit history and must not become extra corrected PASS requirements unless separately prefrozen before corrected values are opened.

## Task 5 — TD57B equivalence

Require identity of:
- Panel 0/1 gene identities;
- 2,048 pair identities per view;
- deterministic triplet sample identities;
- donor split membership;
- matched-null Y permutations;
- measurable donor/triplet support;
- all 24 case decisions;
- terminal.

Historical reference 24/24 PASS is not a tuning target; it is the expected result of the historical fixture equivalence test.

## Task 6 — TD57C equivalence

Use the exact recovered executor bytes SHA-256:

`530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

The adapter qualification must reproduce the historical **failure**, not merely execute successfully.

At minimum require:
- same Panel-0 HVS structural donor set;
- same nearest-third Z-selected triplet identities;
- same donor halves;
- same null identities;
- same 2/4 HVS Panel-0 half-case PASS count;
- exact terminal `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`.

If the adapter cannot reproduce the historical fail state on authenticated historical values, it is not qualified for corrected replay.

## Task 7 — TD59 equivalence

Use only the validated replay-closure successor:
`target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py`

Required successor SHA-256:
`870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`

Preserve historical original executor SHA-256:
`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`
with `original_executor_bytes_recovered=false`.

Require identity of:
- fresh panel gene/pair hashes;
- nearest-half selector behavior and global-row tie break;
- structural donor sets;
- local triplet samples;
- donor splits/nulls;
- all 24 decision-bearing observed/null-p95/null-max rows versus the replay-closure reference;
- 24/24 p95 case decisions;
- 22/24 null-max diagnostic count;
- stage terminal.

Never call the replay-closure successor the original TD59 executor.

## Task 8 — fail-closed code identity

A future replay execution authorization, if ever created, must bind:
- exact G6 receipt/cache hashes;
- exact G7 receipt hash;
- exact replay adapter code identity;
- exact admissible stage executor identities from the provenance ledger;
- exact authenticated TD41-TD58 archive SHA;
- exact science-prefreeze SHA;
- exact machine-prefreeze SHA;
- exact executor-provenance ledger SHA;
- exact TD57C recovery-receipt SHA;
- exact TD59 provenance-addendum SHA.

The adapter/executors must be Git-tracked and clean where Git-tracked copies are used. Platform newline policy must not change code identity semantics. Historical executor identity is the exact recovered/archive member SHA, not a rewritten working-tree copy.

## Task 9 — corrected replay namespaces

Each corrected stage gets a fresh immutable namespace. Never reuse historical result directories.

Recommended logical structure:
`results/target_discovery/corrected_replay_20261010/<stage>/attempt_001/`

An execution-start marker spends a namespace immediately. Any failure leaves the namespace immutable and preserved.

## Task 10 — output comparison contract

Corrected replay output must contain both:
- the frozen stage terminal evaluated on corrected values;
- a descriptive historical-comparison classification:
  - `QUALITATIVE_HISTORICAL_CONCLUSION_REPRODUCED`;
  - `QUALITATIVE_HISTORICAL_CONCLUSION_NOT_REPRODUCED`;
  - `NOT_ESTIMABLE`.

Never substitute the comparison classification for the stage terminal.

## Stop rules

This plan does not authorize implementation execution against corrected values.

Before corrected replay:
- PR #263 or a reviewed successor must first qualify against exact PR #259 evidence;
- G6/G7 require a separate explicit owner decision;
- G6/G7 must both PASS;
- then corrected biological replay requires another explicit owner decision;
- historical-fixture adapter equivalence must pass for every stage.

After all corrected replay receipts, STOP again before target selection, TD60, or training.

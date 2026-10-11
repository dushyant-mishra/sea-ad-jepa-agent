# TD corrected replay adapter qualification plan

Date: 2026-10-10

Status: `PLAN_ONLY__NO_VALUE_READ_AUTHORITY__NO_REPLAY_AUTHORITY`

Controlling science spec:
`docs/superpowers/specs/2026-10-10-td-corrected-biological-replay-prefreeze.md`

Machine prefreeze:
`custody/target_discovery/TD_CORRECTED_BIOLOGICAL_REPLAY_PREFREEZE_20261010.json`

Executor-provenance ledger:
`custody/target_discovery/TD_CORRECTED_REPLAY_EXECUTOR_PROVENANCE_LEDGER_20261010.json`

TD59 provenance addendum:
`docs/superpowers/specs/2026-10-10-td59-replay-provenance-addendum.md`

## Goal

Build a minimal compatibility layer that lets the frozen historical TD56/TD57B/TD57C/TD59 computations consume the future immutable G6 V2 Sample-A cache without changing any historical scientific rule.

The adapter is not allowed to define new panels, thresholds, nulls, donor splits, locality fractions or terminals.

## Core strategy

The future G6 V2 cache is expected to expose a 25,000-row Sample-A sparse matrix in the canonical 41,238-address coordinate system, with nonzero values materialized only for the exact frozen 9,216 replay addresses.

The historical target-discovery executors only need the A_NATURAL_MIXTURE rows and the addresses allocated to their own frozen panels. Therefore the compatibility layer should provide the historical executor with the same logical row/address access it previously received, while sourcing HVS/SEA-AD values from G6 and NPH52 values from the explicitly authenticated historical pass-through already embedded in G6.

Do not rebuild or infer values outside the G6 cache.

## Task 1 — inventory exact historical executors and freezes

Before implementation, use the executor-provenance ledger to resolve for TD56, TD57B, TD57C and TD59:
- historical implementation path;
- historical implementation/freeze commit or file SHA;
- all script/blob SHAs used for the result where multiple source-specific implementations existed;
- exact panel/ranking positions;
- exact output schemas/terminals;
- exact historical input hashes needed for fixture qualification.

Stage-specific provenance rules are mandatory:

- **TD57B:** use the Git-preserved implementation lineage and exact local decision-executor SHA binding.
- **TD57C:** the Sep-8 package binding records that the core script was packaged. Recover authenticated package bytes and require exact SHA-256 `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c` before adapter implementation. If exact bytes cannot be recovered, STOP; do not reconstruct from prose. A separately frozen independent reconstruction/equivalence closure would be required before proceeding.
- **TD59:** the original executor bytes are explicitly documented as unrecovered. Do not chase or fabricate them. Use the already-qualified replay-closure successor SHA-256 `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085` as the executable historical-statistic reference, while preserving original executor SHA `3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0` as historical provenance only.
- **TD56:** recover exact decision-bearing script bytes from authenticated package/history where available. If a required primary executor is not recoverable, establish a separately audited equivalence closure before corrected values are opened; do not reimplement from prose.

No adapter code may be written for a stage until that stage's executable-provenance rule is satisfied.

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

Qualification must include at least the historically decision-bearing primary screens, not only unit-level helper tests.

## Task 4 — TD56 special requirements

Historical TD56 had:
- prospective freeze `d257fd3cf4957ecbb1ab3f03a06e54d043a1326f`;
- HVS/NPH52/SEA_AD primary PASS;
- an exact SEA_AD fast-vs-naive comparison with max absolute difference 0.0;
- a pair-ordering ambiguity audit that was non-material;
- an independent next-2048-pair robustness audit.

The corrected replay's decision-bearing TD56 object is the prospectively frozen primary screen. The historical adversarial/robustness reruns remain audit history and must not become extra corrected PASS requirements unless separately prefrozen before corrected values are opened.

Adapter equivalence should nevertheless demonstrate that the chosen canonical pair-preimage interpretation reproduces the recorded historical primary terminal.

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

The adapter qualification must reproduce the historical **failure**, not merely execute successfully.

At minimum require:
- exact recovered TD57C executor bytes SHA-256 `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`, or a separately frozen replacement closure if and only if exact package recovery is proven impossible;
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

The old weakest p95 margin is descriptive, not a code-tuning target. Never call the replay-closure successor the original TD59 executor.

## Task 8 — fail-closed code identity

A future replay execution authorization, if ever created, must bind:
- exact G6 receipt/cache hashes;
- exact G7 receipt hash;
- exact replay adapter code identity;
- exact admissible stage executor identities from the provenance ledger;
- exact science-prefreeze SHA;
- exact machine-prefreeze SHA;
- exact executor-provenance ledger SHA;
- exact TD59 provenance-addendum SHA.

The adapter/executors must be Git-tracked and clean. Platform newline policy must not change code identity semantics.

## Task 9 — corrected replay namespaces

Each corrected stage gets a fresh immutable namespace. Never reuse historical result directories.

Recommended logical structure:
`results/target_discovery/corrected_replay_20261010/<stage>/attempt_001/`

An execution-start marker spends a namespace immediately.

Any failure leaves the namespace immutable and preserved.

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
- stage-specific executor provenance/equivalence requirements must be satisfied.

After all corrected replay receipts, STOP again before target selection, TD60, or training.

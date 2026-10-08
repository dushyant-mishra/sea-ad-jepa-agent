# JEPA complete takeover — runtime + provenance + S174 custody

Status: **COLD-START TAKEOVER / NON-AUTHORIZING**  
Date: 2026-10-08

This branch is intended to let a future agent clone one branch and recover the complete current working state without reconstructing this chat.

## What is active at the top level

The top-level repository is the audited bounded-rehearsal runtime state from PR #236:

- source branch: `impl/v77-bounded-synthetic-mutation-20261007`
- source head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`
- final execution-bearing commit: `8dabe9ef9ed87b4beaf00acefda1a3073ed751de`
- V77 joined workflow run: `37712331165` — success
- focused regression suite: 51 passed
- independent rehearsal custody rerun: 1 passed

The bounded rehearsal proved exactly one guarded synthetic update, EMA-after-completion, typed persistence, fresh-module restore and exact state-digest agreement. It remains synthetic-only and non-production.

## Exact S174 working snapshot

The entire tracked S174 repository state is embedded byte-identically at:

`custody/takeover_20261008/s174_repo_snapshot/`

Source:

- branch: `claude/s174-train-cache-rebuild-20261007`
- head: `750cb83c8c0535cc67a70d58b62db5607bd7d01e`
- Git tree: `f21515b50a1a7eebc042ac238f5be3231cc0c5e9`
- replay checkpoint: `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`
- replay CI run: `37693603160` — 146 passed, zero skipped

Because this is a whole Git-tree snapshot, its original relative paths are preserved. A future agent can inspect or reproduce the S174 lane by entering that directory rather than trying to merge its highly divergent history into the runtime lineage.

The snapshot contains the tracked S174 audit docs, preregistrations, producing scripts, tests, status addenda, corrected replay results, spillover audits and CI receipt.

Large scientific/cache bytes that were never stored in ordinary Git are **not magically duplicated here**. Their custody hashes, paths and receipts remain inside the S174/prior-custody records. Do not treat absent large bytes as permission to regenerate or substitute them silently.

## Prior handoff snapshot

The previous cold-start handoff is embedded at:

`custody/takeover_20261008/pr230_handoff_snapshot/`

Source:

- PR #230
- branch: `handoff/jepa-20261007-post-v77-s174-takeover`
- commit: `a33deeae9f68ea48eea2119c9cfeb8a80dda8e0f`
- tree: `6c1d101a2a2f6840cb5d036ad52f0760c72dce2e`

Read it for historical failure modes and earlier custody context, but use this file plus the manifest as the newer state.

## Canonical lineage

Do not invent a replacement architecture. The accepted technical chain is:

1. PR #224 runtime — `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
2. PR #226 shared qualification — `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
3. PR #228 V77 joined ZERO_UPDATE — `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
4. PR #232 physical-provenance V2 execution repair — `d3430ce6c0e878272e92b61e01822334e088d8c8`
5. PR #236 one-step bounded synthetic rehearsal — current top-level lineage

The current runtime already owns student, predictor, frozen-copy teacher initialization, guarded optimizer completion, presentation-normalized EMA and typed checkpoint/restart proof.

## Decision-changing audit results

### Physical provenance

The V2 binding initially existed without being mandatory at execution. That was repaired. Execution now requires the physical row/value proof and authenticated payload digest comparison. Synthetic tests prove enforcement of the supplied proof; they do not independently authenticate external real payload bytes.

### 2K observation-operator support

The sampler already contained the repaired stress-twin zero-quota rescue, but CI was not running the out-of-tree 2K regression. PR #233 corrected CI coverage. The executed suite proved 42/42 observation operators with minimum support >= 1 at 2K. Do not restore the calibration-closure regression that erased operators at small scale.

### One-step mutation rehearsal

Self-audit found missing failure custody, repeat-run blocking and true restored-module verification. RED tests exposed those gaps before repair. Final CI proved:

- optimizer step `0 -> 1` only;
- teacher presentations `0 -> 2` only;
- online/predictor/teacher and optimizer state changed;
- EMA only after completed guarded update;
- typed continuation persisted;
- fresh modules restored to exact post-step digests;
- wrong/missing physical proof, wrong runtime/adapter, q-safety replay and same-run reuse fail closed;
- `training_authorized=false`;
- `production_promotable=false`.

This PASS grants no additional update budget.

## Corrected S174 science state

The old Stage81A3R TRAIN cache was experimentally confirmed gene-axis scrambled for HVS/SEA-AD. Frozen G1 failed and remains failed. G1b authorized the corrected rebuild.

Corrected S149 changed the central interpretation: cohort coverage alone explains about 3% of pooled strong-correlation structure rather than about 89%, while coverage still identifies study.

The corrected synthetic replay was performed without tuning: every arm first reproduced its historical old-universe result exactly, then ran unchanged on the corrected universe.

No candidate is selected.

The new structural finding that matters for the next design is:

- corrected real T5 within-class / pooled correlation ratio is about 0.7435;
- all replayed arms remain roughly 1.02–1.21;
- current hidden substates were drawn independently of broad cell class;
- therefore the current family does not reproduce the real contribution of broad cell-class structure to pooled correlation.

The 12-fold dynamic-range arm nearly matches corrected detection density and degree but still misses transitivity, abundance and depth. It is an observation, not a winner.

S159 donor-bootstrap intervals remain descriptive, not qualification thresholds, because some corrected real point estimates lie outside their own reported interval.

The 353 historical Ensembl-ID remappings remain a separate identity-governance issue. Do not opportunistically change them.

## Hard boundaries

Still enforce:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`
- no real-data training
- no production EMA selection
- no target freeze
- no representation freeze

## Next action

The runtime lane should stop drifting unless a new failing regression exposes a real defect.

The next work is scientific design. The leading design to evaluate prospectively is:

`broad cell class -> class-shared biological programs -> within-class continuous/substate biology -> fixed observation operator -> counts`

Compare at least:

1. class-shared program only;
2. class-shared + within-class continuous state (preferred initial hypothesis);
3. class-shared + current substate mechanism.

Hold the observation/counting mechanism fixed initially so biology and measurement are not changed simultaneously. Do not optimize solely to T5; inspect corrected expression structure, detection structure/topology, class separation, abundance and depth jointly.

This is an architectural scientific change. Design/preregister it before implementation.

## First commands/read order for a future agent

1. Read `custody/takeover_20261008/MANIFEST.json`.
2. Read this file.
3. Read `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md` at top level.
4. Read `custody/takeover_20261008/pr230_handoff_snapshot/docs/agent/JEPA_NEW_AGENT_HANDOFF_20261007_POST_V77_ZERO_UPDATE_S174_REPAIR.md`.
5. Read `custody/takeover_20261008/s174_repo_snapshot/docs/agent/S174_REPLAY_SUMMARY.md` and `S174_SYNTHETIC_REPLAY.md`.
6. Inspect top-level PR #236 implementation/tests before modifying runtime.
7. Treat the nested S174 repo as the exact corrected science snapshot, not as runtime code to merge blindly.

Record every future decision-changing result in GitHub with exact SHAs. Do not leave scientific conclusions only in chat.

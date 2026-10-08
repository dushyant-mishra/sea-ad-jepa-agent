# JEPA complete takeover — audited runtime + corrected S174 working state

Status: **COLD-START TAKEOVER / NON-AUTHORIZING**  
Date: 2026-10-08

This branch packages the current working state so a future agent can clone one branch and continue without reconstructing this chat.

## 1. Active top-level runtime

Top-level repository state is the audited PR #236 bounded-rehearsal runtime:

- source branch: `impl/v77-bounded-synthetic-mutation-20261007`
- source head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`
- final execution-bearing commit: `8dabe9ef9ed87b4beaf00acefda1a3073ed751de`
- V77 joined workflow run: `37712331165` — SUCCESS
- focused regression suite: 51 passed
- independent successful rehearsal rerun: 1 passed

The bounded rehearsal proved exactly one guarded synthetic update, EMA-after-completion, typed persistence, fresh-module restore and exact state-digest agreement. It remains synthetic-only and non-production.

Do not replace this top-level runtime with code from the S174 custody snapshot.

## 2. Corrected S174 working snapshot

The exact S174 working/audit surfaces are preserved at:

`custody/takeover_20261008/s174_working_snapshot/`

Source:

- branch: `claude/s174-train-cache-rebuild-20261007`
- head: `750cb83c8c0535cc67a70d58b62db5607bd7d01e`
- source root tree: `f21515b50a1a7eebc042ac238f5be3231cc0c5e9`
- custody snapshot tree: `d52f665aeb393c368102c5b71afc59f03b10225f`
- replay checkpoint: `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`
- replay CI run: `37693603160` — 146 passed, zero skipped

Included exact Git-tree surfaces:

- `.github/workflows/`
- `docs/agent/`
- `results/v77/`
- `scripts/`
- `tests/`

This preserves the S174 preregistrations, audits, rebuild/replay scripts, tests, corrected results, spillover records and CI custody while deliberately excluding unrelated old source/history from the divergent S174 repository lineage.

Large scientific/cache files that were never stored in ordinary Git are not duplicated here. Their exact hashes, paths and custody records are carried by the included runtime-interface custody manifests. Never silently regenerate or substitute missing large bytes.

## 3. Historical takeover and large-artifact custody

Prior PR #230 handoff:

`custody/takeover_20261008/PR230_PRIOR_HANDOFF.md`

PR #227 runtime/interface custody files are carried at original paths:

- `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md`
- `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md`
- `docs/agent/archive/chat_runtime_20261007/JEPA_RUNTIME_INTERFACE_CHAT_CUSTODY_MANIFEST_20261007.json`

Prior exact-hash artifact custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef`

Hash custody proves identity, not biological validity.

## 4. Canonical technical lineage

Do not invent a replacement architecture. Accepted chain:

1. PR #224 runtime — `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
2. PR #226 shared qualification — `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
3. PR #228 joined V77 ZERO_UPDATE — `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
4. PR #232 physical-provenance V2 execution repair — `d3430ce6c0e878272e92b61e01822334e088d8c8`
5. PR #236 bounded one-step synthetic rehearsal — current top-level state

The current runtime already owns student, predictor, frozen-copy teacher initialization, guarded optimizer completion, presentation-normalized EMA and typed checkpoint/restart proof.

## 5. Decision-changing runtime audits

### Physical provenance

Self-audit found V2 physical binding existed but was not mandatory at the ZERO_UPDATE boundary, and payload SHA was not checked against authenticated payload SHA. PR #232 repaired both. Executed expression values are now tied to the physical proof chain.

Qualification: synthetic tests prove enforcement of a supplied V2 proof. They do not independently authenticate external real payload bytes.

### 2K observation-operator support

The repaired stress-twin zero-quota rescue already existed, but V77 CI did not execute the existing 2K regression. PR #233 fixed CI coverage. CI proved all 42 observation operators present with minimum count >= 1 at 2K. No sampler redesign was needed.

Do not restore the calibration-closure small-scale regression that erased operators.

### Bounded mutation rehearsal

Self-audit exposed missing failure custody, repeat-run blocking and true restored-module verification. RED tests failed on those gaps before repair.

Final CI proved:

- optimizer step `0 -> 1` only;
- teacher presentations `0 -> 2` only;
- online/predictor/teacher and optimizer state changed;
- EMA only after a completed guarded optimizer update;
- typed continuation persisted;
- fresh modules restored to exact post-step digests;
- wrong/missing physical proof, wrong adapter/runtime, q-safety proof replay and same-run reuse fail closed;
- `training_authorized=false`;
- `production_promotable=false`.

This PASS grants no additional mutation budget.

## 6. Corrected S174 science state

The old Stage81A3R TRAIN cache was experimentally confirmed gene-axis scrambled for HVS/SEA-AD. Frozen G1 genuinely failed and remains failed. G1b authorized the corrected rebuild.

Corrected S149 changed the central interpretation:

- pooled fraction |r| > 0.3: `0.6148 -> 0.1348`;
- coverage-only null: `0.5463 -> 0.0042`;
- coverage share of strong-correlation structure: about 89% -> about 3%;
- coverage still identifies study.

The old claim that pooled real dependence is mostly cohort-composition artifact does not survive.

Every synthetic arm was first rerun on the old universe and reproduced its committed result exactly, then rerun unchanged on the corrected universe. No seed, preprocessing, arm or scoring rule was tuned.

No candidate is selected.

The important structural finding for the next design:

- corrected real T5 within-class / pooled correlation ratio is about `0.7435`;
- replayed arms remain roughly `1.02–1.21`;
- current hidden substates were drawn independently of broad cell class;
- therefore the current synthetic family does not reproduce the contribution of broad cell-class structure to pooled correlation.

The 12-fold dynamic-range arm nearly matches corrected detection density and degree but still misses transitivity, abundance and depth. It is an observation, not a winner.

S159 donor-bootstrap intervals remain descriptive rather than qualification thresholds because some corrected real point estimates lie outside their own interval.

The 353 historical Ensembl-ID remappings remain a separate identity-governance issue. Do not change them opportunistically.

## 7. Hard boundaries

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

## 8. Next action

Runtime should stop drifting unless a new failing regression exposes a genuine defect.

Next work is scientific design. Leading prospective structure:

`broad cell class -> class-shared biological programs -> within-class continuous/substate biology -> fixed observation operator -> counts`

Compare at least:

1. class-shared program only;
2. class-shared + within-class continuous state — preferred initial hypothesis;
3. class-shared + current substate mechanism.

Hold observation/counting fixed initially. Do not fit only T5; evaluate corrected expression structure, detection structure/topology, class separation, abundance and depth together.

This is an architectural scientific change. Design and preregister it before implementation.

## 9. Read order for a future agent

1. `custody/takeover_20261008/MANIFEST.json`
2. this file
3. `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`
4. `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md`
5. `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md`
6. `custody/takeover_20261008/PR230_PRIOR_HANDOFF.md`
7. `custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_REPLAY_SUMMARY.md`
8. `custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_SYNTHETIC_REPLAY.md`
9. inspect top-level PR #236 implementation/tests before touching runtime
10. use the nested S174 snapshot for corrected science scripts/results/tests; do not merge its old runtime lineage into top-level runtime

Record every future decision-changing result in GitHub with exact SHAs. Do not leave important scientific conclusions only in chat.

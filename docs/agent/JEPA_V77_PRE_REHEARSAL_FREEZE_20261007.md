# JEPA V77 pre-rehearsal freeze — 2026-10-07

Status: **NON-AUTHORIZING FREEZE RECORD**

Purpose: preserve the exact cross-lane state that has been independently re-audited before any bounded synthetic mutation rehearsal is considered. This document does not authorize such a rehearsal; it only records the prerequisites that are currently GREEN and the scientific constraints that must be carried forward.

## 1. Canonical runtime/interface lineage

Accepted runtime:

- PR #224 `Converge canonical V5 runtime safety path`
- branch `reconcile/canonical-v5-runtime-successor-20261006`
- head `9d00684e08ba34ef8d7b04e478b9c380cd36d537`

Accepted shared qualification interface:

- PR #226 `Validate shared qualification V2 on canonical V5 runtime`
- branch `reconcile/shared-qualification-v2-on-canonical-runtime-20261007`
- head `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- deliberately excludes PR #223's obsolete copied V5 runtime sources

Joined V77 ZERO_UPDATE integration:

- PR #228 `Join V77 to qualified ZERO_UPDATE runtime`
- branch `integrate/v77-qualified-zero-update-20261007`
- head `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- current scope: ZERO_UPDATE only

## 2. Provenance-V2 successor audit

PR #232:

- title: `Audit V77 physical payload digest binding`
- branch `audit/v77-payload-digest-binding-20261007`
- base: PR #228 head `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- head: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- draft, mergeable, non-authorizing

Closed gaps:

1. `PhysicalRowValueBindingV2` now carries `authenticated_payload_sha256` and refuses payload-digest substitution.
2. Both canonical ZERO_UPDATE execution boundaries now require a nonempty tuple of `PhysicalRowValueBindingV2` proofs.
3. Each executed expression row is checked against batch-local row position, logical/source cell identity, donor identity, feature-space digest and the actually consumed expression values before model execution.
4. ZERO_UPDATE receipts now bind a digest of the physical-binding set.
5. A self-consistent-but-wrong consumed-values proof is rejected before the model executes.

Verification:

- workflow: `v77-qualified-zero-update-join`
- run: `37693805825`
- result: SUCCESS
- focused suite: **29 passed**

Scope qualification:

These tests prove fail-closed enforcement of a supplied V2 proof chain on synthetic fixtures. They do **not** independently authenticate external real payload bytes. This distinction must not be promoted away.

## 3. Final spillover result on the runtime successor

The PR #232 diff was re-audited after GREEN.

No new alternative training architecture was introduced. The successor changes provenance enforcement, tests and CI coverage. It does not add a new optimizer, EMA implementation, production checkpoint mechanism, target, representation or scientific threshold.

Standing runtime constraints remain:

- optimizer completion must be proven before EMA;
- skipped/rejected/incomplete updates cannot advance the teacher;
- historical fixed `.996` is not production EMA authority;
- `BoundRuntimeMutationProofV1` remains diagnostic only;
- only the typed presentation-EMA V2 continuation can promote runtime mutation proof;
- runtime mechanics do not resolve rich-teacher target identifiability.

## 4. 2K observation-operator smoke gate

Historical defect:

- stress-twin 2K: 42/42 operators, minimum count 1
- calibration-closure 2K: 36/42 operators, minimum count 0

The current synthetic population-geometry implementation already contains the repaired source-feasible zero-quota rescue. The existing regression test explicitly requires at 2,000 cells:

- `source_operator_nonzero_cells == 42`
- `min(operator_counts) >= 1`

Self-audit found that the old V77 workflow ran only `tests/v77`, so the previous `124 passed` did not execute this regression.

PR #233 fixes only that CI omission:

- title: `Audit V77 2K operator smoke CI coverage`
- branch `audit/v77-2k-operator-smoke-ci-20261007`
- head `c919d957de79a3866fdaeab3ae2ae5a0891d4859`
- one workflow file changed; no sampler/science/model/runtime change

Verification:

- workflow run `37695987219`
- result: SUCCESS
- command executed both `tests/v77` and `tests/test_v73_population_geometry_authority.py`
- **128 passed**

Therefore the 42/42 2K operator gate is now supported by actual CI execution, not source inspection alone.

## 5. Corrected S174/S149 science lane

This lane remains separate from runtime implementation.

Branch:

`claude/s174-train-cache-rebuild-20261007`

Corrected synthetic replay commit:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

Verification:

- workflow run `37693603160`
- result: SUCCESS
- **146 tests**, zero skipped

Current branch head:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

The current head adds only the CI receipt and an `ACTIVE_STATE.md` line after the replay checkpoint; it is not a new scientific rerun.

Settled corrected-science findings:

- old Stage81A3R TRAIN cache was gene-axis scrambled for HVS/SEA-AD;
- frozen G1 genuinely failed and remains failed;
- G1b authorized the corrected rebuilt cache;
- cohort coverage explains about 3% of the strong pooled correlation structure, not about 89%;
- coverage still strongly identifies study;
- old `latent mechanism solved / observation bottleneck` premise is superseded;
- factor-family falsification by unreachable transitivity is superseded;
- substate-family and Observer-V2 support claims are superseded;
- no synthetic mechanism is currently qualified;
- detection continues to carry more dependence than expression.

## 6. Corrected synthetic replay

Replay rule:

- each arm was first rerun on the old universe and reproduced its historical committed result exactly;
- only then was the same arm rerun on the corrected universe;
- no seed, arm, preprocessing or scoring rule changed;
- nothing was tuned to the corrected target;
- historical files remain untouched and old/corrected results are side-by-side.

Main observations:

- counting noise still collapses detection topology;
- the 12-fold dynamic-range arm nearly matches corrected detection density and degree, but still overshoots transitivity and retains major abundance/depth defects;
- it is an observation, not a selected model;
- corrected pooled donor-bootstrap p05-p95 envelopes are **not qualification targets** until S159 is resolved;
- real point estimates are descriptive references and donor-resampled distributions are uncertainty diagnostics.

## 7. Decision-changing class-separation constraint

Corrected T5 within-class / pooled correlation ratio is about **0.74**.

Every replayed synthetic arm is approximately **1.02-1.21** on the same ratio. No replayed arm therefore reproduces the real contribution of broad cell-class separation to pooled correlation.

This is decision-changing for the **next synthetic design**, but it does not invalidate or require modification of the completed replay.

Interpretation:

- the completed replay answered whether existing frozen arms survive correction of the gene universe;
- they do not span the real class-separation structure;
- the current substate design draws hidden substates independently of cell class, so failure to reproduce T5 is structurally expected;
- the next design must allow biological state structure to interact with broad cell class rather than assigning all latent substate structure independently of it.

This requirement must **not** be implemented by simply feeding a free dataset/study identity or by erasing donor/biological variation. Technology remains an observation process, not biological identity.

## 8. Replacement synthetic premise

No synthetic mechanism is qualified.

The next synthetic work should identify which biological and observation mechanisms are necessary to jointly reproduce:

- corrected expression dependence;
- detection dependence;
- cell-class contribution to pooled dependence;
- abundance distribution;
- genes-detected-per-cell depth;
- correlation/topological structure;

without tuning to a single pooled correlation statistic.

Factor, substate and observer/capture mechanisms remain reopened: neither accepted nor falsified by the corrected replay.

## 9. What is GREEN now

The following pre-rehearsal mechanics gates have executed successfully:

- canonical runtime lineage established (#224);
- shared typed qualification interface established (#226);
- joined ZERO_UPDATE path established (#228);
- payload digest authentication and mandatory execution-bound V2 row/value proof (#232);
- focused ZERO_UPDATE/provenance suite: 29 passed;
- current 2K synthetic world preserves all 42 observation operators in CI (#233): 128 passed;
- corrected S174 synthetic replay executed without retuning: 146 tests, zero skipped.

## 10. What is NOT GREEN / NOT authorized

This record does not authorize:

- real-data training;
- Stage A execution;
- multimodal training;
- TEST;
- Morabito;
- 500K;
- Stage 4;
- target freeze;
- representation freeze;
- uncertainty-model freeze;
- threshold selection;
- production EMA half-life;
- mutation based on donor-bootstrap envelopes;
- selection of the 12-fold arm;
- opportunistic repair of the 353 historical Ensembl-ID remappings.

A bounded synthetic mutation rehearsal is **not authorized by this document**. If one is proposed next, it must be separately preregistered and must consume the exact frozen runtime/provenance path rather than creating a new teacher/student/EMA architecture.

## 11. Next action

The next action is to write the bounded synthetic mutation rehearsal contract before executing any mutation.

That contract must at minimum freeze:

- exact runtime head `9d00684e08ba34ef8d7b04e478b9c380cd36d537`;
- exact shared-interface head `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`;
- joined ZERO_UPDATE/provenance successor head `d3430ce6c0e878272e92b61e01822334e088d8c8`;
- exact synthetic-world lineage and 2K smoke evidence, including PR #233 head `c919d957de79a3866fdaeab3ae2ae5a0891d4859` and run `37695987219`;
- corrected S174 replay evidence `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2` and current receipt head `750cb83c8c0535cc67a70d58b62db5607bd7d01e`;
- a tiny synthetic-only mutation budget;
- a proof that exactly one intended optimizer route is used;
- a proof that EMA cannot advance unless that optimizer step is proven complete;
- pre/post parameter, optimizer-state, teacher-age and checkpoint identities;
- deterministic reload;
- no use of corrected real targets to tune the rehearsal itself.

Until such a contract is frozen prospectively, mutation remains off.

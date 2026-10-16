# JEPA chat handoff — S149 target re-adjudication, runtime reconciliation, and shared qualification interface

Date: 2026-10-06
Status: handoff / audit checkpoint only. No training or execution authority.
Primary repository: `dushyant-mishra/sea-ad-jepa-agent`
Handoff branch: `handoff/jepa-20261005-final-chat-custody-downstream-audit`
Branch head immediately before this handoff: `cfa24e06c9899554fe980abe1f4aaceebde36307`

## 1. Non-negotiable authority state

The next agent must preserve these as hard boundaries unless the user explicitly authorizes a governance change through the established process:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`
- `TARGET_WINNER=NONE_QUALIFIED`
- `REPRESENTATION_WINNER=NONE_QUALIFIED`
- `SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`
- deciding real-data numeric thresholds remain unset
- no production optimizer or EMA mutation is authorized

`main` remains the prefreeze governance base from merged PR #220 at `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`. Do not casually move or merge `main`; it is not protected.

## 2. Current project structure: three distinct lanes

There are three relevant lanes. Do not collapse them into one branch without an explicit convergence design.

### Lane A — S149-aware scientific target re-adjudication

Purpose: determine which historical target/representation families remain scientifically live after S149 showed that pooled real gene-gene detection/topology statistics can be strongly driven by study/cohort measurement composition.

This lane is not a fresh target brainstorm. It is a salvage/re-adjudication of the historical evidence base.

GitHub checkpoints:

1. `11ed7cd23dca0930ecce420c6f490c608a444e86`
   - commit message: `audit: start S149-aware target-lineage re-adjudication`
   - file: `docs/agent/JEPA_S149_AWARE_TARGET_LINEAGE_READJUDICATION_20261006_V1.md`

2. `c02b7900efbd0181cf1ee5a742294060b658cdc9`
   - commit message: `audit: reopen TD41-TD43 under S149`
   - file: `docs/agent/JEPA_S149_TD41_TD43_PRIMARY_REOPEN_20261006.md`

### Lane B — runtime safety reconciliation

Purpose: recover the safe optimizer/EMA/checkpoint mechanics from historical V64 onto the current V5 inactive mechanics surface, without reviving the old target/E2 authority graph and without enabling training.

There are currently two overlapping draft PRs that must converge rather than be merged independently:

- PR #221 — `Reconcile guarded optimizer-step mechanics onto prefreeze main`
  - branch: `reconcile/runtime-step-guard-onto-prefreeze-main-20261006`
  - current head observed in this handoff: `a87bcfea68fce44ad4b2056ac4a903b3d1f5ac2a`
  - useful because it wraps the actual `inactive_update_reference.py` surface.

- PR #222 — `Reconcile V64 runtime safety core onto prefreeze main`
  - branch: `reconcile/v64-runtime-core-onto-prefreeze-main-20261006`
  - current head observed in this handoff: `890f8800501909a8fad0564b7240bf8e8f7c069e`
  - draft body now explicitly describes the preferred mechanical invariants and remaining blockers.

Do not merge #221 and #222 as competing guards. Treat one as donor to the other or build a single successor branch after whole-branch comparison.

### Lane C — shared qualification interface

Purpose: provide one machine-enforced scientific interface for real/synthetic zero-update qualification: protocol binding, visibility, identity, support, q-safety, source/operator identity, lifecycle, oracle boundary, and provenance.

- PR #223 — `Shared qualification interface V1`
  - branch: `shared-qualification-interface-v1-20261006`
  - current head observed in this handoff: `902de2ee46f62f0dc01122aa48970843a19662f7`
  - still draft / not merge-ready.

Whole-branch audit checkpoint:

- `cfa24e06c9899554fe980abe1f4aaceebde36307`
  - commit message: `audit: checkpoint PR223 whole-branch authority findings`
  - file: `docs/agent/JEPA_SHARED_INTERFACE_WHOLE_BRANCH_AUDIT_20261006.md`

This audit closed three concrete authority defects and exposed one architectural limitation: a generic callback interface cannot prove physical no-mutation. Physical proof of no model/optimizer/GradScaler/EMA mutation must come from a bound runtime successor, not from callback payload inspection.

## 3. Scientific status after the S149 re-adjudication

S149 does not invalidate all historical RNA target evidence. It specifically weakens evidence derived from pooled measurement topology and forces within-observation-process and cross-process transport tests.

The current salvage matrix is conservative:

### Closed / should not be resurrected as if untested

- T0/T1/TCTX forward-only RNA targets dominated by gene/address identity.
- broad static/context sufficiency arguments where incremental information beyond identity/global context was inadequate.
- V6R5B donor-cross-fitted per-address residual rescue (`RESIDUAL_TARGET_DOES_NOT_RESCUE`); gains were overwhelmingly cell-global and molecular recovery remained poor.
- historical PROD41K/T1-u205 learned states/checkpoints as biological evidence; these remain forensic because mandatory tensors were gradient-dead and no target authority existed.
- synthetic T_A/T_B comparisons from PR #178 as a selector; the corrected experiment was explicitly `NOT_INFORMATIVE` because the synthetic fixture did not identify the real biological choice.

### Mechanical substrate only

- V6/V6R4 execution diagnostics.
- F1-B synthetic mechanism bridge.
- V75/V77 measurement architecture.
- contextual/F1 prefreeze producer and provenance machinery.

These can support execution/reproducibility but do not select a biological target.

### Still scientifically live under S149-aware re-testing

1. TD41–TD43-style cell-specific pair-order / excess-over-null structure.
2. value-blind query-local constructions in the PR #163 family, provided q-safety is transitive and proven.
3. program-level targets defined without pooled cohort covariance and reproduced within observation processes.
4. structured-combined targets only if they add transportable biology beyond global/operator/source information.

No target has been selected.

## 4. TD41–TD43: strongest currently reopened historical family

The primary reopen at `c02b7900...` found that S149 does **not** invalidate the core surviving TD41–TD43 signal.

Why:

- TD41 pair identities were pre-frozen; retained pairs were selected by deterministic SHA-256 address hashing, not expression/state/outcome.
- all panel endpoints were in all-42-operator common scalar support; there were zero structural support violations.
- pair-dominance was estimated using donor-balanced pair-direction means separately in HVS, NPH52, and SEA-AD, then averaged across sources equally.
- measurement reliability was reported separately inside each source rather than from one pooled-cell topology.
- in the least globally predetermined quartile, panel 0 had same-cell-over-wrong-cell excess of approximately 0.127 in HVS, 0.134 in NPH52, and 0.134 in SEA-AD; headroom-normalized excess was roughly 0.90–0.95.
- independent panels 1 and 2 reproduced positive Q1 excess in every source and both half-depth views.
- the TD43 reconstruction passed all 24 source × panel × half cases; weakest observed-minus-null-p95 margin was 0.085626 and weakest headroom-normalized excess was 0.89365.

This makes TD41–TD43 more resistant to the S149 pooled-topology confound than previously assumed.

However, the historical status remains correctly non-authorizing: reliable cell-specific RNA order information is not automatically the right JEPA biological objective.

### Immediate unresolved TD41 question

Reconstruct the genealogy of the four 512-gene TD34 panels used upstream by TD41.

This is the current highest-priority scientific audit because S149-like bias could still have entered **before** TD41 if TD34 panel membership was chosen from a pooled source-composition statistic.

Classify the TD34 panel genealogy as exactly one of:

- `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`
- `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES`
- `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`

Do not run a new TD41 outcome analysis before this genealogy is closed.

## 5. Runtime reconciliation: what is already established

The canonical inactive mechanics source is `src/sea_ad_jepa/v5/inactive_update_reference.py` on current `main`. It is explicitly a bounded CPU mechanics harness, not a live trainer.

The mechanically correct ordering to preserve is:

`backward -> unscale -> validate gradients -> guarded optimizer step -> prove completion -> authorize EMA -> EMA -> checkpoint -> deterministic reload`

Important rules already recovered from V64 history:

- gradient validation happens after unscaling and before stepping.
- the guard must execute/bind the actual optimizer mutation; caller-supplied counters or claims are not trusted evidence.
- an optimizer step must be proven complete before EMA.
- rejected, skipped, incomplete, or ambiguous optimizer state cannot authorize EMA.
- EMA is one-shot per proven optimizer step.
- direct unguarded mutation must be unreachable around the canonical consumer.
- checkpoint lineage must treat starting state A and post-update state B as distinct; B must be cryptographically/provenance-linked to A and exact reload of B must be verified.

PR #222’s current body records the open blockers before any canonical mutation boundary:

1. converge #221/#222 into one inactive/test-only consumer;
2. physically qualify the final guard against the actual PyTorch optimizer;
3. prove AMP/GradScaler skipped-step behavior cannot authorize EMA;
4. bind optimizer provenance to the configured optimizer, not only a string label;
5. prove no reachable unguarded optimizer/EMA handle around the canonical consumer;
6. qualify deterministic checkpoint completeness and interrupt/resume equivalence;
7. integrate V77 later only through that one consumer under separate bounded synthetic-mutation authority.

Do not invent a production training authority while doing this. The missing future execution-authority schema is a real blocker, not something to silently approximate.

## 6. Shared qualification interface: what the whole-branch audit found

PR #223 already fixed the following RED-first defects:

### A1 — oracle truth realization binding

The original unblind path could pair truth from synthetic realization B with frozen outputs from realization A under the same run ID. This was repaired by carrying synthetic realization identity into frozen outputs and requiring exact equality during unblinding.

### A2 — known non-authorizing scientific authority still executed callbacks

`evaluation_authorized=False` was structurally valid but the runner had failed to enforce the boolean. The runner now refuses callbacks unless scientific evaluation authority is affirmatively true.

### A3 — development/calibration partition could be promoted to prospective sealed challenge

The unblind path previously hard-coded prospective status instead of mapping the bound partition. Frozen outputs now carry challenge partition and unblinding preserves/matches the actual partition.

### Architectural RED — generic callback cannot prove physical no-mutation

A callback can mutate hidden state through a closure and return a benign payload. String/payload-key defenses cannot establish physical no-mutation.

The interface now distinguishes:

- `MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE`
- `MutationProofStatus.PROVEN_BY_BOUND_RUNTIME`

A provenance receipt cannot claim runtime-proven no-mutation without a bound runtime-successor digest.

### Remaining PR #223 audit targets

- retry/child-run lineage identity;
- oracle demotion/current-status semantics;
- q-safety transformation enforcement boundary;
- final diff and CI/path-trigger audit;
- explicit convergence contract with the runtime lane for future physical mutation proof.

Keep PR #223 draft until these close.

## 7. Critical scientific/governance concepts the next agent must preserve

### Claim ladder

Use:

`RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION`

`OBSERVED_RNA` and `RECOVERABLE_RNA_STRUCTURE` are pre-claim evidence states, not additional claim levels.

### Representation stability

Use canonical statuses:

- `STABLE_COORDINATES`
- `STABLE_SUBSPACE_ONLY`
- `UNSTABLE_REPRESENTATION`
- `INDETERMINATE__INSUFFICIENT_BIOLOGICAL_UNITS`

Stable subspace does not authorize axis semantics. Any alignment must be fit on inner TRAIN only, frozen, and then applied to held donors.

### Uncertainty separation

- `U_bio`: movement when more biological evidence/features/context are available; do not estimate this by count thinning.
- `U_measurement`: movement from depth/count realization with the biological information universe fixed; count-depth thinning belongs here.

### OOD separation

Keep biological support shift separate from measurement/operator shift.

### q-safety

The hidden query value must be absent not only from the direct input but also from normalization, library-size summaries, detected-gene summaries, support features, and any preprocessing-derived quantity. V61-style q-safe preprocessing removes q before all such summaries; downstream consumers must prove transitive safety.

### External validation language

External does not automatically mean independent. Access does not equal exposure. Same-nucleus does not mean separate-nucleus. Cells are not donors. Multimodal observational support is not causal perturbational evidence. Morabito remains protected for target selection.

## 8. Recommended takeover sequence

The next agent should proceed in this order:

1. Verify branch/PR heads before doing any work; do not assume these SHAs remain current if another agent pushed after this handoff.
2. Continue Lane A by reconstructing the TD34 four-panel genealogy from primary commits/files, not retrospective summaries.
3. Write a dated GitHub audit checkpoint with the three-way S149 genealogy classification before any new TD41 real-data outcome analysis.
4. In parallel only if lane ownership is clear, complete the remaining PR #223 whole-branch audit targets. Do not broaden #223 into runtime mutation code.
5. Reconcile PR #221 and #222 into one runtime successor design. Compare whole branches and tests first; do not merge both.
6. TDD every new runtime safety invariant RED-first, then physically test against the actual PyTorch optimizer/GradScaler path in an inactive/test-only harness.
7. Establish exact A->B checkpoint successor semantics and deterministic interrupt/resume equivalence.
8. Bind PR #223 physical mutation-proof status only to the final runtime successor digest; do not let the shared interface self-attest physical no-mutation.
9. Run whole-branch adversarial review and CI/path-trigger audit before marking any PR ready.
10. Do not merge to `main` without explicit user authorization and a final scope check showing no scientific authority was accidentally granted.

## 9. What not to do

Do not:

- start JEPA training;
- open TEST;
- use Morabito for target selection;
- authorize 500K or Stage4;
- select a target/representation/estimand from historical convenience;
- assign biological semantics to the 160D architecture width;
- resurrect identity-dominated T0/T1/TCTX targets;
- rerun V6R5B residual rescue as if unresolved;
- treat PR #178 synthetic T_A/T_B as target evidence;
- treat synthetic instrument success as biological validation;
- accept pooled topology/prediction performance as evidence without source/operator and donor-aware controls;
- let held donors influence alignment;
- use caller-supplied step counters/callback payloads as proof of physical mutation state;
- merge #221 and #222 independently;
- promote PR #223 to a runtime authority layer.

## 10. GitHub pointers

Use these as the entry points for takeover:

- merged governance base: PR #220, `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`
- runtime consumer/guard lane: PR #221
- runtime-core lane: PR #222
- shared interface lane: PR #223
- S149 overall re-adjudication: `docs/agent/JEPA_S149_AWARE_TARGET_LINEAGE_READJUDICATION_20261006_V1.md` at `11ed7cd2...`
- TD41–TD43 reopen: `docs/agent/JEPA_S149_TD41_TD43_PRIMARY_REOPEN_20261006.md` at `c02b7900...`
- shared-interface adversarial audit: `docs/agent/JEPA_SHARED_INTERFACE_WHOLE_BRANCH_AUDIT_20261006.md` at `cfa24e06...`
- this handoff: `docs/agent/JEPA_CHAT_HANDOFF_20261006_S149_RUNTIME_INTERFACE.md`

The next scientific action is TD34 panel genealogy. The next runtime action is #221/#222 convergence plus physical PyTorch/GradScaler proof. The next shared-interface action is finishing the remaining whole-branch adversarial audit and explicitly binding future physical mutation proof to the runtime successor.

# JEPA Handoff Assimilation Audit — 2026-10-06

## Scope

This note records assimilation of the chat handoff `JEPA_CHAT_HANDOFF_20261006_S149_RUNTIME_INTERFACE.md` into the active project state. The handoff was treated as an audit input, not as unquestioned authority. GitHub anchors were rechecked before adoption.

## Hard boundaries retained

The handoff's governing constraints remain controlling unless superseded by a later explicit authority change:

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
- no production optimizer or EMA update is authorized.

Current main base stated in the handoff and confirmed by the runtime PR bases remains `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.

## Three-lane architecture assimilated

The project is intentionally split into three lanes and they must not be collapsed into one authority surface:

1. S149-aware target/representation re-adjudication.
2. V5 runtime-safety reconciliation.
3. Shared real/synthetic qualification interface.

Scientific/provenance authority and physical mutation proof remain separate responsibilities.

## Scientific lane state

The handoff's immediate scientific blocker is accepted:

- Do not launch another TD41 real-RNA outcome analysis yet.
- First reconstruct the genealogy of the four TD34 512-gene panels used by TD41.
- Classify panel provenance as one of:
  - `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`
  - `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES`
  - `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`

The handoff's TD41–TD43 interpretation is retained provisionally: the pair-order/cell-specific-excess result is not automatically invalidated by S149 because TD41/TD43 used prospective hashed pair retention, common support, within-source donor-balanced estimation, separate source evaluation, and wrong-cell controls. This does not select pair-order as the JEPA target.

Closed historical families remain closed absent new primary evidence: T0/T1/TCTX identity-dominated targets, V6R5B residual rescue, historical PROD41K/T1-u205 learned states as target authority, and PR #178 synthetic T_A/T_B as target-selection evidence.

## Runtime lane verification

GitHub recheck confirms PR #221 remains open/draft at head:

`a87bcfea68fce44ad4b2056ac4a903b3d1f5ac2a`

and PR #222 remains open/draft at head:

`890f8800501909a8fad0564b7240bf8e8f7c069e`

Both still target main base `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.

Therefore the handoff's convergence requirement remains current: do not merge #221 and #222 independently. Recover one canonical inactive/test-only mutation boundary with these invariants:

`backward -> unscale -> gradient validation -> guarded optimizer step -> completion proof -> EMA authorization -> EMA -> checkpoint -> exact reload`

Outstanding runtime proof remains centered on real PyTorch optimizer binding, AMP/GradScaler skipped-step behavior, no optimizer/EMA bypass, checkpoint completeness, and deterministic interrupt/resume equivalence.

## Qualification-interface lane: handoff partially superseded

The handoff snapshot recorded PR #223 at head `902de2ee46f62f0dc01122aa48970843a19662f7`. That is stale.

GitHub recheck on 2026-10-06 showed PR #223 still open/draft and already beyond that snapshot. This lane is being changed independently, so every future cross-lane read must re-fetch its exact head rather than inheriting a stale SHA.

Its reported additional closures after the handoff snapshot include:

- retry children require distinct run identity;
- governance tests/state changes retrigger the shared-interface CI gate;
- source/operator/per-element support identity remains fail-closed;
- P0 scientific-authority scope is bound to batch data kind;
- synthetic authority cannot execute `REAL_RNA`;
- shared-interface V1 has no real-RNA execution-authorizing scope, preserving `STAGE_A_EXECUTION=OFF` mechanically.

Accordingly, those items must no longer be treated as open merely because the older handoff listed them that way.

The key architectural limitation remains unchanged and should be preserved: arbitrary callbacks cannot prove physical no-mutation. `MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE` is the correct default; `PROVEN_BY_BOUND_RUNTIME` requires provenance from the converged runtime successor. Likewise q-safety at the interface is a policy/visibility contract, not full transformation-level proof.

## Iterative S149 reconstruction checkpoint

The independent Macha/V77 audit brief has now been incorporated into the working audit. Its branch anchor was rechecked: `claude/v77-synthetic-premise-custody-20261005` remains at `8497916e5a9d9b232597ac1891b6c630d3b17931` at this checkpoint.

Primary S149 evidence was then reconstructed rather than accepted from the handoff summary.

### What is currently reproduced from committed primary evidence

Commit `3cec0c3692c9110b647532db5718eb2a4276bd2f` records the real detection-topology diagnostic. On the frozen 3,000-gene set, the pooled real row had `frac>0.3 = 0.6148` and mean degree `1843.8`; a cohort-composition null with no within-stratum dependence had `0.5463` and `1638.2`. Thus the quoted approximately 89% is simply the null/real ratio for those two measures: approximately 88.9% and 88.8%, respectively. This numerical statement is coherent.

The same diagnostic reports much lower within-stratum density (`0.0768` HVS, `0.0602` SEA-AD, `0.0312` NPH52) and explicitly notes an important caveat: the 3,000 genes were themselves chosen on pooled expression variance. Therefore the within-stratum rows are diagnostic, not a prospectively qualified replacement envelope.

Commit `fd21f649a7671dd345160e60079d0fac8d01418f` records the study/coverage-stratum cross-tabulation. For all 3,292 calibration-cache cells belonging to production donors, inferred detection-support stratum matched the population-authority study label 3,292/3,292. The committed code derives the inferred stratum from which registry source-family support set can contain the cell's detected addresses, while the comparison study label comes from the production donor/operator authority.

### Self-audit qualification on the 3,292/3,292 result

This is strong evidence that the detection-support signature is study/operator-specific. It is not independent biological validation. The registry support signature and the operator study label are separate artifacts, but both encode the same upstream measurement/source structure. The result therefore supports a measurement-process interpretation of S149; it should not be described as two independent biological measurements agreeing.

The depth alternative is weakened but not fully eliminated by the reported medians: HVS-stratum cells have median 4,427.5 detected genes, NPH52 3,717.5, SEA-AD 4,848.5. HVS is therefore not simply the shallowest group. However, a full adversarial audit still needs to inspect the stratum-inference rule and composition-null generator for additional coupled assumptions.

## S146/S147 historical-spillover checkpoint

Commit `954cee9e2a2e818b1ee712569bdd71715890853b` provides primary repair evidence for two observer defects introduced in `4e95aac4`.

- **S146:** truth source indices use `(SEA_AD, NPH52, HVS)` while registry support rows use `(HVS, NPH52, SEA_AD)`. Positional indexing therefore swapped HVS and SEA-AD structural coverage.
- **S147:** operator `structural_missing_fraction` was already registry-relative and therefore already included cohort coverage loss. Applying that keep fraction again within cohort coverage double-counted the structural gap.

The repair maps source/operator cohorts by name and computes operator attrition within cohort support as registry-relative keep divided by cohort coverage. It also writes per-element support into observer shards so consumers no longer need to infer whether a zero was measurable.

The repair commit explicitly scopes the historical spillover: every canonical V2 world already built (`fs_smoke`, `bg2_test`, `off_*`, `sup_*`, `worlds_v2`) carries defective measurement support. Their latent truth generation is not changed by S146/S147, and same-instrument twin contrasts may remain useful, but their absolute measurement structure is wrong and is superseded for calibration/realism claims.

The topology/abundance calibration experiments are not contaminated by S146/S147 in the same way because they did not apply structural support at all. That is not a clean bill of health; it is a different mismatch with real data and is one reason S149 must be audited separately.

### Repaired component rerun has not yet produced evidence

The current Macha/V77 branch head `8497916e5a9d9b232597ac1891b6c630d3b17931` adds `scripts/v77/run_v77_component_detect_reject_v2.py`. Its own commit labels it `Executor only; receipt follows`. Because this is the branch head, there is no downstream committed result receipt on this branch.

Therefore no claim that the B4/C1/C2/C3 component instrument still PASSes on repaired support is accepted yet. The executor is designed to build five fresh worlds, refuse reuse, require the repaired support-rule manifest, keep the frozen signed oracle and thresholds, and compare ON versus component-OFF twins. Those are good prospective safeguards, but execution evidence remains pending.

### Historical-spillover rule now active

No pre-S146/S147 V77 PASS or synthetic-world result is inherited as current evidence merely because it remains in repository history. The active audit will distinguish preserved history from valid current evidence, identify every consumer of the swapped/double-applied support worlds, and verify that repaired executors physically refuse those older worlds before any newer V77 PASS is trusted.

No S149 finding currently selects TD41, invalidates TD41, selects a production target, or authorizes a new real-data outcome analysis. The TD34 panel genealogy remains the immediate scientific blocker for the TD41 lane.

## Active priorities after assimilation

1. Continue adversarial S146/S147/S149 reconstruction and historical-spillover inventory until the assumptions behind S149 and repaired V77 worlds are independently satisfactory.
2. Scientific lane: reconstruct TD34 512-gene-panel genealogy from primary historical artifacts before further TD41 real-RNA outcome work.
3. Runtime lane: compare/converge PR #221 and #222 into one inactive canonical consumer and qualify the actual optimizer/GradScaler/EMA/checkpoint path.
4. Shared-interface lane: always use its current exact head; finish exact-head diff/status review and the explicit runtime-convergence contract.
5. Keep this handoff branch updated as new evidence changes any verdict.

## Non-authorizations

This assimilation does not authorize training, Stage A execution, multimodal training, 500K, Stage 4, TEST opening, Morabito target selection, target selection, representation selection, estimand selection, deciding numeric thresholds, production optimizer mutation, or production EMA mutation.

# V5 independent external-review refresh — 2026-09-13

Status: `REFRESHED_EXTERNAL_REVIEW_COMPLETE__NO_NEW_LIVE_IMPLEMENTATION_DEFECT_DEMONSTRATED__STARTUP_GOVERNANCE_REFRESHED__REAL_FULL104_EXECUTION_NEXT__NO_TRAINING_AUTHORITY`

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Canonical branch: `planning/v5-dataset-first-production-closure-20260912`

Live head observed at start of this refresh: `4ed09382d4b7e6e72dd56920c1d12254f2039cd9`

Last verified code-bearing head: `a388c773feb48ebf3fc6ce20b8782182abc1891b`

Verified CI: GitHub Actions run `34739456264`, success, `177 passed`, authority-source compilation PASS.

This review was performed as three independent viewpoints: computational biology, scientific/statistical inference, and ML/runtime engineering. The purpose was to look for a demonstrable repository defect before real FULL104 execution, not to invent missing biological constants or declare open real-data work complete.

## 1. Computational-biology review

The current V5 scientific direction remains appropriate for the heterogeneous corpus:

- dataset-first ordering is preserved: `DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`;
- source/operator/matrix/technology are treated as shortcut risks rather than free biological labels;
- the observation branch is gradient-firewalled from the biological representation in `biology_observation_adapter_v2.py`;
- same-cell technical interventions and held-out biology remain mandatory because a gradient firewall alone cannot prove absence of indirect technical leakage;
- pooled disease emergence is insufficient in a corpus where disease, source, technology, living/postmortem status and region can be correlated;
- future biological claims must survive donor/source/operator/matrix/technology/depth/support-family attacks and use within-study or matched-context emergence where estimable;
- TD57C nearest-third failure remains closed; TD59 nearest-half remains pilot evidence rather than production locality authority; TD60 remains prospective.

No repository patch can replace the still-missing authenticated real-data evidence for these claims.

## 2. Statistical/scientific review

The current fail-closed distinctions remain necessary and are preserved:

- measurement failure != biology absent;
- estimator failure != biology absent;
- representation failure != biology absent;
- technical confounding unresolved != biology absent;
- biology not demonstrated != qualified biological negative;
- decision-bearing metrics must be unconditional over the declared evaluation population;
- conditional-on-success or survivor-only summaries are diagnostics, not decision evidence.

The refreshed T0 lesson supplied during this review is consistent with, and strengthens, these V5 rules: a procedure can look specific because it rejects almost everything, bootstrap non-convergence cannot be silently conditioned away, and relaxing a failing gate post hoc is unsafe unless false-qualification control is re-demonstrated. T0 remains a separate methodology/test-rig lane and supplies no V5 biological target or numeric threshold.

Current V5 dimension authority correctly remains open. `derive_full_stream_dimension_family_v1.py` implements selection mechanics only; current-V5 FULL104 metric production, prospective Monte-Carlo/donor-resample precision authority, candidate-rule review and real execution evidence remain required. Historical replicate counts and dimensions remain non-authoritative.

## 3. ML/runtime engineering review

The active runtime/dependency chain was re-traced through:

- `production_protected_registry_authority_v1.py`;
- `preexecution_dependency_guard_v1.py`;
- `preexecution_qualification_bundle_v2.py`;
- `trainer_preexecution_contract_v4.py`;
- `atomic_checkpoint_guard_v3.py`;
- `postqualification_dependency_guard_v2.py`;
- `qualification_phase_contract_v3.py`;
- `biology_observation_adapter_v2.py`.

### Exact-48 historical-registry suspicion

A potential defect was investigated because `trainer_preexecution_contract_v2.py` still contains legacy helpers and labels for the historical six-block / 48-tensor mechanics geometry.

Result: **not a live V4 production-authority defect**.

Reason:

1. `TrainerPreexecutionAuthorityV2.validate()` validates the protected-registry digest as a SHA but does not invoke the old `validate_protected_registry()` exact-48 helper.
2. The active `TrainerPreexecutionAuthorityV4` binds the trainer registry SHA to `preexecution_dependency_closure_report.protected_registry_sha256`.
3. The production registry authority derives the protected registry from the prospectively selected model depth and freezes its digest.
4. `preexecution_dependency_guard_v1.py` binds that exact registry digest through production-GPU evidence into the dependency closure.
5. The current checkpoint guard consumes the production protected-registry authority rather than promoting the historical six-block geometry.

Therefore the exact-48 helper is legacy/supporting code and must remain non-authoritative. No functional code change was warranted without a failing reachability test.

### Current runtime verdict

No new live implementation defect was demonstrated after tracing the active V4/V3 paths. In particular:

- trainer/dependency update-geometry anti-splice binding is present;
- trainer/dependency protected-registry anti-splice binding is present;
- historical GPU evidence is supporting-only;
- production GPU qualification must bind actual production geometry;
- protected-gradient liveness, parameter motion beyond decay, both Adam moments, EMA chronology, presentation cursor and atomic checkpoint/telemetry remain required;
- postqualification power evidence must be executable, raw-output bound and independently recomputed;
- current runtime contracts still cannot themselves grant production training authority.

## 4. Demonstrated defect fixed in this refresh

The real defect found was governance/startup drift: the canonical branch's `START_HERE.md` still described the September-9 state, including stale V5 heads and an obsolete statement that branch pruning left only `main`.

This was unsafe because a new chat/external reviewer could follow the wrong authority chain even though the current handoff correctly recorded many live historical/review branches.

Fix committed during this refresh:

- `START_HERE.md` now points to `JEPA_LATEST_HANDOFF_POINTER_20260913.json`, the full-lineage/current handoff and `JEPA_LIVE_BRANCH_INVENTORY_20260913.md`;
- it names `planning/v5-dataset-first-production-closure-20260912` as the current V5 implementation ledger;
- it records the current hard boundaries;
- it states FULL104 is a recover/verify/rebind task, not default rematerialization;
- it explicitly quarantines legacy six-block/48-tensor helpers as historical/supporting APIs rather than production authority;
- it removes the false assumption that only `main` remains.

This is a governance repair only. It changes no scientific threshold, dimension, schedule, training rule or data access.

## 5. Intentionally open work — not defects to paper over

The following remain genuinely open and require authenticated real substrate/model execution or prospective scientific authority:

1. locate/hash/rebind the historical FULL104 Level-4 store;
2. require `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
3. seal `V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`;
4. prospectively freeze metric-specific Monte-Carlo/donor-resample precision authority before reading decision-bearing current-V5 rank outcomes;
5. execute real FULL104 D_shared metrics and freeze D_shared;
6. only then execute/adjudicate D_private;
7. execute/adjudicate D_obs as observation-state only;
8. derive schedule/model/EMA geometry from current data authority;
9. production-geometry CUDA qualification;
10. executable raw-output anti-cheat qualification;
11. bounded base-learning qualification;
12. lawful dataset-derived EMA teacher;
13. TD60;
14. relational student qualification;
15. integrated independent review;
16. only then any explicit production-training authority.

## 6. Hard boundaries

`training_authorized = false`

`protected_data_authorized = false`

`numeric_dimensions_authorized = false`

`td60_authorized = false`

`relational_target_activation_authorized = false`

## 7. Review conclusion

The refreshed external review does **not** justify another V5 architecture redesign before the heavy-data step. The code paths rechecked here are fail-closed in the areas investigated. The one demonstrated defect was stale startup/governance guidance, which was corrected. The next scientific blocker is real FULL104 byte/identity rebinding followed by prospectively precision-controlled full-stream metric execution.

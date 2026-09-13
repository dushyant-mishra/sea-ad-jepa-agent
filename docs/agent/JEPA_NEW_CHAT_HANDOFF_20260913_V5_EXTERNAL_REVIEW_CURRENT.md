# JEPA V5 New-Chat Handoff — External Review / Geometry Anti-Splice Repair

Date: 2026-09-13
Repository: `dushyant-mishra/sea-ad-jepa-agent`
Primary branch: `planning/v5-dataset-first-production-closure-20260912`

## 0. Read this first

Do **not** restart the project analysis from scratch. Re-fetch all live heads before making any current-state claim, because parallel work has been landing on the V5 planning branch.

The code-under-review head at the time this handoff was written was:

`0536dcb5795e5f7f6a64172bde87bf9c8f1bcde0`

Commit message:

`fix(v5): reject trainer dependency geometry authority splice`

Its parent was:

`9440d17a9a50671eac916fdf2ea69d96d4926a46`

The handoff commit itself will necessarily advance the branch. Treat `0536dcb...` as the exact code state being discussed below, then re-fetch the branch before continuing.

## 1. Current scientific / governance status

V5 remains **not training-authorized**.

Fail-closed project status remains conceptually:

`DATASET_FIRST_V5_PRODUCTION_QUALIFICATION_IN_PROGRESS__NO_TRAINING_AUTHORITY`

Hard boundaries remain closed unless a newer live authority explicitly changes them:

- production training OFF
- protected confirmation data closed
- reader oracle closed
- fresh reader validation closed
- pathology endpoint closed
- TD60 not authorized
- relational target activation not authorized
- historical T0/V20/V21 evidence cannot authorize V5 biology or V5 training

Do not weaken these boundaries to make tests pass.

## 2. Project principles that must not be violated

1. Build the architecture/statistics around the dataset, not the dataset around a convenient model.
2. Preserve protected confirmation donors.
3. `IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`.
4. Historical mechanics evidence is not current biological authority.
5. A failed estimator, loss, measurement model, transport test, runtime gate, or architecture is **not** evidence that biology is absent.
6. Loss improvement is insufficient to qualify a biological target.
7. Every authority chain must be hash-bound and fail closed against splicing of individually valid but mutually inconsistent artifacts.
8. Synthetic tests can establish mechanics, not real-data biological authority, unless their geometry/dependency relation is explicitly justified.

## 3. What triggered the current external review

The user asked for one more V5 review from the perspective of:

- a computational biologist,
- an AI/JEPA engineer,
- and a scientist reviewing inference/governance.

The intended process was adversarial and iterative: establish live baseline, try to break the authority chain, patch only demonstrated defects, then run exact-head CI.

Superpowers review/debugging discipline was invoked. Bounded repairs are allowed; architecture-changing work should still pass through explicit design approval rather than being invented ad hoc.

## 4. Important live improvements already present before the latest defect

Recent V5 work had already closed several major historical loopholes:

### 4.1 T0/V21 cannot authorize V5 updates

The active V5 runtime no longer treats the historical T0/V21 teacher or its evidence as V5 production authority. This is an important lineage separation.

### 4.2 Fixed protected-parameter-count assumptions were removed

The historical style of assuming a fixed protected set (for example the old fixed 48-tensor mechanics pattern) has been replaced by a model/data-derived protected registry bound by authority.

### 4.3 Production GPU geometry became an exact authority

GPU evidence is no longer supposed to self-declare arbitrary geometry. The production geometry is bound to an authority chain and historical GPU results are supporting-only.

These were substantive engineering improvements, not merely documentation changes.

## 5. Concrete defect found in this review

A real end-to-end authority-splice gap was identified in:

`src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`

### The defect

`TrainerPreexecutionAuthorityV4` validated:

- the trainer-side V2 mechanics authority,
- the V2 preexecution bundle,
- the dependency-closure artifact,
- the qualification horizon,
- and production-training=false semantics,

but it did **not** verify that the trainer's own:

- `authorities["update_geometry_authority_sha256"]`, and
- `protected_registry_sha256`

were the exact same authorities named by the dependency-closure report.

Therefore, two artifacts could each be individually valid yet be combined across different production geometries or protected registries.

That is a classic authority-splice vulnerability: local validity without end-to-end identity closure.

### Why this matters

For a production JEPA qualification pipeline, geometry and protected-parameter identity are part of the estimand/runtime contract. Allowing a trainer preexecution authority to consume a dependency bundle from a different valid geometry can invalidate the meaning of GPU mechanics evidence, protected-gradient evidence, update semantics, and the claimed qualification state.

## 6. Regression test that exposed the defect

The branch already contained an external-review regression test at:

`tests/test_v5_external_review_preexecution_geometry_binding_v1.py`

The newest CI before the repair was red because that test correctly demonstrated that V4 permitted a geometry/registry splice.

The parent head involved was:

`9440d17a9a50671eac916fdf2ea69d96d4926a46`

The test should be treated as a valid red test, not weakened or removed.

## 7. Repair applied

Commit:

`0536dcb5795e5f7f6a64172bde87bf9c8f1bcde0`

Message:

`fix(v5): reject trainer dependency geometry authority splice`

File changed:

`src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`

The repair added end-to-end anti-splice checks requiring:

```text
trainer authorities[update_geometry_authority_sha256]
    == dependency closure update_geometry_authority_sha256
```

and:

```text
trainer protected_registry_sha256
    == dependency closure protected_registry_sha256
```

Mismatch terminals were added:

`STOP_V5_PREEXECUTION_V4_UPDATE_GEOMETRY_AUTHORITY_MISMATCH`

`STOP_V5_PREEXECUTION_V4_PROTECTED_REGISTRY_AUTHORITY_MISMATCH`

The intent is correct: do not allow two individually-valid authority objects to be stitched together unless they bind the same exact production geometry and protected registry.

## 8. IMPORTANT: current CI is still red

GitHub Actions run:

`34739274544`

Workflow:

`V5 dataset-first production closure`

Head SHA:

`0536dcb5795e5f7f6a64172bde87bf9c8f1bcde0`

Conclusion:

`failure`

Therefore **do not describe the current branch as green or complete**.

The repair itself is conceptually correct, but its follow-up CI exposed a compatibility failure elsewhere in the existing suite/fixtures. At the time of handoff, that downstream failure had not yet been fully diagnosed and repaired.

Do not make the anti-splice checks permissive just to recover green CI.

## 9. Exact next task for the new chat

Start here:

1. Re-fetch live head of `planning/v5-dataset-first-production-closure-20260912`.
2. Read `START_HERE.md` first.
3. Inspect GitHub Actions run `34739274544` and its job logs.
4. Determine the **first actual failing test/traceback** after commit `0536dcb...`.
5. Trace the canonical schema of `preexecution_dependency_closure_report` and all fixtures/builders used by `TrainerPreexecutionAuthorityV4`.
6. Decide whether the compatibility failure is:
   - stale test fixture lacking canonical closure fields,
   - a builder that failed to propagate geometry/registry identities,
   - a mismatch in canonical key naming,
   - or a genuine design inconsistency.
7. Preserve the new anti-splice invariant.
8. Use RED -> minimal fix -> targeted GREEN -> exact-head full V5 workflow.
9. Zero promoted skips.
10. Only after CI is green, resume the computational-biology/scientific external review.

Do not speculate from this handoff about the exact failing fixture; obtain the traceback from the live run.

## 10. Files that should be inspected immediately

At minimum:

- `START_HERE.md`
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v2.py`
- `src/sea_ad_jepa/v5/preexecution_qualification_bundle_v2.py`
- `src/sea_ad_jepa/v5/preexecution_dependency_closure_v2.py`
- `tests/test_v5_external_review_preexecution_geometry_binding_v1.py`
- `.github/workflows/v5_dataset_first_production_closure.yml`

Also search every construction site of:

`TrainerPreexecutionAuthorityV4(`

and every producer/fixture of:

`preexecution_dependency_closure_report`

before changing schemas.

## 11. Continue the external review after CI repair

The original review was intentionally broader than the runtime splice bug. Once the branch is green, continue from three lenses.

### Computational-biology lens

Verify that mixed-cohort and technical-confounding protections are **executable gates**, not merely prose. In particular, review whether the active authority chain actually tests or binds appropriate evidence for:

- donor identity / donor memorization,
- source/operator/matrix/batch,
- library depth and other measurement variables,
- specimen/source differences,
- living vs postmortem context where relevant to the available dataset,
- brain region and other lawful cohort descriptors,
- sex/age/pathology variables only where authorized and estimand-appropriate,
- support-family/domain concentration,
- same-cell and shared-view leakage,
- duplicate/lookup leakage,
- technical-only predictive shortcuts,
- biology-corrupted/technology-preserved negatives,
- biology-preserved/technology-perturbed positives.

Do not invent thresholds from T0 or historical V4. If evidence is absent, mark it absent and fail closed.

### AI/JEPA engineering lens

Continue trying to splice or shortcut:

- production geometry,
- protected registry,
- target root,
- metric receipt,
- dimension-selection receipt,
- D_shared / D_private / D_obs identities,
- optimizer start authority,
- protected gradient evidence,
- Adam moment evidence,
- EMA chronology,
- checkpoint/telemetry identity,
- CUDA geometry,
- update cursor/horizon,
- AMP/autocast policy,
- duplicate or stale historical evidence.

Every authority object should be valid **and mutually bound** to the same lineage.

### Scientific-inference lens

Verify that the pipeline distinguishes:

- estimator failure,
- measurement-model failure,
- inadequate Monte Carlo precision,
- influence instability,
- failure of incremental prediction,
- failure of biological necessity,
- transport failure,
- confirmation not authorized,
- target not qualified.

Never collapse these into a claim of absent biology.

Also require operating-characteristic evidence that includes both conditional and unconditional behavior where conditioning on proper fits could bias conclusions.

## 12. FULL104 and heavy-data boundary

The full production dataset is not available in this chat environment. It is >30 GB and accessible on the user's other GPU-enabled laptop / external drive, where Claude can run heavy inference and FULL104 checks.

Do not pretend to inspect those bytes locally.

Historical FULL104 facts retained for lineage/recovery only:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators/matrices
- 8,915 Level-4 expression blocks
- 41,238 molecular addresses
- 17,186 common measured-core
- 1,400 donor x operator groups
- 1,361 groups >=3 cells

Historical physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Frozen historical hashes:

- block manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- materialization contract `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`
- materialization audit `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`
- reader-fit selection `edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b`
- selection manifest `3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e`
- metadata SQLite `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`
- feature matrix `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- multiview manifest `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`
- historical implementation fingerprint `a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`
- historical terminal manifest `8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`

Historical bytes/results must not silently become current V5 numeric or biological authority.

## 13. V5 dimension authority remains dataset-first

Do not inherit historical dimensions or counts merely because they once ran.

Current conceptual order remains:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

Not:

`MODEL -> convenient geometry -> force DATA into it`

No blind inheritance of historical rank 32, cap 4, 256/999/1000 Monte Carlo counts, old locality, or old thresholds.

D_shared / D_private / D_obs require current-V5 authority and real FULL104 evidence before scientific promotion.

## 14. T0 lessons that may inform V5 methodology but not biological authority

T0/V20/V21 is a separate lane. Useful methodological lessons include:

- qualify the measurement/estimator before interpreting a scientific failure,
- real-geometry synthetic qualification is stronger than toy mechanics,
- numeric conventions must be frozen and justified,
- estimator failure != biology absence,
- projection/repair cannot manufacture qualification,
- conclusion stability and influence concentration matter,
- loss improvement is insufficient,
- false-qualification control matters in addition to interval width,
- unconditional operating characteristics matter when selection/fit success is itself stochastic.

Do not import T0 numeric thresholds into V5.

## 15. Historical T1 AMP failure that remains relevant to mechanics design

Historical fp16 autocast backward produced exact-zero protected gradients in the old 128x8 mechanics setup. With backward autocast disabled, protected gradients and Adam moments became live and parameters moved beyond decay.

Permanent mechanics lesson:

`fp16 forward -> backward autocast disabled -> unscale -> protected-gradient gate -> optimizer step proved -> both Adam moments -> EMA`

This is mechanics guidance only, not V5 biological authority and not sufficient evidence for current production geometry.

## 16. Branch hygiene / concurrency warning

Parallel work has been landing on the same planning branch. During the external review, the branch advanced while files were being inspected.

Therefore:

- re-fetch before every write,
- never assume the handoff SHA is still HEAD,
- inspect parentage before applying a patch,
- do not overwrite parallel changes,
- do not create another divergent V5 implementation lane unless necessary,
- prefer minimal union/reconciliation over rewrites.

Historical/relevant V5 branches have included:

- `planning/v5-dataset-first-production-closure-20260912`
- `repair/v5-authority-evidence-integration-20260912`
- `repair/v5-installed-target-root-binding-20260912`
- `repair/v5-qualified-target-guard-20260911`
- `repair/v5-executable-power-authority-20260911`
- multiple `review/integrated-target-v5-repairs-*` branches

Branch names do not confer authority. Inspect live DAG/contents before reuse or cleanup.

## 17. Development discipline

For demonstrated bugs:

`RED -> minimal fix -> GREEN -> adversarial mutation -> exact-head full relevant suite -> commit`

Before architecture-changing implementation:

- inspect live design/docs,
- use the existing Superpowers design/brainstorming discipline,
- obtain explicit approval for a materially new behavior/interface,
- then write/update an implementation plan,
- execute with independently testable steps.

Do not use process discipline as an excuse to stop read-only auditing or diagnosing a failing test.

## 18. What is currently finished vs unfinished

### Finished / demonstrated

- external review identified a genuine trainer/dependency geometry + protected-registry splice vulnerability;
- a fail-closed code repair was committed at `0536dcb...`;
- current V5 lineage already contains stronger runtime separation from historical T0, dynamic protected registry authority, and production-geometry authority binding;
- training authority remains closed.

### Unfinished / immediate blocker

- CI at `0536dcb...` is red (`34739274544`);
- exact downstream compatibility failure still needs traceback-driven diagnosis;
- no claim of completed external review should be made until CI is restored and the biology/scientific authority chain is adversarially checked further;
- heavy FULL104 real-data execution still belongs on the GPU-capable machine and must return compact hash-bound receipts rather than pretending the >30GB substrate exists here.

## 19. First message recommended for the next chat

Use this as the operating instruction:

> Continue the JEPA V5 project; do not restart analysis. Connect to GitHub repository `dushyant-mishra/sea-ad-jepa-agent`, re-fetch the live head of `planning/v5-dataset-first-production-closure-20260912`, and read `START_HERE.md` first. Then read `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260913_V5_EXTERNAL_REVIEW_CURRENT.md` completely. The last code-under-review SHA in that handoff is `0536dcb5795e5f7f6a64172bde87bf9c8f1bcde0`, but do not trust it as current without re-fetching. GitHub Actions run `34739274544` is red after a correct anti-splice repair. Diagnose the first failing traceback, preserve the new geometry/protected-registry identity invariant, repair with RED->GREEN discipline, run the exact-head full V5 workflow, and then resume the three-lens computational-biology / AI-engineering / scientific-inference adversarial review. Training and protected-data authority remain OFF.

## 20. Do not lose this distinction

The current red CI means:

`IMPLEMENTATION INTEGRATION NOT YET CLOSED`

It does **not** mean:

- the anti-splice invariant is wrong,
- the biological target failed,
- FULL104 lacks signal,
- or training should be opened.

Repair the integration boundary, then continue qualification.

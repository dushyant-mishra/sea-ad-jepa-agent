# JEPA NEW-CHAT HANDOFF — V5 TARGET AUTHORITY / CARRYOVER / MASKING

Date: 2026-09-15
Status: `CURRENT_V5_TARGET_AUTHORITY_CARRYOVER_AND_MASKING_REVIEW__NO_TRAINING_AUTHORITY`

This is the current startup handoff. Historical audits are indexed separately in `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`; read that file before repeating any audit.

## Startup order
1. `START_HERE.md`
2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
3. this handoff
4. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
5. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260915_CURRENT.json` — prior Layer-2 machine-readable snapshot; current target/carryover state is in this handoff
6. `docs/agent/JEPA_WORK_LEDGER_AND_FINDINGS_20260915_CURRENT.md`
7. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260915_LAYER2_MASKING_CURRENT.md`
8. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md`
9. runtime assets, formulas/heavy-asset references, authority/supersession maps referenced by the pointer.

Always re-fetch live heads before acting.

## Governing boundaries
`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

No protected/pathology/DEV/SEALED outcomes, D_private, D_obs outcomes, TD60 or relational activation while design choices remain open.

## Live lanes observed during this handoff
- Claude Layer-2: `analysis/v5-layer2-cross-view-shortcut-claude-20260915 @ 219831b899b914984369c7a41828bf750554d1d9`.
- teacher/student/D_shared mechanics: `repair/v5-dshared-authority-v2-20260914 @ 3717c9c0a292dfcd883949d5d0bf36d263f79300`.
- canonical planning/carryover audit: `planning/v5-teacher-student-ema-canonical-20260915 @ 88c45b97b3e9a4ad3c0fd178c992f844fd58dbab`.

The planning lane is materially divergent from main. Do not merge it blindly; use exact-SHA evidence until governance reconciliation is deliberate.

## FULL104 and representation
FULL104: 4,553,407 cells; 104 donors; 42 operators; 41,238 addresses; 17,186 common-core addresses; 8,915 Level-4 blocks; SEA-AD/HVS/NPH52.

Historical FULL104 manifest root: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.

Heavy path: `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`.

Permanent normalization fact: `FULL_SOURCE_LIBRARY_EXTENDS_BEYOND_41K_LEDGER__SOURCE_DEPENDENT_OUTSIDE_LEDGER_FRACTION`.

V0=8,568 addresses; V1=8,618; disjoint union 17,186. V0 SHA `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`; V1 SHA `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`.

Visibility is strongly QC/observation-bearing. Current candidate, not frozen: `VALUE_ONLY_256`.

## Claude Layer-2 closeout — completed, pushed, do not repeat
Key results at tested linear model class:
- measurement shortcut not demonstrated; excess matched-state synergy peaks ~0.0051 at p=.25 (~1% of full-depth R2);
- corrected within-donor R2: ALL ~0.1850, HVS ~0.1906, NPH52 ~0.2646, SEA_AD ~0.2487;
- measured QC adds only ~0.003 after V0;
- 93/94 donors positive; 93.6% above 0.10;
- full-refit LODO: SEA_AD ~0.241, HVS ~0.045, NPH52 ~0.055;
- pooled context dominance is estimand-sensitive; empirical/FULL104 weighting increases molecular increment over context from ~+0.031 to ~+0.121;
- residual-over-context remains specification-only.

Permanent rules:
`NO_REAL_RESULT_FROM_THE_DISCARDED_X4_WITHIN_ESTIMATOR_IS_AUTHORITY`.
Do not call source/operator structure technical without causal support.
Do not call within-donor signal biology merely because measured QC does not explain it.

## Teacher/student/EMA mechanics already exist
The architecture exists in V4 mechanics + V5 fail-closed wrapper. Reusable: online gradients, predictor learning, exact-copy frozen EMA teacher, no teacher gradients, one EMA update per proved optimizer step, protected gradient gate and Adam-moment gates.

Historical `160 / 4 heads / 6 blocks / batch128 / microbatch8 / 4 views / .40 mask / 16 target blocks / .996 EMA` are not current V5 authority.

The unresolved problem is current authority binding, not architecture existence.

## Accidental carryover — active blocker
Known seams:
1. V5 wrapper defaults to historical V4 `production_update`.
2. optimizer guard still validates legacy target receipt schema.
3. preexecution V2 hard-codes 6 blocks / 48 tensors / historical 128x8 vocabulary.
4. checkpoint V3 fixes tensor count but still imports part of V2 vocabulary.
5. predictor target query uses online trainable gene-identity table.
6. historical defaults/seeds/visibility/registry hashes can leak into V5.
7. `z_bio` naming can overstate evidence.
8. common-core can be mistaken for biology; native support for private biology.
9. dimension-estimand authority can be mistaken for training-estimand authority.
10. D_shared 512 rank ceiling can be mistaken for model width.

Successful data-first patterns already exist in `data_contract_v2.py`, `schedule_authority_v2.py`, `proposal_policy_v1.py`, `production_protected_registry_authority_v1.py`, and current-registry checkpoint logic.

## Dataset problems -> target design
- keep heterogeneous measurement support explicit;
- unmeasured is not biological zero;
- common-core is comparability/support, not biological truth;
- native support is evidence, not automatically private biology;
- visibility stays observation/QC unless explicitly authorized;
- source/operator context is measured/gated, not blindly removed;
- scientific target p, proposal q and compute packing remain separate;
- source-specific and held-donor qualification remains mandatory;
- correlated-gene interpolation is a separate masking shortcut family;
- target address identity is a separate authority/shortcut family;
- observation/reconstruction losses need a gradient firewall;
- rare/common address coverage and evidence dose must be measured;
- hardware packing must preserve cells, masks and scientific weights exactly.

## Target-identity blocker
Inherited path: `hidden target ID -> predictor query -> JEPA gradient -> online gene-identity table -> EMA teacher -> future target`.

No hidden expression leakage is alleged. The issue is co-adaptation/identity-only predictability.

Draft spec lives on `planning/v5-teacher-target-redteam-20260915`.
Leading candidate, not frozen: fixed/separate replay-stable target-address code plus identity-only and cell-permutation controls under identical targets/masks/weights/loss geometry.

## Masking blocker
Neither historical Pearson-graph masking nor later graph-free uniform masking is current authority. Compare uniform, historical graph diagnostic, and donor/source-recurrent or cross-source-consensus hybrid masking using outcome-blind coverage/exposure metrics. Do not call pooled FULL104 covariance biological truth.

## Semantic carryover rules
`NAMES_DO_NOT_CREATE_CAUSAL_OR_BIOLOGICAL_AUTHORITY`

`COMMON_CORE_SUPPORT_IS_COMPARABILITY_NOT_BIOLOGY_AUTHORITY`

`DIMENSION_ESTIMAND_AUTHORITY != BASE_TRAINING_ESTIMAND_AUTHORITY`

`QUALIFICATION_RANK_CEILING != PRODUCTION_MODEL_WIDTH`

Prefer neutral terms (`z_primary`, `z_molecular`, `primary_state_anchor`, `observation_state`) until biology is independently established.

## EMA
EMA mechanics are reusable. Historical `.996` is not authority. Preferred prospective convention: `m_u = exp(log(0.5) * p_u / H)` using authorized presentation mass; exact unit/half-life remain open.

## Open work
1. exact current-V5 teacher target object/semantics;
2. primary representation freeze;
3. base-training estimand and scientific-weight root;
4. target-address query authority and identity-shortcut gate;
5. dependency-aware masking authority;
6. objective-aligned shortcut thresholds frozen before result inspection;
7. current-V5 preexecution successor without 6/48/128x8 carryover;
8. current-V5 receipt schema/optimizer-guard binding;
9. production rank/model geometry from protected dimension chain;
10. presentation-normalized EMA half-life;
11. HVS/NPH52 donor-transport explanation without forced invariance;
12. V3-null governance reconciliation;
13. measurement-robustness decision rule;
14. explicit production-training authorization only after all upstream roots are immutable and bound.

## Mandatory historical-context rule
Before any new audit, read `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` and classify the task as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

Do not repeat historical audits simply because the conversation changed.

# JEPA historical audits index — do not restart from zero

Date: 2026-09-15
Status: `HISTORICAL_CONTEXT_ONLY__NO_TRAINING_AUTHORITY`

Purpose: stop future chats from repeating already-settled audits or reviving superseded estimands. Before re-running an audit, identify the input, authority, implementation, or scientific question that materially changed.

Standing boundaries: `TRAINING_OFF`; `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`; `IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`.

## Historical audits and findings

### T1/C2 training-mechanics failure and repair — ALREADY AUDITED
Earlier JEPA training could appear to run while protected gradients were exactly zero. The repaired required chain is:
`FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_GRADIENT_GATE -> OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE -> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`.
EMA must not advance on a skipped optimizer step. Reuse the mechanic; rebind it to the current protected registry rather than re-auditing the historical failure.

### Stage81A3 corrected TRAIN cache — ALREADY AUDITED
`stage81a3r_corrected_real_train.zip`, SHA-256 `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`, 42 pairs / 4,726 rows / 41,238 addresses. Scope is byte-bound corrected TRAIN-cache mechanics only. `CORRECTED_TRAIN_CACHE != FULL104`.

### T0 V20 independent review — ALREADY AUDITED
Historical terminal: `PASS_T0_V20_INDEPENDENT_REVIEW`. V20 is immutable for its own scope but does not authorize current V5 training.

### T0 measurement procedure — SETTLED FAILURE STATE
Terminal: `T0_MEASUREMENT_PROCEDURE_NOT_QUALIFIED_AT_N28__BIOLOGY_UNRESOLVED`. Q_DEPTH/Q_DETECT corr ~0.9232; condition number rose ~310.6 -> ~37,671 with both; residual unique fractions ~0.087/~0.096. Do not equate failure to qualify with absence of biology.

### QID semantic audit — ALREADY AUDITED
Historical locus `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`. Intended `qid_margin = own_similarity - paired_wrong_similarity`, but production supplied matched-null student state against the true teacher. Matched-null preserved query identity. Therefore `matched-null state intervention != demonstrated paired-wrong-query intervention`. No frozen authority equating them was recovered. Do not revive this estimand error.

### F1-B optimizer/receipt guard mechanics — ALREADY AUDITED
Resident optimizer guard, receipt/root binding, schedule-cursor binding, exactly-once consumption and atomic checkpoint patterns are reusable. Current warning: current V5 guard still validates through the legacy target-receipt schema; preserve the guard pattern but build a new current-V5 receipt path.

### Dimension/D_shared authority chain — DESIGN ESTABLISHED, OUTCOME SEALED
Prospective hierarchy: `D_total = D_shared + D_private`; `D_obs` separate. Historical ranks/widths `5,96,160,224,320,512` are not production model authority. Real D_shared outcomes remain sealed until design choices are frozen. Dimension-qualification estimand must not silently become base-training estimand.

### FULL104 substrate/lineage — ALREADY RECOVERED
Population: 4,553,407 cells; 104 donors; 42 operators; 41,238 addresses; 17,186 common-core addresses; 8,915 Level-4 blocks; SEA-AD/HVS/NPH52. Historical manifest root `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`. Permanent normalization fact: `FULL_SOURCE_LIBRARY_EXTENDS_BEYOND_41K_LEDGER__SOURCE_DEPENDENT_OUTSIDE_LEDGER_FRACTION`.

### V0/V1 common-core rebuild — ALREADY AUDITED
V0 8,568 addresses; V1 8,618; disjoint union 17,186. FULL104 SHAs: V0 `3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada`; V1 `c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c`. Both halves use the same cells/operators/sources, so address splitting cannot identify cell-level operator/source effects. Do not rebuild expecting it to do so.

### Visibility ablation — ALREADY AUDITED
Visibility-only strongly predicts Q_DEPTH/Q_DETECT (V0 about 0.834/0.977), while VALUE_ONLY is materially lower. Current candidate: `VALUE_ONLY_256`. Visibility is observation/QC-bearing and must not silently re-enter the primary molecular path.

### Same-cell thinning / measurement shortcut — ALREADY AUDITED AT TESTED MODEL CLASS
Frozen p={1,.9,.75,.5,.25}; 201,149 challenged cells; 154,631 pairs. Matched-state prediction never beat clean-predictor prediction. Excess synergy ~0, .0002, .0013, .0051 at p=.9/.75/.5/.25; largest about 1% of full-depth R2. Terminal: `MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`. A later deep objective-aligned gate is still required.

### Pooled context/source/operator reconnaissance — SUPERSEDED AS POPULATION INTERPRETATION
Older donor-held-out sample: Q ~0.031; context ~0.4671; V0 ~0.4666; both ~0.4982. Correct wording was collinearity/redundancy, never “85% technical.”

### Context estimand-sensitivity — ALREADY AUDITED
Claude closeout branch `analysis/v5-layer2-cross-view-shortcut-claude-20260915 @ 219831b899b914984369c7a41828bf750554d1d9`. Molecular increment over context changed from +0.0311 unweighted to +0.1207 under empirical/FULL104 weighting. Therefore pooled context dominance is not population-level authority. Do not hard-code residual-over-context from the old unweighted result.

### Defective x4_within estimator — WITHDRAWN
Initial `x4_within.py` manufactured within-operator signal on operator-only null. Permanent rule: `NO_REAL_RESULT_FROM_THE_DISCARDED_X4_WITHIN_ESTIMATOR_IS_AUTHORITY`. Retained only under withdrawn/do-not-run provenance.

### Corrected within-group estimator — ALREADY FIXTURE-QUALIFIED
Operator-only null -> ~-0.0068; planted latent -> positive; no-shared-structure -> ~-0.002. Donor-only structure under donor-centering -> ~-0.0019; planted cell latent -> ~0.708. Do not repeat unless estimator changes.

### Within-donor/source-specific signal — ALREADY AUDITED
Corrected donor-centred cell-held-out R2: ALL ~0.1850; HVS ~0.1906; NPH52 ~0.2646; SEA_AD ~0.2487. QC adds only ~0.003 after V0. Allowed interpretation: `WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`. Do not call it biology/nontechnical truth.

### Donor recurrence — ALREADY CHARACTERIZED
Claude closeout: 93/94 donors positive; 93.6% above 0.10. The within-donor signal is not carried by a tiny subset.

### Donor generalization — ALREADY CHARACTERIZED AT LINEAR MODEL CLASS
Full-refit source-specific LODO: SEA_AD ~0.241; HVS ~0.045; NPH52 ~0.055. SEA_AD demonstrated; HVS/NPH52 not demonstrated at this model class. Non-demonstration is not absence.

### Loss-geometry proxy — SUPPORTING ONLY
Layer-normalized proxy modestly improved molecular increment/within-donor R2. Classification: `MECHANICS_ALIGNED_PROXY_ONLY`. It does not establish the actual EMA teacher target.

### Correlated-gene masking/CorrMask review — OPEN AUTHORITY, HISTORICAL REVIEW DONE
Random masking can leave correlated partners visible and enable local interpolation. Historical JEPA had Pearson-graph masking; later runtime is graph-free uniform. Do not blindly restore historical graph masking or call pooled FULL104 covariance biological. Compare uniform, historical graph, and donor/source-recurrent or cross-source-consensus hybrid masking under outcome-blind coverage/exposure metrics. Terminal: `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`.

### Residual-over-context — SPECIFICATION ONLY
`prediction = stopgrad(frozen_context_baseline) + molecular_increment`, loss against full target. Allowed label: `PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`. Current posture: `QUALIFY_FIRST__DO_NOT_HARD_CODE_RESIDUAL_BASELINE_YET`.

### Teacher/student/EMA architecture recovery — ALREADY AUDITED
Architecture exists in V4 mechanics + V5 fail-closed wrapper. Teacher exact-copy init, eval-only/no-grad, EMA only after proved step, Adam/gradient gates. Historical `160/4 heads/6 blocks/batch128/microbatch8/4 views/.40 mask/16 blocks/.996 EMA` are mechanics history only. Open issue is current V5 authority binding, not whether architecture exists.

### V5 fail-closed wrapper — ALREADY AUDITED, CARRYOVER DEFECT FOUND
Wrapper rejects legacy authority and requires explicit current config, but defaults to historical V4 `production_update`, which revalidates historical `PRODUCTION_CONFIG` and lacks current scientific-weight input. Terminal: `DO_NOT_UNLOCK_V5_BY_RECEIPT_ONLY`. Build a distinct current-V5 update path.

### Target-identity shortcut — OPEN, AUDIT SPEC DRAFTED
Inherited predictor uses `modules.online.tokenizer.gene_identity` for hidden-target queries. Potential path: target ID -> predictor gradient -> online identity table -> EMA teacher. No hidden expression leakage is alleged. Draft spec lives on `planning/v5-teacher-target-redteam-20260915`. Leading candidate: fixed/separate replay-stable target-address code plus identity-only comparators. Terminal: `TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`.

### Observation-state gradient firewall — MECHANIC REPAIRED
`biology_observation_adapter_v2.py` detaches primary state/observation features before the observation head, preventing auxiliary observation/reconstruction gradients from directly training the primary state through that route. This does not prove the primary state is biological or measurement-free.

### Accidental-carryover audit — ACTIVE
Planning lane `planning/v5-teacher-student-ema-canonical-20260915`. Known seams: V5 wrapper -> V4 production update; optimizer guard -> legacy receipt validator; preexecution V2 -> six-block/48-tensor/128x8 vocabulary; checkpoint V3 -> repaired registry count but imports part of V2 vocabulary; predictor -> shared trainable identity query; historical numeric defaults/seeds/visibility/registry hashes can leak into V5 if not rebound.

### Data-first schema audit — POSITIVE
`data_contract_v2.py`, `schedule_authority_v2.py`, `proposal_policy_v1.py`, and `production_protected_registry_authority_v1.py` separate support, target estimand, proposal, weights, schedule, packing, RNG, presentation horizon and EMA half-life without production defaults. These are the preferred basis for future current-V5 execution.

### Semantic/scope carryover audit — ACTIVE
Planning commit `88c45b97b3e9a4ad3c0fd178c992f844fd58dbab`. Rules: `NAMES_DO_NOT_CREATE_CAUSAL_OR_BIOLOGICAL_AUTHORITY`; `COMMON_CORE_SUPPORT_IS_COMPARABILITY_NOT_BIOLOGY_AUTHORITY`; `DIMENSION_ESTIMAND_AUTHORITY != BASE_TRAINING_ESTIMAND_AUTHORITY`; `QUALIFICATION_RANK_CEILING != PRODUCTION_MODEL_WIDTH`. `z_bio` labels are provisional; common-core is not biological truth; native support is not automatically private biology; 512 qualification ceiling is not model width.

### Preexecution-contract carryover — OPEN REPAIR
`trainer_preexecution_contract_v2.py` still hard-codes six blocks, 48 protected tensors, `PROTECTED_48_*`, and `HISTORICAL_128X8_CORRECTED_UPDATE_REGRESSION`. A current-V5 successor is required.

### Protected-registry/checkpoint anti-carryover — SUCCESSFUL PATTERN
`production_protected_registry_authority_v1.py` derives current tensor count from supplied model depth instead of historical 48. `atomic_checkpoint_guard_v3.py` uses that current registry. Retain this pattern.

### EMA timescale — MECHANIC SETTLED, AUTHORITY OPEN
Historical `.996` is not V5 authority. Preferred prospective convention: `m_u = exp(log(0.5) * p_u / H)` in authorized scientific presentation units. Exact unit/half-life remain open.

### Branch/governance audit — ACTIVE
Do not blindly merge/delete V5 lanes. Re-fetch heads. At 2026-09-15 the canonical planning lane and main were substantially divergent. Use docs-only governance on main and exact branch/commit references until reconciliation is deliberate.

### Runtime asset provenance — KNOWN WARNING
`operator_address_state_npz` had observed SHA beginning `001375ec...` versus historical expected `14734303...`; status `PROVENANCE_MISMATCH_DO_NOT_USE`. Heavy immutable inputs should be referenced by path/size/SHA rather than copied into handoffs.

## Do not repeat by default
Do not restart from zero: V20 review; T1/C2 zero-gradient failure; QID semantic archaeology; corrected TRAIN cache scope; visibility ablation; initial x4 defect; corrected within-donor recurrence; context estimand sensitivity; existence of teacher/student/EMA mechanics; fail-closed legacy-receipt behavior; common-core-is-not-biology rule; target-identity shortcut discovery.

## Genuinely open work
1. exact current-V5 teacher target object/semantics;
2. primary representation freeze;
3. base-training estimand and scientific-weight root;
4. target-address query authority and identity-shortcut gate;
5. dependency-aware masking authority;
6. objective-aligned shortcut thresholds frozen before results;
7. current-V5 preexecution successor without 6/48/128x8 carryover;
8. current-V5 receipt/optimizer-guard schema;
9. model/rank geometry from the protected dimension chain;
10. presentation-normalized EMA half-life;
11. HVS/NPH52 donor-transport explanation without forced invariance;
12. V3-null governance reconciliation;
13. measurement-robustness decision rule;
14. explicit production-training authorization only after all upstream roots are immutable and bound.

Future chats must classify proposed work as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION` before doing new computation.

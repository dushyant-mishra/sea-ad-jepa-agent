# V5 Teacher/Student Objective Authority — prospective draft

Date: 2026-09-15
Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`
Base evidence head: `analysis/v5-layer2-cross-view-shortcut-claude-20260915 @ 219831b899b914984369c7a41828bf750554d1d9`

This is a prospective architecture contract only. It does **not** authorize training, D_shared inspection, protected confirmation, representation change, residualization, or production masking.

Standing gates remain:

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`
- `PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`
- `MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`
- `V3_NULL_NOT_YET_FROZEN`
- `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`
- `CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`
- `SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`
- `TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

## 1. What Claude's Layer-2 closeout changes

The pushed closeout at `219831b8...` establishes, at the audited linear model class and frozen VALUE_ONLY substrate, that:

- shared measurement-state synergy is small (~1% of full-depth cross-view R2 at the worst tested thinning corner) and does **not** justify a measurement-decorrelated objective;
- within-donor cross-view molecular-view signal beyond measured `Q_DEPTH/Q_DETECT` recurs across all three sources and almost all donors;
- donor-generalizable linear cross-view signal is demonstrated in SEA_AD but not demonstrated in HVS/NPH52 at this model class;
- apparent context dominance is strongly estimand-sensitive: under the empirical/FULL104 structure the context-only R2 falls and the molecular increment rises substantially;
- the layer-normalized analysis is only a mechanics-aligned proxy because the real V5 trained teacher target is not yet defined;
- the residual-over-context construction remains specification-only and explicitly blocked on teacher and representation authority.

Therefore the next architecture step is **not** to add measurement decorrelation. The live questions are teacher target semantics, target-address identity, correlated-gene masking, context credit assignment, and scientific weighting.

## 2. Recovered current executable mechanics

### 2.1 V5 inactive update reference

`src/sea_ad_jepa/v5/inactive_update_reference.py`
blob `3dc61b629c1d4723e7df058f72c1497c4b4c6c20`

The closest current V5 objective path is explicitly an inactive mechanics harness, not a production trainer. It currently does the following:

- online/student encoder: `KeyedIPBEncoderV2Reference`;
- teacher: deep copy of online encoder, evaluation mode, gradients disabled;
- teacher view: all measured addresses for the cell;
- student view: measured support minus externally supplied hidden targets;
- predictor: inherited V4 `BlockPredictor`;
- target: block summaries gathered from teacher final gene states;
- loss: scientific-cell-weighted MSE against detached teacher block states;
- optimizer: online encoder + predictor only;
- EMA: teacher follows online parameters only after the optimizer step;
- masking is external to the harness and therefore not established here.

There is no production-active V5 teacher/student trainer under `src/sea_ad_jepa/v5/`. Thus the teacher-authority blocker is structural, not a documentation omission.

### 2.2 V5 encoder view semantics

`src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`
blob `0fd06ae0891625924761ef097b20ba6e11495cb3`

- student valid genes = `measurement_mask & ~hidden_target_mask`;
- teacher/target valid genes = `measurement_mask`;
- canonical gene identities are retained;
- stochasticity is keyed by scientific identity/view coordinates.

### 2.3 Inherited V4 target and predictor semantics

`src/sea_ad_jepa/v4/ipb_jepa.py`
blob `3bd9d601a6779818a45c437cc21fd4a64749eb6e`

Current reference inheritance:

- teacher block target = layer-normalized mean of final teacher gene states over the target block;
- predictor target query = mean target-gene identity embedding projected to model width plus a learned block mask;
- predictor query attends to visible student gene states plus the student cell state.

Historical Pearson-graph target-block sampling, the historical 0.40 mask fraction, 16 blocks, and every other V4 numeric default are historical evidence only and are **not** V5 authority.

## 3. Newly identified target-identity shortcut family

`src/sea_ad_jepa/v4/gene_tokenizer.py`
blob `0fd283136323a49b5554f2fb33d0c65ee31be576`

Each encoder token begins from a trainable gene-identity component plus a continuous value component:

`token_g = LN(identity_projection(E_id[g]) + value_encoder(x_g))`.

The current inactive V5 update calls the inherited predictor with:

`modules.online.tokenizer.gene_identity`

for **hidden target block query construction**. That embedding table is part of the online encoder and therefore part of the optimizer parameter set.

So the present candidate has a direct path:

`hidden target identity -> predictor query -> JEPA gradient -> online identity embedding -> EMA teacher identity component -> future teacher target`.

This does not prove historical exploitation. It does prove that hidden target expression is not the only hidden-target information channel and that target identity is coupled to both predictor and moving target parameters.

There is a second, broader risk even after direct parameter sharing is removed: if teacher latent targets contain a large stable address-identity component, an identity-only predictor can obtain low loss without using cell-specific molecular state.

Therefore the statement

`target identities may query the predictor`

is **not eligible to be frozen as written**.

New blocker:

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`.

## 4. Candidate invariant core that survives current review

The following mechanics are reasonable candidates for independent review, but remain unfrozen.

### 4.1 Teacher view

For cell `i` with measured support `M_i`, an EMA teacher `E_bar` receives the complete measured molecular view:

`T_i = {(g, x_ig): g in M_i}`.

Required invariants:

- no hidden-mask removal from the teacher view;
- teacher outputs are detached from online/predictor gradients;
- teacher parameters are not directly optimized;
- EMA is performed only after an accepted optimizer step;
- EMA clock remains the separately authorized scientific-presentation clock;
- source/operator/donor/Q metadata do not enter the teacher encoder unless separately authorized.

### 4.2 Student view

For an externally authorized hidden set `H_i subset M_i`:

`V_i = M_i \ H_i`.

Student encoder receives only values and identities in `V_i`.

Required invariants:

- hidden target values and hidden target tokens are absent from student encoder memory;
- visible canonical identities are retained;
- cell keys may control deterministic replay/dropout but are not learnable biological features;
- source/operator/donor/Q metadata do not enter the molecular encoder by default;
- mask generation uses only prospectively authorized outcome-blind information.

### 4.3 Direct JEPA loss geometry

For cell weights `w_i`, target blocks `b`, latent width `d`, prediction `y_hat_ibd`, and detached teacher target `zT_ibd`:

`L_direct = [sum_i w_i * mean_(b,d) (y_hat_ibd - stopgrad(zT_ibd))^2] / sum_i w_i`.

Multiple mask views may be averaged only while preserving the same scientific cell weighting. Compute packing/microbatching must be algebraically transparent.

This is a candidate **loss geometry**, not authorization of the inherited target representation or predictor query.

## 5. Teacher target semantics remain undecided

The current inherited candidate is:

`zT_ib = LN(mean_{g in B_ib} H^T_ig)`.

This must not be frozen merely because it is executable. The decision must answer:

1. Why final-layer gene states rather than another layer/head?
2. Why a mean over a target block rather than address-level targets or a different set function?
3. Why post-mean LayerNorm?
4. How much of target variance is cell-specific versus address-identity-only?
5. Can an identity-only competitor predict the target under the same scientific weighting and block geometry?
6. Does the target retain useful within-donor/cross-donor molecular state after identity-only predictability is accounted for?

Until these are answered, historical V4 target semantics remain a mechanics reference only.

## 6. Context handling after Claude's closeout

Claude's pushed specification defines the leading candidate as:

`baseline_i   = g_phi(C_i)`
`increment_i  = f_theta(V_i)`
`prediction_i = stop_gradient(baseline_i) + increment_i`
`loss         = L(prediction_i, T_i)`

with the full target left unmodified.

The correct interpretation is:

`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`

never "biology" or "nontechnical residual".

This construction is **not ready to implement** because its own pushed preconditions remain open:

- V5 teacher target semantics;
- primary representation authority;
- admissible context family, especially whether operator identity may be a training-time input;
- prospective evidence rule;
- anti-cheat protection against an overfit frozen context baseline.

One additional requirement follows from the estimand results: the context baseline must be fitted/evaluated under the same externally frozen scientific weighting as the JEPA objective. A reconnaissance-distribution context baseline cannot silently become the production baseline.

## 7. Masking remains an independent shortcut problem

The Layer-2 closeout does not resolve the local correlated-gene shortcut class.

A future outcome-blind masking audit must compare at least:

- graph-free uniform masking;
- historical graph-expanded masking as a diagnostic only;
- recurrent/consensus dependency-aware hybrid masking.

A pooled FULL104 covariance graph is not automatically safe because pooled covariance can encode cohort/source/operator composition.

Required audit outputs should include correlated-partner exposure, address coverage, mask-budget concentration, source/operator dependence, rare-address coverage, deterministic replay, and sensitivity to graph construction.

No protected downstream result may choose the structural/random mixture.

## 8. Scientific estimand remains separate

Claude's closeout demonstrates material estimand sensitivity. The production objective therefore must accept externally frozen scientific cell weights and must not choose its own estimand based on whichever weighting gives the best representation metric.

At minimum, the decision must explicitly distinguish:

- empirical/FULL104 population structure;
- source-uniform weighting;
- donor-primary/operator-balanced weighting;
- any future source-environment/worst-environment construction.

`SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN` remains open.

## 9. Required target-identity audit before predictor authority can freeze

The next non-training audit should prospectively test the target identity channel under the exact candidate target geometry.

Required comparisons:

1. **Identity-only predictor**: target address/block identity, no student molecular memory.
2. **Student-only/no-target-ID control** where mathematically definable.
3. **Decoupled fixed target-address code**: target code independent of online/teacher trainable identity embeddings.
4. **EMA-only target-address code**: no direct predictor gradient into target identity parameters, as a diagnostic rather than presumed solution.
5. **Full current inherited predictor**.

Required mechanistic checks:

- hidden-target identity embedding direct gradient path present/absent;
- target variance explained by identity-only prediction;
- incremental target prediction supplied by student molecular memory over identity-only;
- invariance to cell/order/packing/restart;
- source/operator dependence of the identity-only fraction;
- address-frequency dependence and rare-address behavior.

No architecture variant should be selected using D_shared or another protected outcome.

## 10. Anti-cheat requirements implied by the combined evidence

Before production training authorization, the eventual executable trainer must prove:

1. hidden target values/tokens do not enter student encoder or predictor memory;
2. target-address information cannot update the online encoder's target identity parameters through an unintended direct shortcut;
3. identity-only target prediction is measured and prospectively bounded under the actual target geometry;
4. teacher targets are detached and teacher gradients remain absent;
5. EMA occurs only after accepted updates using the authorized scientific clock;
6. masking blocks the prospectively selected correlated-gene shortcut family;
7. context baseline, if used, is frozen, fold-lawful, weighting-aligned, and gradient-isolated;
8. scientific weighting is externally frozen and microbatch packing cannot change it;
9. objective-aligned shortcut competitors are evaluated under the same target/loss geometry;
10. target/mask/context rules cannot be redefined in response to protected downstream results.

## 11. Ordered next work

1. Complete independent review of this teacher/student lineage and the new target-identity shortcut.
2. Freeze an **audit specification**, not an architecture choice, for target identity.
3. Decide the scientific teacher target only after identity-only versus molecular-increment behavior is prospectively measurable.
4. Run the dependency-aware masking audit separately.
5. Decide whether context remains qualification-only or becomes a frozen additive baseline.
6. Freeze the scientific training estimand.
7. Only then write a production V5 trainer matching the frozen contracts.
8. Keep training OFF through mechanics and anti-cheat qualification; production training needs a separate explicit authority action.

## 12. Terminal status

`V5_TEACHER_STUDENT_OBJECTIVE_AUTHORITY_DRAFTED_NOT_FROZEN`

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

`CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`

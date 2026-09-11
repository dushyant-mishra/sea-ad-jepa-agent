# JEPA NEW-CHAT HANDOFF — TARGET DISCOVERY → V5 INTEGRATED EXTERNAL-REVIEW STATE

Date: 2026-09-11
Status: `CURRENT_INTEGRATED_TARGET_DISCOVERY_V5_EXTERNAL_REVIEW__NO_TRAINING_AUTHORITY`

## 0. Read this first

This handoff corrects an important review-scope error in the preceding V5 review.

The previous external-review pass inspected the V5 anti-shortcut / qualification / training-path machinery in substantial detail, but it did **not** independently re-audit the entire upstream target-discovery pipeline end-to-end. That omission matters because the production system is not “V5 alone.” The relevant scientific chain is:

`raw SEA-AD substrate → discovery population/masks → target discovery → target statistical qualification and freeze → teacher-target construction → V5 student/teacher training → downstream evaluation`

Therefore the prior V5 review is useful but **not sufficient as an integrated production-readiness review**. A V5 training authorization cannot be issued until the upstream target is itself prospectively discovered, statistically qualified, frozen, provenance-bound, and shown to enter V5 without substitution or result-driven redefinition.

Current integrated verdict: **NO-GO FOR PRODUCTION TRAINING.**

This is not a recommendation to redesign V5 from scratch. The V5 architecture is worth hardening. The next work is targeted closure of the confirmed V5 issues plus a complete external audit of the target-discovery/qualification path.

---

## 1. Live branch state observed for this handoff

Re-fetch all heads before acting. The following were the live observed heads during preparation of this handoff:

- `main` = `04d91537358f5adc8973c091d4bfae4e2390bd22` before this governance update
- frozen V20: `t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`
- V21 prospective target-design lane: `t0/v21-prospective-design-20260910 @ 11e76d36ace556ac48cdd2992995e63c1e35df18`
- V5 hardening lane: `planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

V20 is immutable. Branch names do not confer scientific authority.

---

## 2. Current production population / substrate authority

The authenticated intended reader-fit production population remains:

- 4,553,407 cells
- 104 donors
- 42 operators / matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic data may be used for unit/mechanics tests only. It may not set production biology, thresholds, architecture dimensions, schedules, target definitions, or training authority.

The corrected real TRAIN cache is only:

- 42/42 corrected TRAIN counts/meta shard pairs
- 4,726 physical TRAIN rows
- 41,238 addresses
- terminal: `PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY`

It is **not** FULL104. It cannot satisfy a full-population predicate.

The historical FULL104 Phase-2 substrate authority requires:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators/matrices
- 41,238 addresses
- 8,915 Level-4 blocks
- historical manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

Current V5 expression blocker remains:

`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

Required terminal closure remains:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

The proposal-weight / affine-order / packing / restart path has separately closed for the real full reader population:

- total presentations H = 5,267,086
- terminal `PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY`
- presentation-stream SHA-256 `08a1df725b3803d049cf6a0a75811c1863b4bd0b537ed2ecaf70445380f02f74`

That closure does **not** create expression-substrate, biological-target, production-dimension, GPU, or training authority.

---

## 3. Target-discovery / T0 authority: what is actually established

### 3.1 Frozen V20

V20 remains immutable and records:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- training unauthorized

Do not mutate V20 to make later designs fit.

### 3.2 V21 prospective design

V21 at `11e76d36…` is still `DRAFT_FOR_REVIEW_NOT_FROZEN`.

The current prospective design records a broad-expression T1 target whose discovery/selection logic is AT8-supervised within the 28 discovery donors. The donor hierarchy is:

- 28 discovery donors: method / estimator / ridge / power choices
- 18 spent historical-validation donors: development/internal sensitivity only
- 12 fresh `reader_validation` donors: one single-shot T1 confirmation only after design freeze and passing power gate
- 10 `reader_oracle` donors: sealed final reserve

No fresh AT8 has been opened. No protected partition has been opened. Estimator selection has not run. The power gate has not run. V21 has not executed.

### 3.3 V21 design-level repairs already documented

The current design addresses four important prior contract problems at the prose/design level:

1. **Outer LODO / HC3 construction**
   - 28 outer models, each holding out one discovery donor;
   - inner LODO ridge selection uses only the remaining 27 donors;
   - exactly one OOF predictor is generated for each donor;
   - the 28 OOF rows are assembled once;
   - one HC3 regression is then evaluated with the frozen nuisance design;
   - expected residual df = 23 if the nuisance model contains five coefficients including the intercept.

2. **Power gate / effect-sensitivity construction**
   - 28 leave-one-donor influence refits;
   - directional disagreement fails closed as `STOP_EFFECT_DIRECTION_NOT_CONSISTENT`;
   - standardized leave-one-donor effect uses the 27-row refit, not the 28-row full fit;
   - `δ_{(-i)} = t_{(-i)} / sqrt(27)`;
   - `δ_min = min_i δ_{(-i)}` after directional consistency;
   - projection to fresh n=12 uses `t_proj = δ_min * sqrt(12)`, df=7;
   - minimum projected power threshold is 0.80 at the frozen alpha.

Important interpretation: `δ_min` is a jackknife / observed-donor sensitivity lower envelope. It must **not** be described as a formal confidence lower bound. HC3 over 28 OOF rows also does not by itself solve dependence caused by overlapping training sets; unless separately justified, treat this as a predeclared selection/gate statistic rather than formal population inference.

3. **T2 decoupling**
   - T2 inherits the frozen T1 estimator;
   - T2 cannot retroactively change T1.

4. **S0–S4 candidate family**
   - candidate family fixed to S0–S4;
   - admissibility begins inside S0's own LODO biology envelope;
   - ranking uses worst-case standardized displacement across all required retention levels/draws;
   - ties against the LODO envelope resolve toward the earliest member `S0 < S1 < S2 < S3 < S4`;
   - all 28 LODO refits are required.

### 3.4 What is NOT yet established for target discovery

The important correction in this handoff is that the target-discovery path has **not yet received a complete end-to-end external code/evidence audit** in the current review cycle.

Specifically, the following remain open until demonstrated from executable code and immutable evidence:

- exact raw-expression population and mask identities used in discovery;
- donor-level split independence and absence of cell-level pseudoreplication;
- absence of leakage from protected AT8 / fresh-validation / oracle data into candidate construction;
- normalization / variable selection / PCA / cache construction being fit only on legally available data where applicable;
- exact S0–S4 feature/candidate construction implementation;
- exact nested outer-LODO / inner-LODO implementation;
- the HC3 design matrix and nuisance-variable implementation;
- jackknife influence refits and power calculation implementation;
- prospective threshold binding before observing protected outcomes;
- negative, permutation and technical-confound controls;
- robustness across donors, retention levels, sparsity and preprocessing choices;
- donor/batch/library/depth/source/specimen confounding;
- duplicate / near-duplicate leakage across partitions;
- target measurability at the intended inference/deployment point;
- exact immutable artifact lineage from discovered target to the teacher target consumed by V5;
- proof that V5 cannot substitute, recompute, tune or redefine the target after downstream evidence is observed.

Therefore:

**S0–S4 selection remains NOT AUTHORIZED.**

**Fresh-12 `reader_validation` remains sealed.**

**Reader-oracle remains sealed.**

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

---

## 4. Correct integrated scientific question

The production question is not merely “does V5 block explicit metadata leakage?” It is:

> Can an independently discovered, donor-reproducible, technically nontrivial biological target be frozen using only authorized discovery information, and can V5 be forced to learn predictive structure for that frozen target without exploiting identity, technical nuisance, target leakage, same-cell shortcuts, partition leakage, or post hoc tuning?

Both halves must close. A perfectly anti-cheat student/teacher architecture trained against a circular, technically predictable, or leakage-derived target would still fail scientifically. Conversely, a strong target does not help if the representation/trainer can cheat.

---

## 5. V5 external review already completed at `1de20b1c…`

The V5 review remains valid for the components actually inspected, but it must now be understood as one half of the integrated review.

### 5.1 V5 verdict

`MAJOR REVISION / NO-GO FOR PRODUCTION TRAINING`

Assessment at the reviewed commit:

- scientific / dataset-first framing: strong in design;
- explicit shortcut and leakage controls: strong in design;
- representation firewall: useful and broadly correct for explicit fields, with proxy-learning reservations;
- representation-collapse controls: useful but not biology-specific proof;
- same-cell technical intervention probe: confirmed numerical edge-case defect;
- pre-execution dependency gating: strong fail-closed design;
- rejection-power qualification: not independently established because the reviewed evaluator accepts report-level assertions rather than necessarily recomputing gate outcomes from raw control evidence;
- FULL104 expression substrate: not closed;
- exact-head executed CI evidence: not demonstrated during the review;
- actual optimizer-path non-bypassability: not yet proven;
- production training: unauthorized.

Do not redesign V5 from scratch. Repair and re-review it.

---

## 6. Confirmed V5 findings requiring repair

### 6.1 Same-cell technical intervention cosine edge case

File reviewed:
`src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`

The reviewed `_cosine_rows` logic forms a denominator from the product of row norms and treats `denom == 0` as cosine similarity 1.0. A zero denominator occurs whenever **either** row has zero norm, not only when both rows are zero. Therefore asymmetric `(nonzero, zero)` and `(zero, nonzero)` pairs can be reported as perfect cosine similarity.

Required fix/test matrix:

- zero vs nonzero;
- nonzero vs zero;
- zero vs zero;
- near-zero norms;
- NaN / Inf;
- extreme scale.

The companion relative-L2 metric may catch many asymmetric-zero cases, so this was not classified as a demonstrated standalone critical bypass. It remains a real numerical defect and must be repaired.

### 6.2 Rejection-power qualification is not independently established

File reviewed:
`src/sea_ad_jepa/v5/rejection_gate_power_calibration_v3.py`

The reviewed evaluator validates report fields/booleans including concepts such as:

- `gate_rejects_invalid_control`
- `gate_accepts_valid_control`
- `used_actual_frozen_gate`
- `used_frozen_thresholds`
- `raw_artifact_sha_match`

That can become circular/self-attested evidence if the qualification layer merely verifies that a report says the true frozen gate rejected/accepted a control.

Required closure:

1. deterministically generate or load frozen positive/negative controls;
2. execute each control through the **actual frozen production gate**;
3. retain raw numerical gate outputs;
4. independently recompute the gate verdict from those outputs;
5. hash-bind code, thresholds, control artifacts, raw outputs and verdict into the receipt;
6. do not accept caller-supplied “rejected=true” as scientific authority.

### 6.3 Pre-execution contract is strong in design but must be non-bypassable

Files reviewed include:

- `src/sea_ad_jepa/v5/preexecution_dependency_guard_v1.py`
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`

The dependency guard is appropriately fail-closed and requires multiple evidence classes. Even a passing dependency set yields only `QUALIFIED_FOR_PRESPECIFIED_T1_ONLY`, not blanket production authority.

Remaining requirement: prove the real executable optimizer path cannot perform even one parameter update without a valid, current, hash-bound pre-execution receipt.

Add a deliberate bypass/attack test. It must fail **before `optimizer.step()`**.

### 6.4 Representation firewall blocks explicit columns but not learned proxies

File reviewed:
`src/sea_ad_jepa/v5/representation_firewall_v2.py`

The schema firewall explicitly forbids donor/subject/patient, specimen/sample, batch, library, dataset, row/cell IDs, target/label fields and technical-depth fields from the backbone representation interface.

This is necessary but not sufficient. Expression itself may encode donor, library, batch, source and depth structure. Required empirical donor-held-out nuisance-recovery attacks include:

- donor identity;
- library/batch;
- sequencing/depth proxies;
- source/dataset;
- specimen-related structure.

A nuisance-rich representation can be noncollapsed and can pass a schema firewall.

### 6.5 Collapse guard is one layer only

File reviewed:
`src/sea_ad_jepa/v5/representation_collapse_guard_v1.py`

Variance / total variance / effective rank / covariance participation / unique-row style controls are useful against obvious collapse. They do not prove that the surviving information is biological rather than donor/library/depth signal.

---

## 7. Required adversarial V5 attack set

Before production authorization, intentionally try to make the candidate pass while cheating. At minimum attack:

- direct identity copy;
- masked-input leakage;
- teacher/student shared-view leakage;
- constant and near-constant outputs;
- depth-only solution;
- donor encoding;
- batch/library encoding;
- dataset/source encoding;
- row/cell-index or lookup-table memorization;
- duplicate / near-duplicate cells across partitions;
- deterministic-preprocessing leakage;
- target-gene overlap that makes teacher target trivially reconstructable;
- pre-split cached-artifact leakage;
- checkpoint/threshold selection against data intended as single-shot confirmation;
- deliberately corrupted biological structure with preserved technical structure.

A decreasing loss, attractive embeddings, or mechanics pass is not sufficient evidence.

---

## 8. Target-discovery external-review checklist for the next reviewer/chat

This must be completed before treating V5 as a production-ready pipeline.

### A. Data lineage and cohort authority

Recover and verify the exact discovery inputs, row identities, donor identities, masks, tissue/region scope, expression transformation, address ledger, missingness semantics and artifact hashes. Confirm all rows belong to authorized discovery data.

### B. Experimental unit

Donor is the primary experimental unit. Confirm no statistic, CV split, p-value, confidence statement or power calculation silently treats cells as independent biological replicates.

### C. Leakage audit

Trace every preprocessing and feature-construction step. Anything estimated from multiple donors—normalization parameters where relevant, feature ranking, PCA/loadings, module construction, ridge tuning, candidate ranking—must obey the prospective split contract. Verify that no protected validation/oracle outcome can affect discovery choices.

### D. AT8/pathology semantics

The V21 broad target is intentionally AT8-supervised inside the 28 discovery donors. Verify exactly where AT8 enters, and prove it does not enter through any forbidden fresh-validation or oracle path. Distinguish target discovery from pathology-blind representation claims; do not call an AT8-supervised discovery statistic pathology-blind.

### E. Confounding / nuisance recovery

Quantify donor-level associations with age/sex/pathology and available technical covariates, but do not automatically “regress away” meaningful biology. Assess batch/library/depth/source/specimen effects and donor-by-state imbalance. Use donor-held-out nuisance-recovery attacks.

### F. Candidate family and selection

Audit exact S0–S4 construction and frozen ordering. Confirm candidate generation and ranking cannot be changed after looking at protected outcomes. Recompute the LODO biology-envelope admissibility and worst-case retention/draw criterion from raw artifacts.

### G. Nested CV correctness

For each of 28 outer folds, verify ridge/model selection sees only the other 27 donors, with inner donor-level CV. Confirm one—and only one—OOF prediction is emitted for each held-out donor.

### H. HC3 gate statistic

Audit nuisance matrix, rank, leverage and df. Confirm the 28 OOF rows are assembled before the single HC3 regression. Do not overstate HC3 as solving dependence from training overlap.

### I. Power gate

Recompute all 28 leave-one-donor influence refits, effect standardization and direction check. Confirm n=27 standardization for each jackknife refit, n=12 projection, df=7 and prospective alpha/power threshold. Ensure no arbitrary seed or hand-selected constant creates the lower envelope.

### J. Negative controls

Require permutation / label-shuffle controls, technical-only predictors, random-gene/module controls where scientifically appropriate, donor-label recovery attacks, and controls that intentionally destroy biological donor recurrence while retaining technical structure.

### K. Robustness

Check donor recurrence, retention/downsampling levels, sparsity, preprocessing sensitivity, influential donors and stability of selected target direction/magnitude. A target driven by one or two donors is not adequate merely because aggregate cell counts are large.

### L. Freeze and lineage into V5

Produce a machine-readable target receipt containing at least:

- discovery code commit SHA;
- input population/manifests and hashes;
- donor partition identities/hashes;
- expression/address ledger hashes;
- target formula and all hyperparameters;
- selected S candidate;
- ridge/model settings;
- nuisance design;
- thresholds and gate versions;
- raw OOF/jackknife evidence hashes;
- frozen output target artifact hash.

Then make V5 accept only that receipt/artifact (or an explicitly superseding reviewed receipt). V5 must not be able to recompute or substitute a target based on downstream training/validation behavior.

---

## 9. Integrated production closure order

The safest order is:

1. keep V20 immutable and fresh validation/oracle sealed;
2. externally audit executable V21 discovery/selection/power code before running S0–S4;
3. if executable review passes, execute the predeclared discovery-only selection/power procedure once;
4. freeze the complete target receipt before any protected confirmation;
5. only then open the authorized fresh-12 confirmation exactly once under the frozen contract;
6. independently review/freeze the target that is allowed to feed training;
7. repair V5 same-cell cosine and rejection-power evidence defects;
8. prove the true optimizer path is non-bypassable;
9. close FULL104 expression block + identity substrate;
10. run empirical nuisance-recovery and adversarial shortcut attacks;
11. resolve production dimensions from production data under predeclared rules;
12. run production-geometry GPU / gradient qualification;
13. complete bounded qualification and postqualification;
14. run a fresh integrated independent review on the exact frozen candidate SHA and immutable evidence bundle;
15. only then consider production training authorization.

These tasks may be engineered in parallel where they do not consume sealed data or change frozen scientific choices, but their **authority dependencies remain sequential**.

---

## 10. Historical anti-cheat context that must not be lost

Earlier JEPA student/teacher runs repeatedly found shortcuts. Low loss, attractive embedding geometry and successful mechanics are not sufficient.

Standing shortcut threats include:

- same-cell target visibility / deterministic near-copy;
- donor/batch/source/platform/pathology proxies;
- global normalization or feature selection using held-out donors;
- mask patterns leaking target identity;
- teacher/student shared cues;
- split leakage over donors/cells/genes;
- global PCA/hyperparameter contamination;
- target generation using information unavailable at inference time;
- representation collapse or low-variance solutions that fool other metrics;
- donor/library depth/sparsity memorization;
- tuning/checkpoint selection against one-shot validation;
- pre-split cache leakage;
- duplicate/near-duplicate cells;
- pseudoreplication;
- label/crosswalk leakage;
- teacher target trivially inferable from overlapping genes.

Historical C2 gradient-gate context remains relevant:

- later qualification suite reached 44 passed, 0 skipped;
- historical RTX3080 128×8 geometry produced `GATE STOPPED, rejected=48/48 (EXACT_ZERO=48)`;
- gradient health remains mandatory for the eventual production geometry.

---

## 11. Prequalification philosophy

QC/gating must be justified by measurement reliability, anti-cheat protection and statistical validity—not by whether a biologically attractive effect appears.

Do not move thresholds after seeing the result. Do not turn historical/synthetic dimensions into production constants. Do not use the 4,726-row corrected TRAIN cache to satisfy FULL104. Do not promote a workflow definition or a unit-test pass into biological authority.

---

## 12. Evidence actually inspected during the V5 review

The review inspected GitHub source/test/workflow artifacts including the following V5 components:

- `.github/workflows/v5_full_population_cheat_proofing.yml`
- `src/sea_ad_jepa/v5/representation_firewall_v2.py`
- `tests/test_representation_firewall_v2.py`
- `src/sea_ad_jepa/v5/preexecution_dependency_guard_v1.py`
- `tests/test_preexecution_dependency_guard_v1.py`
- `src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`
- `tests/test_same_cell_technical_intervention_probe_v1.py`
- `src/sea_ad_jepa/v5/representation_collapse_guard_v1.py`
- `tests/test_representation_collapse_guard_v1.py`
- `src/sea_ad_jepa/v5/rejection_gate_power_calibration_v3.py`
- `tests/test_rejection_gate_power_calibration_v3.py`
- `src/sea_ad_jepa/v5/trainer_preexecution_contract_v4.py`

The review also inspected the project authority/handoff state and the V21 prospective design document.

Important execution limitation: a local repository clone attempt from the execution container failed because the container could not resolve `github.com`. Therefore **the reviewer did not locally execute the V5 test suite**. GitHub source/tests/workflows and run/status metadata were inspected. At the reviewed V5 head, exact-head executed CI evidence was not demonstrated in that review. Do not rewrite this as “tests passed locally.”

---

## 13. Runtime assets available to the current ChatGPT project

Observed local project assets include:

- `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — `PROVENANCE_MISMATCH_DO_NOT_USE`
- `/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `/mnt/data/checkpoints.zip`
- `/mnt/data/expression.zip`
- `/mnt/data/t1_checkpoint_u0200.zip`

Historical reference hashes:

- Foundation 41K discovery expression archive SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- Foundation calibration bundle SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Historical T0 cohort references:

- `biology_evaluation_cohort.csv`: 4,540 rows; SHA-256 `d7cfbe006f6dc04bee96041fcf4ce78595b87a724f8a78d14f32a07651f268a1`
- `biology_cohort_intrinsic_labels.csv`: 4,540 rows; SHA-256 `ba50eb0a6683621fc60fd30f2126bb9fb4a609286360463a964dfb8a7b4af52b`

Use the runtime-asset authority file and hash checks before consuming any of these. Presence is not provenance.

---

## 14. Immediate next action for the new chat

Do **not** restart the science from scratch.

1. Open `START_HERE.md`.
2. Open `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Read this handoff and `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json`.
4. Re-fetch live heads for main, V20, V21 and V5.
5. Treat this handoff's correction as binding: target discovery is a required upstream part of the V5 production review.
6. Keep V20/fresh-12/oracle sealed according to governance.
7. Audit the executable target-discovery/selection/power implementation end-to-end before any S0–S4 execution.
8. In parallel, repair the two confirmed V5 defects and add non-bypassability/adversarial tests on a successor engineering branch—without claiming training authority.
9. Recover/bind the real FULL104 expression block store rather than substituting the small TRAIN cache.
10. Re-review the complete target→V5 lineage on the exact frozen candidate and evidence bundle.

### Current hard stop statements

- `TARGET_DISCOVERY_EXTERNAL_CODE_EVIDENCE_REVIEW_COMPLETE = FALSE`
- `S0_S4_SELECTION_AUTHORIZED = FALSE`
- `FRESH_READER_VALIDATION_OPEN_AUTHORIZED = FALSE`
- `READER_ORACLE_OPEN_AUTHORIZED = FALSE`
- `V5_FULL104_EXPRESSION_CLOSURE = FALSE`
- `V5_EXACT_HEAD_INTEGRATED_QUALIFICATION = FALSE`
- `V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE`

Training remains OFF.

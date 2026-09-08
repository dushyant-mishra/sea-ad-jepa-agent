# TD60 — Learned-Teacher Relational Continuity Gate

Status: `PROSPECTIVE_ONLY__WAITING_FOR_LAWFUL_SUCCESSOR_U40__NO_TRAINING_AUTHORITY`
Date: 2026-09-08

## Purpose

TD56/TD57B and TD59 establish qualified relational structure directly from the Molecular Ledger:

- TD57B: donor-recurrent, scale-free **global/unrestricted** relational ordering across two independent molecular panels and all three sources;
- TD59: donor-recurrent **nearest-half mesoscale** relational ordering across two fresh three-view panels and all three sources under the frozen p95 criterion;
- TD57C: nearest-one-third hard localization failed and remains failed.

TD60 asks whether a legally produced learned EMA teacher preserves these already-qualified relational objects in its direct 160-D `cell_state`.

TD60 is not another molecular-view search. It introduces no new locality fraction and no new winning panel selection.

## 1. Decision-bearing checkpoint eligibility

The first decision-bearing checkpoint is the **successor u40 EMA teacher**.

It must satisfy all of the following before TD60 may open any u40 latent outcome:

1. checkpoint schema exactly:
   `JEPA_HEALTHY_TEACHER_CHECKPOINT_V1`;
2. phase exactly:
   `QUALIFICATION`;
3. `schedule_cursor = global_update_step = ema_update_count = 40`;
4. zero accumulation position;
5. exact reviewed successor source/root and authority bindings;
6. exact successor-u0 materialization attestation;
7. exact u0->u40 execution-binding overlay;
8. explicit u0->u40 execution authority;
9. `PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED`;
10. the u40 checkpoint bytes and SHA-256 are frozen before TD60 evaluation;
11. no u41 or u40->u205 continuation has occurred before the TD60 decision is frozen.

The target-discovery evaluator uses the checkpoint's **EMA teacher only**.

The online encoder and predictor are not scientific substitutes for this gate.

### Explicitly ineligible

- historical u10-u205;
- any defect-inherited historical continuation checkpoint;
- any checkpoint without exact successor authority bindings;
- any checkpoint produced before the reviewed successor u0;
- any checkpoint produced after biology-dependent selection or continuation;
- any locally modified/ad-hoc model state.

## 2. Reference-only u0 arm

The exact successor-bound u0 may be evaluated with the same TD60 evaluator after the evaluator is frozen.

Its role is descriptive/reference only:

- it is not a learned state;
- it cannot PASS TD60;
- it cannot authorize a relational objective;
- it cannot be used to tune the u40 decision rule.

Historical clean u0 SHA-256
`19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`
remains a clean state source/reference only. The decision-bearing arm must use the successor-bound u40.

TD60 does **not** require u40 to exceed u0 numerically. It requires u40 itself to satisfy the prospectively frozen recurrence/null criterion. u0 is reported so a future reviewer can distinguish preservation from learning-induced change.

## 3. Evaluation population and firewalls

Use the exact frozen Target Discovery `A_NATURAL_MIXTURE` evaluation rows from the immutable 50k discovery archive.

The discovery materialization authority proves the frozen 50k sample contains zero original historical-T1 cells.

No pathology, reader-validation, reader-oracle, DEV, SEALED, external holdout, biological annotation, or outcome label may be opened.

Allowed metadata are limited to the already frozen donor/operator/stable-cell identity and technical matching fields used by TD57B/TD59.

The 50k archive remains falsification-only. TD60 cannot set production k, D, loss weight, threshold, replay cap, or training authority.

## 4. No new molecular-panel search

TD60 reuses already-qualified panels exactly.

### Global continuity arm

Reuse the exact two TD57B molecular panels, pair-coordinate construction, deterministic cell-triplet sampler, donor splits, donor×operator strata, technical matching blocks, and 64-null wrong-cell construction.

No TD57B gene/pair/triplet identity may be replaced after the u40 checkpoint exists.

### Mesoscale continuity arm

Reuse the exact two TD59 panels and all frozen TD59 mechanics:

- independent Z molecular selector;
- nearest-half locality only;
- exact X/Y panels;
- exact 2,048 Z pair coordinates;
- exact nearest-half global-row tie break;
- exact deterministic local-triplet sampler;
- exact donor splits;
- exact technical matching blocks;
- exact 64-null wrong-cell construction.

No new 50k locality fraction is allowed.

## 5. Teacher view construction

For each already-frozen X or Y panel:

1. slice only the exact 512 canonical Molecular Ledger addresses in that panel;
2. preserve the exact frozen log1p10k expression values for those addresses;
3. use the canonical address IDs as gene IDs;
4. because the panels are drawn from the exact all-42-operator common-scalar intersection, all 512 selected addresses are physically scalar-measured for every eligible operator;
5. encode the panel as a lawful measured 512-gene view;
6. do not expose any expression value outside that panel;
7. run the EMA teacher in `eval()`, under `torch.no_grad()`, with no dropout and no parameter/state mutation;
8. extract the direct 160-D `cell_state`.

No learned projection head is allowed.

The two latent views for the same cell are therefore:

`z_X(cell) in R^160`

and

`z_Y(cell) in R^160`.

## 6. Frozen latent geometry

Primary latent cell-cell distance is cosine distance on the direct 160-D cell state:

`d_V(a,b) = 1 - cosine(z_V(a), z_V(b))`

for `V in {X,Y}`.

Reason:

- the target is scale-free relational ordering;
- `cell_state` is already the canonical direct teacher representation;
- cosine requires no learned projection and no fitted scale;
- no threshold is calibrated from u0 or u40 outcomes.

Euclidean cell-state distance may be reported as a non-decision diagnostic, but it cannot rescue or overturn the frozen cosine result.

For an anchored cell triplet `(i,j,k)`:

`q_V(i;j,k) = sign(d_V(i,j) - d_V(i,k))`.

Exact ties are unresolved.

## 7. Global TD57B-on-latents arm

For every exact TD57B sampled triplet:

- keep the original TD57B anchor/comparison cell identities;
- replace fixed molecular concordance distance with the learned-teacher cosine distance computed separately in the exact X and Y molecular views;
- define:
  `q_X^latent = sign(d_X^latent(i,j)-d_X^latent(i,k))`
  and
  `q_Y^latent = sign(d_Y^latent(i,j)-d_Y^latent(i,k))`.

A triplet is observed-scorable only when both relations are resolved.

Per donor:
- pool across its frozen donor×operator strata exactly as TD57B;
- require >=20 scorable triplets;
- donor statistic = fraction with `q_X^latent = q_Y^latent`.

The exact TD57B donor splits/halves are reused.

## 8. Mesoscale TD59-on-latents arm

For every exact TD59 local triplet:

- preserve the frozen Z-derived nearest-half candidate set and triplet identity;
- do **not** re-select locality from the learned teacher;
- compute only X/Y learned-teacher cosine geometry;
- define latent X/Y triplet order exactly as in Section 7.

This prevents a learned embedding from choosing its own favorable neighborhood.

Per donor:
- use the exact TD59 structural-eligible donor set;
- require >=20 scorable local triplets;
- donor statistic = latent X/Y order agreement fraction.

The exact TD59 donor splits/halves are reused.

## 9. Matched wrong-cell latent null

For each arm, reuse the corresponding frozen TD57B or TD59 matched-null blocks and deterministic null identities.

For null `q=0..63`:

- X latent identities remain correct;
- Z selector/triplet identities remain fixed for the mesoscale arm;
- only Y latent cell identities are reassigned within the exact frozen donor×operator technical-matching block;
- null-specific Y relation and measurability are recomputed after reassignment;
- observed-Y support must not condition null support.

Every null half must independently satisfy the frozen minimum measurable-donor rule.

`null_p95 = sorted(null_values)[60]`.

## 10. PASS cases

A donor half passes iff:

1. observed median donor latent-order agreement > 0.5; and
2. observed median donor latent-order agreement > matched-null p95.

No null-max requirement is added post hoc. Null max is reported as a stronger diagnostic only.

### Global arm

Two TD57B panels × three sources × two splits × two halves:

**24 cases**.

All 24 must PASS.

### Mesoscale arm

Two TD59 panels × three sources × two splits × two halves:

**24 cases**.

All 24 must PASS.

### Full TD60

All **48/48** cases must PASS.

A mechanics/support failure is `NOT_ESTIMABLE`, never PASS.

## 11. Sequential opening

Decision-bearing u40 execution order:

1. global arm, Panel 0: HVS -> NPH52 -> SEA_AD;
2. global arm, Panel 1: HVS -> NPH52 -> SEA_AD;
3. mesoscale arm, Panel 0: HVS -> NPH52 -> SEA_AD;
4. mesoscale arm, Panel 1: HVS -> NPH52 -> SEA_AD.

Stop on the first source-panel failure.

The u40 checkpoint is immutable throughout. No training/continuation is allowed in response to intermediate TD60 outcomes.

## 12. Collapse/degeneracy telemetry

For every source × panel × view, report on direct cell states:

- finite-state fraction;
- centered variance;
- median pairwise spread;
- entropy effective rank;
- cosine-distance tie fraction;
- number of measurable donors/triplets.

No numerical collapse ratio is invented here.

Missing, nonfinite, or nonpositive geometry sufficient to make the recurrence statistic undefined is fail-closed / NOT_ESTIMABLE.

A future relational-training collapse threshold remains separately governed by
`RELATIONAL_COLLAPSE_CALIBRATION_V1`.

## 13. Required reproducibility

Before freezing a PASS terminal:

- rerun every opened source-panel from the same checkpoint and immutable inputs;
- require byte-identical result JSONs, or document and independently adjudicate any deterministic floating-point non-identity before scientific interpretation;
- bind checkpoint SHA-256, source/root, evaluator SHA-256, all input roots, and result hashes.

No biological result may alter evaluator code after its prospective freeze.

## 14. Current execution blocker

TD60 cannot execute yet because there is no lawful successor u40.

Additionally, the current Teacher/Student package contains a review-terminal integration mismatch that must be resolved before a successor execution overlay can validate:

- Claude's V3 review instructions request:
  `PASS_TEACHER_STUDENT_UNIFIED_V3_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`;
- `validate_healthy_teacher_execution_binding_overlay_v1.py` currently accepts only an independent-review terminal beginning:
  `PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW`.

No ad-hoc string substitution is allowed.

The Teacher/Student lane must explicitly reconcile this review-terminal binding under its own source/review authority before successor-u0/u40 execution. TD60 does not modify that branch.

## 15. Interpretation

### PASS

PASS establishes that the exact learned u40 EMA teacher preserves donor-recurrent relational geometry across:

- already-qualified global TD57B molecular views; and
- already-qualified TD59 nearest-half mesoscale views;

with correct-cell specificity above matched wrong-cell nulls.

This would qualify the learned teacher's direct 160-D geometry for the **next** gate: partial-evidence student relational predictability.

It would not authorize relational training.

PASS terminal:

`TD60_U40_LEARNED_TEACHER_GLOBAL_AND_MESOSCALE_RELATIONAL_CONTINUITY_SURVIVES__FREEZE_PARTIAL_EVIDENCE_STUDENT_GATE_NEXT__NO_TRAINING_AUTHORITY`

### FAIL

FAIL means the current learned teacher cannot yet be treated as a scientifically qualified relational target, even if its pointwise JEPA mechanics and optimization are healthy.

FAIL terminal:

`NO_U40_LEARNED_TEACHER_RELATIONAL_CONTINUITY__TD60_FAIL__DO_NOT_PROMOTE_RELATIONAL_SUPERVISION`

## 16. Authority boundary

TD60 does not authorize:

- successor u0 materialization;
- u1;
- u0->u40 execution;
- u40->u205 continuation;
- relational-loss integration;
- a production locality fraction;
- a relational loss weight;
- full-reader training;
- pathology;
- DEV/SEALED;
- reader-validation/oracle.

Current terminal:

`TD60_PROSPECTIVE_GATE_FROZEN_IN_DESIGN__WAITING_FOR_LAWFUL_SUCCESSOR_U40__TRAINING_UNAUTHORIZED`

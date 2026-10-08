# S174 ETL → synthetic broad-class propagation design

Date: 2026-10-08
Status: DESIGN SPECIFICATION — NON-AUTHORIZING
Base audited handoff head: `ef8612f7ece7bd6af629d25146bbfdc6f318ae77`
Design branch: `design/s174-etl-class-propagation-20261008`

## 1. Purpose

Repair one identified propagation defect between the existing real-data ETL/calibration layer and the V73/V77 synthetic truth generator: broad biological cell class is measured in TRAIN and used in corrected S174 diagnostics, but is not currently instantiated as a causal variable in synthetic truth.

The experiment is designed to answer a narrow mechanistic question:

> Does prospectively propagating pathology-blind TRAIN broad-cell-class composition into synthetic truth, through random-content class-shared biological programs while retaining within-class variation, move the corrected S174 invariant set toward the real reference jointly without breaking already-correct source/donor/operator and measurement geometry?

This design does **not** select a production JEPA target, qualify a biological representation, validate a SCENIC+/eRegulon network, authorize Stage 4, authorize real-data training, authorize additional optimizer updates, or choose a production sampling estimand.

## 2. Why this is the next experiment

The audited ETL/calibration layer already captures substantial real-data geometry: source composition, 104-donor imbalance, 42 observation operators, donor×operator support, operator-specific structural availability, depth/detection summaries, abundance/detection summaries, covariance shape, topology diagnostics, and broad-cell-class composition.

The active V73/V77 truth builders propagate most of the population and observation geometry but do not carry an explicit `broad_cell_class` field and do not condition their biological latent programs on broad class. Broad-class structure is therefore evaluated after generation rather than generating part of the covariance structure.

The corrected S174 replay makes this defect decision-relevant: corrected real T5 (within-class / pooled correlation statistic) is approximately `0.7435`, while every replayed synthetic arm is approximately `1.02–1.21`. The experiment family can alter covariance strength, counting and generic state biology, but cannot presently generate the pooled-vs-within-class contrast that T5 measures.

The required repair is therefore a propagation repair, not a new simulator architecture invented from scratch.

## 3. Historical evidence boundaries incorporated into this design

### 3.1 Target-discovery evidence

Historical TD56/TD57B/TD59 supports recurrent **relational** RNA geometry at global/mesoscale resolution. TD57C rejects deep nearest-third locality as a primary objective. None of these experiments confers production target authority.

Historical TD34 panel genealogy remains `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` under S149. This experiment must not reuse historical TD34 panel membership as if it were provenance-cleared biological content.

### 3.2 Regulatory evidence

The V52/V53–V58 audit chain does not establish a validated SCENIC+/eRegulon hierarchy. Stage75F remained `biological_regulatory_claim=NONE`; synthetic cis signatures improved but failed prospective gates; external-regulatory confirmation remained closed.

V74/Macha later improved infrastructure/provenance but still produced no qualified SCENIC+ network and no Stage-4 biological correspondence authority.

Therefore the first class-propagation experiment must preserve the existing rule:

> **real geometry, random content**

No real SCENIC+ module, Nott/E2 relationship, protected correspondence result, or historical TD34 panel is planted into synthetic biological truth.

### 3.3 Multimodal evidence

Nott/E2 is a sparse anchor rather than a universal target. NIH-CARD provides broad paired regulatory measurement, but E2 anchoring and RNA measurability share strong activity/detectability selection. Resource count is not evidence-independence count.

Consequently ATAC/SCENIC+/Nott biology is outside the causal content of this first repair. Those resources remain relevant to the later target/evidence-atlas lane, not to repairing the missing broad-class generator path.

## 4. In-scope and out-of-scope

### In scope

- Carry pathology-blind TRAIN `broad_cell_class` into synthetic truth as an explicit variable.
- Reproduce the frozen TRAIN broad-class composition under a content-bound calibration artifact.
- Add class-shared biological programs with **random gene/program content**.
- Retain continuous within-class biological variation.
- Preserve donor identity.
- Test donor×class interaction only as a separate final ablation.
- Hold the observation/counting model fixed for the primary E0–E3 comparison.
- Recompute the same corrected S174 diagnostic family.
- Preserve exact provenance and deterministic replay.

### Out of scope

- Real gene-program identities or class markers as planted content.
- SCENIC+, Nott/E2, NIH-CARD correspondence or ATAC-derived real target content.
- Pathology/cognition/disease effects.
- Morabito or sealed TEST access.
- Production target selection.
- Production representation dimension selection.
- Production sampling estimand selection.
- Production EMA selection.
- Runtime/training authority changes.
- Any post-outcome tuning of locality, effect sizes, thresholds, or program membership.

## 5. Frozen data contract

The new class-propagation input must be derived only from the same pathology-blind TRAIN metadata authority already used by the real calibration lane.

The class calibration artifact must bind at minimum:

- source calibration artifact digest;
- metadata source digest or existing authenticated identity binding;
- exact class label vocabulary;
- exact per-class counts;
- source × class counts;
- donor × class counts where available/meaningful;
- total eligible TRAIN cell count;
- missing/unknown-class count and explicit handling rule;
- deterministic class-assignment seed/rule for synthetic cells;
- producer source digest.

No biological expression outcome may be used to decide program membership after the arm definitions are frozen.

## 6. Generative architecture

The existing V73/V77 population geometry remains authoritative for source, donor, operator and donor×operator realization. Broad class is added as a biological truth variable without replacing operator identity.

The conceptual order is:

`source/donor/operator population geometry`
→ `broad_cell_class`
→ `class-shared random-content biological program`
→ `within-class continuous/state biology`
→ optional `donor×class interaction` ablation
→ existing generic biological components retained as specified
→ frozen observation/counting operator
→ observed counts

### 6.1 Broad class is not operator

Operator semantics are source-specific and sometimes class-pure, but operator is a measurement/support identity and is not promoted into a universal biological class label. Class assignment must be explicitly represented and provenance-bound.

### 6.2 Class-shared program

Each broad class receives one or more class-shared program effects. Program **content** is generated deterministically from preregistered random seeds and the lawful synthetic gene universe, not copied from real differential-expression markers, SCENIC+ modules, ATAC peaks, Nott/E2 edges, or protected outcomes.

The program mechanism must create covariance shared by members of the same class; a mere class-specific scalar library shift is insufficient because it would confound biology with depth and would not test the intended covariance mechanism.

### 6.3 Within-class biology

Within each class, cells retain continuous biological variation. The class program may shift the center/structured covariance, but cells in a class must not collapse to a deterministic block. This is required to avoid trivially forcing T5 downward by making all within-class cells equivalent.

### 6.4 Donor×class interaction

Donor×class interaction is not included in the first causal arm. It is tested only as E4 after E2/E3, because bundling it initially would make a positive result uninterpretable: we would not know whether class sharing or donor-specific class effects caused the change.

## 7. Prospective arm family

### E0 — existing generator control

Current corrected generator/observer path, unchanged. This is the replay control and establishes that the successor machinery reproduces the current result before the new mechanism is evaluated.

### E1 — class composition only

Adds explicit broad-class assignment with the frozen TRAIN composition but **no class-dependent expression program**.

Purpose: negative/mechanical control. If labels alone materially alter expression/detection metrics, class is leaking into a downstream pathway that was not intended.

### E2 — class-shared random-content program

E1 plus class-shared random-content biological programs. Existing within-cell generic latent components remain unchanged.

Purpose: isolate whether missing shared class biology explains part of the pooled/within-class mismatch.

### E3 — class-shared + within-class continuous biology

E2 plus an explicitly represented continuous within-class biological state under a frozen mechanism.

Purpose: represent the biologically plausible hierarchy `class-shared structure + continuous cell state` rather than discrete class blocks.

### E4 — donor×class interaction ablation

Adds a preregistered donor×class biological interaction to the better-specified class mechanism, without changing the observer.

Purpose: test whether the remaining mismatch plausibly requires donor-specific class biology. E4 is interpretive follow-up, not permission to keep adding mechanisms until metrics fit.

## 8. Parameter discipline

The design must not choose an effect magnitude by solving for T5 ≈ `0.7435`.

Before outcomes are computed, the implementation plan must freeze a **small finite set** of mechanistically interpretable program-strength settings or one fixed strength derived without consulting the corrected outcome values. If a small strength ladder is used, it is a mechanistic sensitivity analysis, not a winner search; all settings and multiplicity/interpretation rules must be frozen together.

Program count, program width, random seed block, loading distribution, class-effect scaling, within-class-state distribution, and any donor×class scaling must be frozen before the deciding S174 metrics are opened for the new arms.

## 9. Observation model freeze

For E0–E3, the current qualified synthetic observation/counting path is held byte-equivalent or content-digest equivalent wherever possible.

No simultaneous retuning of:

- depth model;
- count family;
- dropout/detection mechanism;
- operator support;
- structural availability;
- dynamic-range transform;
- technical latent geometry.

This isolates the biological propagation hypothesis. If the class mechanism improves T5 but abundance/depth/detection remain wrong, that is evidence for a later factorial biology × observer experiment, not permission to modify the observer in the same run.

## 10. Evaluation contract

The experiment reports the corrected real reference values as descriptive anchors and compares every synthetic arm on the same metric family. At minimum:

- expression median |r|;
- expression fraction |r| > 0.3;
- expression top-10 variance fraction;
- detection median |r|;
- detection fraction |r| > 0.3;
- detection graph mean degree;
- detection graph transitivity;
- largest-community fraction;
- T5 within-class / pooled separation statistic;
- abundance max/median-nonzero;
- top-1% count share;
- median detected genes per cell.

The corrected real points are **descriptive references**, not optimization targets.

S159 donor-bootstrap intervals remain uncertainty diagnostics and must not be converted into binary qualification intervals until the S159 issue is repaired.

## 11. Decision semantics

This design deliberately avoids a single scalar “PASS” based on T5.

The primary interpretation asks three ordered questions:

1. **Mechanism activation:** Does E1 behave like E0, and does E2/E3 materially alter class-conditioned correlation structure in the expected direction?
2. **Joint movement:** Does the class mechanism move T5 toward the corrected real reference without materially degrading the other already-tracked expression/detection/population invariants?
3. **Span/bracketing:** Across the frozen mechanistic arms/settings, is the corrected real multivariate reference better bracketed or spanned than under E0, without selecting a setting post hoc?

Possible terminal classifications should distinguish at least:

- `NO_EFFECT__CLASS_PROPAGATION_MECHANISM_NOT_EXPLANATORY`
- `PARTIAL_MECHANISTIC_SUPPORT__CLASS_STRUCTURE_MOVES_EXPECTED_INVARIANTS_BUT_MISMATCH_REMAINS`
- `TRADEOFF__T5_IMPROVES_WHILE_OTHER_INVARIANTS_DEGRADE`
- `JOINT_SPAN_IMPROVED__NEXT_FACTORIAL_DESIGN_JUSTIFIED`
- `EXECUTION_INVALID__PROVENANCE_OR_FREEZE_VIOLATION`

None of these terminals is production-target or training authority.

## 12. Negative and adversarial controls

The eventual implementation/test plan must include controls capable of detecting:

- broad-class labels added but not consumed by the truth builder;
- class program accidentally conditioned on operator rather than class;
- class composition mismatch relative to frozen calibration;
- real marker/program content accidentally entering random-content programs;
- pathology/protected metadata entering class assignment or program construction;
- E1 changing expression despite no class-dependent biological effect;
- deterministic-class collapse / loss of within-class variance;
- random seed or program membership drift across replay;
- observer/counting digest drift between E0–E3;
- donor×class effect leaking into E2/E3;
- outcome-dependent effect-size selection;
- stale S174 reference or old-universe replay;
- non-content-bound class calibration input.

## 13. Provenance and replay requirements

Each arm receipt must bind:

- base source commit;
- relevant producer source digests;
- corrected S174 universe/reference digest;
- class calibration artifact digest;
- class-assignment digest;
- random program-definition digest;
- arm configuration digest;
- observation/counting implementation/configuration digest;
- seed block;
- output metric artifact digest;
- explicit protected-data/training flags.

E0 must reproduce the current corrected baseline under the successor harness before any E1–E4 result is decision-bearing.

A fresh replay from the same frozen inputs must reproduce arm definitions and deciding metric rows deterministically within the same numerical semantics already accepted by the S174 replay lane.

## 14. Relationship to the longer-term target architecture

This experiment is **not** the target-discovery tournament.

The longer-term JEPA scientific architecture remains a separate hypothesis family:

- `Z_global(cell)`: broad recurrent RNA state;
- `Z_query(cell,q)`: query-conditioned state beyond generic identity;
- `Z_reg(cell,q)`: regulatory state where lawful paired/orthogonal evidence exists;
- `Z_response(cell,q/intervention)`: perturbational response state.

Historical TD56/TD57B/TD59 motivates scale-free global/mesoscale relational supervision, but no production target is yet qualified. Regulatory evidence must be represented with coverage and independence metadata; Nott/E2, NIH-CARD, SCENIC+ and perturbation sources cannot simply be concatenated or counted as independent support.

The S174 class-propagation repair improves the synthetic premise-testing environment used to evaluate such designs. It does not itself choose among them.

## 15. Success criteria for this design stage

The design is ready for implementation planning only if review agrees that:

1. the experiment repairs the identified ETL→truth propagation gap rather than broadening scope;
2. real class **geometry/composition** is allowed but real biological **program content** remains excluded;
3. E0–E4 isolate causal additions in a scientifically interpretable order;
4. the observer is frozen for the primary comparison;
5. T5 is not optimized in isolation;
6. S159 intervals are not promoted to qualification thresholds;
7. all historical target/regulatory boundaries remain intact;
8. no training or production authority is implied.

## 16. Governance terminal

`DESIGN_FROZEN_FOR_REVIEW__S174_ETL_TO_SYNTHETIC_BROAD_CLASS_PROPAGATION__NO_IMPLEMENTATION_OR_TRAINING_AUTHORITY`

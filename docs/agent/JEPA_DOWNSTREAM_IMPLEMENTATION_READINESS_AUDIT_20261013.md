# JEPA downstream implementation-readiness audit

**Date:** 2026-10-13  
**Terminal:** `RUNTIME_MATURE__POST_TD_ARCHITECTURE_INTEGRATION_INCOMPLETE__TRAINING_OFF`

This is the downstream counterpart to the historical decision ledger. Its purpose is to distinguish:

- machinery that already exists and should be reused;
- architecture ideas that survived historical testing;
- ideas that are now controls/negative priors rather than active tournament arms;
- integration components that still must be built after TD target qualification.

Machine mirror:

`results/target_discovery/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json`

Historical decision filter:

`docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md`

---

# 1. Canonical runtime already exists

The project does **not** need a new JEPA training engine from scratch.

Canonical runtime documentation:

`docs/agent/TEACHER_STUDENT_CANONICAL_RUNTIME_V1_20260907.md`

Canonical API/modules:

- `sea_ad_jepa.v4.teacher_student_runtime`
- `src/sea_ad_jepa/v4/teacher_student_runtime.py`
- `src/sea_ad_jepa/v4/teacher_student_checkpoint.py`
- `src/sea_ad_jepa/v4/teacher_student_movement.py`
- `src/sea_ad_jepa/v4/teacher_student_diagnostics.py`

The historical canonical runtime already integrated:

- trainable `IPBEncoder` student;
- eval/no-grad `EMATargetEncoder` teacher;
- `BlockPredictor`;
- deterministic masking/schedule chronology;
- scaled backward with autocast explicitly disabled around backward;
- `GradScaler.unscale_` before mandatory gradient gates;
- finite/nonzero mandatory backbone + predictor gradient checks;
- optimizer state-step and moment checks;
- EMA only after a proved valid optimizer update;
- exact EMA equation verification;
- restart-bound write-once checkpointing with optimizer, scaler, EMA counters, schedule cursor and RNG state;
- a biological firewall separating the trainer from protected downstream evaluators.

This is **mechanics infrastructure**, not target or training authority. Its old frozen schedule, historical u0/u205 trajectory and historical target semantics must not be inherited as new biology.

---

# 2. EMA state after historical audit

## Keep

The native timescale should remain:

**EMA half-life in successful scientific/base-cell presentations.**

Historical formula authority records:

`momentum = 2^(-m/h) = exp(log(0.5) * m / h)`

where `m` is successful presentations in the update and `h` is the presentation half-life.

This is superior to choosing a fixed per-step beta because it remains meaningful under different packing/accumulation/update geometry.

## Do not inherit

Historical fixed values `.992`, `.996`, `.99925`, `.9995`, `.9999` and schedules such as `.996 -> 1.0` are **mechanics controls/history only**. They demonstrated responsiveness/lag behavior but no production winner.

No production EMA half-life is selected.

## Future test

After target semantics and enough of the architecture are fixed, run a compact **short / intermediate / long** presentation-half-life screen. Decide with target stability, donor transport, evidence response, collapse/rank, rare preservation and teacher lag — not JEPA loss alone.

---

# 3. Teacher target-construction state

Do **not** replay old T0/T1/TCTX/V6R5B as if unresolved.

The remaining target-construction question is narrower and belongs **after TD target semantics are known**:

### A. Rich q-value-visible teacher — reference/control

Useful as an information-rich reference, but it can inject the queried scalar into contextual target construction before mixing. It is not automatically the desired biological target.

### B. Rich q-value-blind complementary teacher — active candidate

Teacher receives richer lawful complementary RNA evidence but not the queried value. This remains one of the strongest scientifically clean constructions for a query-local target.

### C. Same-evidence value-blind teacher — control

Teacher and student receive the same molecular evidence. This tests whether richer teacher evidence actually matters beyond EMA/capacity asymmetry.

### D. Whole-block-blind teacher — conditional

Relevant only if the eventual TD portfolio contains a block/program target whose semantics justify blinding the whole block.

### E. Residualized teacher — diagnostic only

Not a preferred production target. Nonlinear scalar leakage may remain, and the historical residual-target lineage did not rescue the target.

**Important:** the corrected synthetic T_A/T_B comparison was explicitly not informative for real biology. Do not use it to pick the winner.

The next lawful comparison should be a **zero optimizer / zero EMA update** target-construction screen on repaired real TRAIN evidence after TD has frozen the target semantics.

---

# 4. Teacher topology state

The active topology space is much smaller after historical reconciliation.

## Primary 1 — single rich EMA teacher

Keep as the simplest serious neural baseline.

## Primary 2 — shared EMA backbone + biologically typed heads

This is the strongest current architectural prior.

Why:

- it preserves full shared capacity;
- it supports explicit C1/C3/C2/etc failure accounting;
- the repaired-41K V44 proxy modestly favored shared multi-head over equal-evidence single teacher;
- independent/rare specialist proxy arms did not earn their additional complexity.

V44 remains only a proxy, not a neural winner.

## Conditional challenger — independent/complementary EMA teacher team

Do **not** automatically put this into every expensive tournament.

Activation rule:

> first demonstrate a prospectively defined shared-teacher interference/negative-transfer problem that materially damages already-qualified target biology.

Only then earn the independent teacher team.

## Conditional multimodal design — RNA teacher + privileged auxiliary critics

Preserve the later privileged-information insight:

- privileged ATAC/SCENIC/spatial/regulatory evidence may constrain/corroborate an RNA state;
- it must not automatically become realization-level point targets that an RNA-only student cannot identify.

This option is downstream of RNA target freeze and separate multimodal authorization.

---

# 5. Student topology state

## Primary

**One full-capacity shared student backbone + typed prediction heads.**

This is the default implementation target.

## Conditional challenger

Core + specialist students / light shared stem + specialists should be built only after a measured negative-transfer result in the shared student.

The historical rare-auxiliary and graph-auxiliary lineages do not justify default specialist capacity:

- Stage70 did not earn a benchmark lock;
- Stage71 failed the real-graph-vs-randomized-graph specificity challenge.

Those lineages remain controls/negative priors.

---

# 6. Student output semantics remain a live scientific requirement

Target and topology are not enough. Each qualified target component must be assigned a recoverability type from permitted student evidence.

Implementation must support:

1. **point / conditional mean** where the component is identifiable;
2. **state + calibrated biological uncertainty** when additional lawful evidence could materially change the inferred state;
3. **conditional distribution** when realization-level point prediction is not identifiable but a distribution is;
4. **teacher-private / critic-only** state when privileged evidence has no lawful RNA point estimator;
5. **abstention / NOT_ESTIMABLE** when support is insufficient.

A single deterministic MSE head for every target block is therefore not an acceptable universal downstream design.

---

# 7. Evidence and observation-process rules that are already project principles

Do not treat these as new architecture ideas requiring another historical audit:

- common/core-only evidence is insufficient for difficult/rare biology;
- complementary/native-support evidence must be preserved lawfully;
- evidence amount and measurement quality/depth are distinct axes;
- technology should be represented as a physical observation operator, not an unrestricted dataset identity embedding;
- donor variability is not automatically nuisance;
- rare biological novelty must not be collapsed into measurement-domain OOD;
- stable biological subspaces are more accountable than arbitrarily named rotating coordinates;
- molecular ledger / high-resolution measured state remains an escape hatch even if a global accountable state is lower dimensional.

Historical external-context notes preserving these ideas are included in the successor takeover branch as non-authoritative snapshots, while the current audit records their carry-forward status.

---

# 8. OPF / JEPA-Anything placement

OPF is **not** a target-discovery replacement.

Potential future experiment after target freeze:

- ordinary typed head;
- capacity-matched multi-head control;
- optional fixed orthogonal basis mechanism control;
- optional OPF-like factorization **inside one already-qualified biological block**.

Do not force C1/C2/C3 biological blocks to be mutually orthogonal. Geometric orthogonality is not biological independence and cannot rescue a failed biological gate.

---

# 9. Components still missing for a clean post-TD implementation

The runtime exists. The target-agnostic integration layer does not yet exist as one canonical runnable system.

## Missing A — TargetPortfolio adapter

Input: frozen TD portfolio and eligibility/support contracts.  
Output: versioned teacher/student target blocks without manual scientific code edits after seeing outcomes.

## Missing B — TeacherTargetPolicy registry

Versioned constructors for the surviving target-construction policies and controls, with exact evidence masks and q leakage rules.

## Missing C — TeacherTopology registry

One interface for:

- single rich teacher;
- shared typed-head teacher;
- conditional independent teacher team.

## Missing D — Student output semantics registry

Typed heads for point/mean, uncertainty/distributional and abstention semantics plus target eligibility masks.

## Missing E — loss / non-compensation ledger

Optimization may combine losses, but authority/evaluation must retain block-specific results. A strong shared-state block cannot compensate for destroyed query specificity, rare biology, relational state or transfer.

## Missing F — matched-compute tournament controller

Bind at minimum:

- trainable parameter budget where feasible;
- teacher/student FLOPs;
- cell presentations;
- evidence/mask budgets;
- optimizer updates;
- evaluation exposures;
- hardware/runtime provenance.

## Missing G — architecture evaluator

Reuse the project’s already-earned biological gates:

- held donor;
- held source/operator/technology where lawful;
- query specificity and wrong-q controls;
- rare preservation;
- relational preservation;
- evidence-response vs depth-response;
- support / not-estimable behavior;
- subspace stability and representation-health telemetry.

## Missing H — one-command synthetic rehearsal

Known-truth synthetic target package -> target portfolio -> teacher/student constructor -> canonical runtime -> EMA/checkpoint -> evaluation receipt.

This rehearsal is still **not real training authority**. It exists to prove that the final integration path behaves correctly before touching real training.

---

# 10. Dependency on the current TD synthetic qualification

Current audited successor chain:

- TD PR #320 @ `1f474a44a6baabc667dbfda726e0755426c732e7`;
- synthetic PR #321 @ `15f519c00137d581e25232c16be52c2b9badd83e`;
- package `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`;
- pre-fit archive `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`;
- certification receipt `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`;
- terminal `READY_TO_EXECUTE_BLIND_FIT`.

Next lawful sequence:

1. independent phase-1 blinded fit;
2. durable V4 blinded receipt + SHA;
3. STOP;
4. independent receipt audit;
5. only then separate controller-adjudication authorization.

The downstream architecture harness can be engineered prospectively, but it must not smuggle target choice or training authority around this gate.

---

# 11. Recommended implementation order after TD science is ready

1. implement `TargetPortfolio` + eligibility/support schema;
2. implement zero-update `TeacherTargetPolicy` registry and controls;
3. run target-construction screen;
4. implement single-rich and shared-typed teacher topologies on the canonical runtime;
5. implement shared full-capacity typed-head student;
6. implement typed output/recoverability semantics;
7. implement matched-compute tournament/evaluator;
8. choose production EMA half-life only within that frozen enough system;
9. add independent teachers only if shared-teacher interference is demonstrated;
10. add internal OPF/factorization only as a late capacity-allocation challenger;
11. add privileged multimodal critics only after RNA target freeze and separate authorization.

---

# Authority boundary

This audit is implementation/navigation authority only. It does not select a target, teacher, student, EMA half-life or factorization method and does not authorize TD60, Stage4, multimodal training or JEPA training.

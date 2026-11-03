# Macha review of #526 and the reuse-first synthetic evaluation matrix — 2026-11-03

**Reviewed head:** #526 at `0e1c539a8fa5aa2f5e117b6224b535980ed728cb`. This review is append-only, and nothing in #526 is changed. No world was regenerated with new parameters, no model was fitted, and no truth was modified.

**Verdict on #526:**

| Question | Verdict |
|---|---|
| Arithmetic and replication | **REPLICATED** |
| Software (panel-target construction) | **ACCEPT_SCOPED** |
| Scientific interpretation | **CORRECTION_REQUIRED.** The per-source pattern is an artifact of how PR #328 encodes support, not evidence about measurability. |

## 1. Independent replication
`scripts/v79/macha_independent_replicate_526_v1.py` rebuilds PR #328's world and fit view from the frozen seeds (20261013, 20261014). It does not import #526's diagnostic. It checks both receipt hashes and then counts with its own code.
- The generator, fit view, observation operator, rare generator and receipt are byte-identical to PR #328 head `25bbdbe1`.
- World SHA `dedd53c3…` and fit SHA `fc5fa5c0…` both match receipt V2.

| Synthetic source | Cells | Panel genes structurally unmeasured | All 9 measured | Estimable (denominator > 0) |
|---|---:|---|---:|---:|
| HVS-like | 180 | 1, 8 | 0 | **0** |
| NPH52-like | 150 | none | 150 | **149** |
| SEA-AD-like | 150 | 7 | 0 | **0** |

These match GPT's published aggregates exactly. The local run used Windows with numpy 2.4.6; the CI run is listed in the PR. The q-scalar invariance and NaN abstention in #526's construction are correct, and the software result stands.

## 2. Why the per-source pattern says nothing about measurability
**How PR #328 decides support.** The fit view sets structural support as `support = VISIBILITY > 0`, tiled by gene position (`unified_synthetic_fit_view_v1.py:78-81`).
- `VISIBILITY` is documented as "detection fractions measured in the authenticated 665-cell TRAIN microglia subset" (`v79_rare_biology_generator_v1.py:12-17`). The denominators are HVS 128, NPH52 304 and SEA-AD 233.
- So a gene with **zero detected cells among 128 HVS microglia** becomes **structurally unmeasured** for every HVS-like cell.
- That breaks the project invariant `MEASURED_SCALAR != STRUCTURALLY_UNMEASURED`: a measured zero remains measured evidence.
- The original rare generator used the same vector correctly, as a detection probability: `binomial(vis + 0.25·R)` lets a vis = 0 gene be detected in program-active cells. PR #328's fit view changed that meaning.

**Resulting geometry:**
- **Simulated:** HVS-like measures **60.4%** of the 48 genes, SEA-AD-like **81.3%**, NPH52-like **100%**. Only 26 genes are measured in all three.
- **Real:** HVS deposits a fixed 18,736-gene matrix for every cell, and SEA-AD a fixed feature set per matrix. **NPH52** is the real source with per-cell-type feature sets, which is where genuine structural absence lives.

**The simulated geometry is the reverse of the real one.**

**The outcome was knowable from the constants.** #526's own note says the visibility code was inspected before the panel was fixed. HVS indices 1 and 8, and SEA-AD index 7, are exactly the zeros of `VISIBILITY`. The diagnostic therefore adds no information beyond reading those constants.

**Do not use the result to:**
- prefer NPH52-like sources;
- design source-specific teacher support;
- reason about real estimability.

**Decision needed (owner and controller), before any #328-based learning test:** whether #328's observation semantics should be corrected in a **new, prospectively frozen, versioned world**, with structural support taken from per-source feature-set tables and detection kept probabilistic. Editing V2 is not an option. This is an observation-semantics correction, decided before any result exists. It is not tuning toward JEPA success.

## 3. Reuse-first scientific evaluation matrix
The facts come from a read-only helper (citations in its report); I spot-checked three of them myself: the #325 conflict, the #328 single operator, and the #321 receipt `53820343`.

**V79 Q00–Q11 (#325)**
- **Mechanism and truth:** two-part per-gene model (detection logit plus lognormal positive; depth, class, source, donor). 12 worlds × 44 genes, truth planted by Latin hypercube; truth tree sealed until 13 authentication steps.
- **Observation:** continuous lognormal positives (integer discretization untested). 5 of 44 genes per world structurally absent. 42 matrices; Q10 and Q11 use the exact S174 design (4,726 cells, 149 donors).
- **Controls:** component-absent nulls Q04–Q07; stress worlds Q01, Q02 and Q08–Q11; operator offset in Q11. **No technical twin, no wrong-query control, no relational or rare truth.**
- **Done and adjudicated:** one scoring run, 1,056 fits (1,053 complete, 3 NOT_DIAGNOSED in Q08), 291/292 gates. Hard FAIL on gate 206, `Q08_SPARSE_DETECTION / positive / CONVERGENCE_ALL_FITS_DIAGNOSED`. Terminal **`V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`**, preserved.
- **Missing comparison that could change a decision:** resolve, in advance, the conflict between the **207 confirmatory rows** and V80's **all-291 non-regression rule** (#325, 6160809564). Then run one frozen successor estimator, once, on V79 plus V80. Until then, "no successor-estimator run may proceed".

**V80 (#348)**
- **Mechanism and truth:** its own two-source generator: 8 families × 24 genes, 24 donors × 80 cells. Truth sits in a controller transport (`24120a8c…`).
- **Observation:** detection plus lognormal positives; support mask thinned to 0.55 in SP04; no real-like sources or operator.
- **Controls:** SP05 and SP06 not estimable by construction (they test abstention); donor imbalance, source shift, support thinning, new donor. **No null world, no twin, no wrong-query control.**
- **Done and adjudicated:** package, custody and adjudication mechanics QUALIFIED (workflow 38504094639; adjudicator tested with oracle estimates). **No estimator qualified** (`PROSPECTIVE__NO_ESTIMATOR_RUN`).
- **Missing comparison:** as V79.

**#318 → #319/#321 (relational)**
- **Mechanism and truth:** nine relational challenges (broad, fine, rare island, multi-island, donor-restricted, source stress, twin, null, underpowered). Controller truth is excluded from the fit.
- **Observation:** V2.1 delivers 512-feature Z/X/Y observations with masks, 6 donors × 35 cells, one operator per challenge.
- **Controls:** technical-twin negative, null negative, underpowered (correct answer is NOT_ESTIMABLE), source-visibility counterfactual. V2.1 adds donor-, depth- and source-matched, wrong-cell and pseudo-rare controls. **No wrong-query control.**
- **Done and adjudicated:** phase 2 emitted **QUALIFIED**: gate `R_RELATIONAL_SUCCESSOR_TEST_OF_TEST_V2`, candidate `C2_RELATIONAL_SHARED`, scope `TEST_QUALIFICATION_ONLY`, receipt `53820343…`.
- **Missing comparison:** **the independent audit of receipt `53820343` has no recorded verdict** (branch `audit/td-phase2-independent-20261013`, `b92f335b`). This is cheap and decides whether the C2 relational test can be used.

**#328 (unified world)**
- **Mechanism and truth:** 480 cells × 48 genes × 16 donors. Rare regimes are stress presets; context niches; perturbation arms with a matched perturb-null; controller C1–C6 summaries, with C3 at query address 0.
- **Observation:** integer RNA counts and continuous ATAC; context true/shuffled/distant; single operator `RNA_V79_PR311`; **support = VISIBILITY > 0, the measured-zero conflation above**; no library-size field.
- **Controls:** perturbation control, active and matched null; shuffled and distant context; pseudo-rarity at 0.05; same- versus separate-nucleus. **No null world, no operator variation, no wrong-query control.**
- **Done and adjudicated:** mechanics only: CI green, external audit #339 `PASS_WITH_LIMITATIONS`, classified `QUALIFIED_MECHANICS_INTERFACE_FIXTURE`.
- **Missing comparison:** **(1)** the support-semantics ruling (§2), before any learning test. **(2)** Then a prospectively frozen **right-query versus wrong-query and program versus matched-perturb-null** comparison on C3 truth, under donor isolation. That is the only design here that can falsify query-specific biological learning, and it needs separate synthetic-training authority.

**#469**
- **Mechanism and truth:** no new biology; a new unsealed world (seed 31) with planted labels.
- **Observation:** 18 TRAIN cells × 24 genes.
- **Controls:** interface checks only.
- **Done and adjudicated:** executed (run 40559858670), **not adjudicated**. Its own audit says it gives "zero incremental biological information".
- **Missing comparison:** none that changes a scientific decision. Its stated edge, issuer to CaseBundle, is software readiness.

**#526**
- **Mechanism and truth:** reuses #328 exactly.
- **Observation:** a fixed query plus an 8-gene panel.
- **Controls:** q-scalar invariance.
- **Done and adjudicated:** executed and replicated here; scientific reading corrected.
- **Missing comparison:** none. Its pattern follows from the constants.

**Cross-asset gaps:**
- **No wrong-query control exists in any asset.**
- **No estimator or encoder has ever been scored** against #328 truth or V80.
- Realistic multi-operator structure exists only in V79.
- Integer counts with source support exist only in #328 and #469, and #328's support is semantically wrong.

## 4. Ranked next steps (reuse first; nothing here authorizes training)
1. **Owner and controller ruling on #328 support semantics** (§2). Until it is made, every #328-based learning result is confounded by the reversed source geometry.
2. **Independent audit of the #321 phase-2 receipt `53820343`.** It is cheap, and it decides whether the C2 relational test-of-test is usable.
3. **Resolve the 207-versus-291 V79/V80 conflict in advance.** That unblocks the single successor-estimator run.
4. **Freeze the falsification design in advance:** right- versus wrong-query, program versus matched null, and donor isolation. It should be ready for the first authorized synthetic JEPA run. Freeze the failure criteria, and equal-capacity decoders, before any fit (the #438 lesson).

**Preserved:** V79 `NOT_QUALIFIED` (291/292; Q08 hard FAIL). V80 qualifies a benchmark package, not an estimator. #438 is rejected. Truth was not modified and parameters were not tuned.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

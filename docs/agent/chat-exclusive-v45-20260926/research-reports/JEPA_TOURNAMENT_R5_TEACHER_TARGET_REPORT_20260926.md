# JEPA R5 — explicit teacher, measurable target, and genuinely query-dependent student test

**2026-09-26 | Research-only historical developmental population | NO FULL104 production training, Audit-B N1, D_shared or protected outcomes.**

## 1. Why previous rounds did not answer the months-old scientific question

We want a cellular world-state predictor, **not hidden-gene regression**, a generic cell-state classifier, or a mechanical ability to match a self-generated embedding. R1–R3 evaluated generic reconstruction of 96 held-out RNA genes. R4 applied query-specific readout selection but both its purported "teacher" and student PCA representations were learned on the *same 700 other genes*, **excluding the measured target panel**. Thus R4's teacher had no richer access to the proposed target and was another proxy predictor. R4's first raw student label alignment was also wrong and was explicitly withdrawn and corrected; the corrected score cannot be replaced by the withdrawn negative. R5 distinguishes genuine original measured teacher observations from lawful student inputs, uses actual q-conditioned readouts and retains all outcome and authority limitations.

## 2. Operational answer: what the teacher sees and what exactly the student predicts

**Developmental incumbent:** one rich same-original-cell teacher with authenticated measurement support, entire allowed native RNA and query address. The teacher **may observe** the queried RNA scalar as evidence of the cellular state. It is **not** rewarded simply for copying that scalar. Preserve a q-excluded teacher as a mandatory independent ablation. The eventual learned teacher produces a compact shared cellular state plus a q-conditioned local contextual state with separate support/uncertainty; optional fine and rare components may abstain. No compact neural teacher-state geometry is frozen by this pilot.

**Explicit measured R5 target, not just an architecture sketch:** for cell `c`, query canonical address `q`, and training-donor-selected ordered set `N(q)` of **8 other genes**, the teacher provides the same-cell original UMI vector `k_c,N(q)` and the anchored contextual target

`a_T(c,q)[j] = log1p(10000 * k_c,N(q)[j] / sum(k_c,N(q)))`.

If structurally unsupported, or the eight-gene sum is zero, the q-head **abstains**; computational zeros are not valid biological states. A measured zero within a supported nonempty panel is a legitimate zero. The identity of every non-q gene, query, source and original cell must be bound; full-library q-bearing normalization must not enter the target. The observed query count can be a **separately recorded teacher-only covariate**. In a future learned model the anchored `a_T` is only one part of the structured target `[z_shared(c), z_query(c,q), eligible specialist state, support, uncertainty]`. It is **not** a claim that eight observationally correlated genes constitute the complete biological world state or a causal regulator circuit.

**Student information:** a donor-training-selected, complementary 700-gene RNA panel, independently masked and normalized after removing the query and the entire separate 96-gene teacher/evaluation panel, plus the canonical q address. The student must predict the teacher's measured eight-component q-context; the q scalar cannot enter through direct values, full-library normalization, QC descendants, or copied teacher embeddings. Q is a *conditioning variable*, not a substitute for RNA.

**How the 8 genes were chosen here:** for each of eight q addresses per each of five donor folds, absolute microglia/PVM observational `log1p(raw UMI)` correlations among a previously used 96-gene panel, calculated on training donors only; q itself removed. These 40 q–fold cases depend on only 50 donor test units and reuse R1–R4-development material. This identifies a measurable **exploratory** target but emphatically NOT a stable regulatory neighborhood, production q registry, causality, untouched confirmation or independently validated biological program. See machine-readable contract for the future target's scientific acceptance requirements.

## 3. Actual executed results: 50 unique donor test units; 5 folds; 40 q-fold tasks

Each fold trains on 32 donors, reserves 8 for validation and holds out 10. The eight selected q targets vary by fold. Every original donor enters test exactly once; repeated queries per donor are **dependent**. Principal metric is mean q–fold heldout `R²` relative to the q-specific training mean, restricted to measured/supported teacher q-contexts.

| Developmental predictor | All heldout cells | Microglia/PVM |
|:--|--:|--:|
| Shared 32D RNA state + separate q-specific learned linear readout | **0.4300** | **0.3457** |
| Operator / visible technical features + q-specific readout | 0.3496 | 0.2784 |
| Shared 32D slope + q-specific bias | 0.3229 | 0.2611 |
| Larger 256D shared slope + q-specific bias | 0.3155 | 0.2536 |
| Query-agnostic 32D state/readout | 0.2760 | 0.2022 |
| Wrong-q slope + CORRECT true-q training bias (stress control) | 0.1652 | 0.1167 |
| q count only (TEACHER-ONLY diagnostic, inaccessible to student) | 0.1610 | 0.1347 |
| q-only train mean | 0.0000 | 0.0000 |

**Interpretation:** the learned q-dependent slope contributes beyond using q to select an intercept, and beyond one shared readout with approximately equal coefficient budget (256D × 8 outputs versus 8 q × 32D × 8 outputs). The 256D shared encoder uses additional representation capacity/compute, so this is an approximate *readout*-budget control, not equal overall training compute or a neural JEPA comparison. Technical+q remains substantial. The wrong-q slope test preserves the correct q mean, removing the easiest q-identity-only artifact, **but the eight target-vector coordinates represent different genes for different q**: it is a stress control, not a valid fully matched-coordinate QID estimand. These tests show a usable learnable query-conditioned prediction problem **within this reused same-study assay**, not independent biology.

At the unit of 50 donors, the q-specific score minus technical+q averages **+0.0708**, with a naive descriptive donor-bootstrap interval **[+0.0610,+0.0804]**, positive for all 50 donors. Against the q-bias/shared 32D slope the donor-mean difference is **+0.0946** (49/50 positive); against the 256D q-blind capacity control **+0.1022** (49/50). Five-fold mean q-specific-minus-technical is positive in every fold. These intervals are **not prospective inferential intervals** because R1–R4 already used the population/panels and the model family was chosen after seeing previous scores; fold-wise fitted model dependencies also remain.

## 4. Teacher-only fidelity challenge: is observing q informative or just copying scalar?

Second **physically executed** historical original-RNA test: for each training-only q, choose 8 non-q teacher-observed context genes `N(q)` from one 48-gene partition and 8 disjoint non-q heldout outcome genes `H(q)` from a second 48-gene partition. Only development training donors select the genes. Both N and H are independently normalized from their OWN non-q UMI sums; zeros/structural non-support abstain. Compare the measured N-context alone, N-context plus **teacher-visible** q count, and q count alone for predicting H on heldout donors.

| Teacher-visible measurement | All heldout cells R² | Microglia/PVM R² |
|:--|--:|--:|
| Measured N-context alone | 0.3031 | 0.2218 |
| N-context plus q scalar | **0.3106** | **0.2301** |
| q scalar alone | 0.1210 | 0.1081 |

Adding q contributed about **+0.00753 R²**, positive in 38 of 40 dependent q-fold cases and in all five fold means. This argues **against automatically forbidding the teacher from observing the queried count**, while also showing that q-count alone is a poor replacement for multi-gene context in this assay. Both outcomes are RNA features from **the same original assay and same cells**, so this is neither independent modality confirmation nor evidence of perturbation causality, and does not settle the final teacher-q input policy.

**Research decision:** a rich q-visible teacher is the developmental incumbent because its extra direct measurement may contribute context; the identical q-excluded teacher stays as an indispensable comparator. The **primary supervised anchor remains the non-q multidimensional measured program**, never direct scalar imputation. The provisional student reference is the 32D masked-RNA state with a q-dependent head. Any actual neural teacher core/latent requires independent biological falsifiers, noncollapse, technical-only and count-only challenge before promotion.

## 5. Historical red-team gates actually applied

- Original August calibration SHA and both original discovery-part SHA values were recomputed; exact subset CSR and metadata SHA checked. Calibration operator-support eligibility is respected. The ambiguous historical NPZ `66e64913...` is **not** used.
- Five nonoverlapping 10-donor test folds, 8 validation and 32 training; training-microglia-only panel derivation. Do not call 40 q–fold events 40 biological replicates.
- Correct *mask-major* repetition of training labels (`np.tile`, not withdrawn wrong `repeat`).
- All 40 measured q-targets exactly invariant under synthetic change to original q UMI. A deliberately wrong normalization including q count fails the counterfactual test.
- Explicit q-context support and zero-panel abstention. Source and ordered neighborhood hashes retained for every fold.
- q-only, generic-cell, q-biased shared slope, approximate matched-readout 256D, technical+q, q-count-only and wrong-q-slope diagnostics.
- Historical Stage69–71 rare-biology nonconfirmation, withdrawn x4_within, false QID matched-null/wrong-query equivalence, V0/V1 same-cell operator leakage, and obsolete V4 numeric/EMA settings are **not** imported as authority.
- **34/34 red-team and consistency checks passed.** Original files and research outputs were unchanged by mutation fixtures; the report deliberately retains all caveats.

## 6. What is now *defined*, and what is still scientifically unsolved

**Now operationally defined and measured:** one specific query-conditioned student target `a_T(c,q)`; teacher's required privileged evidence; permitted teacher-vs-prohibited-student q count; same-cell identity, support, abstention and per-q gene-address lineage; donor-split experiment; query-conditioned 32D benchmark; exact criteria by which generic-cell and technical baselines can refute it. This closes the prior problem of having **no actual target to hand the student in a developmental experiment**.

**Still unqualified for current V5 production:** the *biological meaning* of training-donor-selected eight-gene neighborhoods; independently supported predeclared canonical q set; learned compact neural `z_shared/z_query` teacher and its EMA update semantics; actual current V5 student and masking law; capacity-matched single-vs-multi-teacher with heldout original data; independent biological measurement (e.g. approved separate-nucleus ATAC population-level measurement with no circular teacher use); demonstrable across-source transport; approved prospective success margins; all 33 current authority roots and original critical-suite execution provenance. We must not call this observational anchor the complete biological world model. If independent biology fails, change the anchor **before** using protected confirmation; do not continue tuning anti-cheating code to defend an invalid target.

**Immediate next scientific gate:** agree on independent q-conditioned biological falsifiers for a target discovered from untouched **development-only** donors and annotation-authenticated neighborhoods; compare the q-visible teacher and its q-excluded ablation on that fixed assay with uncertainty and technical adjustment; only then train tiny EMA single/shared/team contestants with matched compute. No FULL104 training authorization follows from this tournament.

## 7. Files and reruns

- `JEPA_TOURNAMENT_R5_EXPLICIT_TARGET_PROBE_20260926.py` → `JEPA_TOURNAMENT_R5_EXPLICIT_TARGET_RESULTS_20260926.json`
- `JEPA_TOURNAMENT_R5_TEACHER_FIDELITY_PROBE_20260926.py` → `JEPA_TOURNAMENT_R5_TEACHER_FIDELITY_RESULTS_20260926.json`
- `JEPA_TOURNAMENT_R5_REDTEAM_20260926.py` → `JEPA_TOURNAMENT_R5_REDTEAM_RESULTS_20260926.json`
- `JEPA_R5_TEACHER_AND_TARGET_RESEARCH_CONTRACT_20260926.json` — machine-readable developmental specification, explicitly non-authorizing.

These scripts require exact `/tmp/jepa_tour_logexpr.npz` and `/tmp/jepa_tour_meta.csv`, created previously with `JEPA_TINY_TOURNAMENT_PREPARE_20260926.py` from original archived bytes. Original raw cell-level data are intentionally not enclosed in the portable report.

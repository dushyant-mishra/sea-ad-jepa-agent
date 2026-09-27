# JEPA historical tiny tournament: round-2 discriminatory audit and teacher-view ablation

**Date:** 2026-09-26  
**Status:** completed CPU developmental follow-up; NOT current V5/FULL104 training or teacher-target qualification.  
**Source:** the previous exact historical tiny tournament's **same 1,561 cells, 50 donors, 15 operators, 700 common-supported inputs and 96 disjoint held-out RNA features**, rather than an unreviewed new population. Its 361 “Microglia-PVM”/“Microglia-PVMSubclass” labels are not purified microglia. Source SHA-256 checks re-executed on the original two expression parts, the calibration bundle and expression.zip. Initial neural results are carried forward without pretending their unretained weights have been independently replayed in this round.

## 1. Historical anti-repeat review (live GitHub, read first)

Reviewed `main/START_HERE.md`, `main/docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, `main/docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` and V43 draft #176 `JEPA_V43_COMPLEMENTARY_TEACHER_STUDENT_RESEARCH_20260926.md`. At review the V43 head was `e7555ed0cc4dea07a2425da4185924a2d5728359` and `main` remained `c49b13bd75c2d23716c777336db8fbfc78c09cd0`. The following are **historical boundaries**, not new discoveries or permissions:

| Earlier finding | Explicit prevention in this round |
|---|---|
| Withdrawn `x4_within.py` fabricated signal on an operator-only null | Did not run/reuse that estimator; use donor-disjoint direct probes, visible technical positive controls and shuffled-training-label negative control. |
| Visibility-only strongly predicted Q_DEPTH/Q_DETECT | Separately measured operator + visible sparsity/depth baseline rather than equating latent R² to biological learning. This does **not** rule out all technical leakage. |
| Stage69 rare-head advantage weakened against Stage27C in Stage70; Stage71 real graph did not beat randomized graph | Low-prevalence RNA is called **rare-feature proxy**, not a validated rare cellular state. Added random and unpaired/shuffled specialist controls; no graph authority inferred. |
| Context and source effects change with estimand/sample weighting | Same historical donor splits and same evaluation task as the previous tiny round; no FULL104-weighted or source-general interpretation. Future actual training requires donor-uniform and source-transport gates. |
| Stage81A3 corrected TRAIN cache and historical V0/V1 cannot establish FULL104 generalization or remove shared cell-level technical effects | Historical discovery fit-donor matrix only. The 700 features are all observed on the **15 represented operators**; true native-support abstention and 42-operator performance remain untested. |
| QID matched-null did not establish wrong-query intervention; V43 target q-policy is UNSET | All present neural and linear targets are generic-cell, and query identity is NOT fed to the existing toy neural models. No query specificity result; no target selected. |
| T1/C2 zero-gradient, EMA/update/skipped-step repairs already audited | Did not modify production optimizer or claim the earlier toy EMA `.99` is current authority. No FULL104 updates. |
| Original September masking freeze, current G3 successor and critical-test provenance have separate authority | The tiny round does not select masking, open N1, claim full 33-root closure, or replace #169/#170/#173 scientific signoff. |

The independent prospective biological evaluator (separate-nucleus ATAC) was not inspected or used here. No pathology, D_shared, terminal masking, N1 or protected outcomes were accessed. All claims below are *same-study developmental RNA recoverability*, not biological teacher fidelity.

## 2. Why a second round was necessary

The earlier tournament had two donor resampling splits, 26/38-epoch AE training caps, unequal teacher+student parameter counts, an EMA **proxy rather than the current V5 model**, different A/B/C training losses, and generic rather than query-conditioned targets. Its leading R² differences (~.001–.01) were not a valid scientific architecture selection. Before training more neural teachers, one must ask whether simple unsupervised 32-dimensional masked-RNA compression and technical covariates already explain the measured score.

### Round 2A: direct student-input baselines

A new **PCA-32 of masked visible RNA** was fitted on TRAINING donors alone, followed by the same fixed-alpha-20 linear ridge prediction of the original 96 completely disjoint RNA features. The PCA fit and feature standardizer used training donors only. Test input used the **exact existing neural evaluation mask seed** for each fold. The direct ridge comparators received one fixed training mask whereas original neural students received newly drawn masks across epochs, so this comparison is a diagnostic baseline, not a controlled head-to-head training-method experiment. No held-out test label selected PCA or its hyperparameters.

| Input or model | Mean test R², all cells | Mean R², Microglia/PVM subset |
|---|---:|---:|
| First round EMA student **proxy** | .4538 | .3833 |
| First round rich-teacher student | .4630 | .3859 |
| First round shared-head student | .4622 | .3913 |
| First round teacher-team students | .4606 | .3896 |
| **Masked visible 700 RNA → PCA-32 → ridge** | **.4638** | **.3954** |
| Operator + visible technical summary → ridge | .3270 | .2862 |
| **Prohibited** full-panel depth technical diagnostic | .3331 | .2814 |
| Shuffled TRAIN-label negative control | -1.4170 | -1.4633 |

The PCA result was stable under a second, prospectively selected **test-input mask**, with mean R² .4665 (no weight retraining). This is not an external validation and should not be used to tune the masked input. Direct 700-feature ridge was regularization-sensitive: alpha=20 gave negative test R², while alpha=200 gave mean .2466; this demonstrates why a naive unregularized/direct baseline would be misleading. All learned models and PCA exceed this *particular* operator+visible-technical control, but the technical R² itself is substantial, and there is no causal argument that the remaining difference is biology. The original RNA evaluation is relative composition across its own 96-feature denominator, **not absolute held-out transcript abundance**.

### Round 2B: teacher-only, capacity-matched linear view ablation

On full, unmasked teacher RNA, fit three **unsupervised PCA representations using TRAINING donors only**, all with the same aggregate 32 dimensions. For the matched-normalization comparison, the rich-32, split-(16 core + 8 fine + 8 low-prevalence), and core-16 all use the **same 700-feature full-teacher normalization**. This avoids misattributing differences caused by independent per-panel library normalization to teacher architecture. Shuffled specialist controls unpair fine/rare embeddings **only within the same donor train/validation/test partition**, with an additional null that preserves the measurement operator. Probe/evaluation panels and training donors match Round 1 exactly.

| Construction (no neural teacher training) | Mean test R² | Mean microglia/PVM R² |
|---|---:|---:|
| **Single rich PCA-32** | **.4963** | **.4286** |
| Split PCA-16/8/8, matched full-teacher normalization | .4859 | .4212 |
| Core PCA-16 alone | .4782 | .4131 |
| Core + within-operator shuffled specialists (32 dimensions) | .4711 | .4030 |
| Split PCA-16/8/8, independently normalized component inputs — **sensitivity only** | .4902 | .4223 |

The split representation contains incremental same-study RNA information beyond core alone (~.0078 all-cell R² under matched full normalization), and that contribution drops when specialist vectors are unpaired even while preserving operator identity. Nevertheless the capacity-matched rich PCA-32 carries **more** withheld-RNA signal. Independently normalizing each specialist panel changes performance; the full single-teacher and independently normalized split are **not** normalization-matched. These results do not show that a trained specialist teacher is redundant or biologically faithful. The original teacher-only AE vs this PCA baseline is likewise not compute- or objective-matched.

## 3. Physical audit and adversaries

`JEPA_TOURNAMENT_ROUND2_REDTEAM_20260926.py` re-hashes **four original heavy source files** (both original discovery ZIP parts, calibration ZIP and expression ZIP), checks old-results hashes and feature-selection parity across folds, validates the exact two-fold control/test inventory, checks original donor separation against real mounted metadata, probes a label-shuffle null, and requires a detected effect of specialist unpairing. It also invokes the original student masking code with a planted change to the hidden query count and verifies identical lawful student inputs, while a deliberately flawed full-library denominator produces visibly changed inputs. **31/31 local checks passed**, no protected outcomes opened. These are independently executable local source/input controls, not externally attested GitHub test runs or approved V5 critical-suite provenance.

Important limitation: a source SHA pinned in a local code file verifies these specific original bytes against historical published inventory; it does not prove the legitimacy of an unclassified NPZ or any current V5 teacher/measurement authority. The old first-round neural scores are imported from their recorded results, not independently retrained. We deliberately did NOT execute a historical discredited estimator or redo the settled T1/C2 mechanics.

## 4. Decision and next useful scientific run

**No qualified architectural winner.** On the currently available measurement, simple PCA compression is as effective as, or stronger than, the tiny neural models. The split linear teacher captures some additional same-study RNA beyond core alone, but has not demonstrated independent *biological* information missed by an equally expressive rich teacher. We should not reward extra specialists for generic RNA recovery alone.

For a genuinely discriminating next neural round: (1) prospectively define biological fidelity and query-value policy **per teacher head**, reconciling #152 and #163; (2) select an outcome-safe, authenticated developmental dataset and preserve an independent biological evaluator; (3) compare A single rich, B shared multi-head and C independently specialized teachers with matched effective capacity, compute, donor exposure, source/measurement support and independently fixed seeds; (4) require query-aware vs generic-state, q-only, direct/derived q leakage, technical-only, rare donor recurrence, within-operator shuffled specialists and teacher-noncollapse controls; (5) freeze donor- or source-aware statistics and distinct independent ATAC evaluation *before* looking at that evaluation; and only then test separately whether students can predict the biologically supported teacher components.

The current V43 support-aware component assembler is a research data-contract prototype, not a neural trained world model. Current V5 33-root authority remains 0/33 closed in the last reviewed handoff. `TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED`.

## 5. Reproduce locally

The companion ZIP contains both original tiny round source/results and the new Round 2 scripts, two results JSON files, this report, and the new 31-check audit receipt. Execute the preparation script against the **original historical files with known SHA-256** if the staged historical subset is unavailable, then run both Round 2 scripts with CPU NumPy/SciPy/scikit-learn/PyTorch and finally the red-team script. No cell-level dataset or external GPU original bytes are bundled. Round 2A and Round 2B run independently and do not require rerunning the original four neural training arms. Do not promote a historic developmental result into FULL104 production authority.

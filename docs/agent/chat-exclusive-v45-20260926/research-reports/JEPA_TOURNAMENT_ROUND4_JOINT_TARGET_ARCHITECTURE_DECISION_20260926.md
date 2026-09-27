# JEPA exploratory tournament round 4 — joint target and architecture decision

**2026-09-26 | RESEARCH_ONLY | no current FULL104 authorization or protected-outcome access**

## Why this round exists

Rounds 1–3 measured generic recovery of 96 heldout RNA features, not the query-conditioned cellular world state we intend the student to predict. A tiny EMA proxy, autoencoders and PCA scored closely; an honest single 32D PCA was as strong as the more complicated split. The historical index additionally warns that matched-null is NOT the wrong-query estimand, V0/V1 share the same cell-level operator effects, historical rare-head gains were inconclusive, and the old x4_within estimator was withdrawn. A production target cannot be chosen by generic RNA reconstruction alone.

This round instead examines a **non-scalar, query-selected context vector** and the capacity-matched single-vs-split 32D *linear teacher* proxies on the same donor-disjoint historical developmental data. No new neural JEPA teacher or student architecture was trained.

## Data and target construction

Original historical discovery subset: 1,561 cells, 361 microglia/PVM-labelled, 50 donors, 15 operators. Five disjoint heldout ten-donor groups (32 train, eight validation donors per fold). The original 41,238-column log-expression archive is invertible to integer counts for these cells, error <1e-5. On each fold, a training-donor-defined, disjoint panel of 700 eligible genes is the teacher/student input. The previously disjoint 96-gene evaluation panel contains the candidate q values and contextual readouts; this panel was used in prior historical development and is NOT untouched independent validation.

For each of eight reproducibly sampled q indices per fold, use only training-donor microglia/PVM-labelled cells to identify eight other evaluation-panel genes with the strongest absolute observational log-count correlation to q (exclude q itself). Those eight form a **demonstration target**, not a proven regulatory network, a fixed production target address set or a causal biological program. The original evaluation 96 and the q identities vary by fold; a stable production q registry remains to be agreed prospectively.

Two target definitions were explicitly compared as measurements:

* R4 original raw log-count context: `log1p(raw UMI of eight non-q genes)` per same cell. q excluded, but absolute depth and technical covariates remain influential. A teacher with q scalar could additionally encode `log1p(raw q)`, but that is a *separate scalar diagnostic*, not our primary target.
* R4B q-safe, view-local context: `log1p(10,000 * raw_context_gene / sum(raw_eight_non_q))`; zero-view cells return an all-zero computational placeholder for this **diagnostic only**, not evidence that biology was truly zero or a valid production support policy. The context is invariant under counterfactual q count changes and has no q-bearing full-library denominator. This changes the target estimand; never compare its R² magnitude directly to the raw-count estimand.

For an eventual production target, the intended **object** is structured and query-address-conditioned: `(same_cell_key, q, shared molecular state, query-context molecular state, optional supported fine/rare components, observed-support/abstention flags, biological vs measurement uncertainty, exact source roots)`. A teacher may use q's measured value if the scientific experiment warrants it; the student may not see q's measured value directly or through normalization, QC or global-feature descendants. Teacher q-scalar use and scalar-decodability must be explicitly audited rather than automatically forbidden or automatically accepted.

## Executed exploratory measurements

Means across 40 query–fold combinations (eight q/fold × five folds). **Query–fold combinations within a fold are dependent and cannot be counted as 40 independent biological replicates.** A full donor-macro and source-transport analysis, stable target addresses, nontrivial learned q-conditioned predictor, independently observed biological label and actual current V5 model are absent.

| Linear representation or diagnostic | Raw log-count q-context R² all | Q-safe eight-gene context R² all | Q-safe microglia/PVM R² |
|---|---:|---:|---:|
| Rich PCA32 teacher proxy | 0.6686 | 0.5068 | 0.4163 |
| Split PCA16/8/8 teacher proxy | 0.6616 | 0.5007 | 0.4107 |
| Three-mask PCA32 student baseline (generic encoder, q-selected readout) | **0.6272** | 0.4889 | 0.3946 |
| Visible operator + technical-only baseline | 0.6043 | 0.4240 | 0.3348 |
| q-count-only diagnostic (teacher can observe q; student cannot) | 0.4576 | 0.2022 | 0.1575 |

Within the q-safe estimator, the masked student exceeds the visible-technical model and the rich teacher exceeds split representation on each of five all-cell folds. Neither result establishes causal, independent or query-specific biology. The teacher proxy is trained **without q-conditioned attention**, and the student has no q input: q currently determines which context-vector readout is evaluated. This is an **intermediate falsification probe**, not the final target competition. Microglia/PVM is the original metadata category, not purified microglia.

### Mandatory withdrawn result

The **first raw R4** output showed student R² `-0.0207` only because its code incorrectly used `y[tr].repeat(3,axis=0)` while the three input masks were concatenated mask-major; the correct target alignment is `np.tile(y[tr],(3,1))`. The raw R4 score after correction is **0.6272**. The original incorrect script is preserved under `WITHDRAWN_LABEL_ALIGNMENT`; it must never be quoted as a scientific finding. R4B's active per-q training already used the correct tiling. The red-team now requires correct alignment and verifies the withdrawn artifact is distinct.

## Joint tournament interpretation and provisional design

**Developmental architecture reference:** keep a single rich teacher as the incumbent because it represents the full panel within the same 32D budget and retains slightly more of these same-study q-context measurements than the split PCA proxy. A multi-head shared backbone remains the lower-cost complexity challenger. Retain fully independent teacher teams only when specialist teachers demonstrate distinct reproducible information under equal total capacity/compute, across independent donors and appropriate biological measurements. No trained-teacher winner has emerged.

**Developmental target reference:** q-safe, view-local same-cell context is an executable *proxy* for a multidimensional non-q molecular context; a rich-teacher variant may separately observe q count, but a no-scalar-teacher variant must remain in the blinded comparison. Keep the q scalar a separately reported diagnostic and forbid using it as the only target. The exact eight-gene correlated panel is a temporary probe and **must not be imported as a biologically faithful production q-neighborhood**. Discovery of q-neighborhoods by correlation is observational and susceptible to donor, cell-state and technical confounding.

**What would finish the actual scientific target choice:** freeze (i) exact common biological meaning per head and q, (ii) q-visible vs q-excluded teacher evidence plus all normalization descendants, (iii) exact same-cell source-provenance and support rules, (iv) independent falsifiers of q-linked biology and the comparison to q-only/generic-cell/technical/null teachers, (v) stable canonical q set and donor-aware calibration panels, and (vi) prospectively chosen decision margins before opening any independent evaluator. On authentically qualified **development** RNA, test that the representation changes nontrivially under q exchange beyond a copied q embedding, predicts independent developmental biology while generalizing donors/technologies, and retains rare donor recurrence without using future protected endpoints. Then run capacity/compute-matched neural A/B/C and select using those frozen endpoints. Separate-nucleus GSE174367 ATAC could serve only an approved population-level external evaluator; it must not be used for both teacher construction/model selection and independent testing.

**What we may move past right now:** generic-RNA reconstruction tournament as the principal selection criterion. Adopt rich32 and q-safe context as *research controls only*, not final production geometry/target. **What remains blocking:** true teacher biological fidelity, learned q-dependent state, current V5 approved target choice, 33-root authorization and the frozen original FULL104 execution requirements. Do not use these historical scores to authorize current V5 training or inspect protected outcomes.

## Reproduction, scope and integrity

`JEPA_TOURNAMENT_ROUND4_TARGET_JOINT_PROBE_20260926.py` and `JEPA_TOURNAMENT_ROUND4B_QSAFE_TARGET_PROBE_20260926.py` need the existing prepared historical `/tmp/jepa_tour_*` assets or the previous exact original archive preparation script. Full original cell-level data are excluded from this package. The corrected raw and q-safe JSON include per-query fold scores, selected canonical-address digests, actual five-fold counts and q-count counterfactual test records. `JEPA_TOURNAMENT_ROUND4_TARGET_REDTEAM_20260926.py` runs 27 static/result checks. This work did not modify GitHub, re-open N1, train current FULL104, or use protected outcomes.

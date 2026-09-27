# JEPA R7 — explicit biological-program challenge of the teacher target

**2026-09-26 | Historical development only | All FULL104 training and protected outcomes remain OFF.** This round challenges target *meaning*, not neural architecture performance. It deliberately uses the same 1,561 historical cells developed repeatedly in R1–R6; the results are not independent confirmation. No prospective biological target or production neural topology has been selected.

## Why the previous tournament did not answer the scientific question

R5 established that a query-specific linear readout could predict an eight-component, same-cell, correlated-RNA target from separate RNA. R6 found that the measured queried scalar added only about 0.0025 held-out-RNA R² after its technical comparator. Both findings concern *same-assay RNA*. Neither establishes that the teacher has constructed a coherent biological program, and successful student imitation of an arbitrary contextual panel is insufficient.

The R7 change is to name biological programs **before this round's outcomes**, use exact original Ensembl-address feature mappings, exclude queried and target genes from the student's complementary 700-gene input, and measure teacher-only transfer to separate, prespecified program readouts. There are five 10-donor test folds covering the same 50 historical donors once each, with 32 training and eight validation donors in each. Only the 361 microglia-labelled cells are used to fit/scoring targets; other training cells can inform the unsupervised student PCA basis. There are 15 measurement operators in the sample. This is not the four-fold production masking geometry.

## The three actual candidate target objects

| Query | Four measured teacher partner genes | Separate readout RNA (not seen by teacher or student) |
|---|---|---|
| APOE / lipid-associated | APOC1, ABCA1, GPNMB, TREM2 | CTSD, LPL |
| P2RY12 / homeostatic-associated | TMEM119, CX3CR1, GPR34, C1QA | SALL1, CSF1R |
| HLA-DRA / antigen-processing-associated | CD74, HLA-DPA1, HLA-DMA, IFI30 | HLA-DMB, CTSS |

These gene collections are **expert-motivated exploratory hypotheses**, not validated causal modules or imported frozen pathway authorities. Exact current-Ensembl-address mapping was recovered from the original calibration bundle. All 12 teacher partner genes and all three queries are observed in all 15 relevant operators; the LPL held-out readout is structurally unmeasured in four of them. LPL rows are **not** interpreted as expression zero when unavailable; teacher-readout scoring excludes them. We used two target coordinate choices: independent four-gene panel `log1p(10,000 * UMI / sum(panel UMI))`, and unnormalized `log1p(original integer UMI)`.

**Important target-semantic discovery:** the within-panel normalized coordinates are *exactly invariant* when all four program genes scale together. They record the *relative composition* of that program, not the total amount of program activation. Conversely, raw log-UMI retains intensity but is much more vulnerable to capture depth. Neither choice can simply be relabeled a complete biological world-state target.

## Five-fold results on microglia-labelled cells

Means are arithmetic averages of five donor-held-out fold R² scores, with each fold's training-set target mean as the prediction reference. Folds have different microglial-cell and donor support; these are descriptive values, **not statistical evidence of architecture or biological superiority**. The teacher-only evaluation is *additional same-assay RNA*, not independently measured chromatin or protein. The teacher in this diagnostic is a linear readout of its actually observed target genes, **not a trained neural EMA teacher**; the student is a train-only PCA-32 plus q-specific ridge readout, not a trained query-conditioned encoder.

| Target program | Student predicts measured target, composition R² | Non-query technical baseline R² | Teacher predicts separate readout RNA R² |
|---|---:|---:|---:|
| APOE/lipid-associated | **0.558** | 0.362 | **−0.086** |
| P2RY12/homeostatic-associated | 0.097 | 0.088 | −0.095 |
| HLA-DRA/antigen-associated | 0.119 | 0.111 | −0.057 |

Raw `log1p(UMI)` target variant: student R² = 0.545/0.147/0.143; technical R² = 0.349/0.153/0.141; teacher-only separate-readout R² = −0.112/−0.067/−0.049 for APOE/P2RY12/HLA-DRA respectively. The third readout column uses log1p raw counts in all cases. The q-count-only teacher diagnostic did not establish incremental program biology; full per-fold results and baseline combinations are in the JSON.

The APOE student score is **a counterexample to using student success as target validation**. The same program target can be appreciably predicted from remaining RNA without carrying demonstrable added information for other prespecified program markers in this small cohort. This does **not** show APOE biology is absent or that none of these genes form meaningful programs. It shows the candidate targets have **not passed even this preliminary, underpowered teacher-only coherence test**. Most microglia donors have very few cells; APOE teacher-readout testing had only 18–36 test cells across 4–7 donors per fold because LPL was not always measured.

### Measured support and sampling variance

| Program | Microglia with any partner counts | Donors with nonzero partner counts | Median partner UMIs when positive | Half-count repeatability proxy |
|---|---:|---:|---:|---:|
| APOE | 214 / 361 | 46 / 50 | 3 | 0.659 |
| P2RY12 | 206 / 361 | 46 / 50 | 2 | 0.364 |
| HLA-DRA | 217 / 361 | 44 / 50 | 2 | 0.394 |

The half-count experiment partitions observed UMIs within the same cell; it measures sampling stability with all cell-level technical confounding still shared, **not** independent biological reproducibility. The rare/low-count support limits make a larger cell- and donor-supported prospective test more useful than adding network capacity to these exploratory data.

## Red-team and history-preserving correction log

An initial draft of the R7 script **incorrectly required both held-out readout genes to have positive counts and required LPL to be measured by every operator**. Both are wrong: a measured zero is legitimate, and structural missingness requires an evaluation support mask. These errors were caught before interpreting the numerical comparison, fixed without loosening the teacher support rule, and the two target variants were rerun. The final source implements `target.sum > 0` for its provisional measured program target, allows zero-valued *measured* readouts, uses `nan` for structurally unmeasured readouts, and restricts two-marker readout scoring to cells where both are actually observed. The candidate target abstains when its entire four-gene measured panel is zero; this is a *provisional estimability policy*, not a statement of no biology.

The R7 red-team passed 178 assertions/check instances in one local run (many are repeated per arm and fold, **not** 178 independent test methods): source SHA and size, exact program lists, disjoint student input panel, q-value counterfactual, deliberately leaky full-library denominator, all-zero target abstention, original LPL missingness, fold separation, scores finite, planted true signal detected and shuffled synthetic signal rejected. The original 410,278,055-byte calibration archive SHA-256 matched the V42 custody manifest. No synthetic test establishes biological validity, and the round did not inspect protected outcomes.

Historical traps deliberately excluded: Stage81A3 TRAIN cache is not FULL104; original T1/C2 zero-gradient repairs are not rerun; withdrawn x4_within results and wrong-query-versus-matched-null substitutions are not revived; old 0.83 RNA pilots and Stage69 rare gains are not current targets; q-specific readout coordinates are not proof of biologically meaningful q×cell interactions; no historical EMA .996 or four-fold production seeds are inherited from five-fold diagnostics.

## Actual target decision and next science-first pivot

**Do not freeze the R5 eight-gene panel or R7 four-gene programs as the production world-state target.** Keep both as *measured, reproducible developmental anchors* for negative-control development. Do not choose the single-rich or multi-teacher architecture based on predicting these panels. The single-rich model remains a reasonable reference for a future experiment, not a selected production model.

The next prospectively defined target must name (a) its actual original same-cell molecular evidence; (b) a structured multidimensional target, including distinguishable composition versus program amplitude and explicit measurement uncertainty; (c) how q affects the molecular state and which teacher heads may see the q count; (d) support/abstention and original feature lineage; (e) biological measurements **not used in teacher construction or selection** that could falsify each component; and (f) which components a lawful complementary-RNA student should be expected to predict. Compare q-visible and q-excluded teachers only after the target object and biological falsifier are fixed.

The available separate-nucleus microglial ATAC material is an **option for donor-/population-level validation only** if Lane D's source/sample pairing, leakage, cohort overlap and outcome reservations are cleared first. Do not treat donor-shared RNA/ATAC as same-cell pairs, use that ATAC to construct the teacher and validate it simultaneously, or inspect it now to tune this target. Genuine perturbation benchmarks additionally require guide engagement and independent replication; observational markers cannot prove causal effects.

`JEPA_R7_NEXT_TARGET_DECISION_CONTRACT_20260926.json` makes the target boundary explicit. Engineering after biology: preserve the current FULL104 support, sampling, masking source integrity and optimizer/EMA/checkpoint machinery; version only the scientifically changed teacher target, legal teacher/student input policy and any branch-aware topology. **FULL104 TRAINING=OFF; AUDIT-B N1, D_shared G5 and all protected outcomes unopened.**

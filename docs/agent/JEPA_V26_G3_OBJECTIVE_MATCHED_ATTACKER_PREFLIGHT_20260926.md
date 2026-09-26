# V26 G3 objective-matched masking-attacker fit preflight

Status: `G3_FIT_MECHANICS_SYNTHETIC_ONLY__CANONICAL_MASKING_ATTACKER_NOT_CHANGED__NO_PHYSICAL_FULL104_OR_TRAINING_AUTHORITY`.

Scope owner: this isolated G3 review branch. **Do not cherry-pick or overwrite** Claude's active trainer, the stacked PR #129→#130→#132→#135→#139 sampling lane, PR #120/#124 raw verifier, PR #136/#138 new104 linear comparator, PR #133 historical94 or PR #137/#140 CRISPRbrain provenance. The base is exact experimental PR #77 @ `9a2a30e4c4c99be2a8f948aba680524c786d2737`. No experimental, N1, protected, oracle, Siletti, biological perturbation or real JEPA outcomes accessed.

## Changed scientific question — one that project history explicitly left OPEN

September 20 Audit G3 found that `src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py::_fit_ridge_weights` sums per-donor standardized Gram/RHS/RSS components **without donor scaling**, so large donors contribute more fit mass. The frozen JEPA base-training estimand is `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`. The masking score's source-balanced held-out aggregation is a THIRD estimand and must not be conflated with either fit law. The old G3 report calls for comparing three **fit** objectives, keeping feature screening, alpha, folds and held-out score fixed.

Previously completed work that is **not** rerun: donor-balanced JEPA sampler (PR #135/#139), 19-estimator masking qualification and the failed 600/2,000/6,000 masking K/R grid, V0/V1 measurement ablation, full-data Phase-I sufficient-statistics authentication, six-state non-estimability evidence contract, and all existing historical94 LODO analyses.

This branch adds a narrow independent, reusable formula implementation `g3_explicit_attacker_fit_objective_v1.py`. It accepts the current executor's ORIGINAL within-donor standardized Gram/RHS/target-SS triplets and explicit authenticated TRAINING donor counts/source identities. It cannot be called without naming exactly one fit objective:

| id | normalized donor fit mass M_d | meaning |
|---|---|---|
| CURRENT_CELL_WEIGHTED | n_d / sum_j n_j | historical mechanics comparison, not matched to current training |
| PRODUCTION_OBJECTIVE_MATCHED | 1 / D_train | **prospective matched G3 fit** over current outer-training donors |
| SOURCE_DONOR_BALANCED_DIAGNOSTIC | 1 / (S_train * D_train,source(d)) | separate diagnostic: each observed train source has equal total mass |

For every policy, per-row mass `w_i=M_d/n_d`; for each donor keep EXACTLY the existing train-side within-donor X standardization/Y centering, then aggregate `Gram=Σ_d w_d G_d`, `RHS=Σ_d w_d b_d`, `RSS_y=Σ_d w_d RSS_d`, with `w_d=M_d/n_d`. Solve `(Gram+alpha I) beta=RHS/sqrt(RSS_y)`. Thus changing the fit policy changes ONLY row masses; ridge alpha is regularized per unit normalized scientific mass. Exact masses sum to one over outer-training donors. No inference on held-out expression or held-out donor normalization is authorized here. Alpha, features/screening and scoring stay unchanged across fit-objective comparisons.

## Independent self-audit / red-team scope

The new test compares each weighted sufficient-statistic ridge result to a separately implemented DIRECT row-level weighted-ridge calculation on synthetic raw cells, not to the same component helper. It also includes an unequal donor/source fixture that produces conflicting molecular relationships, donor/source mass checks, cell=donor equivalence at equal donor counts, independent donor-order invariance, unexpected held-out-statistics injection, absent source identity, missing/invalid donor counts, nonfinite moments, invalid alpha and a constant-target negative-control that cannot be promoted to a \"clean\" held-out correlation.

**One scientifically important restriction:** `fit_from_standardized_donor_components` may return zero coefficients for an all-constant TRAIN target. That does **not** mean the masking attack is qualified or benign: the separate already-qualified six-state evidence contract MUST classify missing/nonvariable held-out target terms as non-estimable rather than a free zero. This G3 fit module deliberately does not reimplement that contract.

## What would make G3 fixed before the scientific diagnostic

1. Independent review/green exact-head CI of this objective-matched fit module. The exact independent raw-row result is synthetically tested only.
2. At integration, create an explicit current-V5 development-only evaluator contract naming `PRODUCTION_OBJECTIVE_MATCHED` for the *primary* fit, with `CURRENT_CELL_WEIGHTED` and `SOURCE_DONOR_BALANCED_DIAGNOSTIC` prespecified sensitivity columns. Bind the actual donor-count/source map to authenticated PR #132 pass1/metadata and require a complete train-only fold roster. Carry fit-objective ID, weights/root and exact source/target/feature/split SHAs into all receipts, including checkpoint/evaluation manifest. Do **not** silently change historical masking-run outputs or reuse an old score cache with changed objective.
3. Integrate the explicit policy into BOTH `_ridge_primary_score` and `_ridge_partners` (where RIDGE8 selects its partner set) before interpreting any new masking-policy comparison; the top-correlation/PREFIX3 candidate selection and source-balanced heldout score remain separate fixed algorithms. Changing only the primary ridge evaluator while keeping RIDGE8 historical would silently compare differently fitted arms.
4. A real-data read-only preflight must show all per-donor/source row masses and verify the target, visibility, feature/support, fold and source identities. Prespecify the full score terms' six-state estimability/coverage contract and hold protected N1/terminal outcomes CLOSED. When the first real current-V5 reader_fit diagnostic runs, source/measurement-only attacks can be compared using this matched fit on the *development* split, if its separate execution/data authority permits; do not allow result-responsive policy tuning.

**Hard scope distinction:** An authenticated engineering smoke check of real gradients, Adam, EMA and checkpoint resumption does not depend on G3, because G3 applies to an independent attacker, not to JEPA's own donor-uniform training estimator. Conversely, a claim that masked JEPA learned biology rather than a source/size shortcut **does depend** on matched and appropriately sensitive attackers. Never upgrade an engineering-only run into scientific qualification before this G3 integration.

This branch's synthetic CI neither runs FULL104 physical data nor changes the currently integrated G3 caller. After review, the downstream integration remains a named separate task; do not report `G3_CLOSED` from green fixtures alone.

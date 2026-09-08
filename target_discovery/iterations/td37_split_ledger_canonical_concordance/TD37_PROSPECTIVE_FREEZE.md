# TD37 — Split-Ledger Canonical Concordance prospective freeze

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-08

## Historical predecessor
TD35/TD36 variance-defined source subspaces failed corrected donor-half recurrence/null tests. TD19/21/22 same-gene dependency geometry is cross-source null. Hidden-gene reconstruction is historically rejected as a biological training target.

## What is materially new
TD37 does not optimize variance, gene-gene edge agreement, clustering, state matching, or reconstruction of withheld genes.
It asks whether two disjoint gene views of the SAME cell contain a shared low-dimensional signal that can be learned in one donor block and transported without refitting the canonical coefficients.
The within-cell pairing is intrinsic and requires no state correspondence.

## Input boundary
50k archive is falsification-only. Use only B_COVERAGE_DISCOVERY global rows 25000..49999 for the primary pilot.
The explicit freeze-file global row is authoritative for CSR access. `sample_row` and post-merge DataFrame indices are forbidden for expression addressing.
Common-scalar genes are exactly states==MEASURED_SCALAR across all 42 operators (expected n=17186).
Biological annotation columns native_class and broad_class are firewalled until all TD37 discovery statistics are frozen.

## Gene panels / views
Four independent 512-gene panels selected deterministically from the common-scalar set by SHA256 of `TD37|panel|address`.
Within each panel, the first 256 hash-ranked genes form view X and the remaining 256 view Y.
No biological annotation or outcome participates in gene selection.

## Preprocessing
Expression is the frozen log1p10K matrix.
For every row derive detected-gene count from the full CSR row.
Merge exact source_library from operator metadata by stable_key only AFTER preserving explicit global_row.
Primary analysis is measurement-residualized: within each source and donor-training block, regress every selected gene on [1, log1p(source_library), log1p(detected_genes), operator one-hot] using training donors only; apply frozen coefficients to evaluation donors. Missing/unseen operator columns are zero-coded and reported.
Raw analysis is descriptive secondary.

## Canonical model
Linear regularized CCA on the two disjoint 256-gene views.
Numerical regularization is ridge lambda = 1e-3 times the mean diagonal variance of each view covariance; no lambda tuning.
Fit uses equal donor weights: each training donor contributes total weight 1/n_train_donors, divided equally across its cells.
Canonical coefficients are ordered by training canonical correlation. Signs are fixed so the largest-absolute loading in X is positive.
No K is selected. Report prefix statistics r in {1,2,4,8,16}.

## Within-source recurrence gate
For each source use four deterministic donor splits from SHA256(`TD37|split|source|donor`). Fit coefficients on one donor half and evaluate frozen coefficients on the other half, then reverse halves.
Evaluation statistic for prefix r is mean Fisher-z-transformed diagonal cross-view correlation of paired canonical scores, converted back to r-scale for reporting.
Within-source recurrence must be tested before cross-source transfer.

## Cross-source transfer
Only if a source/prefix has within-source recurrence above its null in every split direction, freeze its coefficients and apply them unchanged to cells from each other source after target-source nuisance calibration fit on target-source training donors only. No canonical coefficient refit, rotation, matching, permutation, or graph alignment in the target source.

## Nulls
Primary null is donor/operator/depth-preserving broken pairing: within each donor×operator and detected-gene/source-library joint quantile bin, permute Y-view rows relative to X before every CCA fit. If a stratum is too small, merge adjacent quantile bins deterministically; never cross donor or operator.
Run the COMPLETE fit/evaluate procedure inside each null replicate.
Secondary shortcut control predicts canonical scores using only source_library, detected_genes, and operator.

For the pilot use 64 null replicates per panel/split/direction. This count is computational, not a production threshold.

## Falsification / promotion status
A prefix is `NEW_EVIDENCE_SURVIVES_HISTORICAL_ATTACK` only if:
1. every within-source donor-split direction exceeds the corresponding null p95 for >=3/4 independent gene panels;
2. canonical score correlation remains materially positive after measurement residualization;
3. nuisance-only score predictability does not account for the observed concordance;
4. frozen coefficients transferred to another source exceed that target's full pairing-null p95 in >=3/4 panels.

Otherwise classify `NO_TRANSFERABLE_SPLIT_LEDGER_CANONICAL_STATE_ESTABLISHED_IN_50K_PILOT`.
No result from this pilot may choose production K/D/thresholds or authorize training.

## Post-freeze validation only
Only after discovery statistics are frozen may native/broad annotations be opened to ask whether the surviving canonical scores explain the corrected TD34 relational scaffold. Annotation cannot rescue a failed label-free gate.

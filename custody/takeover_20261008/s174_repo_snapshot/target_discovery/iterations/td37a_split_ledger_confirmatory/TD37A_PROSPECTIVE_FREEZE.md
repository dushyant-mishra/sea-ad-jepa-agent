# TD37A — Split-Ledger Canonical Concordance clean confirmatory freeze

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-08

## Why TD37A exists
TD37 v1 was frozen before its B-sample observed run, but audit found two execution-critical ambiguities:
1. the written four-split donor hash omitted the split index;
2. the primary pairing null did not freeze an executable bin/block construction.
Therefore the completed B observed run is QUARANTINED_DIAGNOSTIC_ONLY and cannot establish a gate.

TD37A uses the untouched, disjoint A_NATURAL_MIXTURE sample as a clean prospective confirmation. A/B stable_key overlap must equal zero before computation.

## Historical predecessor
- TD19/21/22: same-gene dependency geometry not cross-source recurrent after correct row binding.
- TD28/29A/30: label-free clustering/diffusion relational objects fail their own full-search/nulls.
- TD35/36: corrected variance-defined source/global and class-conditioned subspaces fail robust donor recurrence.
- hidden-gene reconstruction remains rejected as a biological target.

## Materially new object
Two disjoint gene views of the SAME cell define correspondence intrinsically. We test whether a low-dimensional signal shared between those views is recurrent across donor blocks and transportable across source families with coefficients frozen. No state labels, state matching, graph matching, clustering, PCA variance ranking, gene-gene edge replication, or hidden-gene reconstruction objective is used.

## Input
Primary confirmatory pilot: A_NATURAL_MIXTURE only.
Exact global rows: 0..24999.
Explicit `global_row=np.arange(len(freeze_csv))` must be inserted BEFORE any merge. CSR access uses only global_row.
B sample is not read for TD37A statistics.
native_class and broad_class are dropped before discovery statistics.
Common-scalar addresses: states==MEASURED_SCALAR for all 42 operators; expected n=17186.
50k archive remains falsification-only and cannot set production dimensions/thresholds.

## Gene panels / views
Four independent 512-address panels.
For panel p in {0,1,2,3}, rank common-scalar address g by SHA256 UTF-8 bytes of:
`TD37A|panel|<p>|address|<g>`
Take the first 512 addresses. First 256 = view X; second 256 = view Y.
No biological annotation or outcome participates.

## Donor splits
For source s and split index k in {0,1,2,3}, rank donor d by SHA256 UTF-8 bytes of:
`TD37A|split|<k>|source|<s>|donor|<d>`
Alternating ranked donors define halves H0=positions 0,2,4... and H1=1,3,5...
Evaluate both directions H0->H1 and H1->H0.

## Preprocessing
Frozen log1p10K expression.
Per row derive:
- log_library = log1p(source_library)
- log_detected = log1p(number of CSR nonzeros in the full 41,238-address row)
Within each source/split/direction and separately for X and Y genes:
- training nuisance design = intercept + log_library + log_detected + operator one-hot with smallest operator as reference;
- weighted least squares with equal total donor weight;
- fit nuisance coefficients on training donors only;
- apply frozen coefficients to train and eval;
- standardize residual genes by weighted training mean/SD (variance floor 1e-8).
Unseen eval operator columns are zero-coded and reported.

## Regularized CCA
Fit linear regularized CCA on paired residualized X/Y training rows with equal total donor weight.
For each view covariance C, ridge lambda = 1e-3 * mean(diag(C)); no tuning.
Use symmetric PSD inverse square-root via eigendecomposition.
Canonical components ordered by training singular value.
Sign fixed so the largest-absolute X loading is positive.
No K is selected. Report fixed prefixes r={1,2,4,8,16}.
Eval component statistic = equal-donor weighted Pearson correlation between paired X/Y canonical scores.
Prefix statistic = tanh(mean(atanh(component correlations))).

## Primary matched broken-pairing null
Nulls operate on the nuisance-residualized, standardized rows so nuisance fitting is identical across observed and null worlds.

Within each source and each donor×operator stratum independently:
1. compute rank fractions for log_library and log_detected within that stratum using stable average-free ordinal ranks, tie-broken by global_row;
2. sort rows lexicographically by (floor(8*rank_detected_fraction), rank_library_fraction, rank_detected_fraction, global_row);
3. partition consecutive sorted rows into blocks of size 8; if the final remainder is exactly 1, merge that row into the previous block (size 9). Strata of size 1 remain singleton and therefore self-paired; their fraction is reported.
4. For null replicate j=0..63 and each block with m>=2, cyclically shift Y rows relative to X by:
   `shift = 1 + SHA256_U64("TD37A|null|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>") mod (m-1)`.
The same deterministic pairing rule is applied independently to training and evaluation rows using their global-row-defined block memberships.
Pairings never cross donor or operator and are locally matched on depth/detection.
All CCA coefficient fitting is repeated in every null replicate. X/Y marginal covariances may be cached only when mathematically identical under the within-donor permutation; Cxy and canonical coefficients must be recomputed.

Primary null statistic is the corresponding prefix correlation distribution. Use null p95; with 64 replicates this is a pilot falsification reference, not a production threshold.

## Secondary shortcut audit
For each observed fitted model/prefix, fit an equal-donor linear ridge predictor (lambda 1e-3 * mean nuisance Gram diagonal; no tuning) from [log_library, log_detected, operator one-hot] to each X canonical score on training donors and evaluate on held-out donors. Report variance-weighted R2. This cannot rescue a failed primary null.

## Within-source gate
For a source/prefix/panel/direction, PASS_NULL if observed prefix > null p95.
A source/prefix is recurrent only if PASS_NULL holds in all 8 split-directions for at least 3 of 4 independent panels and observed residualized prefix correlation is positive in all required directions.
Within-source recurrence is mandatory before any cross-source transfer is computed.

## Cross-source frozen-coefficient transfer
Only for source/prefix combinations satisfying the within-source gate:
- take each source-trained observed model from each split direction;
- in target source, form the same gene panel and fit ONLY target-source nuisance residualization/standardization on the target training donor half defined by the same TD37A split rule;
- apply the source CCA A/B coefficient matrices unchanged to target held-out donor cells;
- no canonical refit, rotation, permutation, component matching, sign search, or model selection in target.
Evaluate paired X/Y canonical score prefix correlation.
Run the exact target pairing-null procedure inside every transfer null; source coefficients remain frozen.

Transfer survives only if observed > target null p95 in all eligible source-split directions for >=3/4 panels.

## Terminals
If no prefix survives within-source recurrence:
`NO_DONOR_RECURRENT_SPLIT_LEDGER_CANONICAL_STATE__TD37A_FAIL`

If within-source recurrence exists but frozen coefficients do not transfer:
`DONOR_RECURRENT_BUT_NOT_CROSS_SOURCE_SPLIT_LEDGER_STATE__TARGET_UNQUALIFIED`

If a fixed prefix survives recurrence and frozen transfer under the prospective rule:
`NEW_EVIDENCE_SURVIVES_HISTORICAL_ATTACK__TD37A_CANDIDATE_FOR_INDEPENDENT_REVIEW_ONLY`

No TD37A result authorizes JEPA training or production target authority.

## Post-freeze annotation validation
Only after all label-free TD37A statistics and terminals are serialized may native/broad annotations be reopened to ask whether surviving coordinates explain TD34 geometry. Annotation cannot alter the TD37A terminal.

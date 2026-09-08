# TD37 null-execution addendum — prospective clarification

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Parent freeze commit: 90056d8fba47d000077a08466ee2a623f202657a
Reason: the parent freeze specified donor×operator + detected-gene/source-library joint quantile bins but did not fix the quantile count/merge implementation. This clarification is frozen before any TD37 null statistic is computed.

## Exact primary null strata
For each training donor×operator stratum independently:
1. stable-sort rows by (detected_genes, source_library, global_row);
2. assign detected-gene quartile q_det by integer rank floor(4*rank/n), clipped 0..3;
3. independently stable-sort by (source_library, detected_genes, global_row) and assign q_lib the same way;
4. initial stratum is (donor_id, operator_index, q_det, q_lib).

Any initial stratum with fewer than 4 rows is deterministically merged first across q_lib within the same (donor,operator,q_det). If that merged stratum still has fewer than 4 rows, merge across q_det to the full donor×operator stratum. Never cross donor or operator.

## Exact permutation
Within each final stratum, derive a deterministic SHA256 key from
TD37|null|panel|source|split|direction|replicate|global_row.
Sort rows by that key and circularly shift Y rows by
1 + SHA256(TD37|shift|panel|source|split|direction|replicate|stratum_id) mod (n-1).
Thus every final stratum of n>=2 is a derangement; no Y row remains paired to its original X row.
If a donor×operator stratum itself has n=1, the replicate is invalid and the analysis fails closed rather than crossing donor/operator.

## Preprocessing and evaluation semantics
Measurement residualization and standardization are fit on the unpermuted training marginal X and Y views exactly as in the observed analysis. The pairing permutation is applied to residualized/standardized Y training rows immediately before CCA cross-covariance estimation. Marginal X and Y covariance/whitening therefore remain identical to the observed fit.

Held-out evaluation remains the true same-cell X/Y pairing. This null asks whether a shared canonical block can be discovered when the training cross-view biological pairing has been destroyed while donor/operator/depth marginals are preserved.

The complete CCA fit (including SVD, canonical ordering/sign fixing) is rerun for every null replicate. Reusing invariant marginal whitening matrices is a numerical optimization only and must reproduce a from-scratch replicate within float64 tolerance on an independently checked subset.

## Decision statistic
No individual canonical axis is selected. The frozen prefixes remain r={1,2,4,8,16}; because axis rotations are possible, prefix/block statistics are conclusion-bearing exactly as defined in the parent freeze.

No null result has been inspected at the time of this clarification.

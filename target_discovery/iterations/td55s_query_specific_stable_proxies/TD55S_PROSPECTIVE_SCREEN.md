# TD55S — Query-Specific Cross-Source-Stable Visible Proxy screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD48–TD54 use generic molecular context shared across all queries. Exact-reference context (TD52) and a fixed quadratic expansion (TD53) improved some metrics but remained donor-fragile. This leaves one specific unresolved mechanism: query-local information may be sparse and query-specific, then diluted by query-agnostic context.

TD55S keeps the TD51 biological target unchanged and changes only how visible reference context is organized.

## Frozen target / train-test

Reuse TD51 exactly:
- 64 fixed query genes Q;
- 512 fixed visible reference genes R;
- 64 TRAIN-prior-balanced query ordinal innovation targets z_iq;
- TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD donors/cells;
- TEST = all A_NATURAL_MIXTURE NPH52 donors/cells;
- no biological labels.

All Q/R genes are in the 17,186 all-operator common-scalar intersection.

## Candidate proxy features

Visible candidate feature for reference gene r is its exact TD52 tie-aware within-cell normalized rank among R.

For each query q and source s in {HVS, SEA_AD}, compute TRAIN-only donor-balanced residual correlation between z_q and each reference-rank feature:

1. residualize z_q and each candidate rank coordinate within source against intercept + log1p(source_library) + log1p(detected_genes) + source-specific operator one-hot;
2. use equal total donor weight;
3. compute weighted Pearson correlation rho_s(q,r) on residuals.

A proxy is cross-source-stable only if rho_HVS and rho_SEA_AD are finite, nonzero, and have the same sign.

Stable score:
`score(q,r) = min(abs(rho_HVS(q,r)), abs(rho_SEA_AD(q,r)))` if signs agree, else 0.

For each query, select exactly the top 16 reference genes by descending score, tie-broken by Molecular Ledger address. K=16 is fixed before outcomes and is not a production parameter.

If fewer than 16 positive-score proxies exist for a query, that query is NOT_MEASURABLE. Require >=48/64 measurable queries.

## Nested model selection

Final query model uses:
shortcut = intercept + log1p(source_library) + log1p(detected_genes)
plus that query's 16 selected exact reference-rank proxy coordinates.

Fit one weighted ridge model per measurable query with equal total donor weight.

Lambda multiplier grid is fixed: {1e-3,1e-2,1e-1,1,10}.
Choose one shared multiplier minimizing mean inner-validation MSE across measurable queries and both inner folds.

Inner folds use the frozen TD50 source/donor hash. Within every inner fold, proxy selection is recomputed using only inner-fit donors; no inner-validation target outcomes may influence proxy identities. Final proxy selection is recomputed on all HVS+SEA_AD TRAIN donors after the multiplier is chosen.

Predictor and target standardization use fit donors only inside inner folds and all TRAIN only for final fitting.

## Primary untouched-NPH52 same-cell gate

Evaluate all measurable query targets on NPH52 with equal donor weighting.

Primary aggregate Delta = (shortcut MSE - query-specific molecular MSE)/shortcut MSE.
Require Delta>0.

Run 64 matched wrong-cell NPH52 evaluation-context permutations using the exact TD52 donor×operator depth/detection blocks with preimage:
`TD55S|evalnull|<j>|source|NPH52|donor|<d>|operator|<o>|block|<b>`.

The complete 512-reference rank row is permuted; each query then reads its already-frozen 16 proxy coordinates from the matched wrong cell. Shortcut, proxy identities, coefficients and target standardization remain frozen.

Aggregate alignment requires correct-cell Delta > max of all 64 wrong-cell Deltas.

## Donor-primary recurrence

Use the exact TD52 MOVABLE donor definition.
For each movable donor, compute aggregate query MSE/Delta across all measurable query coordinates.
DONOR_PASS iff correct-cell donor Delta > median of that donor's 64 matched-wrong-cell Deltas.
Require >=12/16 DONOR_PASS.

Require leave-one-movable-donor-out aggregate alignment against all 64 corresponding nulls in >=12/16 omissions.

## Additional reporting

Report:
- measurable query count;
- stable-score distribution;
- proxy reuse frequency across queries;
- fraction of proxies with matching positive vs matching negative signs;
- per-query Delta distribution on NPH52.

These are descriptive and cannot rescue a failed primary gate.

## Terminal

Any conjunctive failure:
`NO_DONOR_RECURRENT_QUERY_SPECIFIC_VISIBLE_PROXY_SIGNAL__TD55S_FAIL`

All pass:
`TD55S_QUERY_SPECIFIC_PROXY_SIGNAL_SURVIVES__FREEZE_TRAIN_NULL_AND_INDEPENDENT_SOURCE_REPLICATION_NEXT`

No production proxy count, pair/module identity, threshold, target authority or JEPA training authorization is implied by this 50k screen.
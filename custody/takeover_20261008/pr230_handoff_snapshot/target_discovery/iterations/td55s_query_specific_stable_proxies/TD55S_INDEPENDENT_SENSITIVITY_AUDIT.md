# TD55S independent sensitivity and reconstruction audit

Status: `TD55S_PRIMARY_FAILURE_CONFIRMED__SCREEN_SENSITIVITY_CONFIRMED`

This note supplements, but does not replace, the existing TD55 closure.

## Independent primary reconstruction

A second implementation independently recomputed:
- HVS/SEA_AD source-specific nuisance residualization;
- donor-balanced residual correlations;
- same-sign stable proxy scores;
- Molecular Ledger address tie-breaks;
- final top-16 proxy identities per query;
- final per-query ridge fits;
- untouched NPH52 equal-donor MSE.

Exact reproduction:
- measurable queries: 64/64
- unique selected reference proxies: 335
- median weakest selected stable score: 0.0486954998
- shortcut MSE: 3.8057814260
- molecular MSE: 3.8809372533
- Delta: **-0.0197478044**
- queries with molecular MSE below shortcut: 28/64

Thus the primary TD55 failure is not a producing-script artifact.

## Sensitivity-control wording issue

The TD55 prospective text inherited the phrase "replace the 256 context sketch" although TD55 itself uses query-specific 16-proxy contexts.

To ensure this wording mismatch cannot create a false FAIL, a conservative leakage-positive control was tested using only each query's own true z-coordinate as its molecular context. This is less information than supplying the full 64-z vector.

The same NPH52 matched wrong-cell evaluation-context permutations were applied. The control was evaluated at **every** multiplier in the frozen ridge grid, avoiding dependence on any post-hoc lambda choice.

Correct-cell Delta / matched-null maximum:
- 0.001: 0.9999967252 / 0.0764623816
- 0.01: 0.9996880209 / 0.0896018781
- 0.1: 0.9793168046 / 0.1794012702
- 1: 0.6794948004 / 0.2741267421
- 10: 0.1573856200 / 0.0772360635

Correct-cell alignment beats all matched wrong-cell nulls at all five multipliers.

Therefore the screen is decisively sensitive to same-cell query information, and the TD55 negative primary result is a genuine target/predictor failure rather than NOT_MEASURABLE.

Binding interpretation remains:
`NO_DONOR_RECURRENT_QUERY_SPECIFIC_VISIBLE_PROXY_SIGNAL__TD55S_FAIL`.

No target authority or JEPA training authorization.

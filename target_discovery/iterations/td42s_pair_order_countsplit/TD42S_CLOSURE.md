# TD42S closure — exact split-half agreement fails because ties are measurement-unresolved

Status: `PAIR_ORDER_SPLIT_HALF_EXACT_AGREEMENT_FAILS__MEASUREMENT_TIE_DIAGNOSIS`

Prospective freeze commit:
`5d0baf84b7c67a9b56f60b7aaa75518215625094`

First predeclared case HVS / panel 0:
- observed exact split1-vs-split2 pair-order agreement: 0.354608
- matched wrong-cell null median: 0.484045
- null p95: 0.485271
- FAIL

The TD42S terminal is therefore a failure under its exact contract.

Post-failure diagnostic, not part of the TD42S gate:
At 50% count depth, relative to the full-count direction:
- half1 resolved coverage: 0.703413
- half1 directional precision conditional on resolved: 0.987620
- half2 resolved coverage: 0.703771
- half2 directional precision conditional on resolved: 0.987754
- reverse-direction rate among resolved: ~0.0123
- unresolved/tie fraction: ~0.2964

Matched wrong-cell directional precision:
- half1 null p95 ~0.89447
- half2 null p95 ~0.89328

Therefore the exact half-vs-half failure is driven by complementary thinning turning low-count relations into ties/unresolved measurements, not by frequent biological direction reversal.

Implication:
A pair-order target must not encode a measurement tie as biological zero/equality. Pair direction and measurement resolution must be separate semantics.

No target/training authority.

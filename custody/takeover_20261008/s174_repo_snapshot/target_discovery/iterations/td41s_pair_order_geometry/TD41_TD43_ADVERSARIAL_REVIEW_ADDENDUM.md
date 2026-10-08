# TD41–TD43 adversarial review addendum — Claude critique resolved

Status: `CORRECTIVE_INTERPRETATION__NO_TARGET_AUTHORITY`

## TD41 raw-byte reproduction

TD41 was independently reconstructed from:
- the frozen 50k expression matrix;
- B_COVERAGE_DISCOVERY global rows 25000..49999;
- the exact operator support authority;
- the exact sample/operator metadata.

The four GLUT observed geometry values reproduce to numerical precision:

| panel | raw r | depth/detection residual r |
|---:|---:|---:|
|0|0.795417878|0.863849234|
|1|0.798382507|0.877318628|
|2|0.823759803|0.914964567|
|3|0.809855226|0.830679384|

The positive result is therefore independently reproduced from raw bytes.

## Correct interpretation: metric/aggregation changed, not information

Claude's theoretical criticism is correct.

For a tie-free cell, the complete pairwise sign matrix and the within-cell rank vector are bijectively related. Therefore TD41 is not richer in information than full ranks.

The important difference from TD40 is the metric and order of operations:
- TD40 averages/compares rank coordinates;
- TD41 maps each cell to pairwise order signs first, then donor-balances those signs and compares state geometry.

Thus the surviving object is better described as:
`EXPECTED_WITHIN_CELL_CONCORDANCE_GEOMETRY`
or a Kendall-feature geometry, not a richer pair-identity representation.

A direct Kendall distance applied after forming donor-balanced state-mean expression profiles is NOT equivalent to TD41. On the four 512-gene panels its HVS<->SEA_AD GLUT graph correlations were:
- raw: 0.9102, 0.9500, 0.9591, 0.8981
- state depth/detection residualized: 0.5824, 0.5839, 0.5313, 0.5638

This shows that ranking the state mean after aggregation loses the residualized structure retained by averaging within-cell pair orders.

Pair-sample convergence on panel 0 also argues against a lucky 4,096-pair subset:
- 4,096 pairs: raw 0.7954 / residual 0.8638
- 8,192 pairs: raw 0.8017 / residual 0.8722
- 16,384 pairs: raw 0.8009 / residual 0.8652

The hashed subset behaves as a Monte-Carlo probe of the concordance feature geometry, not as an obviously special learned weighting.

## Common-scalar support audit

TD41 uses exactly the TD34 panels, which are selected only from the 17,186 addresses with `MEASURED_SCALAR` state in all 42 operators.

Therefore every endpoint of every TD41 pair lies inside the all-operator common-scalar intersection. The structural-unmeasurement confound raised in review does not apply to TD41.

## TD42 arithmetic/pairing reconciliation

TD42 HVS panel 0 was independently reconstructed from raw integer counts.

Exact prospective observed result:
- equal-donor mean per-cell split1-vs-split2 exact pair-order agreement: 0.354608243.

Decomposition:
- mean per-cell half1 resolved coverage: ~0.6845
- mean per-cell half2 resolved coverage: ~0.6848
- both halves resolved: ~0.3693
- both halves tied for a full-depth informative pair: exactly 0
- resolved same direction: 0.354608243
- resolved opposite direction: ~0.01469
- exactly one half resolved: ~0.6307

The apparent arithmetic paradox came from treating complementary count splits as independent. They are anti-correlated. For a full-depth unequal pair, both complementary halves cannot both have equal counts, because their two differences sum to the nonzero full-depth difference.

The matched wrong-cell arm was also independently reconstructed:
- null median ~0.4841
- null p95 ~0.4855

Thus there is no arm swap and no matched-null pairing bug.

The post-TD42 diagnostic coverage/precision numbers used ratio-style aggregation and are not algebraically interchangeable with TD42's mean-per-cell exact-agreement statistic. That reporting distinction should be explicit going forward.

## Pair informativeness / excess-over-null diagnostic

On label-free A-sample HVS panel 0, pair informativeness was defined by the minority full-depth direction frequency across cells.

| minority direction frequency | n pairs | half-depth coverage | same-cell directional precision | matched wrong-cell median | excess |
|---|---:|---:|---:|---:|---:|
| <=1% | 556 | 0.779 | 0.9991 | 0.9952 | +0.0039 |
| 1-5% | 833 | 0.728 | 0.9958 | 0.9704 | +0.0254 |
| 5-15% | 953 | 0.693 | 0.9867 | 0.9010 | +0.0857 |
| 15-30% | 855 | 0.652 | 0.9791 | 0.8081 | +0.1710 |
| >30% | 899 | 0.639 | 0.9714 | 0.7338 | +0.2376 |

Conclusion:
- raw pair-direction accuracy is dominated by a global gene-order prior for nearly invariant pairs;
- the cell-specific excess is real and increases monotonically with pair informativeness;
- the dynamic signal is not confined to a tiny tail: 2,707/4,096 (~66%) of panel-0 pairs reverse in >5% of HVS cells.

Future trainability metrics must therefore report improvement/excess over a pair-specific matched or prior baseline rather than raw accuracy.

No threshold or pair weighting from this 50k diagnostic becomes production authority.

# Source/fold donor geometry under the current source-balanced score

Derived directly from the authenticated `full104_split_receipt_v1.json` and the current production score definition:

```
source score = mean donor r² within source
primary score = mean of the three source scores
```

No terminal outcome is used.

## Donor counts

- HVS: 41 donors
- NPH52: 17 donors
- SEA_AD: 46 donors

Outer folds:

| fold | HVS train/held | NPH52 train/held | SEA_AD train/held |
|---|---:|---:|---:|
| 0 | 30 / 11 | 12 / 5 | 34 / 12 |
| 1 | 31 / 10 | 13 / 4 | 34 / 12 |
| 2 | 31 / 10 | 13 / 4 | 35 / 11 |
| 3 | 31 / 10 | 13 / 4 | 35 / 11 |

## Consequence of equal source weighting

Because each source receives weight 1/3, each held-out donor's weight in the total primary score is:

[
w_{d} = rac{1}{3 n_{	ext{held,source}}}.
]

Thus an NPH52 donor carries 6.67% of the total score in fold 0 and **8.33%** in folds 1–3, compared with roughly 2.78–3.33% for individual HVS/SEA_AD donors.

The current scorer sets `r = 0` when target or prediction variance is non-estimable (`den <= EPS`). Therefore, if one NPH52 donor/target pair is non-estimable and contributes `r²=0`, the maximum absolute downward effect relative to a hypothetical `r²=1` contribution is **0.08333** on the total source-balanced score in folds 1–3.

This does not mean the current source balancing is wrong. It means:

1. source-specific effective donor count is part of the estimand and precision;
2. target/source/fold non-estimability cannot be treated as harmless zeros;
3. H3 precision and any source guardrail must account for the fact that NPH52 source means are based on only 4–5 held-out donors;
4. the global target eligibility thresholds `train>=20 / heldout>=5` cannot simply be transplanted per source, because NPH52 has only 17 donors total and only 4 held-out donors in three folds.

Status: **CURRENT-GEOMETRY DERIVATION / PRETERMINAL DESIGN EVIDENCE**, not a terminal result.

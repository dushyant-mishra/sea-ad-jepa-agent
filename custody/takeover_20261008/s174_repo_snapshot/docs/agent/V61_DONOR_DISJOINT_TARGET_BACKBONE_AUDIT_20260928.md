# V61 donor-disjoint target-backbone stress test — 2026-09-28

Status: **DISCOVERY STRESS TEST ONLY — NOT BIOLOGICAL SPECIFICITY — NOT TRAINING AUTHORITY**

This is a stricter successor stress test of the source-balanced common-state candidate. The earlier A/B discovery halves can share donors. Here each source's donors are deterministically partitioned into two disjoint sets before fitting either basis.

## Donor split

- HVS: 21 vs 20 donors
- NPH52: 9 vs 8 donors
- SEA-AD: 23 vs 23 donors
- cells: 25,940 vs 24,060
- donor overlap between halves: exactly zero

The split is deterministic by SHA-256 ordering of donor IDs. The 400-gene feature set is selected from donor-half 1 only, using equal-weight within-source variance over the same all-42-operator-measured protein-coding universe used in the V61 discovery audit.

## Result

Independent source-balanced covariances were fit on each donor half. Principal-angle comparisons show strong donor-disjoint recurrence:

| rank | mean cosine | minimum cosine |
|---:|---:|---:|
| 3 | 0.9565 | 0.8825 |
| 4 | 0.9869 | 0.9613 |
| 6 | 0.9878 | 0.9645 |
| 8 | 0.9869 | 0.9672 |
| 10 | 0.9756 | 0.8454 |

When the half-1 basis is projected onto the completely held-out half-2 donors:

- rank 4 biological within-source trace eta-squared: **0.3895**
- rank 4 source trace eta-squared: **0.0363**
- rank 4 donor-after-source+class trace eta-squared: **0.1168**
- rank 4 SEA-AD operator-after-class trace eta-squared: **0.1361**

At rank 8:

- biology: **0.3610**
- source: **0.0268**
- donor residual: **0.0956**
- SEA-AD operator residual: **0.1030**

The held-out biological signal is not diminished by donor separation. This argues against simple donor memorization as the explanation for the common subspace.

## Boundaries

This does **not** prove biological specificity against an unmeasured same-cell technical latent. V48 remains binding. It also does not qualify q-safety: the discovery matrix is already normalized with the historical library denominator, so future target execution must be rebuilt on a q-safe preprocessing path.

No target rank is frozen by this stress test. No individual PC is selected post hoc. No protected regulatory molecular outcome was opened.

`TRAINING=OFF`  
`TD60=BLOCKED`

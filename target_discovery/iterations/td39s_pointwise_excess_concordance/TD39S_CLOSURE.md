# TD39S closure — pointwise excess concordance screen

Status: `NO_PER_CELL_EXCESS_CONCORDANCE_RECURRENCE__TD39S_KILL`

Prospective freeze commit:
`bd59a467205b9485e2eb76c101008e3277f2ca0a`

Single predeclared HVS split-0 H0->H1 screen:

- training rows: 575
- evaluation rows: 554
- Panel A / Panel B gene overlap: 0
- observed equal-donor correlation of per-cell excess bilinear concordance: **0.0350604**
- matched held-out panel-pairing null median: **0.0338126**
- matched held-out panel-pairing null p95: **0.0992544**
- maximum over 16 complete training broken-pair refits: **0.0283616**
- training-null median: -0.0588243

Thus:
- PASS_EVAL = false
- PASS_FIT = true
- screen terminal = FAIL

The failure is decisive under the prospective fast-screen rule. The per-cell excess bilinear statistic is not recurrent across two disjoint molecular panels beyond the matched held-out pairing null.

No additional TD39S cases were run and no annotations were opened.

Interpretation:
TD38S population-level dependence remains real, but neither TD38 quadratic predictable energy nor TD39S pointwise excess concordance has yielded a panel-stable per-cell target. Do not continue this canonical-operator target family without a materially different representation.

No target or training authority.

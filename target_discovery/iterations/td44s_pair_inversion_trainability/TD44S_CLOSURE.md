# TD44S closure — insufficient dynamic target pairs

Status: `TD44S_NOT_MEASURABLE__INSUFFICIENT_DYNAMIC_TARGET_PAIRS`

Prospective freeze: `6560a6d8953bbcb7c557b776cb4688b720330f69`
Technical addendum: `49b436a2b0846709b51ede8a3f026e6b870dddd4`

HVS A-sample screen:
- rows: 1,129
- TRAIN: 553 cells / 21 donors
- EVAL: 576 cells / 20 donors
- fixed target pairs: 256
- pairs satisfying the prospective resolved/both-directions donor estimability rule: **66**

The contract required >=128 estimable/scorable pairs before a scientific screen could be interpreted.

Therefore:
`TD44S_NOT_MEASURABLE__INSUFFICIENT_DYNAMIC_TARGET_PAIRS`

No null-based target terminal is claimed.

Descriptive only, not qualification-bearing:
Among the 66 estimable pairs, the fixed naive per-pair molecular ridge model had median Delta_p ~-0.351 and 0/66 positive Delta_p. This is consistent with severe variance/overfit cost when hundreds of context predictors are added to small per-pair resolved subsets, but it cannot be used as a target FAIL because the frozen minimum-K gate was not met.

Do not tune the per-pair model post hoc. A materially different joint multivariate target/predictor formulation is required.

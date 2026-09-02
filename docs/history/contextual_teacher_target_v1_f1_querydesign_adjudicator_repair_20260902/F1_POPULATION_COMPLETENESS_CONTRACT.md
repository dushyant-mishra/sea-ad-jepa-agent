# F1 population-completeness contract

Status: prospective, outcome-blind repair. The unchanged assignment authority is `F1_QUERY_ASSIGNMENTS_2DRAW.csv`, SHA-256 `12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617`.

Before aggregation, the production adjudicator shall derive its expected population only from that authority and require exactly 44,496 unique assignments, 2,781 cells, 104 donors, 42 operators, eight named programs, and replicates `{0,1}` for every cell-program pair. Each cell has one donor/source/operator/evaluation-row identity.

For evidence levels `{0.2,0.4,0.6,0.8,1.0}`, the required outcome key universe is the Cartesian product of every frozen assignment key with all five levels: exactly 222,480 unique `(assignment_key,evidence)` records. Incoming length, uniqueness, and set equality must all match. Result cell and donor sets and every assignment identity must equal authority. Expected size may never be inferred from received results.

Cell weights are exact numerator/denominator fractions with float64 hexadecimal encodings and semantic root `018d80428c25a0060168a942ca03dc9e814783463cc077e3661008ba5f7b5eeb`. Their mass must equal one independently for every one of the 104 frozen donors. Aggregation remains assignment → program → cell → donor, with equal donor weight at population level. Deduplication is computational only.

`qid_win` has exact domain `{0.0,0.5,1.0}`. Other finite values, NaN, and infinity fail closed. No new bounds are imposed on other finite cosine-derived metrics.

Any missing, duplicate-replacing, extra, donor-relabelled, or cell-relabelled record is `STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE` or `STOP_F1_QUERYDESIGN_METRIC_DOMAIN` as applicable.

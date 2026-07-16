# Stage79 F13 - Graph-Control Testing

Stage79 compares the Real frozen regulatory graph against bounded graph controls using the frozen Stage77 one-hop input-space perturbation contract and the frozen Stage78 JEPA encoder. It is a Model-based graph-control comparison, not causal validation.

## Controls

- Real frozen regulatory graph: references frozen Stage77/Stage78 results and reproduces expression deltas as an integrity check.
- No-graph control: preserves the regulator input-space delta and removes propagated target-gene deltas. This is not a knockout because it does not remove a gene, edit biology, or retrain a model.
- Degree-preserving edge-shuffle control: preserves TF outdegree, target indegree, TF weight slots, and total edge count while disrupting topology.
- TF-label-shuffle control: preserves target/sign/weight templates and TF label counts while disrupting the biological TF-target label assignment. Transferred coactivity signs are not interpreted as biological directionality.
- Expression-matched random-target control: preserves TF outdegree and signed weight slots while replacing targets with JEPA features matched on processed input-space baseline mean and nonzero fraction from the same 32 frozen baseline cells.

## Donor Aggregation

Donor ID is the aggregation unit. Cells are model inputs and are not treated as independent biological replicates.

## Empirical Comparison

For stochastic controls, empirical p-values use `(1 + count(null >= observed)) / (1 + number_of_seeds)` and the corresponding lower tail. The two-sided value is `min(1, 2 * min(upper, lower))`. The 50 seeds define a bounded empirical control panel and do not provide definitive validation. No threshold is used to declare graph validity.

Movement relative to an existing Supertype centroid is a geometric model summary, not rescue. Stage79 does not alter Stage75 evidence tiers.

Approved wording: Stage79 compares the frozen real graph against bounded structural and expression-matched controls. Differences are model-based control results and do not establish causal regulation or therapeutic benefit.


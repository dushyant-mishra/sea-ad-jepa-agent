# JEPA Macha/V77 — S157 and target-sparsity audit

Date: 2026-10-06
Parent observed before write: `26310db87f06363fb783067ea591d52ef1ad2586`
Working Macha head: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Status: `DOCUMENTATION_ONLY__NO_TARGET_OR_GENERATOR_CHANGE`

## 1. S157 wording requires qualification

The register currently frames S157 as a question of whether synthetic worlds should carry `class-linked biology` because within-cohort T5 is about 0.77–0.81 while synthetic T5 is around 1.02.

The primary T5 statistic is:

`mean within-class median |correlation| / pooled median |correlation|`

computed on CPM-log1p RNA for classes with at least 200 cells.

Within-cohort ratios below 1 therefore show that broad cell-class differences contribute materially to pooled RNA dependence.

That supports:

`REAL_RNA_HAS_CLASS_ASSOCIATED_STRUCTURE_NOT_PRESENT_IN_CURRENT_CLASS_INDEPENDENT_SYNTHETIC_SUBSTATES`

It does **not** yet establish:

`THE_MISSING_STRUCTURE_IS_PURELY_BIOLOGICAL_AND_SHOULD_BE_PLANTED_AS_CLASS_LINKED_BIOLOGY`

because T5 does not residualize or stratify class-linked depth, QC, operator, support or other measurement effects before attributing the difference to biology.

Current classification:

`S157_OPEN__CLASS_ASSOCIATED_STRUCTURE_CONFIRMED__BIOLOGICAL_MECHANISM_NOT_IDENTIFIED`

Do not add class-linked synthetic biology solely to improve T5.

## 2. What would be needed before a biological S157 repair

Prospectively separate, within observation process:

- broad cell-class biology;
- library depth / detection burden;
- structural support;
- operator/study effects;
- donor effects.

Then ask whether class-associated dependence remains after accounting for measurement effects.

Only if that survives should a synthetic biological mechanism be proposed, with negative controls showing that the same T5 cannot be recreated by technical class differences alone.

## 3. Zero-heavy hidden-target distribution

The current repaired adapter chooses hidden targets from structurally measurable positions without conditioning on whether the realized value is zero.

In the 2,000-cell integration receipt:

- total hidden targets = 5,529,144
- hidden measured zeros = 4,595,999
- hidden detected values = 933,145

Thus about 83% of hidden targets are measured zeros.

This is not an adapter defect; it is the expected consequence of value-independent query selection in sparse RNA.

However, it is a major target/loss-design constraint.

A future method can obtain an apparently good aggregate reconstruction score by mostly predicting zero unless the evaluation separates:

- measured-zero queries;
- detected/nonzero queries;
- expression magnitude among positives;
- detection-state prediction;
- donor/source-balanced performance.

No particular loss is selected here. This lane has no target-selection authority.

Current classification:

`TARGET_DISTRIBUTION_PROPERTY_CONFIRMED__AGGREGATE_LOSS_AT_RISK_OF_ZERO_DOMINANCE`

## 4. Historical receipt spillover

`results/v77/REHEARSAL_ADAPTER_INTEGRATION_V1.json` remains on disk but was produced by the adapter before S161/S162/S167/S168 repairs.

That historical adapter:

- placed full normalized expression on `SyntheticModelBatch`;
- normalized using total library including hidden target counts;
- carried total library size on the model batch;
- carried source/operator directly on the model batch;
- sourced source/operator identity from hidden truth rather than the observer producer.

Therefore the V1 adapter receipt is:

`SUPERSEDED__HISTORICAL_REPRODUCTION_ONLY__NOT_CURRENT_ANTICHEAT_EVIDENCE`

The V2 integration receipt and PR223 zero-update bridge are the current rehearsal evidence.

## 5. Zero-update receipt wording hazard

The current zero-update receipt correctly records:

- `mutation_proof_status = NOT_PROVEN_BY_SHARED_INTERFACE`
- `q_safety_execution_proof_status = POLICY_ONLY_NOT_EXECUTION_PROVEN`
- challenge partition = `DEVELOPMENT_CALIBRATION`
- claim level = `NO_CLAIM`

It also contains the convenience field `no_mutation: true`.

That field must be read only as the intended behavior of this particular plumbing executor, not as a physical/transitive mutation proof. The later defect-register addendum explicitly preserves the unproven mutation status.

Classification:

`WORDING_HAZARD_CONTAINED_BY_LATER_AUTHORITY_RECORD`

## Authority unchanged

Training OFF; Stage A OFF; Stage 4 not authorized; TEST sealed; Morabito protected; no target winner; no representation winner; no selected estimand; seed 7302 remains development/calibration only.

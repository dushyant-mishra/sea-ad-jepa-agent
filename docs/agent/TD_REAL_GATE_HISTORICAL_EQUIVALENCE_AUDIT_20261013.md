# TD real-gate historical equivalence audit — 2026-10-13

Status: `OUTCOME_BLIND_EQUIVALENCE_AUDIT__NO_THRESHOLD_PROMOTION__NO_REAL_TD_AUTHORITY`

## Question

Which of the 33 frozen real-TD gate concepts already have an exact callable historical component implementing the same frozen estimand, and which still require prospective materialization?

This audit does not inspect current candidate outcomes and does not convert historical descriptive cutoffs into future decision thresholds.

## Result

The 33-gate universe partitions into three classes:

- **2 gates — exact historical component reuse with a thin gate wrapper:**
  - `Q1_Q_SCALAR_STUDENT_ABSENT`
  - `Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE`
- **3 gates — new prospective structural wrappers:**
  - `G1_INTEGRITY_LINEAGE`
  - `R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING`
  - `Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR`
- **28 gates — no exact qualified gate executor recovered; prospective rule still required.**

The 28 unresolved unique rules are the quantitative/biological decision surface. They remain blocked rather than inheriting descriptive thresholds from prior experiments.

## Exact historical reuse

`Q1` and `Q3` reuse the existing dependency-lineage guard:

- implementation: `scripts/v5/td_query_information_guard.py`
- Git blob: `3ca60c5f82b7b07f5f6123a52e7b50f9027a6ebe`
- tests: `tests/v5/test_td_query_information_guard.py`
- test Git blob: `849cfd9b65fadd0c54dfb9f534bcdddc413b4c98`

That component already rejects direct and transitive q-scalar/q-scalar-descendant paths into `student_sink` and `target_normalization_sink`, permits q-address conditioning, and fails closed on invalid/cyclic dependency graphs. The new gate wrapper additionally requires the relevant sink to exist, preventing a vacuous PASS.

This reuse is narrow: it supplies information-lineage exclusion only. It supplies no biological performance threshold.

## New prospective structural wrappers

### G1 — integrity/lineage

The frozen spec defines a structural provenance requirement: exact code/population/split/support/operator/evidence-rights/null-seed/prefreeze identities must be bound and post-outcome redesign/relabeling must be absent. No exact historical callable gate executor was recovered, so a prospective fail-closed wrapper was materialized.

### R2 — locality rule frozen/no fine mining

Historical TD57C/TD59 artifacts establish the project history and negative prior around fine-scale mining, but they are not an exact reusable R2 gate executor. The new wrapper checks only the prospective structural condition: locality rule frozen and forbidden fine-neighborhood mining absent. It does not turn historical TD57C/TD59 performance into a threshold.

### Q2 — q-excluded teacher primary anchor

The frozen candidate definition requires the primary teacher anchor to exclude q scalar. No exact historical callable gate executor was recovered, so a prospective structural predicate was materialized. It does not establish whether the resulting target is biologically useful.

## Explicit non-equivalence

The following are not sufficient to qualify a real biological gate merely because related historical calculations exist:

- raw donor/case falsifier deltas without a prospectively frozen gate decision rule;
- corrected-replay custody/readiness contracts;
- historical R2/cosine/null-count or locality results used as design context;
- fixture-generated executor/estimand/decision-rule hashes;
- synthetic gate performance by itself.

## Remaining blocker

Twenty-eight unique rules remain prospectively unresolved:

`G2,G3,G4,G5,G6,G7,G8,G9,G10,G11,G12,S1,S2,S3,R1,R3,R4,Q4,Q5,Q6,Q7,Q8,C6_INCREMENT_OVER_C1_C3,C4_INCREMENT_OVER_CONSTITUENTS,M1,M2,M3,M4`.

These correspond to 100 of the 117 required candidate×gate roles. They require endpoint-specific estimands and PASS/FAIL/NOT_ESTIMABLE rules prospectively frozen before current candidate outcomes are opened.

## Authority

No candidate outcome was opened. No historical descriptive cutoff was promoted. Real tournament QUALIFY remains ineligible. Target selection, representation selection, TD60, Stage4 and training remain unauthorized.

Terminal:

`FIVE_STRUCTURAL_RULES_MATERIALIZED_OR_REUSED__TWENTY_EIGHT_UNIQUE_RULES_STILL_REQUIRE_PROSPECTIVE_MATERIALIZATION__NO_REAL_TD_AUTHORITY`

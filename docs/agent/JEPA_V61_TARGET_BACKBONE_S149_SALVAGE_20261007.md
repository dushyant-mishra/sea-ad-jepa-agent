# JEPA V61 target-backbone S149 salvage — 2026-10-07

Status: `AUDIT_SALVAGE_ONLY__NO_EXECUTION_AUTHORITY__NO_TARGET_SELECTION`

This note classifies what may and may not be reused from PR #196 / V61 after the S149 measurement-process audit and the merged Stage-A V3 premise-qualification framework.

Hard boundaries: `TRAINING=OFF`; Stage A execution not authorized; encoder/predictor optimizer updates = 0; EMA updates = 0; TEST sealed; Morabito protected; target winner none; representation winner none; selected population estimand unset.

## 1. Historical V61 construction

V61 proposed a source-balanced common-state backbone by:

1. restricting to protein-coding addresses measured in all 42 operators (`n=15,758` in that historical construction);
2. selecting 400 features on one discovery sample by equal-weight average within-source variance across HVS, NPH52 and SEA_AD;
3. within each source, centering genes, regressing a detected-address-count proxy, standardizing residual gene variance and forming a source covariance;
4. averaging the three source covariances with equal source weight;
5. extracting a rotation-invariant top-k subspace and checking recurrence on independent discovery halves.

A stricter stress test then split donors into disjoint halves before feature selection/basis fitting and evaluated recurrence/projection with zero donor overlap.

These design choices are scientifically relevant to current Stage A because they avoid a pooled covariance dominated by source prevalence and treat subspace geometry rather than arbitrary individual PC coordinates as the stable object.

## 2. What cannot be inherited

The historical V61 discovery matrix was already normalized as `log1p(raw * 10000 / library)` under the old library-denominator path.

That means V61 cannot supply current q-safety, normalization-safety or S149 shortcut authority. Its numerical biology/source/operator eta-squared values, principal-angle recurrence values and any apparent preferred rank are historical diagnostics only.

The historical feature axis also belongs to the discovery lineage whose named-gene mappings were later found defective. No historical named-feature interpretation or numerical ranking is reusable without correct prospective reconstruction.

Therefore:

`V61_NUMERICAL_TARGET_BACKBONE_RESULT = SUPERSEDED_FOR_CURRENT_DECISION_AUTHORITY`

This is not a statement that the historical numerical pattern was necessarily false. It means it was measured under a preprocessing/provenance surface that cannot answer the current qualified question.

## 3. What may be salvaged prospectively

The following are reusable as candidate-construction logic, subject to prospective rebuild from authenticated q-safe inputs:

- common-support restriction before cross-source representation discovery;
- outcome/pathology-blind feature construction;
- source-local preprocessing/statistics before any source combination;
- explicit source balancing at the covariance/statistic-construction layer as a candidate design, not a selected foundation population estimand;
- donor-disjoint feature-selection/basis-recurrence stress testing;
- rotation-invariant subspace comparison with principal angles rather than post-hoc individual-PC semantics;
- refusal to regress operator where operator and biology are structurally aliased;
- separate reporting of biological-class, donor, source and identifiable operator structure;
- no target rank frozen from one favorable diagnostic.

## 4. Relationship to Stage-A representation families

A prospectively rebuilt V61-style construction can instantiate candidate arms inside:

- `GLOBAL_CELL_STATE`: the common source-balanced low-rank state/subspace as a cell-level representation;
- `PROGRAM_STATE`: the same construction treated as a reproducible multigene subspace/program backbone, with no coordinate-level semantics unless coordinate stability is separately qualified;
- `STRUCTURED_COMBINED_STATE`: a global/program backbone combined explicitly with an independently tested query-local component.

It does not replace `QUERY_LOCAL_STATE`, and it does not make the structured combined family the default.

## 5. Required prospective rebuild

Before any V61-style arm can contribute to the Stage-A deciding comparison:

1. start from authenticated TRAIN-only raw/count-derived evidence under the current population firewall;
2. bind a q-safe normalization satisfying the S149 Stage-A addendum;
3. use the authenticated all-42 common-scalar support or a prospectively declared outcome-blind subset;
4. freeze feature-selection rules before held-donor outcomes;
5. run feature selection and basis fitting on inner-TRAIN donors only;
6. evaluate basis/subspace recurrence on donor-disjoint held units;
7. run source/operator/depth/support/normalization shortcut controls before interpreting biological structure;
8. report source-specific results before any source-balanced aggregate;
9. leave subspace rank, dimensionality and decision margins unset until prospectively authorized;
10. never import historical V61 numerical thresholds, ranks or candidate winner language.

## 6. Source balancing is not the selected population estimand

Equal-source covariance averaging in a representation-construction arm is a methodological device for preventing the largest source from defining the candidate basis by cell abundance alone.

It does **not** select `SOURCE_BALANCED_DONOR_WEIGHTED` as the future foundation-model population estimand. The production estimand remains `UNSET_REQUIRES_APPROVAL` under the merged V3 population contract.

Any deciding Stage-A inference must still use donor-level biological units and explicitly report sensitivity to the eventual approved estimand where relevant.

## 7. Operator/biology aliasing guard

V61 correctly observed that in historical HVS/NPH52 strata operator identity could be structurally aliased with broad biological class, making naive operator residualization scientifically destructive.

Carry this guard forward:

- do not residualize operator merely to make a representation look technology-invariant;
- where operator and biology are not separately identifiable, mark the axis `NOT_IDENTIFIABLE_UNDER_CURRENT_CONFOUNDING`;
- where operator variation exists within comparable biology, measure residual observation-process imprint there;
- never interpret lower source/operator predictability by itself as stronger biology.

## 8. Current classification

Historical V61 result:

`INFORMATIVE_HISTORICAL_DISCOVERY__NUMERICAL_AUTHORITY_SUPERSEDED`

V61 construction logic:

`PROSPECTIVELY_REUSABLE_AS_GLOBAL_OR_PROGRAM_STAGE_A_CANDIDATE__REBUILD_REQUIRED`

No target, representation, subspace rank, feature list, normalization rule, population estimand or numeric margin is selected by this audit.

## Terminal

`V61_S149_SALVAGE_CLASSIFIED__CONSTRUCTION_REUSABLE__RESULT_NOT_AUTHORITY__NO_WINNER`

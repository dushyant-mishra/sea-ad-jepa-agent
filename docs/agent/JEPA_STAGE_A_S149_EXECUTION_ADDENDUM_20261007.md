# JEPA Stage-A S149 execution addendum — 2026-10-07

Status: `PREFREEZE_SCIENTIFIC_ADDENDUM__NO_EXECUTION_AUTHORITY`

Parent contract: `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_V3_PREFREEZE_20261006.md`.

This addendum refines how the already-merged Stage-A V3 real-RNA target/representation gate must handle the S149 measurement-process confounding finding. It does not replace V3, select a target, select a representation, select an estimand, choose a numeric margin, or authorize execution.

Hard boundaries remain unchanged: `TRAINING=OFF`; encoder/predictor optimizer updates = 0; EMA updates = 0; `STAGE_A_EXECUTION=NOT_AUTHORIZED`; TEST sealed; Morabito protected; no pathology/outcome label available for selection; no external validation outcome available for target/readout/threshold/control tuning.

## 1. Scope and candidate neutrality

All four V3 representation families remain eligible:

- `GLOBAL_CELL_STATE`
- `QUERY_LOCAL_STATE`
- `PROGRAM_STATE`
- `STRUCTURED_COMBINED_STATE`

No family has incumbent priority.

Within `QUERY_LOCAL_STATE`, the historical value-blind constructions `T_B1` and `T_B2` remain candidate sub-arms. `T_A` is not a lawful positive candidate for the stated query-local latent-state claim because the query scalar enters the teacher before contextual mixing; it may exist only as a leakage/reference arm. `T_C` remains blocked by the unresolved block/masking authority and is not rescued by this addendum.

## 2. Binding S149 interpretation

The current qualitative S149 finding is that pooled real-RNA topology is strongly affected by study/cohort measurement composition. The correct scientific response is not to regress out study and call the residual biology, and not to demand that technology become universally unpredictable.

The binding principle is:

`biology within observation process + transport across observation process`

Donors are biological replicates. Cells are observations. Source/study/operator/technology structure may correlate with real biology, so a source-predictability score by itself is not a biological failure criterion.

What must fail is a candidate whose deciding RNA-representation advantage is already explained by trivial measurement channels such as support, normalization denominator, depth, operator/source identity, or their combinations.

## 3. First controlled substrate: common support

For the first controlled Stage-A execution, use the authenticated all-42-operator common-scalar substrate of 17,186 molecular addresses, or a prospectively declared subset derived from that substrate without inspecting deciding candidate outcomes or pooled biological topology.

Purpose: remove the simplest structural-support barcode before asking whether a representation transports.

This is a controlled qualification substrate, not a production 41K restriction and not a claim that biology outside the common support is irrelevant.

A later 41K extension is a distinct experiment. It must separately quantify visibility/support/missingness shortcuts and cannot inherit the common-support result as proof that 41K support states are harmless.

## 4. Normalization is a first-class observation operator

Historical Audit A showed that the production `source_library` denominator carried enough source-specific information for donor-honest source classification to reach 104/104 in that historical substrate. Therefore common support alone does not remove the measurement barcode.

No total-count/source-library normalization is automatically lawful for the deciding Stage-A run merely because it is conventional.

Before any deciding target/representation score is opened, freeze a q-safe normalization policy satisfying all of:

1. changing the hidden query scalar alone cannot change any visible normalized input;
2. changing any other hidden value cannot change visible normalized inputs when that value is outside the lawful evidence view;
3. the normalization rule is independent of mask realization except where a prospectively declared fixed-reference rule explicitly permits otherwise;
4. its source/operator information content is measured as a control, not silently ignored;
5. the exact normalization operator is included in the execution receipt.

Candidate policy classes may include raw/mask-independent values or a prospectively frozen reference-set normalizer. This addendum selects none.

`N_TOTAL_COUNT_INCLUDING_QUERY` is not eligible for q-safe query-local discrimination because it makes every visible token a deterministic descendant of q.

Required counterfactual test: perturb q while holding all lawful visible raw evidence fixed. Under a q-safe input construction, every non-q model-facing input must remain bit-identical.

## 5. Required measurement-shortcut controls

Every candidate family must face, where structurally applicable, the same prospectively frozen control roster:

- address/gene identity only;
- wrong-query / query-exchangeability;
- capacity-matched global summary;
- source/operator identity only;
- depth/library-size only;
- visibility/support/missingness only;
- normalization-denominator only;
- technical/QC-only;
- support × normalization composite;
- biology-absent / covariance-only control where applicable.

The controls are falsifiers, not covariates to regress away from the candidate.

A candidate receives `FAIL_SHORTCUT` if a shortcut control satisfies the prospectively frozen deciding rule or if the candidate's apparent advantage disappears once the trivial measurement channel is removed in the matched counterfactual comparison.

Do not tune a threshold upward or downward to rescue a candidate after a shortcut control fires.

## 6. Biological unit and estimand discipline

The biological resampling unit is the donor unless a later authority explicitly proves another unit is appropriate.

The deciding Stage-A statistic must not be a pooled cell-weighted statistic across HVS, NPH52 and SEA_AD.

Within each declared observation/source stratum, use an approved donor-primary rule such as equal-donor contribution or another prospectively selected donor-primary weighting. The exact population estimand and any cross-source combination weights remain `UNSET_REQUIRES_APPROVAL`.

Report per-source results before any combination.

A donor-cluster bootstrap does not by itself make a cell-weighted statistic equal-donor; the point statistic and resampling scheme must both be explicit.

## 7. Transport axes and identifiability

Keep the V3 axes separate:

- `DONOR_TRANSFER`
- `OPERATOR_TRANSFER`
- `STUDY_TRANSFER`
- `TECHNOLOGY_TRANSFER`

In FULL104, study/source and measurement process can be tightly confounded. When the available design cannot separate study from technology, report `NOT_IDENTIFIABLE_UNDER_CURRENT_CONFOUNDING` rather than assigning separate PASS states.

Cross-source transport is evaluated only across prospectively declared biologically comparable strata. A difference in cell-class composition is not automatically a representation-transport failure and may not be corrected post hoc by regressing source labels from the representation.

The primary question is whether the candidate captures repeatable biological structure within each observation process and whether that structure transports where the design makes transport identifiable.

## 8. Query-local target sub-arms

For `QUERY_LOCAL_STATE`, Stage A should include at minimum the following pretraining constructions if the required value-blind tokenizer/readout path exists:

- `T_B1`: value-blind query slot, teacher hides query value only;
- `T_B2`: value-blind query slot, teacher uses the same visible set as the student.

They must be compared under the same q-safe normalization, same common-support substrate, same donor partitions, same query roster, same readout capacity policy and same evaluation metrics.

`T_A` may be retained only as a planted leakage/reference arm and must not be eligible for qualification under the stated query-local claim.

The T_B1/T_B2 comparison remains `TARGET_OBJECT_RECOVERABILITY`, not biological-truth validation.

## 9. Fitting and held-donor firewall

Any fitted diagnostic readout:

- fits only on a prospectively declared inner-TRAIN donor set;
- freezes features, target, hyperparameters, alignment and control capacities before held-donor evaluation;
- receives no held-donor information during fitting or model selection;
- records donor identities/partitions in the execution receipt;
- cannot update the JEPA encoder, predictor or EMA teacher.

Capacity matching is required for shortcut controls. An intentionally weak control cannot earn a candidate a PASS.

## 10. Ordered execution sequence

A later execution authority must preserve this ordering:

1. authenticate TRAIN-only population, support map, partition and observation-operator identities;
2. bind the common-support substrate or its prospectively declared outcome-blind subset;
3. execute q-counterfactual and normalization/support leakage tests before candidate scoring;
4. construct every candidate target/representation under the frozen rules;
5. execute the common shortcut-control roster;
6. evaluate held-donor transfer within each observation/source stratum under the approved donor-primary statistic;
7. evaluate cross-source/operator transport only where biologically and statistically identifiable;
8. evaluate representation/subspace stability;
9. evaluate biological-evidence convergence separately from measurement-depth convergence;
10. only then issue a Stage-A scientific verdict.

STOP rather than continue if an earlier absolute leakage or shortcut gate fails.

## 11. Historical evidence classifications carried into this addendum

The following historical artifacts inform design but do not decide the Stage-A winner:

- PR #33 information-channel audit: establishes that support/normalization/source channels can be strong and that a within-donor-centred score can be blind to donor/source-level shortcuts. It does not provide a current Stage-A pass threshold.
- PR #177 V44 real-RNA proxy tournament: useful experimental shape, but its numerical architecture ranking is not reusable because the historical feature-axis lineage was later found defective; correct decoded replay would be required for any numeric claim.
- PR #178 synthetic T_A/T_B comparison: `NOT_INFORMATIVE` for real biology and cannot select T_B1/T_B2.
- TD41/TD43: S149-safe cross-source validation/measurability evidence after genealogy recovery, but explicitly `NO_TARGET_AUTHORITY`.
- D1 program-level machinery: donor-first/statistical procedures are reusable; no program target was produced because the lane correctly stopped at `WAIT_HEALTHY_TRAINED_TEACHER`.

## 12. Smallest future Stage-A execution consistent with this addendum

Not authorized by this document.

The smallest scientifically informative real-RNA execution would:

- remain TRAIN-only;
- perform zero encoder/predictor optimizer steps and zero EMA updates;
- use the common-support controlled substrate first;
- use a prospectively frozen q-safe normalization;
- keep all four V3 representation families eligible;
- include `T_B1` and `T_B2` as query-local sub-arms if mechanically realizable;
- use held-donor evaluation with explicit donor-primary weighting;
- report source/operator/study/technology axes separately and honestly mark non-identifiable axes;
- run the full shortcut roster before any aggregate winner rule;
- use no protected outcome or external biological result to rescue selection;
- leave all numeric deciding margins unset until prospectively approved.

## Terminal

`S149_STAGE_A_EXECUTION_CONTRACT_REFINED__NOT_EXECUTED__NO_WINNER__ESTIMAND_UNSET`

No production-training authority is created or implied.
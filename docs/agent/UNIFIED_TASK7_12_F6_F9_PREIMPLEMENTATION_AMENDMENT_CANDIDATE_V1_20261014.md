# Unified Tasks 7–12 F6–F9 preimplementation amendment candidate V1 — 2026-10-14

## Status

`ANALYSIS_ONLY__REQUIRED_BEFORE_AFFECTED_TASK_IMPLEMENTATION__DO_NOT_EDIT_ACCEPTED_PLAN_SILENTLY`

This document records obligations discovered by the Task 0 F6–F9 re-audit that are not explicit enough in accepted PR #380 head `9328f1c00faee8a0ebf1910d412ea129bab566be`.

It does not start Tasks 7–12 and does not change current authority.

Global authority:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Machine source:
`results/target_discovery/unified_qualification_v1/DOWNSTREAM_INHERITED_OBLIGATIONS_F6_F9_V1.json`

---

## 1. Why an explicit amendment is needed

The accepted Task 7 bundle contract generically requires limitations/forbidden interpretations, and Task 8 generically requires permanent historical hostile obligations. That is necessary but no longer sufficient after Task 0 F6–F9.

Without explicit machine-testable inheritance, a future implementation could pass the accepted generic tests while silently losing:

- Foundation `SUBSPACE_ONLY` and partial matrix-identifiability limits;
- same-nucleus versus separate-nucleus multimodal provenance;
- the distinction between independently measured ATAC evidence and RNA-derived regulatory hypotheses;
- FULL104 normalization-denominator/source shortcuts, unequal evidence burden, lawful non-estimability and metric blindness;
- runtime safety as a separate prerequisite between downstream scientific certification and training eligibility.

Therefore the following additions must be incorporated prospectively before the affected task begins.

---

## 2. Task 7 — Target Qualification Bundle required additions

Add RED tests equivalent to:

```python
def test_bundle_preserves_representation_scope_and_forbidden_axis_semantics(): ...
def test_bundle_preserves_matrix_identifiability_and_unavailable_matrix_scope(): ...
def test_bundle_cannot_claim_technology_invariance_when_not_qualified(): ...
def test_bundle_preserves_source_acquisition_limitations_without_relabeling_as_pure_technical(): ...
def test_bundle_binds_multimodal_evidence_provenance_and_observation_operator(): ...
def test_bundle_distinguishes_same_nucleus_from_separate_nucleus_evidence(): ...
def test_bundle_cannot_promote_rna_derived_edge_or_nearest_gene_to_independent_regulatory_truth(): ...
def test_bundle_preserves_incomplete_stopped_regulatory_work_and_negative_graph_control_prior(): ...
def test_bundle_preserves_normalization_library_provenance_and_full_library_mass_scope(): ...
def test_bundle_preserves_per_source_estimability_and_no_zero_fill_interpretation(): ...
def test_bundle_preserves_metric_blindness_and_nuisance_source_channel_obligations(): ...
```

Required bundle fields or equivalent schema coverage:

- `representation_scope`
- `technology_invariance_qualified`
- `matrix_identifiability_scope`
- `unavailable_matrices_or_strata`
- `source_acquisition_limitations`
- `forbidden_axis_semantics`
- `evidence_provenance`
- `observation_operator`
- `same_nucleus_vs_separate_nucleus`
- `independence_boundary`
- `regulatory_truth_status`
- `incomplete_stopped_regulatory_work`
- `negative_graph_control_prior`
- `normalization_and_library_provenance`
- `full_library_mass_where_decision_bearing`
- `support_and_estimability_scope`
- `no_zero_fill_interpretation`
- `metric_blindness_limitations`
- `nuisance_source_channel_obligations`

`TARGET=NONE` bundles must preserve the same limitations and obligations rather than dropping them because no target was selected.

---

## 3. Task 8 — downstream certification required additions

The historical hostile-obligation set must explicitly include these F6/F7/F9 failures in addition to the already listed normalization/query/hidden-total/support leakage and teacher/student failures:

### F6 representation failures

- `AXIS_SEMANTICS_SUBSTITUTED_FOR_SUBSPACE`
- `UNIVERSAL_TECH_TRANSFER_CLAIMED_FROM_PARTIAL_COVERAGE`
- `UNAVAILABLE_MATRICES_DROPPED_FROM_LIMITATION_SCOPE`
- `SOURCE_ACQUISITION_SIGNAL_DECLARED_PURE_TECHNICAL_WITHOUT_QUALIFICATION`

### F7 multimodal/regulatory failures

- `SAME_AND_SEPARATE_NUCLEUS_CONFLATED`
- `RNA_DERIVED_EDGE_USED_AS_INDEPENDENT_REGULATORY_TRUTH`
- `NEAREST_GENE_PROMOTED_TO_CAUSAL_TARGET`
- `INCOMPLETE_SCENIC_WORK_PROMOTED`
- `STRUCTURALLY_IDENTICAL_GRAPH_CONTROL_ACCEPTED`

### F9 information-channel failures

- `DENOMINATOR_SOURCE_SHORTCUT_UNTESTED`
- `ADDRESS_PARITY_TREATED_AS_EVIDENCE_PARITY`
- `NONESTIMABLE_TARGET_ZERO_FILLED`
- `METRIC_USED_TO_CERTIFY_ABSENCE_OF_CHANNEL_IT_IS_INVARIANT_TO`

Add RED tests equivalent to:

```python
def test_every_f6_f7_f9_inherited_obligation_has_exercised_receipt(): ...
def test_subspace_only_bundle_cannot_be_consumed_as_axis_semantics(): ...
def test_partial_matrix_scope_cannot_be_widened_downstream(): ...
def test_same_separate_nucleus_provenance_cannot_be_erased(): ...
def test_rna_regulatory_hypothesis_cannot_be_relabelled_as_independent_atac_truth(): ...
def test_normalization_denominator_shortcut_requires_explicit_adversarial_receipt(): ...
def test_nonestimable_target_cannot_be_zero_filled_for_downstream_score(): ...
def test_metric_blindness_limitation_cannot_be_dropped(): ...
```

A downstream receipt is invalid if an inherited obligation is present in the TQB but absent from exercised downstream test receipts.

---

## 4. Task 9 — challenge family additions

Existing A–I families already cover many structural cases, but the Task 0 re-audit requires explicit challenge realizations for:

- normalization denominator/source shortcut;
- equal address count with unequal evidence burden;
- silent/nonvarying target where zero-fill would create false ease;
- within-donor metric mathematically blind to a donor/source affine channel;
- same-nucleus versus separate-nucleus provenance distinction;
- RNA-derived regulatory hypothesis versus independently measured ATAC evidence;
- structurally identical graph-control trap.

These can be subfamilies of existing F/G/I where scientifically coherent; they need not create new top-level letters. The requirement is that each failure mode is executable and receipt-bearing.

---

## 5. Task 11/12 — old Task 2 custody external obligations

The old PR #356 Task 2 custody module explicitly leaves several guarantees to packaging/finalization/whole-pipeline review. They must be placed prospectively as follows.

### Task 11 finalizer / CI

Add requirements/tests for:

- one anchored genesis ledger identity per testbed;
- exact expected ledger head verification against the externally published prior head;
- receipt index includes both method-local and lineage-wide qualification draw multiplicity;
- revealed realization content is regenerated and content digests are checked before final qualification receipt;
- secret-scan receipt binds an exact committed-tree identity, not a dirty/sparse working tree.

### Task 12 independent hostile audit

Explicitly adjudicate:

- no alternate genesis/new ledger can bypass exposure history;
- no tail truncation/re-chaining can pass anchored-head verification;
- no method relabel can reset lineage-wide qualification multiplicity;
- every published committed tree required by sealed custody was scanned at the promised scope;
- generator-defect records were independently reviewed rather than accepted as self-declared truth.

---

## 6. F8 — explicit runtime eligibility bridge after Task 8

The accepted plan correctly says Task 8 does not toggle project training authority, but the qualification-stage model contains:

`DOWNSTREAM_CERTIFIED → TRAINING_ELIGIBLE → TRAINING_AUTHORIZED`

Task 0 F8 establishes that downstream scientific certification alone cannot justify the first of those transitions.

Before any future `TRAINING_ELIGIBLE` promotion, require a distinct typed receipt, provisionally:

`RUNTIME_ELIGIBILITY_RECEIPT_V1`

It must bind at minimum:

- exact downstream certification receipt identity;
- exact runtime source identity;
- exact typed checkpoint/continuation identity;
- `OPTIMIZER_COMPLETION_BEFORE_EMA` proof;
- `NO_EMA_ADVANCE_ON_REJECTED_OR_INCOMPLETE_UPDATE` proof;
- `COORDINATE_VALUE_COUPLING` proof;
- final joined `Q_SAFETY` execution proof;
- explicit statement that runtime correctness does not expand target/representation/evidence scope.

Required law:

`DOWNSTREAM_CERTIFIED` **cannot** promote to `TRAINING_ELIGIBLE` without a valid active `RUNTIME_ELIGIBILITY_RECEIPT_V1` whose parents recompute to the exact downstream and runtime artifacts.

This receipt does not itself authorize training; `TRAINING_AUTHORIZED` remains a separate later authority decision.

---

## 7. Withdrawn finding preservation

`FULL104_G_WITHDRAWN__DO_NOT_RESURRECT` remains a negative governance invariant.

No challenge, bundle limitation or downstream obligation may reintroduce the withdrawn calibration-cache distortion claim merely because other FULL104 findings are inherited.

---

## 8. Incorporation gate

Before implementation of Task 7 or Task 8 begins, the accepted execution plan must be prospectively amended or the task-specific reviewed spec must contain equivalent machine-testable requirements.

Do not silently treat this analysis file as authority sufficient to change an already-running task.

Terminal state:

`F6_F9_TASK7_12_AMENDMENT_REQUIREMENTS_FROZEN__TASK7_8_NOT_STARTED__RUNTIME_ELIGIBILITY_BRIDGE_REQUIRED__NO_TRAINING_AUTHORITY`

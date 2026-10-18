# Unified Task 5 CaseBundle / TruthBundle / mode-equivalence contract V1 — 2026-10-14

## Status

`ANALYSIS_ONLY__PREIMPLEMENTATION_CONTRACT__TASK5_NOT_STARTED`

This document refines accepted Architecture V1 §6–7 plus V1.1 A4/A7 and accepted Task 5. It creates no known-truth or human outcome and authorizes no execution.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

---

## 1. One scientific path, two external wrappers

The scientific path is one path:

```text
observable gate-facing payload
→ manifest/access validation
→ exact registered producer
→ authenticated artifact
→ exact registered executor
→ metric/support/reference/status logic
→ TD/controller output
```

Known-truth and human-sealed modes may differ only outside that path.

Known-truth owns a separate hidden `TRUTH_BUNDLE_V1`; human mode does not.

The TruthBundle is never an argument, parent, metadata side channel, cache key, seed namespace, baseline selector, support selector, reference selector, or branch input to scientific code.

---

## 2. `KNOWN_TRUTH_CASEBUNDLE_V1` required structure

Required fields or exact equivalents:

```text
casebundle_schema
casebundle_identity
manifest_compatibility_identity
canonical_address_universe
population_hierarchy
partition/access projection
candidate/endpoint/source/operator identities
observation_payloads
observation_state_payloads
library_mass_payloads
support_payloads
evidence_rights_payloads
normalization_provenance
biological_context_metadata
measurement_technology_metadata
nuisance_context_metadata
reference_generation_observables
numeric_definedness_metadata
parent_receipt_digests
```

### 2.1 Canonical addresses

Every molecular feature is addressed through the same canonical address identity system used by human execution. Synthetic/known-truth local row position cannot be scientific identity.

### 2.2 Population hierarchy

The bundle must be able to represent donor/source/operator/cell hierarchy and ragged support without requiring balanced matrices.

Known-truth partition labels implement the same **logical** access roles as the manifest policy. A known-truth wrapper cannot bypass `reader_fit`/protected-partition semantics merely because no human data are being used.

---

## 3. Observation semantics

The CaseBundle must distinguish at minimum the controlling semantic categories required by Architecture V1:

- measured scalar observations;
- structural/unmeasured observations;
- collision/unresolved observations;
- evidence-right withholding/blocked access.

A measured value of numeric zero remains a measurement. It must never be reclassified as unsupported, structural absence, unresolved measurement, or evidence-right denial merely because its value is zero.

If the final schema uses an explicit `MEASURED_ZERO` token, that token remains inside the measured family and is not an absence state. If instead zero is represented as `MEASURED_SCALAR` with value `0`, the same law holds. The implementation must choose one unambiguous schema and test it prospectively; it must not allow both representations to acquire divergent scientific meaning.

### 3.1 Numerical failure is separate

Failure to compute a required statistic is not an observation state and not biological FAIL. Numerical definedness/status is carried separately from measured/unmeasured/evidence semantics.

---

## 4. Library-mass semantics

The CaseBundle must separately represent, where decision-bearing:

```text
stored/measured scalar counts
unmaterialized or off-address library mass
full normalization-library quantity
structural/unmeasured state
collision/unresolved state
evidence-right withholding
```

A lawful depth/thinning operator acting on measured counts must transform the corresponding normalization-library quantity consistently.

A count can thin to zero while remaining measured.

F9 applies: a normalization denominator is an information channel and its source/provenance is part of the observable contract.

---

## 5. Evidence acquisition versus measurement depth

Evidence rights and measurement depth are orthogonal axes.

The CaseBundle must support scenarios where:

- an address is measurable but withheld by evidence rights;
- an address is lawfully acquired but measured shallowly;
- an address is structurally unmeasurable regardless of depth;
- an address is measured zero;
- an address is unresolved due to collision/measurement ambiguity.

No depth operation may manufacture an evidence right. No evidence-right expansion may be presented as merely deeper remeasurement.

---

## 6. Technology and biology

Technology descriptors describe the physical measurement operator, for example modality/platform/chemistry/vocabulary/depth/detected-feature/count-split/acquisition properties where physically justified.

They do not define latent biological identity.

Known-truth biology must include donor/state/context variation that can remain source-associated; the generator must not erase legitimate biological variation merely because it predicts source.

Arbitrary dataset labels cannot be used as a shortcut to choose latent biological truth.

---

## 7. `TRUTH_BUNDLE_V1` contents and firewall

The TruthBundle may contain hidden controller-known quantities such as:

```text
latent biological mechanisms
true candidate/target identity or TARGET=NONE truth
true support/estimability class by construction
true positive/negative/null class
challenge-family identity
expected lawful terminal TD state
malformed-artifact truth
hidden novelty/mechanism labels
```

Required laws:

1. physical/logical object separation from CaseBundle;
2. no TruthBundle digest appears as a scientific-path parent/input;
3. no hidden truth field name/value appears in the CaseBundle payload tree;
4. TruthBundle is unreadable by producers/executors/controller until normal output is frozen;
5. post-freeze adjudicator may score only; it cannot repair, rerun, retune, select, discard, reseed or replace a world.

---

## 8. Scientific execution trace

`ScientificExecutionTrace` must commit the decision-bearing path, not only final output.

Required identities or equivalents:

```text
manifest/access validator identities
population access policy identity
actual access receipt identity
producer entrypoint/code identities
artifact schema + serializer identities
receipt validator identities
executor entrypoint/code identities
metric implementation identities
support logic identity
reference logic identity
status/abstention logic identity
branch-condition trace digest
scientific output digest
```

External wrapper-only events such as TruthBundle adjudication are excluded from this trace.

---

## 9. `MODE_PATH_EQUIVALENCE_RECEIPT`

A SAME_CODE_PATH claim requires machine comparison of known-truth and human-sealed wrappers given semantically equivalent observable payloads.

Required fields or equivalents:

```text
observable_payload_digest
known_truth_execution_trace_digest
human_mode_execution_trace_digest
producer_identity_set_digest
executor_identity_set_digest
validator_identity_set_digest
branch_condition_audit_digest
access_policy_equivalence
support_logic_equivalence
reference_logic_equivalence
metric_equivalence
status_logic_equivalence
scientific_output_equivalence
permitted_wrapper_differences
parent_receipt_digests
independent_review_identity
```

### 9.1 Equivalence is structural, not only numerical

Two modes producing the same final number are **not** same-code-path if they traversed different scientific branches, validators, support/reference logic or access policy.

Conversely, truth adjudication can legitimately differ because it is external to the scientific trace.

---

## 10. Prohibited known-truth-only scientific branches

Hard failures include:

```text
synthetic-only threshold
synthetic-only support law
synthetic-only null law
synthetic-only metric orientation
synthetic-only baseline roster
synthetic-only reference construction
relaxed receipt validation in known truth
truth-dependent estimability or abstention
truth-dependent seed/RNG namespace
truth-dependent producer selection
truth-dependent candidate or winner policy
```

A generic wrapper flag such as `is_synthetic` must not be visible to decision-bearing scientific functions unless the only use is external logging/trace metadata proven not to affect scientific branching.

---

## 11. F7 multimodal provenance in CaseBundle

Where multimodal evidence is present, the CaseBundle must bind:

- modality;
- same-nucleus versus separate-nucleus observation operator;
- independently measured evidence versus RNA-derived hypothesis;
- regulatory-truth status.

Independent ATAC measurement can test a regulatory hypothesis. An RNA-derived edge, nearest-gene mapping or proximity mapping cannot become hidden truth merely because it was used to propose the candidate.

Incomplete stopped SCENIC+ work remains unavailable as answer-key truth.

---

## 12. Required hostile RED tests beyond accepted Task 5

```python
def test_measured_zero_cannot_be_relabelled_as_structural_absence(): ...
def test_measured_zero_cannot_be_relabelled_as_evidence_denial(): ...
def test_numerical_failure_is_not_an_observation_state_or_biological_fail(): ...
def test_depth_thinning_updates_matching_library_quantity(): ...
def test_depth_change_cannot_grant_new_evidence_right(): ...
def test_truth_digest_cannot_enter_scientific_parent_chain(): ...
def test_truth_field_hidden_in_metadata_or_rng_namespace_is_rejected(): ...
def test_same_numeric_output_with_different_scientific_branch_is_not_equivalent(): ...
def test_known_truth_and_human_access_policy_paths_are_trace_equivalent(): ...
def test_multimodal_same_nucleus_and_separate_nucleus_operator_identity_differs(): ...
def test_rna_derived_regulatory_hypothesis_is_not_truthbundle_independent_measurement(): ...
```

---

## 13. Terminal state

`TASK5_CASE_TRUTH_EQUIVALENCE_CONTRACT_FROZEN__TRUTH_FIREWALL_EXPLICIT__MEASURED_ZERO_PRESERVED__TASK5_NOT_STARTED__NO_AUTHORITY_CHANGE`

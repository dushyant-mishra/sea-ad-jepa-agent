# Unified Task 2 manifest/access schema contract V1 — 2026-10-14

## Status

`ANALYSIS_ONLY__PREIMPLEMENTATION_CONTRACT__TASK2_NOT_STARTED`

This document refines the accepted Task 2 interface at PR #380 head `9328f1c00faee8a0ebf1910d412ea129bab566be`. It does not authorize implementation before Task 0 independent acceptance and does not invent current candidate outcomes.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Current population law remains:

- current TD may use only `reader_fit` values under deterministic cross-fitting;
- `reader_validation` value access is denied;
- `reader_oracle` value access is denied;
- no protected partition may rescue support, estimability, reference generation, threshold selection, model fitting, baseline choice or a failed/underpowered result.

---

## 1. Design principle: access authority must describe what actually happened

A manifest declares what a producer **may** access. A `ProducerAccessReceipt` records what the producer **did** access.

Neither can stand in for the other.

A numerically correct artifact is invalid if its access receipt proves a forbidden read.

An intended-access declaration such as `held_out=true`, `fit_only=true`, or `no_oracle=true` has no authority unless the actual access receipt independently supports it.

---

## 2. `PopulationAccessPolicy` required fields

Required semantic fields or exact equivalents:

```text
schema_version
policy_id
policy_semantic_digest
population_registry_digest
partition_registry_digest
allowed_partition_classes
forbidden_partition_classes
current_td_mode
crossfit_policy
protected_partition_policy
support_resolution_policy
reference_generation_policy
normalization_library_policy
candidate_outcome_access_policy
authority_scope
parent_receipt_digests
```

### 2.1 Current fixed values

For current TD:

```text
current_td_mode = READER_FIT_CROSSFIT_ONLY
allowed_partition_classes = [reader_fit]
forbidden_partition_classes = [reader_validation, reader_oracle]
candidate_outcome_access_policy = CLOSED
```

The policy may bind exact authenticated population counts as integrity assertions, but counts do not substitute for membership identities.

Current audited navigation facts that can be checked against the bound population registry include:

- total donors: 149
- reader_fit donors: 104
- reader_validation donors: 22
- reader_oracle donors: 23
- reader_fit nuclei: 4,553,407
- reader_fit donor×operator groups: 1,400

These values are integrity context, not a license to reconstruct membership from counts.

---

## 3. Cross-fitting contract

`crossfit_policy` must bind all decision-bearing fold semantics before candidate outcomes are visible.

Required fields or equivalents:

```text
assignment_object_digest
assignment_algorithm_identity
identity_keys
n_folds
fold_labels
fit_role
heldout_role
stratification_keys_if_any
candidate_independent = true
outcome_independent = true
storage_order_independent = true
```

No fold count is frozen by this analysis document. `n_folds` must be an explicit prospective manifest value when Task 2 is implemented.

### 3.1 Required laws

1. Assignment is a function of frozen scientific identities/policy only.
2. Reordering rows/files/shards cannot move a donor/cell between folds.
3. Candidate identity cannot change fold assignment unless a prospectively different candidate-specific policy is explicitly authorized by the manifest; current default is candidate-independent.
4. Candidate outcome values cannot influence assignment.
5. Every evaluation row has exactly one lawful held-out role inside `reader_fit`.
6. The same `reader_fit` observation cannot be simultaneously treated as train and held-out for the same decision unit unless the declared estimator explicitly defines a nested lawful structure and its receipt exposes that structure.
7. `reader_validation` and `reader_oracle` cannot appear in any fold.
8. Missing support inside a held-out `reader_fit` fold remains missing/unsupported/not-estimable as appropriate; it cannot be replaced by protected-partition values.

---

## 4. `ProducerAccessReceipt` required fields

Required fields or exact equivalents:

```text
schema_version
receipt_id
producer_identity_digest
producer_policy_digest
manifest_digest
population_access_policy_digest
input_artifact_digests
output_artifact_digest
execution_identity
start_state_digest
actual_access_events_digest
actual_partition_classes
actual_access_classes
actual_population_membership_digest
actual_cell_count
actual_donor_count
actual_source_set_digest
actual_operator_set_digest
crossfit_assignment_digest
folds_touched
normalization_library_provenance_digest
support_evidence_provenance_digest
forbidden_access_detected
forbidden_access_classes
status
parent_receipt_digests
```

### 4.1 `actual_access_events_digest`

This is decision-bearing. It must summarize/commit the actual lower-level read events or a content-addressed access log, not a caller-authored sentence saying what the producer intended to read.

The implementation may choose an efficient receipt representation, but it must make these hostile cases distinguishable:

- declared `reader_fit` only, actual `reader_fit` only → potentially lawful;
- declared `reader_fit` only, actual one `reader_validation` read → invalid;
- declared no oracle, actual oracle metadata-only read → whether lawful depends on a separately typed metadata-vs-value access class, never on an untyped partition token;
- declared held-out, no actual access log → invalid/unverifiable;
- numerically identical output after forbidden read → invalid.

---

## 5. Typed access classes

Partition identity and access class are orthogonal.

At minimum distinguish classes equivalent to:

```text
VALUE_READ
MEMBERSHIP_IDENTITY_READ
NON_OUTCOME_METADATA_READ
SCHEMA_READ
SUPPORT_RIGHTS_READ
NORMALIZATION_LIBRARY_READ
REFERENCE_ARTIFACT_READ
```

Do not use a single `READ` boolean if the scientific law treats metadata, counts, support/evidence rights and protected outcome values differently.

For current TD, the policy must explicitly state which non-value metadata classes, if any, are lawful for protected partitions. Absence of such a declaration means deny by default.

Protected **value** access is denied.

---

## 6. F9 normalization/library provenance

Task 0 FULL104 custody makes normalization/library provenance part of the access law whenever it is decision-bearing.

The manifest/access policy must bind:

- source-library/normalization denominator definition;
- whether denominator mass is stored, unmaterialized/off-address, or full-library mass;
- exact observation operator that generates both numerator counts and normalization-library quantity;
- source/donor/operator hierarchy used by the producer;
- any per-source estimability policy.

A producer cannot claim `reader_fit`-only access while consuming a normalization denominator computed from forbidden protected values.

A count matrix and its normalization library are one access dependency graph for this purpose.

---

## 7. Support/evidence access law

Support cannot be manufactured by access-policy generalization.

Required status distinctions remain:

- measured scalar / measured zero;
- unmeasured structural;
- unresolved/collision state;
- blocked evidence contract.

A producer receipt must bind the exact support/evidence-rights artifact used.

Generic source coverage is not candidate-specific evidence support.

Protected partitions cannot be consulted to reclassify a current `reader_fit` candidate from unsupported/not-estimable to supported/estimable.

---

## 8. Manifest identity content

`TDExecutionManifest` must bind exact semantic identities for at least:

```text
canonical address registry
candidate registry
endpoint registry
source/operator registry
population registry
partition registry
PopulationAccessPolicy
crossfit assignment object/policy
observation operator contract
support/evidence-rights contract
normalization/library contract
qualification registry
TD controller code + policy
TargetPortfolio code + policy
per-unit producer code/policy/schema
per-unit executor code/policy/schema
metric definitions
reference-producer identities
falsifier/control identities
```

PR number, branch name, workflow name and prose status may be navigation metadata but cannot satisfy any of the above identities.

---

## 9. Required hostile RED tests beyond the accepted plan

Add tests equivalent to:

```python
def test_declared_fit_only_does_not_override_actual_validation_value_read(): ...
def test_producer_access_receipt_without_actual_event_commitment_is_invalid(): ...
def test_protected_partition_metadata_and_value_access_are_typed_separately(): ...
def test_crossfit_assignment_is_stable_under_storage_and_shard_reordering(): ...
def test_crossfit_assignment_cannot_depend_on_candidate_outcome(): ...
def test_protected_partition_cannot_fill_missing_reader_fit_support(): ...
def test_normalization_denominator_with_forbidden_value_dependency_invalidates_receipt(): ...
def test_counts_fit_only_but_library_from_validation_is_forbidden_access(): ...
def test_population_counts_cannot_substitute_for_membership_digest(): ...
def test_same_counts_different_membership_changes_population_identity(): ...
def test_manifest_digest_moves_when_crossfit_assignment_or_access_policy_moves(): ...
def test_manifest_digest_moves_when_support_or_normalization_contract_moves(): ...
```

---

## 10. Fail-closed status law

Suggested typed access-validation outcomes:

```text
ACCESS_VALID
ACCESS_POLICY_VIOLATION
ACCESS_RECEIPT_UNVERIFIABLE
MANIFEST_IDENTITY_MISMATCH
PROTECTED_VALUE_ACCESS
CROSSFIT_ASSIGNMENT_MISMATCH
NORMALIZATION_PROVENANCE_VIOLATION
SUPPORT_EVIDENCE_PROVENANCE_VIOLATION
```

These are access/authority statuses, not biological PASS/FAIL and not estimability statuses.

A forbidden-access result cannot be converted to `BIOLOGICAL_FAIL`, `NOT_ESTIMABLE`, or a valid numeric gate result. The scientific output loses authority because the execution provenance is invalid.

---

## 11. Current non-authorizing terminal state

`TASK2_MANIFEST_ACCESS_SCHEMA_CONTRACT_FROZEN__READER_FIT_CROSSFIT_ONLY__VALIDATION_ORACLE_VALUE_ACCESS_DENIED__ACTUAL_ACCESS_RECEIPT_REQUIRED__TASK2_NOT_STARTED__NO_AUTHORITY_CHANGE`

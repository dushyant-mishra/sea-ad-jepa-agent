# Unified TD Qualification and Downstream Custody Architecture V1.1 — Hostile-Review Corrective Amendment

## 0. Status, precedence and authority

This document is a binding corrective amendment to:

`docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1.md`

It incorporates the nine required design-gate amendments recorded in PR #379 issue comment `6173550971`.

Where this amendment conflicts with V1, this amendment controls. V1 remains immutable historical design evidence; V1.1 defines the corrected architecture to be reviewed for controlling implementation authority.

No implementation plan may be written until V1 + V1.1 are accepted as one architecture.

No human candidate outcome is opened. No target/representation choice, TD60, Stage4, synthetic training or real training is authorized.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

---

## A1. Canonical payload authentication is mandatory

### A1.1 Digest strings are claims, not authority

No caller-provided `*_sha`, digest string, receipt ID, parent ID or code-identity string confers scientific authority by itself.

Every scientific object that participates in manifest validation, registry promotion, reference readiness, human execution, Target Qualification Bundle issuance or downstream certification must be authenticated by recomputing its digest from canonical payload bytes.

### A1.2 Canonical verification procedure

For every authenticated scientific object, the verifier must:

1. validate the declared schema identity against an allowed schema registry;
2. canonicalize the payload using the project canonical serializer;
3. recompute the payload digest from canonical bytes;
4. compare the recomputed digest to the declared digest;
5. recursively verify all parent/dependency objects named by the payload;
6. verify exact producer code identity and, where applicable, static-policy identity;
7. verify exact input identities;
8. verify that the output payload itself is included in the signed/hash-bound receipt envelope;
9. fail closed on missing bytes, missing parents, digest mismatch, unknown schema, duplicate/conflicting identity or unverifiable lineage.

### A1.3 Minimum receipt envelope

A scientific receipt must bind at least:

```text
receipt_schema
receipt_payload
receipt_payload_digest
schema_identity
producer_code_identity
static_policy_identities[]
exact_input_digests[]
parent_receipt_digests[]
parent_artifact_digests[]
output_artifact_digest
execution_manifest_digest
qualification_registry_digest
population_access_receipt_digest
created_at
```

The receipt digest is computed over the canonical full receipt payload, not accepted from a caller.

### A1.4 Parent-chain verification

A verifier must walk the complete authority-bearing parent chain to a frozen root set. A valid child digest with an invalid, revoked, moved or unverifiable parent is invalid for active authority.

Historical byte identity remains preserved even when active authority is later revoked.

---

## A2. Revocation, supersession and requalification semantics

### A2.1 Historical qualification stage and active authority are separate

A valid historical qualification transition is never deleted or rewritten.

Every registry unit carries two orthogonal canonical fields:

```text
qualification_stage
active_lineage_status
```

### A2.2 Canonical qualification stage

The single ordered qualification stage is:

```text
SEMANTICS_ONLY
→ FIXTURE_SAME_INTERFACE
→ SAME_CODE_PATH
→ KNOWN_TRUTH_QUALIFIED
→ REAL_REFERENCE_READY
→ HUMAN_EXECUTABLE
→ HUMAN_EXECUTED
→ DOWNSTREAM_CERTIFIED
→ TRAINING_ELIGIBLE
→ TRAINING_AUTHORIZED
```

This replaces the overlapping §4 and §12 taxonomies in V1. Terms such as `MECHANICS_QUALIFIED`, `GREEN`, `PASS`, or bare `QUALIFIED` may appear only as descriptive evidence labels and never as canonical authority states.

### A2.3 Canonical active-lineage status

The active lineage status is exactly one of:

```text
ACTIVE
SUPERSEDED
REVOKED_BY_DEFECT
REQUIRES_REQUALIFICATION
```

Only an `ACTIVE` registry identity may participate in a new execution manifest.

### A2.4 Revocation receipt

Any hostile review or defect that invalidates active authority must produce an immutable revocation/supersession receipt binding:

```text
affected_registry_identity
affected_stage
defect_class
defect_evidence_digests[]
revocation_status
successor_identity_or_null
required_requalification_scope
review_identity
```

A previously `KNOWN_TRUTH_QUALIFIED` or later unit marked `REVOKED_BY_DEFECT` or `REQUIRES_REQUALIFICATION` cannot remain executable merely because its historical promotion receipt was valid when created.

### A2.5 Code or policy change

Any decision-bearing implementation, policy, metric, support law, population-access law, reference law or challenge-law change creates a new registry identity. Historical states do not transfer automatically.

---

## A3. Sealed development-versus-qualification firewall

### A3.1 Two challenge surfaces are mandatory

Known-truth work must distinguish:

```text
DEVELOPMENT_CHALLENGES
SEALED_FINAL_QUALIFICATION_CHALLENGES
```

Development fixtures may be inspected and iterated on. They cannot themselves establish final `KNOWN_TRUTH_QUALIFIED` authority.

### A3.2 Sealed final qualification commitment

Before any final-qualification realization is exposed to an implementer or production unit, freeze and authenticate:

- challenge-family registry version;
- sealed challenge specification commitment;
- exact realization manifest;
- world identities;
- seed / identity-keyed RNG namespaces;
- expected terminal-class commitments;
- candidate policy version;
- manifest version;
- adjudicator identity;
- qualification budget;
- no-retuning rule.

Secret challenge details may remain controller-only under commitment/reveal custody where necessary, but the pre-exposure commitment must be public and verifiable.

### A3.3 No retuning after exposure

After final qualification exposure begins, no producer, executor, controller, policy, challenge threshold, support law, reference law, seed set, expected class, or realization set may be tuned against observed outcomes.

A defect repair creates a new qualification identity and requires a fresh sealed final-qualification set. Failed worlds may not be silently removed or replaced.

### A3.4 Adversarial holdout

At least one adversarial/holdout challenge subset must remain unavailable to the implementer until fit/execution outputs are irrevocably frozen. Gate-specific development fixtures cannot substitute for this holdout.

---

## A4. Population split and data-access law is manifest-bound

### A4.1 Required manifest identities

`TD_EXECUTION_MANIFEST_V1` must bind exact identities for:

```text
population_split_registry_digest
data_access_policy_digest
reader_fit_policy_digest
reader_validation_policy_digest
reader_oracle_policy_digest
cross_fitting_policy_digest
protected_partition_policy_digest
```

### A4.2 Allowed-use semantics

The data-access policy must specify, per producer/controller stage:

- which population partitions may be read;
- whether values, metadata, support-only summaries or calibration-only statistics are allowed;
- whether cross-fitting is required within `reader_fit`;
- whether `reader_validation` is inaccessible, calibration-only or otherwise protected;
- whether `reader_oracle` is inaccessible until an explicit later authority transition;
- whether donor identities may cross folds/partitions;
- whether any aggregate derived from a protected partition may flow upstream.

The term `held-out` has no authority unless resolved through this exact policy object.

### A4.3 Producer access receipts

Every producer receipt must enumerate the exact population partitions and access classes read during execution.

A receipt whose observed accesses exceed the manifest policy is invalid regardless of numeric output correctness.

### A4.4 Known-truth mode

Known-truth CaseBundles must implement the same logical partition/access semantics so that access-policy enforcement can be qualified without opening protected human data.

---

## A5. Qualification independence

### A5.1 No self-qualification of human semantics

A producer/artifact/executor unit cannot issue the authority receipt that qualifies its own human semantics.

Known-truth qualification requires a distinct, independently controlled qualification/adjudication identity bound in the registry and manifest.

### A5.2 Required identities

Registry entries must bind, as applicable:

```text
scientific_unit_identity
qualification_controller_identity
truth_adjudicator_identity
independent_review_identity
qualification_receipt_digest
```

The qualification controller must be outside the unit under test and must not accept caller-supplied PASS/FAIL/qualification assertions from that unit.

### A5.3 Human promotion

Promotion to `HUMAN_EXECUTABLE` requires an independently produced promotion receipt confirming that:

- same-code-path known-truth qualification is active;
- all real prerequisites are active and complete;
- no required unit is revoked/superseded;
- exact manifest and access-policy identities match;
- human semantics were not self-certified by the deciding unit.

---

## A6. `REAL_REFERENCE_READY` is dependency-complete

### A6.1 Required prerequisite graph

A registry unit that can advance to `REAL_REFERENCE_READY` must carry an explicit prerequisite graph rather than a coarse boolean.

At minimum each prerequisite record contains:

```text
prerequisite_id
prerequisite_type
required_artifact_schema
required_producer_identity
required_policy_identity
required_population_access_class
expected_manifest_digest
actual_artifact_digest_or_null
prerequisite_stage
active_lineage_status
independent_qualification_receipt_digest_or_null
satisfied
```

### A6.2 Promotion law

`REAL_REFERENCE_READY` is lawful only when every mandatory prerequisite is:

- present;
- canonically authenticated;
- bound to the current manifest;
- produced by the required active producer/policy identity;
- independently qualified where required;
- within the lawful population-access policy;
- at or above the required prerequisite stage;
- `ACTIVE`.

A single missing or revoked reference/support/null/calibration dependency blocks promotion and remains visible in the registry.

No aggregate `ready=true` field may override the prerequisite graph.

---

## A7. Machine-testable known-truth ↔ human-mode path equivalence

### A7.1 Equivalence requirement

The prose prohibition on synthetic-specific scientific behavior is replaced by an executable certification requirement.

Given a lawful observable payload that is byte/semantically equivalent at the gate-facing boundary, known-truth and human-sealed wrappers must traverse the same:

- schema validators;
- population-access validator;
- producer entry points;
- artifact serializers;
- receipt validators;
- executor entry points;
- metric implementation;
- support logic;
- reference logic;
- status/abstention logic.

### A7.2 Path-equivalence receipt

Qualification must emit a `MODE_PATH_EQUIVALENCE_RECEIPT` binding:

```text
observable_payload_digest
known_truth_execution_trace_digest
human_mode_execution_trace_digest
producer_identity_set
executor_identity_set
validator_identity_set
branch_condition_audit_digest
scientific_output_equivalence
```

Any mode-dependent scientific branch invalidates `SAME_CODE_PATH`.

### A7.3 Permitted differences

Only external wrapper behavior may differ:

- known-truth mode may possess a separate inaccessible `TRUTH_BUNDLE_V1`;
- human-sealed mode lacks that object;
- external challenge metadata may identify known-truth world class;
- post-freeze adjudication may compare the frozen TD output to hidden truth.

These differences must not enter the scientific execution trace.

---

## A8. Downstream exact-consumption law

### A8.1 Exact Target Qualification Bundle binding

Every downstream certification and later training-eligibility receipt must bind the recomputed canonical digest of the exact `TARGET_QUALIFICATION_BUNDLE_V1` payload consumed.

A downstream process must fail closed if it attempts to:

- widen support/estimability scope;
- change target or relation semantics;
- substitute canonical molecular addresses;
- alter the observation contract;
- alter the evidence-right contract;
- drop or weaken mandatory falsifiers;
- omit inherited negative controls;
- relax required source/endpoint noncompensation;
- replace uncertainty semantics;
- drop forbidden interpretations;
- substitute producer/executor/reference identities.

### A8.2 Downstream certification receipt

`DOWNSTREAM_CERTIFICATION_CONTRACT_V1` must emit a receipt enumerating every inherited obligation from the Target Qualification Bundle and whether/how it was exercised.

At minimum:

```text
target_qualification_bundle_digest
inherited_obligations[]
obligation_test_receipts[]
observation_contract_digest
evidence_rights_contract_digest
support_universe_digest
falsifier_set_digest
negative_control_set_digest
target_semantics_digest
representation_semantics_digest
teacher_construction_digest
student_restriction_digest
evaluation_contract_digest
```

Downstream certification is invalid if any mandatory inherited obligation is untested, changed or dropped.

---

## A9. One canonical authority model

### A9.1 Canonical fields

All manifest, registry, receipt, Target Qualification Bundle and downstream certification schemas use the same authority model:

```text
qualification_stage
active_lineage_status
```

No second overlapping authority enum is permitted.

### A9.2 Ordered qualification stage

The canonical order is:

```text
SEMANTICS_ONLY
→ FIXTURE_SAME_INTERFACE
→ SAME_CODE_PATH
→ KNOWN_TRUTH_QUALIFIED
→ REAL_REFERENCE_READY
→ HUMAN_EXECUTABLE
→ HUMAN_EXECUTED
→ DOWNSTREAM_CERTIFIED
→ TRAINING_ELIGIBLE
→ TRAINING_AUTHORIZED
```

A component or pipeline may remain indefinitely at any stage. No stage is implied by green CI or by a later stage achieved by a different identity.

### A9.3 Active lineage status

The canonical active-lineage statuses are:

```text
ACTIVE
SUPERSEDED
REVOKED_BY_DEFECT
REQUIRES_REQUALIFICATION
```

Historical receipts retain their historical `qualification_stage`; active usability is determined jointly by stage and active-lineage status.

### A9.4 Scope field

Every authority record also binds `authority_scope`, for example:

```text
UNIT:G8
UNIT:R1
PIPELINE:TD
BUNDLE:TARGET_QUALIFICATION
PIPELINE:DOWNSTREAM
PROJECT:TRAINING
```

This prevents a unit-level `KNOWN_TRUTH_QUALIFIED` state from being confused with pipeline-level human or training authority.

### A9.5 Global project authority remains independent

No registry state automatically changes the global project invariant. `TRAINING_AUTHORIZED` at project scope requires a separate explicit owner authorization after all prerequisite certification has completed.

---

## A10. Required schema changes before implementation planning

Before the replacement implementation plan is written, the corrected architecture must require schemas that can represent:

1. canonical payload bytes and recomputed digests;
2. parent/dependency chain verification;
3. active-lineage status and revocation receipts;
4. development versus sealed qualification challenge custody;
5. population/data-access policy and producer access receipts;
6. independent qualification/adjudication identity;
7. dependency-complete real-reference prerequisite graphs;
8. mode-path equivalence receipts;
9. exact downstream Target Qualification Bundle consumption;
10. the canonical qualification-stage + active-lineage authority model.

The intended schema-first implementation order after design acceptance remains:

```text
TD_EXECUTION_MANIFEST_V1
→ TD_QUALIFICATION_REGISTRY_V1
→ KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1
→ TARGET_QUALIFICATION_BUNDLE_V1
→ DOWNSTREAM_CERTIFICATION_CONTRACT_V1
```

but each schema must implement A1–A9 from inception.

---

## A11. Review closure criteria

PR #379 may be frozen as controlling implementation architecture only after focused review confirms:

- A1 canonical payload verification closes SHA-string trust;
- A2 preserves immutable history while revoking stale active authority;
- A3 prevents challenge-set tuning after qualification exposure;
- A4 makes population/holdout access machine-enforced;
- A5 prevents self-issued human qualification;
- A6 makes real-reference readiness dependency-complete;
- A7 makes same-code-path equivalence executable;
- A8 binds downstream to the exact Target Qualification Bundle;
- A9 eliminates overlapping authority-state taxonomies.

Until that review passes, no replacement implementation plan is authorized.

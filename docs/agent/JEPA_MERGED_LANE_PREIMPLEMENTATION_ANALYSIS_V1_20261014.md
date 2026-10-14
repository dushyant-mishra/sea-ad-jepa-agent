# JEPA merged-lane preimplementation analysis V1 — 2026-10-14

Status: `ANALYSIS_COMPLETE__NO_UNIFIED_IMPLEMENTATION_STARTED__TASK1_BLOCKED`

Binding authority remains exactly:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Purpose

This document freezes analysis that can be completed while Macha is unavailable and before final Task 0 custody acceptance. It does not implement unified Task 1, open candidate outcomes, or cross any Task 0 stop gate.

It resolves four questions prospectively:
1. how old PR #356 Tasks 1–2 may be absorbed without creating a parallel authority chain;
2. which parts of unified Tasks 1–3 still remain even if Macha's work is perfect;
3. how Task 0 findings F6–F9 must propagate into Target Qualification Bundle/downstream/runtime obligations;
4. which unresolved dependencies are true implementation blockers versus already-analyzed future work.

## 1. Macha old Task 1 absorption law

Old PR #356 Task 1 interfaces:
- `canonical_json_bytes(obj)`
- `raw_sha256(data)`
- `semantic_sha256(obj)`
- `ordered_registry_digest(rows, identity_keys)`

Unified Task 1 requires:
- `canonical_bytes(payload)`
- `canonical_sha256(payload)`
- recursive `verify_scientific_receipt(receipt, object_resolver)`
- exact parent/dependency verification to a frozen root
- one canonical `QualificationStage`
- one canonical `ActiveLineageStatus`
- required `authority_scope`

Therefore old Task 1 can provide shared canonicalization/digest primitives and hostile tests, but **cannot by itself complete unified Task 1**. Authority-state semantics and recursive authority-bearing receipt verification remain unified-only work.

### Acceptance classes for returned Task 1 objects

`DIRECT_REUSE` only if the implementation:
- is deterministic and order-stable where scientific identity is stable;
- rejects unsupported/non-JSON scientific values;
- recomputes digests from bytes rather than trusting declared strings;
- has no generator/synthetic authority embedded in the canonical primitive;
- does not use PR/branch identity as scientific identity.

`ADAPT_AND_WRAP` if the primitive is scientifically sound but has production-synthetic-specific naming or lacks unified receipt/authority integration.

`TEST_ONLY` if hostile tests expose useful ordering/numeric/serialization edge cases but implementation semantics conflict with V1.1.

`REJECT` if it trusts declared digests, embeds synthetic authority, tolerates ambiguous scientific values, or permits branch/PR navigation metadata to determine identity.

### Mandatory post-return hostile checks

- JSON key permutation leaves semantic/canonical identity unchanged.
- Stable identity-key row/shard reordering leaves registry semantic identity unchanged.
- Different raw bytes retain distinct raw transport hashes even when semantic payloads agree.
- Nonfinite/non-JSON scientific values fail closed.
- Altered payload with a copied 64-hex digest fails.
- Child receipt with missing/invalid parent fails recursively.
- Conflicting duplicate dependency identities fail.
- No second canonical serializer remains active after consolidation.

## 2. Macha old Task 2 absorption law

Old PR #356 Task 2 interfaces:
- `freeze_generator_version`
- `commit_secret`
- `derive_stream`
- `record_exposure`
- `validate_successor_version`
- `attest_realization_set`
- `scan_secret_absence`
- `attest_no_unique_withheld_code_path`

These map primarily to **unified Task 4 sealed challenge custody** and shared identity-keyed RNG/custody primitives. They do **not** satisfy unified Task 2, whose scientific role is `TD_EXECUTION_MANIFEST_V1` plus current-TD population/access law.

### Reusable Task 2 substrate

Potential `DIRECT_REUSE` / `ADAPT_AND_WRAP` pieces:
- commit/reveal primitive;
- >=256-bit nonce enforcement;
- domain-separated identity-keyed RNG;
- row/storage-order-invariant scientific streams;
- exposure append-only state;
- exact realization-budget attestation;
- post-exposure successor requalification law;
- secret-absence scanner;
- unique withheld-only code-path scanner.

### Hard boundaries

Returned old Task 2 must never:
- create a second execution manifest;
- define qualification stage or human authority;
- expose hidden truth to producer/executor/controller inputs;
- use seed offsets/index positions as scientific RNG namespaces;
- permit seed shopping or discarded realizations;
- let a post-exposure repair inherit qualification;
- make known-truth challenge success imply human biological validity.

## 3. Unified Task 1 remains after consolidation

Even with accepted Macha Task 1 primitives, unified Task 1 still owns:
- the single canonical receipt envelope;
- recursive parent/dependency-chain verification;
- authority-bearing schema validation;
- ordered qualification-stage model;
- four-state active-lineage model;
- authority scope;
- rejection of `PASS`, `GREEN`, `MECHANICALLY_QUALIFIED`, PR state, or branch state as authority enums.

The consolidation rule is **one serializer, one digest law, one authority model**. If Macha canonicalization is reused, `scripts/v5/td_unified/canonical_v1.py` must import/wrap or physically migrate that exact accepted primitive; it must not independently reimplement a subtly different encoding.

## 4. Unified Task 2 remains after consolidation

Unified Task 2 is not old synthetic Task 2.

It still must implement:
- `TD_EXECUTION_MANIFEST_V1`;
- `PopulationAccessPolicy`;
- exact current policy: deterministic cross-fitting within `reader_fit` only;
- protected `reader_validation` and `reader_oracle`;
- per-producer actual access receipts;
- invalidation of numeric success after forbidden access;
- exact binding of registry/observation/support/controller/candidate/endpoint/source/policy identities.

No custody/RNG implementation can substitute for population-access law.

## 5. Unified Task 3 remains after consolidation

Unified Task 3 remains wholly required:
- immutable historical promotion receipts;
- active revocation/supersession;
- new identity after code/policy change with no inherited stage;
- independent qualification controller identity;
- no self-qualification;
- complete prerequisite graph;
- derived `REAL_REFERENCE_READY`, never trusted aggregate `ready=true`.

It must also register both Macha historical streams as history without promotion and preserve current unresolved dependencies.

## 6. F6 Foundation representation propagation

Task 0 current state:
- representation policy: `SUBSPACE_ONLY`;
- learned T1 technology invariance: not qualified;
- canonical broad endpoint: 34/42 matrices available;
- all seven NPH52 matrices unavailable for that endpoint;
- source/acquisition signal remains strong;
- coordinate-axis semantics are not promoted.

### Required Target Qualification Bundle fields/obligations

Any selected target bundle must carry, where applicable:
- `representation_scope = SUBSPACE_ONLY`;
- `technology_invariance_qualified = false` unless a later prospective qualification changes it;
- exact matrix-identifiability/availability scope;
- exact unavailable matrices/strata;
- source/acquisition limitation statement;
- forbidden interpretation: individual learned coordinates are not stable biological axes unless separately qualified.

### Required downstream hostile tests

Certification must fail if downstream:
- substitutes axis-level semantics for a subspace-qualified object;
- claims universal matrix/technology transfer from partial coverage;
- drops unavailable matrices from the declared limitation surface;
- treats residual source/acquisition predictability as proven purely technical batch.

## 7. F7 multimodal/regulatory propagation

Permanent distinctions:
- Stage75F/SCENIC+-related RNA-derived edges are hypothesis-generating, not validated regulatory truth;
- authenticated ATAC is independent measurement only within its actual observation design;
- `SAME_NUCLEUS` and `SEPARATE_NUCLEUS` are distinct observation operators;
- nearest-gene/proximity is not validated regulatory target identity;
- PR #179 remains `INCOMPLETE_STOPPED`;
- randomized/target-shuffled graph history remains a negative prior/control obligation.

### Required CaseBundle/TQB semantics

Carry exact modality/observation provenance:
- RNA vs ATAC/fragments;
- same-nucleus vs separate-nucleus;
- measured evidence vs RNA-derived regulatory hypothesis;
- independently measured chromatin vs circular RNA-derived edge evidence.

### Required downstream/challenge obligations

- no cross-modal claim may conflate same-nucleus and separate-nucleus designs;
- no RNA-derived graph may serve as an independent regulatory answer key;
- proximity cannot be promoted to target causality;
- structural graph controls must be genuinely structurally distinct.

## 8. F8 runtime/training-safety propagation

PR #223/#224 invariants are **post-science runtime prerequisites**, not target authority:
- optimizer completion precedes EMA;
- rejected/incomplete update cannot advance EMA;
- typed checkpoint/receipt/runtime-source provenance must be physically authenticated;
- coordinate/logical-row/payload-byte/consumed-value coupling is mandatory;
- q-safety remains unproven until the final joined path executes every required channel;
- runtime correctness cannot substitute for target/representation/teacher-student scientific validity.

### Lifecycle consequence

The current unified plan implements through `DOWNSTREAM_CERTIFIED`; it does not currently provide a standalone runtime module for `TRAINING_ELIGIBLE` promotion. Therefore F8 is a **hard future prerequisite for any transition from DOWNSTREAM_CERTIFIED to TRAINING_ELIGIBLE**.

Until an explicit runtime-eligibility receipt binds these invariants, the registry must not promote to `TRAINING_ELIGIBLE` even if downstream scientific certification passes.

## 9. F9 FULL104 information-channel propagation

Permanent invariants:
- normalization denominator/library information can encode source;
- equal molecular-address burden is not equal evidence burden;
- estimability must be explicit per required source/stratum;
- silent/nonvarying targets cannot be zero-filled into favorable scores;
- a metric invariant to donor/source-level transformations cannot certify absence of those channels;
- withdrawn Audit-G remains withdrawn and must not be resurrected.

### Task placement

- Task 2 manifest/observation policy: bind normalization/library provenance and nuisance-channel declarations where decision-bearing.
- Task 5 CaseBundle: preserve stored mass, unmaterialized/off-address mass, full library mass, observation state and source/donor/operator hierarchy.
- Task 7 TQB: export exact estimability/support/source limitations and forbidden zero-fill interpretation.
- Task 8 downstream certification: inherited leakage/falsifier receipts must exercise denominator/source shortcut and metric-blindness traps.
- Task 9 challenge families: include information-channel worlds where apparent performance is driven only by normalization/source/evidence burden and the lawful result is no biological promotion.

## 10. Unresolved-ledger dependency classes

### Foundation/custody blockers — must resolve before meaningful known-truth promotion
- `U_MACHA_SYNTH_TASK1_CANONICAL_IDENTITY_ACTIVE`
- `U_MACHA_SYNTH_TASK2_CUSTODY_RNG_ACTIVE_OR_PENDING`
- `U_TASK1_3_FOUNDATION`
- `U_A7_MODE_EQUIVALENCE`
- `U_SEALED_EXAM_INFRA`
- `U_KNOWN_TRUTH_SUBSTRATE`

### Registered-unit producer/reference blockers — later Tasks 6/10
- `U_G8_REFERENCE`
- `U_G6_MARGIN`
- `U_GEOMETRY_PRODUCER`
- `U_R1_NULL`
- `U_G2_POLICY`
- `U_G7_EVIDENCE_PRODUCER`
- `U_INCREMENT_PRODUCERS`
- `U_G12_HUMAN_SUPPORT`
- `U_CANDIDATE_SUPPORT_OVERLAYS`
- `U_REAL_REFERENCE_ARTIFACTS`

### Controller/portfolio/unified authority blockers
- `U_CONTROLLER_EXACT_BINDING`
- `U_TARGETPORTFOLIO_BINDING`
- `U_READINESS_MATRIX_REGEN`
- `U_MACHA_REAL_TD_HISTORY_REGISTRATION`
- `U_MACHA_V79_HISTORY_REGISTRATION`

### Downstream/post-science blockers
- `U_FOUNDATION_REPRESENTATION_CUSTODY`
- `U_MULTIMODAL_REGULATORY_CUSTODY`
- `U_FULL104_INFORMATION_CHANNEL_CUSTODY`
- `U_DOWNSTREAM_CERTIFICATION`
- `U_RUNTIME_TRAINING_SAFETY_CUSTODY`

### Deferred/noncritical to current unified foundation
- `U_V79_V80_SUCCESSOR_CONFLICT` — only if a successor-estimator lane is still needed.

## 11. What can be completed before Macha returns

Completed by this analysis:
- absorption acceptance law for old Tasks 1–2;
- proof that old Task 1 != complete unified Task 1;
- proof that old Task 2 != unified Task 2 and maps mainly to unified Task 4 custody;
- F6–F9 propagation requirements;
- unresolved-dependency classification;
- future training-eligibility boundary for F8.

Can still be prepared without implementation authority:
- exact RED-test inventory for unified Tasks 1–3;
- exact downstream inherited-obligation matrix for Tasks 7–9;
- Macha Task 1–2 return-package audit checklist;
- Task 0 final-acceptance checklist that requires no invented Task 3/4 completion.

Must wait:
- any code in unified Task 1–12;
- any registration/promotion receipt;
- any new real reference generation;
- any candidate outcome access;
- any training action.

Terminal:
`PREIMPLEMENTATION_ANALYSIS_COMPLETE__MACHA_TASK1_2_ABSORPTION_LAW_FROZEN__F6_F9_PROPAGATION_FROZEN__TASK1_IMPLEMENTATION_STILL_BLOCKED`

# Unified Task 3 — Qualification Registry Preparation V1

Date: 2026-10-15
Status: `PREPARED_NOT_STARTED__TASK2_ACCEPTANCE_REQUIRED`
Authority effect: **NONE**

> **DO NOT EXECUTE OR PROMOTE TASK 3 BEFORE UNIFIED TASK 2 IS INDEPENDENTLY ACCEPTED AND FROZEN.**

Binding project authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Purpose

This document prepares Unified Task 3 so implementation can begin immediately after a lawful Task 2 freeze without redesigning the authority model under time pressure.

Unified Task 3 implements `TD_QUALIFICATION_REGISTRY_V1` and the active prerequisite / promotion / revocation graph required by architecture laws A2, A5 and A6.

Task 3 is governance and machine-verifiable scientific custody. It does **not** run target discovery, open protected biological values, qualify a target, choose a representation, authorize Stage 4, or authorize training.

## 2. Gate into Task 3

Task 3 may start only if all of the following are true on one exact Task 2 head:

1. Macha independently rechecks T2-B1 through T2-B4 and explicitly accepts the exact candidate head.
2. Task 2 is frozen on that accepted exact head.
3. The frozen Task 2 manifest/access implementation descends from frozen Task 1 `799d2e235901dfad9ce3b305c767a1c989e362f6` and frozen Task 0 `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.
4. The Task 2 freeze identifies the exact `TD_EXECUTION_MANIFEST_V1`, access-policy semantics, population-authority rule and per-unit execution-identity surface that Task 3 must consume.
5. No protected reader-validation/oracle values were opened to obtain the acceptance.

Current repair candidate `c7dfff1cee608e4a101855d42cf0af08491c2aaf` is **not** treated here as accepted authority; it is only the current review candidate.

## 3. Controlling design

Controlling implementation-plan Task 3 interface:

- Create `scripts/v5/td_unified/registry_v1.py`.
- Create `schemas/target_discovery/unified_v1/td_qualification_registry_v1.json`.
- Create `tests/v5/td_unified/test_registry_v1.py`.
- Consume Task 1 canonical/authority primitives and frozen Task 2 manifest/access objects.
- Produce `RegistryUnit`, `PrerequisiteRecord`, `RevocationReceipt`, `PromotionReceipt`, `TDQualificationRegistry`, `derive_real_reference_ready(...)`, `promote_unit(...)`, and `revoke_or_supersede(...)`.

The canonical stage vocabulary must come from the accepted Task 1 authority model. Task 3 must not invent a second stage system.

## 4. Historical substrate classification

Historical branch `integration/td-qualification-registry-v1-20261014` at `02cd6c641be726e1e1cddc37580e731f6302d70d` contains a prior `scripts/v5/td_qualification_registry_v1.py` and integration tests.

Classification:

`SUPERSEDED_AS_AUTHORITY__REQUIREMENTS_AND_NEGATIVE_DESIGN_EVIDENCE_ONLY`

Useful ideas to carry forward:

- explicit lifecycle vocabulary;
- exact executor/code identities;
- producer qualification state;
- required real-reference artifacts;
- explicit challenge families;
- visible open prerequisites;
- fail-closed authority defaults;
- inherited tournament regression coverage.

Do **not** directly promote or wrap the old registry as current authority because it has material architectural differences:

- it derives an aggregate `human_readiness(...)->{"ready": ...}` helper from partly hand-authored status fields;
- it hard-codes historical system PR/run identities;
- it lacks V1.1 active-lineage revocation/supersession receipts;
- it does not recursively authenticate the complete current Task 2 manifest/access/per-unit dependency graph;
- it predates the no-self-qualification and exact prerequisite-completeness law in its current form.

Old code therefore serves as hostile-test material and requirements history, not authority inheritance.

## 5. Registry object model to implement after the gate

### 5.1 `RegistryUnit`

Each unit must bind, at minimum:

- stable `unit_id` and scope;
- exact current scientific stage;
- exact active-lineage status: `ACTIVE | SUPERSEDED | REVOKED_BY_DEFECT | REQUIRES_REQUALIFICATION`;
- exact frozen Task 2 manifest identity;
- exact Task 2 access-policy identity;
- exact per-unit execution-identity row from the Task 2 manifest;
- exact producer and executor code identities;
- exact producer and executor policy identities;
- exact schema identity;
- exact metric-definition identity;
- exact reference-producer identity;
- exact falsifier/control identity;
- exact prerequisite-record identities;
- immutable prior promotion/revocation receipt references;
- authority scope explicitly excluding anything not granted.

No branch name, PR number, prose status, green CI badge, copied digest string, or navigation alias is sufficient scientific identity.

### 5.2 `PrerequisiteRecord`

A prerequisite is an authenticated edge, not a text checklist item. It must bind:

- dependent unit identity;
- prerequisite unit/object identity;
- required minimum stage;
- required active-lineage state;
- exact manifest/access identity under which the prerequisite was qualified;
- exact producer/policy/schema/metric/reference/falsifier identities where relevant;
- whether the edge is required for `REAL_REFERENCE_READY`, `HUMAN_EXECUTABLE`, or a lower transition;
- current satisfaction result derived at validation time.

There is no authoritative stored `ready=true` field.

### 5.3 `PromotionReceipt`

Promotion must be one stage at a time and must bind:

- pre-promotion registry identity;
- unit identity;
- source and destination stages;
- exact prerequisite set and resolved identities;
- exact manifest/access identity;
- distinct qualification-controller identity;
- where required, distinct truth-adjudicator and independent-reviewer identity;
- canonical decision payload and digest;
- immutable timestamp/navigation metadata only as non-authoritative annotations.

A unit may be promoted only while `ACTIVE`.

### 5.4 `RevocationReceipt`

Revocation or supersession must preserve historical evidence while preventing future use. It must bind:

- exact affected registry/unit identity;
- prior stage;
- new lineage state;
- concrete defect/change reason class;
- successor identity when superseded;
- exact requalification scope;
- controller/reviewer identity;
- immutable historical promotion receipts rather than deleting or rewriting them.

Changed code, policy, schema, metric, reference producer, falsifier, manifest or access law creates a new registry identity and cannot inherit stage silently.

## 6. Readiness derivation law

`REAL_REFERENCE_READY` is **derived**, never asserted.

Each call to `derive_real_reference_ready(...)` must recursively resolve the complete active prerequisite graph and fail closed if any required edge is:

- absent;
- unresolved;
- at insufficient stage;
- superseded;
- revoked;
- marked `REQUIRES_REQUALIFICATION`;
- bound to a different manifest/access identity;
- bound to changed producer/policy/schema/metric/reference/falsifier identities;
- supplied only by a status string, prose, PR, branch, CI result or caller-provided digest.

A cached readiness result cannot override changed dependencies. If caching is later introduced, the cache itself must be canonically bound to the complete dependency identity set and revalidated before use.

## 7. Independence law

Task 3 must enforce A5 mechanically.

At minimum:

- a scientific producer cannot issue its own qualification promotion;
- the qualification controller identity must be distinct from the producer/executor identity where the architecture requires independence;
- truth adjudication cannot be performed by the scientific producer;
- `HUMAN_EXECUTABLE` requires an independent promotion receipt;
- Macha execution evidence is not automatically Macha independent adjudication; the roles must be represented separately even when the same external agent infrastructure is used.

## 8. Task 2 binding law

Task 3 consumes the **frozen** Task 2 authority surface. It must not recreate population/access authority from strings.

On every promotion/readiness validation involving current-TD authority:

- resolve the exact frozen Task 2 manifest object;
- recursively verify its dependencies using the Task 1 canonical primitives;
- require the exact access-policy identity and lawful population-authority semantics from frozen Task 2;
- require the exact per-unit execution-identity row expected for the unit;
- once scientific producers begin emitting access receipts, bind those exact harness-attested receipts into the corresponding scientific/promotion receipt.

The historical population-registry SHA `50b29d7e...` remains custody annotation unless/until frozen Task 2 independently establishes byte-level authority for it.

## 9. RED-first hostile test matrix

The first Task 3 implementation commit must be preceded by preserved RED tests. Minimum matrix:

### A2 lineage and history

1. historical promotion receipt remains immutable after revocation;
2. revoked unit cannot satisfy a new manifest/prerequisite;
3. superseded unit cannot promote;
4. supersession requires explicit successor and requalification scope;
5. code change produces new identity with no silent stage inheritance;
6. policy/schema/metric/reference/falsifier change produces new identity with no silent stage inheritance;
7. conflicting parent histories fail closed;
8. duplicate `unit_id` with different identity fails closed.

### A5 independence

9. producer self-qualification rejected;
10. executor self-promotion rejected where controller separation is required;
11. controller identity copied into reviewer/adjudicator role rejected where independence is required;
12. `HUMAN_EXECUTABLE` without independent promotion receipt rejected;
13. green CI/prose approval cannot substitute for a promotion receipt.

### A6 prerequisite completeness

14. caller-provided `ready=true` cannot override a missing prerequisite;
15. one revoked prerequisite blocks readiness;
16. one superseded prerequisite blocks readiness unless the exact successor is required/resolved;
17. one `REQUIRES_REQUALIFICATION` prerequisite blocks readiness;
18. stale Task 2 manifest identity blocks readiness;
19. stale access-policy identity blocks readiness;
20. changed producer/policy/schema/metric/reference/falsifier identity blocks readiness;
21. unresolved recursive dependency blocks readiness;
22. cyclic prerequisite graph fails closed with an explicit error;
23. unsatisfied prerequisites remain visible in machine-readable output;
24. readiness recomputation after dependency mutation changes the result rather than reusing a cached boolean.

### Population/access inheritance

25. forged copied Task 2 digest without resolvable object is rejected;
26. access receipt not issued by the frozen lawful harness path cannot satisfy a scientific prerequisite once such receipts are required;
27. validation/oracle value access cannot be reintroduced through a registry prerequisite;
28. pooled cross-fit qualification cannot be relabeled as per-fold source-stratified qualification; fold-4 NPH52=1 limitation remains explicit.

## 10. Planned implementation sequence after Task 2 freeze

1. Branch from the **exact frozen Task 2 head**, not current PR tip or Task 1.
2. Add only `test_registry_v1.py` and any minimal fixture helpers needed to express the RED matrix.
3. Run focused tests and preserve the intended RED commit.
4. Implement schema and `registry_v1.py` minimally to satisfy the law.
5. Run focused Task 3 suite.
6. Run inherited Task 2 + Task 1 + unified synthetic integration regressions.
7. Self-audit hostile cases not represented by the implementation author.
8. Freeze an exact review candidate.
9. Obtain independent Macha exact-head adjudication.
10. Only after explicit acceptance, create a Task 3 freeze receipt/branch and allow Task 4 implementation to consume it.

## 11. Acceptance criteria

Task 3 is not accepted merely because tests pass. Freeze requires an independent exact-head verdict demonstrating:

- one canonical stage system;
- immutable historical evidence plus active revocation/supersession;
- no self-qualification;
- dependency-complete recursively authenticated readiness;
- exact binding to frozen Task 2 manifest/access/per-unit identities;
- no aggregate readiness override;
- no protected partition rescue;
- changed inputs trigger a new identity/requalification rather than silent inheritance;
- all intended RED probes are demonstrably GREEN for the correct reason.

## 12. Explicit non-goals

Task 3 preparation and implementation do not:

- register current repaired biological gates at a higher stage (that is later Task 6 and remains conservative);
- create a known-truth CaseBundle/TruthBundle (Task 5);
- construct real reference artifacts;
- open validation/oracle values;
- execute human biology;
- select a target or representation;
- authorize downstream training.

## 13. Start command for the future implementer

Only after Task 2 is independently accepted/frozen:

> Implement Unified Task 3 exactly from the frozen Task 2 head. Preserve RED first. Treat the historical `td_qualification_registry_v1.py` as superseded requirements/negative evidence, not authority code. Derive readiness recursively from authenticated active prerequisites on every validation call; do not add a trusted aggregate ready flag. Do not start Task 4 until Task 3 has an independently accepted exact head.

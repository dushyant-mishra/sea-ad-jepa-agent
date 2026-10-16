# Unified Task 4 — C1–C9 Binding Amendment

Date: 2026-10-16
Status: DESIGN APPROVED; IMPLEMENTATION PLAN READY FOR REVIEW
Controls with: `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`
Implementation plan: `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`
Authority effect: NONE
Frozen prerequisite: Unified Task 3 accepted/frozen code identity `117dd51dea827e734b299982da93991b934bdc8f`
Independent acceptance verdict: `ACCEPT_UNIFIED_TASK3` at review head `c33f2bd2`

Binding global state remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Purpose and precedence

This amendment incorporates the binding carry-forward conditions C1–C9 from the final independent Task 3 acceptance review into Unified Task 4 before implementation begins.

The 2026-10-15 Task 4 sealed-challenge custody design remains controlling except where this amendment is more restrictive or more explicit. Where the two documents conflict, this amendment controls.

Task 4 remains a custody subsystem. It does not decide biological PASS/FAIL, target choice, representation choice, Stage 4 eligibility, or training authority.

## 2. Task 3 freeze and prospective Task 4 boundary

Task 3 is frozen at exact code identity:

`117dd51dea827e734b299982da93991b934bdc8f`

Task 4 may begin prospectively from those exact bytes.

No final qualification secrets, hidden final nonces, final realization roots, protected biological values, candidate outcomes, reader-validation values, reader-oracle values, or real qualification worlds may be created during design, planning, or RED-only implementation setup.

No Task 4 implementation may reinterpret or mutate frozen Task 0–3 production code. Any needed successor behavior must be implemented prospectively in Task 4-owned code and interfaces.

## 3. New top-level invariant

Before any path can make `KNOWN_TRUTH_QUALIFIED` or any later registry stage reachable, all C1 requirements in Section 4 must be GREEN under hostile tests and persistent cross-process custody must be operational.

Until then, the required state is:

`TASK3_FROZEN_117DD51D__TASK4_PROSPECTIVE_ONLY__C1_C9_BINDING__KTQ_AND_LATER_CLOSED_UNTIL_C1_R4_GREEN`

This is stronger than merely requiring custody at one promotion call. It applies to every route to the same authority state, including construction, reload, fork, replay, nested prerequisite traversal, revocation/supersession, legacy import, campaign continuation, and campaign restart.

## 4. C1 — hard pre-authority barrier

C1 is a mandatory blocker before `KNOWN_TRUTH_QUALIFIED` or later becomes reachable.

### 4.1 Defect-bearing revocation identity

Revoked-unit identity must be based on defect-bearing execution identity and must not be bypassable by cosmetic authority metadata.

At minimum:

- `authority_restrictions` must be excluded from the revocation identity or represented as a sorted, closed canonical form;
- `authority_scope` must be excluded from the revocation identity where it is non-defect-bearing, or represented by a closed canonical form if the controlling authority law requires it;
- token ordering, duplicate-equivalent representations, cosmetic additions, whitespace/case aliases, or equivalent serialization changes must not create a fresh revocation identity;
- a scientifically or mechanically changed defect-bearing dependency must create a distinct identity rather than being collapsed into the revoked one.

The exact identity law must be explicit in code and schema, not inferred from a broad object digest.

### 4.2 Revocation over the full prerequisite closure

Every authority-bearing transition must check revocation/supersession/requalification status for every unit traversed by the same prerequisite closure used to establish readiness.

Checking only the promoted unit or its direct prerequisites is insufficient.

A nested prerequisite at depth 2, depth 3, or later that is revoked, superseded, or requires requalification must fail the transition closed.

### 4.3 Persistent cross-process revocation/history custody

Task 3's process-local revocation anchor remains a labelled stopgap only.

Before `KNOWN_TRUTH_QUALIFIED` or later becomes reachable, Task 4 must provide persistent cross-process custody with all of the following:

- append-only durable history;
- exact replay validation from genesis;
- externally anchored/published expected head after every authority-bearing append;
- every load/replay must verify the expected prior head;
- a fresh process cannot erase revocation by constructing a new in-memory custody object;
- a caller-provided truncated/rechained ledger cannot regain authority;
- cross-process verification must not require giving the producer the long-lived signing secret.

This closes R4 only when implemented and independently reviewed; this design amendment does not itself close R4.

### 4.4 Mandatory RED-first attacks

Before implementing the C1 repair, RED tests must include at least:

1. revoked identity re-enters after adding a cosmetic `authority_restrictions` token;
2. revoked identity re-enters after reordering equivalent restriction tokens;
3. target-fork/restriction-mutation variant attempting to preserve scientific identity while evading revocation;
4. nested revoked prerequisite at depth 2;
5. nested revoked prerequisite at depth 3 or deeper;
6. fresh-process/fresh-custody restart after revocation;
7. ledger truncation/rechain after revocation;
8. changed stage/lineage representation of the same revoked defect-bearing unit;
9. no-custody promotion path to an authority-bearing stage;
10. construction/reload path attempting to declare a post-revocation authority stage.

The first two tests are direct preservation of the two BAD rows from the accepting Task 3 review and must fail before production repair is written.

## 5. C2 — R4 remains open until Task 4 closes it

Task 4 owns the transition from process-local stopgap custody to persistent cross-process custody.

R4 remains explicitly OPEN until the Section 4.3 implementation is independently verified.

No documentation, fixture success, same-process HMAC, in-memory anchor, or process-local replay may be described as closing R4.

Fixture-mode mechanics may exercise the APIs but must remain non-authorizing.

## 6. C3 — only the current registry facade may carry authority

All Task 4 and later production consumers must use `scripts/v5/td_unified/registry_v1.py` through its current facade and must require successful `RegistryHistoryCustody.validate_current` or its explicitly reviewed successor.

`registry_v1_legacy.promote_unit` is historical/mechanical code only and must never be imported by Task 4 or later authority-bearing production code.

Task 4 RED must include repository-wide import-guard tests that fail if:

- Task 4 production code imports `registry_v1_legacy`;
- a downstream authority module imports `registry_v1_legacy`;
- an indirect helper re-exports a legacy authority function into Task 4;
- a caller can select the legacy route by configuration or alias.

Historical tests may import the legacy module only when explicitly scoped to historical regression and incapable of issuing current authority.

## 7. C4 — `derive_real_reference_ready` is diagnostic only

`derive_real_reference_ready` may be used to compute diagnostics or mechanics state, but its return value must never itself grant authority.

Task 4 must prove this both statically and dynamically:

- no Task 4 authority-bearing transition may accept its boolean/result as sufficient evidence;
- no schema may contain a caller-asserted field whose semantic meaning is equivalent to `derive_real_reference_ready == true`;
- promotion/campaign transitions must re-run the authoritative registry/custody checks independently;
- a hostile test must force the diagnostic to report ready while authoritative Task 2/Task 3/custody evidence is invalid and confirm authority remains closed.

## 8. C5 — actor names are not credentials (R7)

Pinned names such as `C1`, `R1`, `validator-1`, and `HARNESS` are identifiers/conventions, not proof of who acted.

Before any human/current-TD authority stage is reachable, actor actions must be authenticated by a mechanism outside producer control, such as signed or harness-attested action receipts.

The exact cryptographic mechanism may be selected in the implementation plan, but the design requirements are fixed:

- actor identity used for an authority-bearing action must bind an authenticated credential/attestation;
- producer-controlled strings or mappings cannot mint the credential;
- controller/reviewer/validator/evidence-issuer role separation is checked on authenticated underlying actor identity;
- aliasing two role names onto the same authenticated actor is refused;
- authentication failure cannot degrade to name-only acceptance.

This requirement is part of the human/final authority boundary; fixture mechanics may use synthetic actors but remain non-authorizing.

## 9. C6 — frozen actor policy applies to revocation and supersession

The same frozen privileged-actor policy that constrains promotion must constrain `revoke_or_supersede` and any Task 4 successor mutation operation.

Task 4 must refuse:

- unregistered revoker/superseder;
- minted privileged actor names;
- producer or executor acting as privileged revoker where forbidden by role law;
- aliasing through whitespace, case, Unicode, or alternate registration;
- caller-provided actor registry substitution.

The authenticated actor registry/policy used for the action must be the same authority chain used by the current registry snapshot, not a caller-created parallel registry.

## 10. C7 — close the requirement-class vocabulary and issuer law

Requirement classes must form a closed, versioned vocabulary.

For every non-`UNIT` requirement class:

- the class must be explicitly enumerated;
- the authorized issuer role(s) must be explicit;
- content validation requirements must be explicit;
- unknown classes fail closed;
- generic fallback classes are forbidden on authority-bearing paths;
- a bare role label or caller-authored dictionary cannot satisfy the requirement.

Adding a new requirement class is an authority-contract change requiring prospective review and new tests; it cannot happen dynamically at runtime.

## 11. C8 — Task 1 authority law applies at `RegistryUnit` construction

A `RegistryUnit` must satisfy frozen Task 1 `validate_authority_record` semantics at creation/construction, not only later at promotion.

Task 4 planning and implementation must treat invalid registry records as non-constructible authority objects.

RED tests must cover at least:

- forbidden scope/stage combination at construction;
- `NO_TRAINING_AUTHORITY` record constructed at a training-capable stage;
- malformed/unknown authority scope;
- restrictions inconsistent with the frozen scope→stage law;
- reconstruction/reload of an invalid record from serialized bytes.

Historical parsing may retain invalid legacy evidence as data, but it must not instantiate an active current-authority `RegistryUnit` without explicit historical/non-authorizing typing.

## 12. C9 — in-process tampering remains non-authorizing (R1)

Task 4 must move authority-bearing finalization state outside the producer process.

Before human/current-TD authority is reachable:

- authoritative registry state is loaded/validated outside producer process;
- persistent custody ledger is outside producer process;
- long-lived signing key is outside producer process;
- exposure issuance is harness-controlled;
- output freeze/finalization is harness-controlled;
- protected partitions remain physically unavailable under Task 2 access law;
- producer code cannot mutate an in-memory object and have that mutation become authority.

Same-process fixture tests remain allowed only with an explicit non-authorizing mode that cannot be upgraded by a caller flag.

## 13. R5 claim scope remains pooled donor-level only

Task 4 and downstream evidence packaging must preserve the accepted Task 2/3 R5 limitation:

- claims supported by the five-fold design are pooled donor-level claims;
- no per-fold source-stratified performance or biological claim is authorized from that design;
- evidence-package schemas must carry this scope restriction forward rather than requiring downstream consumers to remember it from prose.

## 14. Sibling-route attack rule

After any gate is repaired, hostile review must attack every materially distinct route to the same state, not only the function that was patched.

For each authority-bearing state transition, tests must consider as applicable:

- direct API promotion;
- object construction with a declared stage;
- deserialization/reload;
- replay from history;
- fresh custody/fresh process;
- nested prerequisite traversal;
- revocation/supersession mutation;
- legacy facade/import path;
- campaign continuation;
- campaign fork/restart;
- configuration or alias substitution;
- stale cached/derived diagnostic state.

A fix is not accepted merely because the originally reported call path is closed.

## 15. Integration with existing Task 4 state machine

The existing Task 4 state machine remains:

`CAMPAIGN_CREATED`
→ `DEFINITION_SEALED`
→ `REALIZATION_SET_SEALED`
→ `EXPOSURE_ACTIVE`
→ `ALL_REQUIRED_OUTPUTS_FROZEN`
→ `HIDDEN_MATERIAL_REVEALED`
→ `REGENERATION_VERIFIED`
→ `CUSTODY_COMPLETE`

with terminal invalidation state:

`INVALIDATED`

This amendment adds a prerequisite barrier below the state machine:

`C1_C9_PREAUTHORITY_BARRIER_GREEN`

No transition that can contribute to `KNOWN_TRUTH_QUALIFIED` or later authority may be considered authority-bearing unless this barrier is GREEN under current registry state and persistent custody state.

Development/fixture campaigns remain allowed below the barrier with `promotion_authority = NONE`.

## 16. Implementation decomposition

Task 4 implementation should be decomposed into isolated components rather than one authority monolith:

1. **registry authority adapter** — current `registry_v1` only; full prerequisite closure; Task 1 validation; no legacy route;
2. **revocation identity + persistent custody store** — defect-bearing identity, durable append-only replay, external head anchoring;
3. **actor attestation adapter** — authenticated actor action boundary and frozen actor-policy enforcement;
4. **closed requirement-class registry** — versioned classes and issuer/content-validation law;
5. **campaign/sealing mechanics** — the existing Task 4 campaign, commitment, realization, exposure, freeze, reveal, regeneration objects;
6. **authority barrier evaluator** — evaluates C1–C9 and refuses all KTQ-or-later authority until every required condition is current and GREEN;
7. **non-authorizing fixture adapter** — allows deterministic mechanics tests without a caller-upgradable path to current-TD/human authority.

Each component must expose a narrow interface and be independently hostile-testable.

## 17. RED-first execution order

After this written amendment and its implementation plan are reviewed, Task 4 execution begins from exact frozen Task 3 head `117dd51dea827e734b299982da93991b934bdc8f`.

Required order:

1. create a Task 4 RED-only branch from the frozen Task 3 head;
2. add C1 two-BAD-row tests plus the expanded C1 attacks from Section 4.4;
3. add C3 legacy-import guards;
4. add C4 diagnostic-only authority attacks;
5. add C5/C6 actor-authentication/revocation-policy attacks;
6. add C7 unknown/unissued requirement-class attacks;
7. add C8 construction-time Task 1 authority-law attacks;
8. add C9 same-process tampering/non-authorizing fixture attacks;
9. add sibling-route attacks for every authority state touched;
10. prove RED before production repair;
11. implement the minimum prospective Task 4 production surface needed to make those tests GREEN;
12. run the existing 13 inherited custody attacks and 36 expanded Task 4 attacks from the controlling design;
13. run focused Task 4 tests, full `tests/v5/td_unified`, frozen Task 3/2/1 regressions, and inherited unified synthetic integration;
14. perform owner hostile re-audit focused on alternate routes to authority;
15. obtain independent exact-head Macha review before Task 5 begins.

No final challenge secret material is generated merely to make the RED suite executable; RED uses synthetic/fixture hidden material only.

## 18. CI and workflow constraints

Task 4 qualification workflows must be read-only with respect to repository contents unless an independently reviewed workflow explicitly exists for a non-qualification maintenance purpose.

The Task 4 verification workflow must:

- declare `permissions: contents: read`;
- use full-history checkout where ancestry/archive scans are required;
- never auto-edit, auto-commit, or auto-push production/tests in response to failures;
- preserve failed RED evidence;
- separate fixture mechanics from any future protected/human execution harness;
- never publish hidden final challenge material in logs or artifacts.

A workflow-policy regression analogous to accepted Task 3 B6 protection must run on Task 4.

## 19. Acceptance conditions for enabling KTQ-or-later

Task 4 must not make `KNOWN_TRUTH_QUALIFIED` or later reachable until an independent review confirms all of the following on one exact head:

- C1 defect-bearing revocation identity is canonical and both accepted-review BAD rows are closed;
- revocation is checked over the complete prerequisite closure;
- persistent cross-process revocation/history custody is operational and R4 is closed for the claimed authority scope;
- current production consumers use `registry_v1` only and validate custody;
- `derive_real_reference_ready` is diagnostic-only;
- authority actors are authenticated beyond names for the claimed human/current-TD scope;
- frozen actor policy applies to revocation/supersession;
- requirement classes are closed and issuer-bound;
- Task 1 authority law is enforced at `RegistryUnit` construction;
- producer-process tampering cannot become authority;
- R5 pooled donor-level claim restriction is carried into downstream evidence;
- sibling-route hostile attacks find no alternate route to the same authority stages;
- frozen Task 0–3 regressions remain GREEN;
- no final secret/publication leak is present.

Only then may a later task prospectively enable KTQ-or-later transitions under the exact reviewed custody contract.

## 20. Explicit non-goals

This amendment does not:

- create final challenge secrets or realization worlds;
- execute qualification;
- open candidate outcomes;
- interpret biological PASS/FAIL;
- select targets;
- select representations;
- authorize Stage 4;
- authorize training;
- close R4 merely by specifying it;
- close R7 merely by naming an actor-attestation requirement;
- modify frozen Task 0–3 production code.

## 21. Design completion condition

This amendment is approved for implementation planning. The implementation plan is now written and must be reviewed before the RED-only execution branch is created. After plan approval, preserve the exact order: RED attacks first, minimal prospective repair, inherited regressions, sibling-route hostile re-audit, then independent exact-head Macha review.
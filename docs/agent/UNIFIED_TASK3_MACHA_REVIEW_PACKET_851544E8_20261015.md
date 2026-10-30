# Macha independent hostile review packet — Unified Task 3 — exact head 851544e8 — 2026-10-15

Role: independent hostile reviewer.
Scope: Unified Task 3 A2/A5/A6 plus binding Task 2 residuals R1–R6.
Do **not** re-audit the whole project.
Do **not** start Unified Task 4.
Do **not** open protected biological/candidate/validation/oracle values.

## Exact candidate

Repository: `dushyant-mishra/sea-ad-jepa-agent`
Task 3 PR: #392
Exact head:

`851544e8dc2a3881193a4d5bbcf07933e1d61149`

Frozen ancestors:

- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`

Original Task 3 RED:
`9456553d7352bb4f620baaba95051f85aab448ae`

Final owner hostile RED6:
`eff7afe99163fc7b18a5adda52bd17a6c3f89174`

Task 3 is **OPEN**. This packet does not grant authority.

Binding project authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## What the controller claims

The candidate implements `TD_QUALIFICATION_REGISTRY_V1` under A2, A5 and A6:

1. one canonical Task-1 stage system and active-lineage system;
2. immutable promotion history;
3. active revocation/supersession;
4. one-stage promotion only;
5. recursively authenticated prerequisite graphs;
6. no authoritative aggregate `ready=true` override;
7. exact frozen Task-2 manifest/access/per-unit dependency binding;
8. exact controller/reviewer/producer/executor actor identity and role separation;
9. identity changes force requalification;
10. content validation and external-evidence receipts where appropriate;
11. R1–R6 remain binding;
12. recursive verification cache invalidates on dependency mutation including reverse dependencies.

Treat all of these as claims to attack, not facts to assume.

## Controller test evidence — not independent acceptance

On exact head `851544e8...`:

- Task 3 workflow `38754803093`, job `116490276627`:
  - 51 focused Task 3 tests passed;
  - 154 complete unified Task 0–3 tests passed.
- frozen Task 2 workflow `38754803025`: SUCCESS;
- frozen Task 1 workflow `38754803012`: SUCCESS;
- inherited unified synthetic integration `38754803248`: SUCCESS.

The diff from frozen Task 2 adds Task-3-only implementation/schema/tests/workflows/audit scripts. Do not treat green CI as scientific authority.

## Required hostile review

### T3-A — canonical stage / lineage / historical evidence

Attack at minimum:

1. try to introduce a second stage vocabulary;
2. try to promote by more than one stage in one call;
3. try to promote a `SUPERSEDED`, `REVOKED_BY_DEFECT`, or `REQUIRES_REQUALIFICATION` unit;
4. revoke a unit and verify its historical promotion receipt remains immutable;
5. supersede without exact successor identity or requalification scope;
6. change code, policy, schema, metric, reference producer, falsifier, manifest, access law, producer actor, or executor actor and attempt silent stage inheritance;
7. construct conflicting or duplicate current unit identities and see whether validation fails closed.

Expected law: changed decision-bearing identity creates a new identity / requalification requirement; historical receipts remain historical evidence rather than being rewritten.

### T3-B — A5 actor-level no-self-qualification

This is the most important new owner-found defect and must be independently re-attacked.

Attack with distinct canonical objects whose `actor_id` values alias:

1. scientific producer actor == qualification controller actor;
2. scientific executor actor == qualification controller actor;
3. producer actor == independent reviewer actor;
4. executor actor == independent reviewer actor;
5. controller actor == independent reviewer actor;
6. same actor with different role labels and different object bytes/nonces;
7. unresolved producer/executor actor object;
8. actor-object digest mismatch;
9. wrong actor role for a matching digest;
10. producer/executor actor identity changed after prior qualification.

Expected law:

- producer/executor actor objects are exact resolved dependencies;
- controller/reviewer are exact resolved authority objects;
- their underlying `actor_id` values, not merely their object digests or code SHAs, enforce independence;
- actor changes reset qualification to `SEMANTICS_ONLY` and `REQUIRES_REQUALIFICATION`.

### T3-C — A6 prerequisite graph completeness

Attack:

1. caller-supplied `ready=true` with missing prerequisites;
2. revoked prerequisite;
3. superseded prerequisite without exact required successor;
4. `REQUIRES_REQUALIFICATION` prerequisite;
5. prerequisite at insufficient stage;
6. stale dependent-unit identity;
7. stale prerequisite-unit identity;
8. stale manifest/access identity;
9. missing dependency resolver;
10. boolean `True` resolver instead of actual bytes/object;
11. digest string with no resolvable object;
12. recursive missing dependency;
13. cyclic prerequisite graph;
14. changed nested dependency after a cached positive result;
15. changed reverse dependency after a cached positive result.

Expected law: readiness is derived from the complete active graph every validation context; an unsatisfied prerequisite remains visible in machine-readable output.

### T3-D — exact frozen Task 2 binding

Attack:

1. copied Task-2 manifest/access digests without actual objects;
2. different manifest with matching-looking labels;
3. wrong per-unit execution identity row;
4. `FIXTURE_UNBOUND` substituted for `AUTHENTICATED_READER_SPLIT`;
5. population or access authority represented only by prose/status strings;
6. protected validation/oracle value access smuggled through a prerequisite/evidence receipt.

Expected law: Task 3 cannot manufacture new population/access authority or reopen protected partitions.

### T3-E — Task 2 residual R1–R6

#### R1 process isolation

Before any `HUMAN_EXECUTABLE` transition, require actual resolved evidence whose content states all of:

- producer process isolated;
- harness drives finalization;
- reader-fit values out of producer process;
- protected partitions physically absent.

A role label alone must fail.

#### R2 nested content

Where a prerequisite declares content qualification, a role-tagged/vacuous object or `content_validated=true` alone must not satisfy it. Require an exact content-validation receipt/object.

#### R3 fixture authority

`FIXTURE_UNBOUND` may exist for mechanics but must never satisfy current-TD real-reference/human authority.

#### R4 cross-process ledger/key custody

Before cross-process receipt use / human execution, require actual resolved evidence of:

- persistent ledger;
- signing key out of producer process;
- key custodian = harness (or exact controlling equivalent).

#### R5 claim scope

Pooled five-fold donor-level evidence must not be relabelled as per-fold source-stratified evidence. Preserve the known limitation that fold 4 contains only one held-out NPH52 donor.

#### R6 cache

Verify cache entries are identity-bound and invalidated when any direct or reverse dependency changes. Cached positive readiness must never survive changed dependency identities.

### T3-F — promotion/revocation provenance

Attack:

1. hand-construct an advanced-stage unit with no lawful prior promotion history and try to advance again;
2. fabricate a `PromotionReceipt` with plausible strings but wrong `pre_registry_sha`, unit identity, prerequisite identities, controller/reviewer identities, or stage edge;
3. fabricate revocation/supersession receipts;
4. use green CI, PR number, branch name, prose approval or status booleans as authority;
5. mutate historical receipts after revocation.

Expected law: promotion/revocation receipts are canonical historical evidence whose provenance is recomputed and whose existence cannot be substituted by navigation metadata.

## No-repeat / scope restriction

Do not reopen Task 0, Task 1 or Task 2 accepted findings unless this exact Task 3 candidate exposes a concrete new defect that invalidates their interface assumptions.

Do not recompute settled biological audits or protected values.

Do not begin Task 4 implementation.

## Required verdict

Return exactly one top-level verdict:

`ACCEPT_UNIFIED_TASK3`

or

`REJECT_UNIFIED_TASK3`

Then report:

1. exact reviewed head;
2. A2 lineage/history verdict + evidence;
3. A5 actor-independence verdict + evidence;
4. A6 prerequisite/readiness verdict + evidence;
5. frozen Task-2 binding verdict + evidence;
6. R1–R6 verdicts;
7. promotion/revocation provenance verdict;
8. independent hostile test/probe count and result;
9. residual non-blocking carry-forward;
10. freeze decision.

If accepted, state exactly:

`TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

If rejected, state exactly:

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

If rejecting, every blocker should identify the exact file/function/field, the hostile attack, why current validation is insufficient, and the smallest lawful repair.

No Task 3 verdict changes target, representation, protected-value, Stage 4 or training authority.

## Standing successor protocol

The lane owner requires iterative self-audit/fix cycles and continuous preservation of historical audits, scripts, results, failures and exact identities in PR #322 and PR #323. Future agents must reuse this custody rather than restart settled audits. Heavy/private data remain hash/path-custodied.

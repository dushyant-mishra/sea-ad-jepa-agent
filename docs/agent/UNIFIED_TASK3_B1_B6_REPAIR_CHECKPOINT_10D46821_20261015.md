# Unified Task 3 B1-B6 repair checkpoint

Date: 2026-10-15
Status: `TASK3_B1_B6_REPAIRED__MACHA_FOCUSED_RECHECK_PENDING__TASK4_BLOCKED`
Authority effect: NONE

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Rejected candidate

Independently rejected Task 3 head:
`851544e8dc2a3881193a4d5bbcf07933e1d61149` (PR #392).

Macha review head:
`869ca777` on `review/macha-task0-independent-review-20261014`.

Verdict:
`REJECT_UNIFIED_TASK3`
`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

The rejected head is permanently non-freezable. Prior controller GREEN does not transfer authority after independent rejection.

## Blocking findings being repaired

- T3-B1: promotion did not enforce Task 1 authority scope/stage restrictions; UNIT scope could reach TRAINING_AUTHORIZED.
- T3-B2: stage evidence was incomplete; KNOWN_TRUTH_QUALIFIED and HUMAN_EXECUTED could advance without the required evidence types.
- T3-B3: no-self-qualification could be bypassed by lookalike/unregistered actor names.
- T3-B4: caller-controlled verification cache could forge readiness or survive a resolver change.
- T3-B5: revocation/history could be deleted/rebuilt; internally consistent receipts did not prove lawful provenance.
- T3-B6: write-capable GitHub Actions workflows could rewrite source/tests on human push and could silently mutate a future RED test.

## Repair branch and exact candidate

Branch:
`repair/unified-task3-b1-b6-20261015`

Draft PR #397.

Exact focused-recheck candidate:
`10d468214aa057be023e38cd7a89d64f208d92e3`

Task 4 remains blocked until independent exact-head acceptance.

## B6 containment occurred first

Before changing registry authority logic, the repair removed the two write-capable workflows identified by the hostile review:

1. `711e6973468e3a81af4c70fc701e09512360d3eb`
   removed `.github/workflows/task3-red6-actor-repair.yml`.
2. `71ea41871b7ef0d7dd775838e28612b129c24c7f`
   removed `.github/workflows/apply-task3-cycle4-hardening.yml`.

At the rejected head, `task3-red6-actor-repair.yml` had `contents: write`, ran:
- `scripts/agent/task3_red6_actor_identity_repair.py`
- `scripts/agent/task3_green6_actor_resolver_patch.py`
- `scripts/agent/task3_green6_fixture_migration.py`
then committed/pushed source/schema/tests as `github-actions[bot]`.

At the rejected head, `apply-task3-cycle4-hardening.yml` had `contents: write`, ran:
- `scripts/v5/td_unified/apply_task3_cycle4_hardening.py`
then committed/pushed registry/test changes as `github-actions[bot]`.

The older Task 3 cycle1/cycle2/cycle3 workflows are retained only as read-only verification/history; they do not have authority to rewrite the repair candidate.

### Bot-mutation custody note

A prior controller custody record observed bot-authored GREEN migration history, including the GREEN6 fixture/source migration lineage. The exact workflow source above proves both removed workflows were capable of committing under `github-actions[bot]`, including their exact producer scripts and commit-message templates. Current connector commit search did not reliably reproduce all historical bot-authored commit enumeration, so this checkpoint does **not** invent an exhaustive bot-SHA list. The verified workflow/script mapping is retained here, and the removed workflows themselves remain historical evidence. This uncertainty is custody metadata only and does not authorize the rejected lineage.

## Preserved RED and repair lineage

- `3bf538bc968c9b1fc7934ef366052c3683e3ffef`: preserves Macha B1-B6 probes as RED tests.
- `96d896a16b0f788fd5314b76d3851df0ec6a7beb`: binds exact pre-registry snapshots for B1/B2/B5 RED probes before repair.
- `c4774b77785f27e9dbc093b97f447e43c5df8194`: hardened authority facade.
- `4cea6424a96173073cd07c9977c5117deb175630`: closed authority and migrated unsafe legacy tests.
- `19841dcacfdbd0b123eec7e0d916056ea6bcd94e`: fixed-start history plus R1/R4 diagnostics.
- `10d468214aa057be023e38cd7a89d64f208d92e3`: anchors forged-history checks before human evidence and completes aggregate R1/R4 diagnostics.

## Repair semantics

### B1
Every promotion is checked against the Task 1 authority model. UNIT-scoped authority cannot silently reach forbidden training stages. `NO_TRAINING_AUTHORITY` remains decision-bearing.

### B2
Promotion uses a fixed stage-evidence table. Stages whose required authoritative evidence does not yet exist fail closed. Controller sign-off alone cannot manufacture KNOWN_TRUTH_QUALIFIED or HUMAN_EXECUTED authority.

### B3
Controller/reviewer authority uses a registered actor/role surface with strict actor identifiers. Producer/executor actor objects remain exact unit dependencies. Whitespace/case/fullwidth lookalikes and newly invented authority actors are refused rather than normalized into authority.

### B4
Verification caching is local to the verification operation. Caller-supplied cache contents do not grant readiness and cannot be carried across an unrelated resolver as authority.

### B5
Promotion/revocation is checked against fixed-start current history. Advanced hand-built history, deleted revocations and forged reconstruction cannot create lawful promotion provenance.

### B6
The self-mutating workflows were removed before authority repair. The normal Task 3 verification workflow is read-only.

## R1-R6 state

- R1: NOT solved for human execution. Process-local synthetic mechanics are not a real process-isolation trust anchor. HUMAN_EXECUTABLE must remain blocked until the harness/registry/reader-fit custody boundary is genuinely out-of-process.
- R2: content qualification still requires registered/authenticated validators; role labels alone remain insufficient.
- R3: binding; fixture authority cannot become current-TD authority.
- R4: NOT solved for human cross-process use. Durable ledger/signing-key custody still requires a real external trust anchor.
- R5: binding; pooled donor-level cross-fit scope only, not per-fold source-stratified claims.
- R6: repaired as per-call identity-sensitive verification/cache behavior; caller cache is not authority.

Compatibility-only parameters such as `asserted_ready`, `verification_cache`, and `prerequisite_evidence_verifier` may still appear in the current facade signature solely for historical ABI compatibility but are explicitly ignored for authority. They should be removed prospectively once doing so will not obscure the focused B1-B6 recheck lineage.

## Exact-head controller verification

On exact `10d468214aa057be023e38cd7a89d64f208d92e3`:

Task 3 workflow run `38764885273`, job `116525386712`:
- focused `tests/v5/td_unified/test_registry_v1*.py`: **57 passed**;
- complete `tests/v5/td_unified`: **160 passed**;
- full-history checkout;
- read-only workflow token.

Same exact head:
- frozen Task 2 workflow `38764885283`: SUCCESS;
- inherited unified synthetic integration `38764885312`: SUCCESS.

No frozen Task 0-2 production file is modified by the repair. No protected biological/candidate/validation/oracle values were opened.

Controller GREEN is not independent acceptance.

## Next lawful action

Macha should recheck only T3-B1 through T3-B6 on exact:
`10d468214aa057be023e38cd7a89d64f208d92e3`.

If and only if Macha accepts this exact head may Task 3 be frozen and Task 4 begin prospectively from that accepted Task 3 head.

# Unified Task 1 Macha rejection and focused repair checkpoint V1 — 2026-10-15

Status: `MACHA_REJECTED_86FA996F__FOCUSED_REPAIR_799D2E23_CONTROLLER_GREEN__INDEPENDENT_RECHECK_PENDING__TASK2_BLOCKED`

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Independent rejection

Macha independently reviewed Unified Task 1 exact head:

`86fa996f609bec3f39d0f6a12d7f040b2544af39`

Review branch exact head:

`9b9278452144890dce2825025da4b2814a640ee5`

Verdict: `REJECT_UNIFIED_TASK1`.

Exact review artifacts on the Macha branch:
- `docs/agent/MACHA_UNIFIED_TASK1_INDEPENDENT_REVIEW_86FA996F_20261015.md`
- `results/target_discovery/unified_qualification_v1/MACHA_UNIFIED_TASK1_REVIEW_VERDICT_V1.json`
- `docs/agent/macha_task1_review_evidence_86fa996f/`

The machine verdict records five blocking findings:
- `T1-B1` critical: canonical encoder trusted subclass/NumPy self-description;
- `T1-B2`: producer code identity was format-checked but not resolved/recomputed;
- `T1-B3`: authority-bearing dependency roles were not typed or cross-role distinct;
- `T1-B4`: free-text scope could imply widened pipeline/project authority;
- `T1-B5`: no fixed known-answer fingerprints froze the identity format.

Non-blocking carry-forward from the review:
- M1 memoize recursive verification before Task 3 registry chains;
- M2 non-text unit-ID error typing;
- M3 Task 2 must add raw-file byte identity verification;
- M4 Task 3 must prevent revoked records from active use.

No protected human partition or candidate outcome was opened by the review.

## RED-first focused repair

Repair PR: `#386`.

Repair branch:
`repair/unified-task1-macha-b1-b5-20261015`

The repair branch is based directly on rejected head `86fa996f...` so its PR delta is only the focused B1–B5 repair.

RED head:
`d6f716828be3dda5fa2c5523396f8d8eb1368686`

RED evidence:
- workflow run `38672565504`;
- job `116218830306`;
- result: expected FAILURE, `9 failed, 18 passed`;
- all nine failures were the intended Macha blocker probes.

## Focused repair candidate

Exact controller-GREEN candidate:

`799d2e235901dfad9ce3b305c767a1c989e362f6`

Repairs:
1. exact built-in scalar/container canonical dispatch; hostile subclasses rejected; frozen old-compatible NumPy scalar policy;
2. producer code resolves exact bytes and recomputes Git blob SHA-1;
3. INPUT/OUTPUT/MANIFEST/REGISTRY/ACCESS_POLICY dependency roles are explicit; authority roles are cross-role distinct; receipt inputs remain recursively verified;
4. authority scope grammar is closed to `UNIT:<id> | PIPELINE:<id> | PROJECT`, restrictions are separate, and code/schema freeze a scope-stage table;
5. `FINGERPRINT FORMAT V1` documents byte semantics and fixed known-answer digests pin canonical and receipt identities.

Exact-head controller evidence:
- focused Task 1 run `38672796995`, job `116219561771`: SUCCESS, `27 passed`;
- inherited unified synthetic integration run `38672796999`, job `116219562500`: SUCCESS.

Comparison from rejected head `86fa996f...` to repair candidate `799d2e23...` changes only seven focused surfaces: Task 1 workflow, authority schema, canonical implementation, authority implementation, the two inherited Task 1 test files, and the new Macha repair test file.

## Authority boundary and next lawful action

Controller GREEN is not independent acceptance.

Task 1 remains open until Macha performs the promised focused re-check of exact head:

`799d2e235901dfad9ce3b305c767a1c989e362f6`

Unified Task 2 remains blocked until that exact Task 1 repair is independently accepted and frozen. The previously prepared Task 2 launch package is non-executing preparation only and must be rebound if the accepted Task 1 head differs.

No candidate outcomes, `reader_validation`, `reader_oracle`, target selection, representation selection, Stage4, or training authority changed.

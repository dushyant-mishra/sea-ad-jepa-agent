# JEPA lane takeover handoff — 2026-10-15

This is the read-first handoff for the JEPA Target Discovery → known-truth qualification → downstream lane.

## 0. Permanent operating rule

Every successor agent must work iteratively and preserve custody continuously:

1. assimilate existing audits before new work;
2. self-audit → RED → minimal repair → focused regression → inherited regression → renewed hostile audit;
3. update PR #322 (durable audit/custody) and PR #323 (read-first navigation) as work evolves;
4. preserve exact heads, scripts, tests, results, receipts, failures, negative findings and no-repeat classifications;
5. do not repeat settled historical audits absent changed bytes, changed authority/scientific context, or a concrete uncovered defect;
6. do not promote mechanics evidence into biological authority;
7. do not open protected validation/oracle values or enable real training without explicit later authorization.

## 1. Read these first

On PR #322 / branch `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`:

1. `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md`
2. `results/target_discovery/unified_qualification_v1/JEPA_LANE_TAKEOVER_STATE_V1_20261015.json`
3. `results/target_discovery/unified_qualification_v1/INDEPENDENT_REVIEW_CUSTODY_INDEX_20261015.json`
4. `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_20261015.json`
5. `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`
6. `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt`
7. `docs/agent/historical_imports/WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`

Independent Task 3 hostile review is preserved at exact review head `869ca777a498181c519ccfc04b8bf5db0f2888c7` on `review/macha-task0-independent-review-20261014`:

- `docs/agent/MACHA_UNIFIED_TASK3_INDEPENDENT_REVIEW_851544E8_20261015.md`
- `results/target_discovery/unified_qualification_v1/MACHA_UNIFIED_TASK3_REVIEW_VERDICT_V1.json`
- `docs/agent/macha_task3_review_evidence_851544e8/task3_probe1.py`

## 2. Current authority state

Frozen accepted heads:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Unified Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Unified Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`

Unified Task 3 candidate `851544e8dc2a3881193a4d5bbcf07933e1d61149` / PR #392 is **REJECTED**.

Unified Task 4 has a controlling approved design but **implementation remains blocked**.

Binding global stop state:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No target winner, representation winner, protected-value access, Stage 4 authority or training authority has been granted.

## 3. Immediate next action — Task 3 repair only

Macha verdict:

`REJECT_UNIFIED_TASK3`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Repair order is important.

### First: T3-B6 custody fix BEFORE any further Task 3 repair push

Two write-capable workflows on the rejected branch can rewrite code/tests as `github-actions[bot]`, including future RED tests. Disarm/delete them or convert them to read-only/manual-only without commit/push behavior before doing anything else:

- `.github/workflows/task3-red6-actor-repair.yml`
- `.github/workflows/apply-task3-cycle4-hardening.yml`

Also enumerate CI-bot-authored Task 3 commits in the custody record with the script/workflow that generated each.

### Then preserve Macha’s hostile probes as RED tests

Use the exact probe at review head `869ca777...`, especially H1–H6 and actor-alias cases. RED must fail for the intended reasons before production repair.

### T3-B1 — authority scope/stage bypass

`promote_unit` must apply frozen Task 1 `validate_authority_record` to every promoted result. `UNIT:<id>` cannot exceed `HUMAN_EXECUTED`; `NO_TRAINING_AUTHORITY` must refuse all `TRAINING_*` stages. Later pipeline/project stages are not unit-registry transitions.

### T3-B2 — missing stage evidence gates

Add a closed table of required evidence per promotion stage. Fail closed where evidence types are not yet defined. In particular:

- `KNOWN_TRUTH_QUALIFIED` cannot be granted before Task 4/5 sealed challenge/adjudication evidence exists;
- `HUMAN_EXECUTED` requires an execution receipt;
- independent reviewer evidence is required where specified.

Do not invent placeholder evidence that makes unavailable stages pass.

### T3-B3 — actor registry / no-self-qualification

Free-form actor strings are not authority. Add a frozen identity-bound actor registry with strict ASCII canonical IDs and permitted roles. Refuse unknown/self-minted actors. Compare authenticated actor registry identities, not raw free-text equality. Apply this to controller, reviewer, prerequisite evidence authors and content validators.

### T3-B4 — verification cache trust

Remove caller-owned writable authority cache. Verification memoization must be internal to one call or bound to an opaque verified context. Never trust caller-preloaded positives; resolver/context change must force re-verification.

### T3-B5 — immutable history / revocation

Add replay-validated append-only history from a fixed genesis anchor. Before promotion/readiness:

- replay promotions/revocations;
- require every `pre_registry_sha` to equal the replayed state;
- rederive readiness for gated transitions on the replayed pre-state;
- require current stage/lineage to equal replay output;
- externally anchor the current registry head.

A deleted revocation receipt or fabricated historical snapshot must not create authority.

### Cleanup

Remove dead `asserted_ready` and `prerequisite_evidence_verifier` compatibility parameters so they cannot be mistaken for authority surfaces.

### Gate after repair

Run focused Task 3 tests + complete unified tests + frozen Task 2/1 + inherited synthetic integration, then obtain a **focused independent Macha recheck of T3-B1…B6 only**. Task 4 stays blocked until explicit acceptance.

## 4. What already works in Task 3 and should not be rebuilt

Macha confirmed these mechanics on rejected head `851544e8...`:

- one-stage promotion sequencing;
- non-ACTIVE units are refused;
- re-identifying a unit resets to `SEMANTICS_ONLY` / `REQUIRES_REQUALIFICATION`;
- supersession binds successor identity;
- missing/boolean dependency resolver blocks;
- `asserted_ready` is ignored;
- revoked/stale/insufficient-stage dependencies block in normal prerequisite checking;
- cycles fail;
- unsatisfied prerequisites remain visible;
- exact Task 2 execution-identity row binding works;
- access-policy population authority matches registry unit;
- `FIXTURE_UNBOUND` is blocked at `REAL_REFERENCE_READY`;
- per-fold source-stratified claims are blocked under the accepted five-fold limitation.

Do not rewrite these surfaces unless required by B1–B6 repair.

## 5. Task 2 residual obligations carried into Task 3+

- R1: before `HUMAN_EXECUTABLE`, real harness registry/key/reader-fit values must be outside producer process; self-asserted booleans are not a trust anchor.
- R2: nested contracts need substantive content qualification, not role labels alone; content validators must themselves be registered/authorized actors.
- R3: fixture authority cannot satisfy current-TD authority.
- R4: persistent ledger + signing-key custody before cross-process receipt consumption; self-asserted custody dicts are insufficient.
- R5: accepted 5-fold design supports pooled donor-level analyses only, not per-fold source-stratified claims; fold 4 has one held-out NPH52 donor.
- R6: verification cache must be internal/context-bound and invalidated/rechecked on dependency changes.

## 6. Task 4 status — design ready, code blocked

Controlling design:

`docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`

Do not start Task 4 production implementation until Task 3 is independently accepted/frozen.

Settled Task 4 laws:

- Task 4 certifies exam custody, not generic scientific difficulty or biological PASS/FAIL;
- one immutable `QualificationCampaign` genesis prevents fresh-ledger/reset attacks;
- complete finite realization inventory sealed before first final exposure;
- exposure spends information budget even on crash/abort/defect;
- Task 3 registry/unit authority re-resolved before each authority-bearing transition;
- no generic harder/easier oracle; changed/ambiguous challenge defaults to new campaign;
- reviewed additive stress may augment but never replace prior failures/exposures;
- harness, not producer, issues exposures/finalization;
- method output freezes before reveal;
- reveal regenerates committed realization set rather than trusting caller lists;
- persistent append-only ledger with externally anchored heads;
- signer/key outside producer process;
- secret scanning covers exact repository archive, CI logs, workflow artifacts, receipts, errors, paths and cache metadata;
- custody receipt and qualification evidence package are separate; Task 5 interprets the science.

Historical old synthetic Task 2 at `ff597faf2182522a320ec5322f8db9b67c9c6094` is substrate only. Preserve its 13 historical custody attacks, E2 non-circular commitment interpretation and D1 exception hardening.

## 7. Historical no-repeat map

Read `JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` rather than restarting project archaeology.

Important controlling repaired Target Discovery lineages already audited:

- G8 #364
- G6 #365
- geometry G9/S1/S2 #366
- R1 #367
- G2 #368
- G7 #362
- R4/C6/C4 #358
- C4→C6 firewall #351
- G12 #360
- system battery #369

PRs #375–#378 are superseded duplicates.

Population/support registry: PR #349 head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`, registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`.

Old production-synthetic Tasks 1–2 implementation head `ff597faf2182522a320ec5322f8db9b67c9c6094`; checkpoint/docs descendant `f53c13e6eed329651b1088775782fea399ba1bf6`.

Task 0, Task 1 and Task 2 rejection→repair→independent-acceptance histories are settled and must not be repeated absent changed exact bytes or authority context.

## 8. Historical science constraints that remain binding

- measured zero ≠ unsupported;
- unsupported ≠ unresolved;
- unresolved ≠ biological FAIL;
- numerical failure ≠ biological FAIL;
- generic RNA presence ≠ candidate support;
- source failure cannot average away;
- denominator/off-address mass must remain explicit;
- address parity ≠ evidence parity;
- no favorable zero-fill;
- validation/oracle cannot rescue reader-fit estimability;
- common-core support is comparability, not truth;
- native support is not automatically private biology;
- dimension-qualification estimand ≠ training estimand;
- qualification rank ceiling ≠ model width;
- evidence acquisition ≠ measurement depth;
- false certainty and false abstention are both failures.

Technology is an observation operator `O_t`, not a donor/dataset identity. Preserve legitimate donor biology; separate measurement OOD from biological novelty; audit subspace/axis stability; distinguish biological-evidence convergence from measurement-depth convergence; use held donor/matrix/dataset/technology transfer and hierarchical dataset→donor→cell sampling before real training.

## 9. Local/private artifact custody

Large/private artifacts available in the current project environment are **not** copied into Git. Their exact sizes/SHA-256 and notable contents are recorded in:

`results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_20261015.json`

Key bundles include:

- FOUNDATION discovery expression split archive, reconstructed SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- calibration bundle SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- expression audit bundle SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`;
- checkpoints bundle SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`;
- T1 checkpoint history bundle SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.

Verify bytes against the manifest before use. Presence is not authority.

## 10. Do not do these things

- Do not call Task 3 accepted at `851544e8...`.
- Do not start Task 4 implementation before Task 3 acceptance.
- Do not let CI auto-rewrite RED tests or production code.
- Do not use self-minted actor/evidence dictionaries as trust anchors.
- Do not use caller-supplied caches as authority.
- Do not rebuild registry history from a convenient current snapshot.
- Do not reactivate old Tasks 3–12 as a parallel lane.
- Do not rerun spent biological experiments merely for migration.
- Do not open validation/oracle values to rescue reader-fit failures.
- Do not enable real training.

## 11. Successor's first working sequence

1. Re-fetch PR #392 exact branch head and verify no unexpected mutation after rejected `851544e8...`.
2. Read Macha review at `869ca777...` and preserve H1–H6/alias probes.
3. Disarm/delete B6 write-capable workflows FIRST.
4. Cut a focused Task 3 repair branch from the rejected candidate or controlling repair base according to governance; preserve rejected candidate immutably.
5. Add RED tests for B1–B6 and prove intended failures.
6. Repair minimally in B1→B5 order while keeping known-good A6/Task2-binding mechanics intact.
7. Run focused + full inherited CI on one exact head.
8. Update PR #322/#323 with every RED/GREEN head and result.
9. Ask Macha for focused B1–B6 recheck only.
10. Only after acceptance/freeze, derive the Task 4 implementation plan from the controlling Task 4 design and start Task 4 RED-first.

This handoff grants no authority beyond the frozen heads listed above.
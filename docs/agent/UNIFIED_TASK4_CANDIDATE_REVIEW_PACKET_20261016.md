# Unified Task 4 candidate review packet

Status: `CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`

Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Implementation PR: #404  
Implementation branch: `work/unified-task4-impl-20261016`  
Candidate exact SHA: pin the immutable `candidate/unified-task4-green-<shortsha>-20261016` branch named in the PR conversation after the final verification run.

## Scope

Review only prospective Unified Task 4 custody/mechanics. Task 4 does not authorize biological PASS/FAIL, target selection, representation selection, Stage 4, protected values, or training. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated.

## Read first

1. `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`
2. `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`
3. `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`
4. `results/target_discovery/unified_qualification_v1/TASK4_ATTACK_MATRIX_V1.json`
5. Task 4 production modules under `scripts/v5/td_unified/` and strict Task 4 schemas/tests.

## RED evidence that must remain explainable

The original valid RED is PR #403, run `38938697657`, job `117100597615`: 14 intentional missing-interface failures under a read-only token.

Later REDs found real defects and must not be rewritten as if the implementation was initially correct:

- terminal accounting: `38943608912` / `117117078319`;
- schema drift: `38944319232` / `117119472176`;
- incomplete/aliasable C1-C9 barrier law: `38944836349` / `117121219990`;
- unauthenticated trusted-signer object: `38945592644` / `117123776998`;
- self-asserted actor/process context: `38946266116` / `117126036930`.

## Last fully verified code/test head before candidate-packet-only edits

`cfa3b7c4f92a1569639b6733a6956c516d7f4cf4`

Task 4 run `38946411134`, job `117126540739`:

- focused Task 4 suites PASS;
- dedicated 100k replay benchmark PASS;
- full unified Task 0-4 regression PASS.

Same-head regression runs:

- Task 1: `38946411299` PASS;
- Task 2: `38946411331` PASS;
- Task 3 registry: `38946411463` PASS;
- unified synthetic integration: `38946411400` PASS.

The final candidate SHA must receive a fresh equivalent Task 4 GREEN run before review starts.

## Inherited CI defects that are not Task 4 regressions

The following read-only workflows fail during import because their setup installs pytest but not NumPy; logs terminate with `ModuleNotFoundError: No module named 'numpy'` before their intended assertions execute:

- Task 0 migration audit `38946411227`;
- Task 0 B1-B5 verification `38946411361`;
- Task 3 B6 workflow policy `38946411617`.

Do not infer a Task 4 authority regression from those environment failures. Also do not silently repair frozen Task 0-3 workflows in this review.

## Required hostile review questions

A candidate is rejectable if any answer below is YES:

1. Can cosmetic stage/status/restriction mutation, restart, truncation, or rechain make a persistently revoked defect-bearing unit authoritative again?
2. Can any Task 4 path directly or indirectly regain authority through `registry_v1_legacy`, a stale readiness diagnostic, or a hand-constructed RegistryUnit/status object?
3. Can a signer object, actor name, alias, role string, caller trust root, or self-asserted context mapping substitute for externally authenticated actor-action evidence?
4. Can C5-C9 become GREEN without genuine external evidence for actor credentials, privileged policy currency, requirement/construction law, and process isolation?
5. Can an exposure crash, rerun, rename, method rename, or campaign restart reset a spent qualification exposure?
6. Can hidden material reveal before every required output is frozen, or can a frozen output mutate afterward?
7. Can missing/unsupported/technical-failure realizations disappear from terminal accounting or be favorably zero-filled?
8. Can repository/log/artifact/receipt/path publication leak hidden material or echo attacker-supplied secrets through refusal messages?
9. Can reference and optimized replay disagree, or can the 10k/100k custody path violate the committed replay semantics?
10. Did Task 4 modify any frozen Task 0-3 production file or create biological/target/representation/training/Stage4 authority?

## Acceptance rule

Independent reviewer must pin and state the exact candidate SHA, run or independently reproduce the relevant hostile suites, and return explicit `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` with concrete blockers. Review attacks must be made on a separate review branch; do not modify the candidate branch.

Even ACCEPT means only that the Task 4 custody candidate is mechanically accepted. It does not itself select a target, select a representation, authorize real training, authorize Stage 4, or create biological truth.

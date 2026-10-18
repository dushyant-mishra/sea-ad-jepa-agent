# Task 4 — Macha T4-B1…B5 repair and recheck packet

**Status: RECHECK_READY, NOT ACCEPTED.** Exact hostile-review input is frozen only after this packet and its matching JSON/tests pass exact-head CI.

## Immutable basis

- Task 3 accepted base: `117dd51dea827e734b299982da93991b934bdc8f`.
- Rejected successor-5: `36e3b46f1ca44465864a11872b459b5d108d6a67`, PR #421. Macha review head `d4d9ef94`, `REJECT_TASK4_CUSTODY_CANDIDATE`.
- Prior successor-6: `211375de57cc1f70d46c6eb3a4860d61a1aba0a6` (PR #425). It repaired separate same-identity re-mint and concurrent exposure attacks (PRs #422–#424), but **did not repair Macha B1/B2/B4/B5**.
- Macha immutable evidence: `results/target_discovery/unified_qualification_v1/MACHA_UNIFIED_TASK4_REVIEW_VERDICT_V1.json` and `docs/agent/macha_task4_review_evidence_36e3b46f/` on review branch `review/macha-task0-independent-review-20261014` at `d4d9ef94`.

## Repair sequence and observed RED

- T4-B1/B2: `tests/v5/td_unified/test_task4_macha_b1_b2_red.py` first committed at `f5c16f50590a83ec4b545c9b8fb3322ad38a4b4f`. CI `39091118650`, job `117567897946`: **4 failed, 129 passed, 1 skipped**. All four fail with `DID NOT RAISE`: forged campaign subclass, forged FINAL harness, forged exposure subclass, forged sealed definition subclass.
- Production repair `5ca886544a33ef697be55be57223add7f325ed7b`: exact `QualificationCampaign` type at lifecycle boundary, nonvirtual campaign payload digest, exact sealed definition/set identity, exact exposure and class-owned `identity_tuple`, exact Task4AuthorityHarness and class-bound genuine `current_status`. Do not treat this as independent external authority: it is in-process mechanics.
- T4-B3: successor-6 already introduced atomic in-process campaign identity lease plus concurrent state-transition locking. No new Task0–3 production changes. Cross-process identity persistence for FINAL remains **unwired** and fail-closed.
- T4-B4: only the three failing CI workflow YAMLs modified to install pinned `numpy==1.26.4` alongside pytest. These workflows were RED on earlier exact heads from NumPy imports triggered by Task3 `conftest.py`; no frozen production file modified.
- T4-B5: new simulated Windows-EBADF test in `tests/v5/td_unified/test_task4_macha_b5_fsync_red.py` first committed at `fb180b1901afb19db8a6ae04053d0857eba5e227`. CI `39091241599`, job `117568264331`: **1 failed, 133 passed, 1 skipped** (read-only file descriptor fsync). Production repair `a07f7c46fdd38e998a37eed913be5806369955dd` reopens existing/new files writable for fsync, and fsyncs containing directory after atomic head rename on POSIX. Added a POSIX directory-fsync assertion. **Actual Windows test recheck by Macha is still required.**

## Exact repair-code and test verification

Exact source head before this packet: `fba240661e7bd2cea4dd5b9cf512f5b37dcc6ede`.

Read-only GitHub Actions on that head:
- Task 4 `39091336589`, job `117568560592`: focused **135 passed, 1 skipped**, projected 100k replay **1 passed**, full unified Task0–4 **326 passed, 1 skipped**.
- Task0 migration `39091336493`: PASS.
- Task0 B1–B5 `39091336567`: PASS.
- Task3 B6 workflow policy `39091336417`: PASS.
- Task1 `39091336440`: PASS.
- Task2 `39091336401`: PASS.
- Task3 registry `39091336423`: PASS.
- Synthetic integration `39091336377`: PASS.

Diff from successor-6 touches only Task4 scripts/tests and three workflow dependencies. No Task0–3 production files changed. Historic PR #417 replay and PR #419 swapped generator REDs remain intact.

## Independent recheck scope

Macha should rerun his original 14-check probe (especially A1–A5), the two previously accepted hostile regeneration attacks, the new T4-B1/B2 tests, duplicate identity and concurrency tests, the three restored CI workflows, **and all 16 Windows-local custody tests**. Additionally check nonvirtual fingerprint computation, inherited exposed-world/hidden-reveal chronology, and whether class-specific checks leave an alternative caller-object path. Reconfirm FINAL cannot reach hidden reveal through subclassed or fake harness; cross-process authority never inferred from process-local locks or digest registries. Reply with `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` bound to the immutable final candidate SHA.

Even acceptance could qualify only non-authorizing Task4 mechanics; it would not authorize biology, target/representation selection, protected challenge, Stage4 or training.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

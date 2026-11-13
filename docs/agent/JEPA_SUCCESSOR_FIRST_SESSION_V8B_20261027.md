# JEPA new-agent first session — V8b smooth takeover checklist (2026-10-27)

This file exists to prevent a new agent from spending its first session reconstructing history that is already audited.

**Active handoff:** PR #460.  
**Durable audit:** PR #322, exact V8b audit head `c07659ccce04bec18a43cc4a371ec0bf277c9255`.  
**Historical handoff only:** PR #323.  
**Global authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## First 15 minutes — establish exact state, do not search broadly

1. Read this file and `JEPA_SUCCESSOR_HANDOFF_V8_20261027.md`.
2. On PR #322 read, in order:
   - `JEPA_POST_V8A_DELTA_V8B_20261027.md`;
   - `JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.md`;
   - `JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json`;
   - `JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.md`;
   - `JEPA_NO_REPEAT_DELTA_V8_20261027.md`;
   - attachment custody CSV.
3. Re-fetch exact current PR heads before acting. The V8b snapshot expects:
   - #457 `17e7cc8818d27222fac5c0a3e91677640ea81153`;
   - #458 `3b08081d7fb3fa99cf1459b13cbe47d5b0962547`;
   - #459 `57e707149b46ca011eee096f01dc08b64aeb8f9f`;
   - #460 this successor.
4. If any head differs, do **not** rewrite old handoffs. Add a new append-only audit delta before making decisions.

## Minutes 15–30 — classify the requested work

Every proposed action must be labeled one of:

- `ALREADY_AUDITED`
- `REJECTED_OR_CLOSED`
- `SUPERSEDED`
- `OPEN_DEFECT`
- `CHANGED_INPUT_REQUIRES_REQUALIFICATION`
- `AUTHORITY_NOT_EARNED`

Only the last three normally justify new implementation/review.

If unsure whether something exists, search the complete takeover index **before** repository-wide code search.

## Current ownership / do-not-duplicate map

### Unified Task4 custody
- Cumulative implementation: Macha-authored PR #428.
- Prior independent RED lineage: #443, #452.
- ChatGPT bounded repair: #454.
- Current Macha X1 transaction candidate: #459 `57e707149...`.
- **Next action:** independent adversarial review of #459, not another X1 implementation.
- **Still open:** cumulative non-author acceptance, X3 mixed Windows/WSL coordination, external publisher/issuer trust, power-loss/crash claims beyond tested scope.

### Production Synthetic Tasks1–3
- Task1 author-disclosed hostile RED: #448.
- ChatGPT Task1 repair: #453.
- Task2 independent hostile RED: #455.
- ChatGPT Task2 repair: #456.
- Current hostile recheck: #458 with **13 RED** against #453/#456.
- Task3: #437 was accepted **fixture mechanics only on older dependencies**.
- **Next action:** repair/review #458 issues, obtain independent cumulative Tasks1–2 verdict, then requalify Task3. No Production Synthetic Task4 before checkpoint.

### Task5 / downstream
- Existing JEPA downstream stack already exists in #326/#332/#351.
- #444 original bridge rejected by #450.
- #451 bridge repair received narrow incremental acceptance with limitations.
- **Next action:** integrate only after accepted Task4 and genuine A7. Do not duplicate TargetPortfolio, teacher/student, EMA, rehearsal or controller code.

### Real G7 E3
- #433 and repair #446 are rejected by hostile #441/#449.
- Decision law itself remains source-aware; **input provenance is the blocker**.
- **Next action:** authenticated physical observation identity, evidence-right ownership, q-excluded depth/normalization and actual V3 deciding-row digest consumption.
- Do not add more regex aliases or pooled-depth formulas to fake general E3 qualification.

### JEPA representation / anti-collapse
- PR #438 is rejected/closed after #442.
- Historical RBB-JEPA/Bayesian belief-head work remains negative evidence.
- **Next action:** none unless a genuinely new preregistered biological/nuisance design exists.

### Unified Tasks6–8
- #447 is fixture-only blocked gate inventory, fixture `TARGET=NONE` and abstention.
- **Next action:** none until accepted Task4/5 and authenticated real producers/target receipts.

### External E2G reference
- #457 current head is GREEN for its own public-reference workflows.
- It remains **symbol-level public context, noncausal and nonauthorizing**.
- Do not use as G7/target PASS or reopen old graph auxiliary claims.

## Minutes 30–60 — run only the relevant verifier

For takeover integrity on PR #322:
```bash
python scripts/v5/verify_jepa_lane_audit_v8.py
python scripts/v5/verify_jepa_lane_audit_v8a.py
python scripts/v5/verify_jepa_lane_audit_v8b.py
python -m pytest -q tests/v5/test_verify_jepa_lane_audit_v8.py
python -m pytest -q tests/v5/test_verify_jepa_lane_audit_v8a.py
python -m pytest -q tests/v5/test_verify_jepa_lane_audit_v8b.py
```

For successor integrity on PR #460:
```bash
python scripts/v5/verify_jepa_lane_handoff_v8.py
python -m pytest -q tests/v5/test_verify_jepa_lane_handoff_v8.py
```

Do not run every historical scientific experiment. The purpose of the audit layer is to avoid that.

## Environment and custody traps

- Large ZIP/NPZ/PT archives are intentionally external; use recorded raw SHA-256/size before requesting/re-downloading them.
- PyTorch checkpoint files are untrusted forensic evidence. Do not unrestrictedly unpickle.
- The 41K discovery archive exists as two split parts; prior audit verified their concatenated byte stream hash. Do not reconstruct/publish it just to prove identity again.
- Windows and WSL locks are not assumed interchangeable; X3 remains open.
- A GitHub Actions GREEN result verifies that code/test head only. It is not biological or external custody authority.
- PR titles/descriptions can lag later hostile reviews. Exact SHA + hostile test lineage controls.
- Historical source texts imported from chats are context, not authority. Old "next action" prose is superseded by V8b.

## What a new agent must preserve when modifying anything

1. Keep the original RED test commit and run.
2. Pin the repair SHA.
3. Re-run unchanged hostile tests.
4. Re-run inherited focused/full suites appropriate to the dependency.
5. State skipped/xfail tests explicitly.
6. Separate mechanics evidence from source/biological evidence.
7. State reviewer independence scope.
8. Add a new audit delta when an active head changes.
9. Update the clean successor pointer only after the audit delta is committed and qualified.
10. Never delete/rewrite rejected history to make a new candidate look continuously correct.

## What counts as a successful takeover

The new agent should be able to answer, without re-auditing history:

- Which target/representation is currently qualified? **None.**
- Can real training or Stage4 start? **No.**
- What is the immediate Task4 action? **Review #459, not reimplement X1.**
- Are Production Synthetic Tasks1–2 accepted? **No; #458 has 13 RED.**
- Is Task3 acceptance current under repaired dependencies? **No, dependency requalification pending.**
- Is real G7 E3 qualified? **No.**
- Does the downstream JEPA harness already exist? **Yes; reuse #326/#332/#351.**
- Is #457 biological validation? **No; public reference context only.**
- Where are historical audits/scripts/results/data identities? **PR #322 complete V8a index + V8b supplement.**
- Where is the active handoff? **PR #460.**

If those answers remain true, the global invariant remains unchanged.

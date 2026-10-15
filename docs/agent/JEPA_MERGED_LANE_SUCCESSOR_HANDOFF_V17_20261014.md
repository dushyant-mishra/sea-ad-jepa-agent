# JEPA merged-lane successor handoff V17 — 2026-10-14

Status: `CURRENT_READ_FIRST_HANDOFF__MACHA_ROLE_INDEPENDENCE_CORRECTED__TASK0_REVIEW_PENDING`

Supersedes V16 for current operational instructions. V16 remains historical provenance.

Binding authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Read first

1. PR #322 canonical audit/custody surface.
2. `docs/agent/JEPA_NEW_AGENT_TAKEOVER_MANIFEST_V1_20261014.md` on PR #322.
3. `docs/agent/JEPA_COMPLETE_TAKEOVER_AUDIT_MANIFEST_V1_20261014.md` on PR #322.
4. `docs/agent/MACHA_TASK0_FINAL_INDEPENDENT_REVIEW_PACKET_V2_20261014.md` on PR #322.
5. `docs/agent/MACHA_ROLE_INDEPENDENCE_CORRECTION_V1_20261014.md` on PR #322.
6. `docs/agent/MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md` on PR #322.
7. `docs/agent/JEPA_SUCCESSOR_FIRST_24_HOURS_CHECKLIST_V1_20261014.md`.
8. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`.
9. downstream reuse-first ledgers and no-repeat decision table on PR #322.

Do not reconstruct history from chat. Classify proposed work first as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

## Critical Macha role correction

Macha has three relevant roles:

- Claude coding/execution agent on the GPU laptop;
- author/implementer of old synthetic Tasks 1–2 at `ff597faf2182522a320ec5322f8db9b67c9c6094`;
- hostile reviewer of controller-authored merged-lane work.

Independence is claim-specific:

`SAME_AGENT_SEPARATE_PASS != INDEPENDENT_REVIEW`

Therefore:

- Macha **may independently review Task 0 custody/consolidation**, because Task 0 is controller-authored.
- Macha **cannot independently qualify/adjudicate his own old Task 1–2 code**.
- controller review PR #382 is the independent verification layer over those Macha-authored bytes.
- Macha may provide author/provenance attestation for Tasks 1–2 and may independently challenge the controller's migration/classification of them.
- a future GPU run performed by Macha must be reviewed/adjudicated by another reviewer before promotion.

## Current Task 0 gate

Task 0 PR #381 exact review candidate:

`c80d7398b41f10208ec1622bc52599383b940be6`

Evidence:
- focused run `38645994312`, job `116132861396`: SUCCESS, 29 passed;
- inherited run `38645994388`: SUCCESS.

Old synthetic Task 1–2 Macha-author head:

`ff597faf2182522a320ec5322f8db9b67c9c6094`

Independent controller verification PR #382:
- focused run `38644641042`, job `116128364543`: SUCCESS, 332 passed in 8.94s;
- inherited run `38644640881`: SUCCESS.

Correct remaining Task 0 review dependency:

1. Macha independently reviews the controller-authored Task 0 custody/consolidation at `c80d7398...`.
2. In that review he may assess whether the controller's migration treatment of old Task 1–2 is correct.
3. He must not describe his self-review of Task 1–2 as independent qualification.
4. Task 0 acceptance may rely on the separate controller verification of Macha-authored Task 1–2 plus Macha's independent review of the controller-authored custody layer, subject to the architecture's independence requirements.

## Stop law

Until Task 0 is accepted/frozen:

- unified Task 1 must not start;
- candidate outcomes remain closed;
- `reader_validation` remains closed;
- `reader_oracle` remains closed;
- old synthetic Task 3 and Task 4 remain `STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY`;
- old Tasks 5–12 have no independent continuation;
- no production GPU training is authorized.

## GPU execution model

The project already has a production-capable GPU executor: Macha on the GPU laptop. Do not create a dependency to obtain or build another execution environment.

Task 0 review does **not** require a new GPU run.

Later downstream qualification should use:

`frozen current TQB/runtime contract -> Macha GPU execution -> exact receipts -> separate reviewer/adjudicator -> possible qualification promotion`

Historical GPU mechanics and environment evidence are already custodied on PR #322. Re-detect current hardware/driver/CUDA/PyTorch/kernel/environment before future execution; historical software values are not current authority.

## Old synthetic merger state

- old Task 1: reusable/adaptable canonical primitives; does not complete unified Task 1.
- old Task 2: reusable/adaptable sealed-custody/RNG primitives; does not complete unified Task 2.
- old Tasks 3–4: stopped, requirements migrate only.
- old Tasks 5–12: no separate continuation.

Unified Task 2 remains the real TD manifest/access law: deterministic reader-fit cross-fitting, validation/oracle firewall, and actual producer-access receipts.

## Downstream reuse-first law

Do not restart teacher/student/EMA archaeology. Historical mechanics, tests, negative controls, V5 scientific-target/proposal work, target-identity audit, carryover audits, inactive weighted update, keyed RNG/dropout, checkpoint/resume and GPU execution history are already indexed on PR #322.

Current merged downstream gaps remain changed-input/current-authority gaps, especially exact TQB binding, teacher/student evidence rights, target-identity and masking shortcuts, final scientific weighting/proposal, current model/protected registry, EMA timescale, exact joined GPU runtime, downstream certification, runtime eligibility, training eligibility and explicit training authorization.

## Immediate next action

Give Macha the V2 Task 0 review packet, not V1.

If Macha finds no Critical/Important defect in controller-authored Task 0 custody and accepts the migration treatment:

1. freeze Task 0 acceptance at exact `c80d7398...`;
2. update #322/#323 custody pointers;
3. prospectively reconcile the downstream A–T amendment into PR #380;
4. begin unified Task 1 only, RED-first;
5. do not start human candidate execution or training.

If Macha finds a blocker, repair only the named Task 0 custody defect RED-first and keep unified Task 1 blocked.

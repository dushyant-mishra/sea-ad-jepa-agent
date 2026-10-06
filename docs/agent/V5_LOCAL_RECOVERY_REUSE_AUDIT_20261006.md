# V5 local-recovery reuse audit — 2026-10-06

## Scope

This note records the audit of the newly preserved local-only branches against the current downstream-runtime reconciliation task. It does **not** grant training authority and does **not** promote historical F1 scientific results.

Preserved refs audited here:

- `f1-real-production-executor-20260904` @ `f1b591613d0a593cc49e7765845aa36b12c1ae01`
- `claude/v5-phase4-preexecution-redteam-20260921` @ `d5ab33b337b50ac1b90bdac9ea239018cfea6cb7`
- custody branch `custody/local-only-jepa-recovery-20261006` @ `c86dac574bdf99f228d3e2040673855c701b10c4` is preservation evidence only and is not runtime authority.

## Finding 1 — the 8-commit F1 executor branch is a bounded executor/verification unit, not a trainer

The branch is exactly eight commits ahead of base `14e41030ffac65b3d58a45ae4159d30b8517e470` and adds a production executor, independent validator, contract, focused tests, and package receipts.

The terminal validator explicitly checks that the executor exposes no neural update surface: no `.backward(`, `optimizer.step(`, `ema.update(`, or `.train()` calls. Therefore this branch must **not** be used as evidence of healthy JEPA training mechanics.

Classification:

`VALID_HISTORICAL_EXECUTOR_MECHANICS__REUSE_DESIGN_PATTERNS_ONLY`

Reusable requirements recovered from this branch:

1. Production launch must fail closed before execution unless an externally bound authority object is present.
2. Authority bytes must be tied to an actual remote Git ref/commit, not merely a local JSON field.
3. Runtime authority must bind exact source/contract bytes and reject dirty implementation bytes.
4. Private-result destinations must be validated fail-closed.
5. Resume qualification must compare uninterrupted and interrupted/resumed execution by both semantic root and final serialized bytes.
6. An independent validator must reconstruct claims from raw artifacts/code rather than trust producer `PASS` fields.

These are candidate requirements for the current canonical V5 consumer/checkpoint path; the historical F1 executor itself is not to be transplanted wholesale.

## Finding 2 — Phase-IV red-team supplies a current integration rule

The preserved Phase-IV report identified a durable anti-cheat principle:

> A contract/authority object is not in force merely because it exists and tests in isolation; the actual executor must consume and enforce it.

The report demonstrated this concretely for `MaskingRngReplayAuthorityV3`: the authority module passed its own checks, but the bound executor still accepted a free `global_seed`, so panel-independence was not actually enforced.

It also recorded two reusable hardening rules:

- decision/execution rules must be cryptographically frozen prospectively, not only sample membership;
- caller-supplied identifiers/sets must be constrained against the authenticated split/authority they claim to represent.

Classification:

`VALID_HISTORICAL_REDTEAM_FINDING__CURRENT_INTEGRATION_REQUIREMENT`

## Finding 3 — what this changes in the active downstream plan

The active reconciliation target is the latest recovered **V5 teacher/student runtime** plus the newest mutually compatible q-safe, training-authority, authority-root, optimizer-guard, EMA, and checkpoint machinery.

The newly preserved branches change the acceptance criteria but do not eliminate the missing seam.

Before a canonical consumer can qualify, the audit must establish the executable call graph:

`41K reader -> q-safe views -> V5 encoder/predictor/teacher -> loss -> backward -> current training authority -> current optimizer guard -> optimizer -> EMA -> checkpoint -> reload/resume -> representation extraction`

For every authority object in that path, qualification requires positive proof that the consuming executor enforces it.

## Checkpoint/resume consequence

Save/load success is insufficient. The successor checkpoint qualification must include deterministic continuation:

- same next samples/masks;
- same loss sequence within prospectively frozen tolerance/exactness rule;
- same model parameters;
- same optimizer moments;
- same EMA state;
- same schedule cursor;
- same RNG/sampler state;
- same authority binding;
- same final semantic root and, where deterministic serialization permits, byte identity.

This requirement is inherited from the strongest useful part of the recovered F1 executor while remaining separate from its historical scientific purpose.

## Non-promotions

This audit does **not** promote:

- the historical PROD41K/T1 checkpoint;
- any F1 biological result;
- the recovered nuisance-authority workstream;
- the historical F1 executor as the current canonical runtime;
- any real training or EMA execution.

`TRAINING = OFF` remains unchanged.

## Next action

Continue the current-main reconciliation by locating the newest compatible V5 runtime/authority closure, then write RED tests against direct optimizer-step bypass, EMA chronology violations, stale/wrong authority, and non-deterministic resume before implementing any new consumer seam.

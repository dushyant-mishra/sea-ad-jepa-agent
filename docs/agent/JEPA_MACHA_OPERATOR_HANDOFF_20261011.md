# JEPA Macha operator handoff — 2026-10-11

Status: `CURRENT_MACHA_COORDINATION_HANDOFF__NO_VALUE_AUTHORITY`

This document exists so a new chat agent can immediately continue managing **Macha as the canonical-machine execution worker** without relying on prior chat context.

Hard project terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Roles

### Coordinator / new chat agent
The coordinator owns:
- scientific adjudication;
- authority boundaries;
- prospective freeze interpretation;
- deciding what Macha is allowed to execute next;
- independently auditing every returned execution record;
- keeping PR #247 (handoff) and PR #251 (audit/design) synchronized;
- never upgrading a Macha result beyond what its evidence supports.

### Macha
Macha is the canonical-machine execution worker.
Macha may:
- create clean worktrees pinned to exact approved heads;
- run the exact qualification/execution commands the coordinator supplies;
- collect environment, hashes, logs and receipts;
- open evidence-only draft PRs;
- report failures exactly.

Macha may **not infer new authority** from a PASS, mergeability, available data, or prior instructions.

If an instruction says STOP, Macha stops and returns evidence.

## 2. Current target-discovery state Macha must inherit

Accepted value-blind corrected-substrate execution:
- PR #259 head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- driver physical SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping physical SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Interpretation:
- G4/G5 technical/data-integrity PASS only;
- no corrected expression/count arrays opened;
- no G6/G7 run;
- no value-read authorization;
- no corrected biological replay.

Current engineering candidate:
- PR #267
- branch `fix/td-g7-counterpart-auth-immutable-attempt-20261011`
- exact head `16f05bd3845565bb2c24d70143d447d7ef2b8904`
- status `IMPLEMENTED__UNQUALIFIED__DO_NOT_EXECUTE_G6_G7`

Superseded heads that Macha must not qualify or execute:
- PR #258
- PR #263 head `a509c59238bcdc60b88fa265e7e4473760a41025`

Historical failed execution evidence that must never be rerun/relabelled:
- PR #245 — CRLF manifest failure before G4/G5;
- PR #252 — Sample-A label / geometry failure;
- PR #254 — independent identical repeat.

## 3. Macha's current assignment

**Qualify PR #267 only.**

Macha is not currently authorized to:
- create a value-read authorization;
- run G6;
- run G7;
- read corrected expression/count values through the target-discovery value path;
- run corrected TD56/TD57B/TD57C/TD59/TD60;
- select a target;
- train.

The exact qualification contract is:
`docs/agent/TD_PR267_CANONICAL_QUALIFICATION_20261011.md`

A ready-to-send instruction is preserved as:
`docs/agent/MACHA_NEXT_INSTRUCTION_PR267_20261011.md`

## 4. What the coordinator must demand back from Macha

A valid qualification return must contain all of the following:

1. exact `git rev-parse HEAD` = `16f05bd3845565bb2c24d70143d447d7ef2b8904`;
2. clean `git status --short` before qualification;
3. Python/numpy/pandas/scipy/h5py/pytest versions;
4. full focused pytest log for:
   - `tests/v5/test_td_relational_value_read_v2_common.py`
   - `tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py`
   - `tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py`
   - `tests/v5/test_td_g7_counterpart_attempt_custody.py`;
5. exact physical PR #259 receipt SHA verification;
6. separate real-receipt compatibility test result with exactly `1 passed / 0 skipped / 0 failed`;
7. base-to-head changed-file comparison showing only:
   - `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
   - `tests/v5/test_td_g7_counterpart_attempt_custody.py`;
8. confirmation no production code was edited in the qualification worktree;
9. confirmation no runtime authorization object was created;
10. confirmation G6 was not run;
11. confirmation G7 was not run;
12. confirmation no corrected expression/count array was opened;
13. evidence-only draft qualification PR/head containing all logs/receipts.

Any missing item means the coordinator does **not** accept qualification yet.

## 5. Failure handling

If any required test or receipt check fails, Macha must:
- STOP;
- preserve the exact failed output;
- not edit production code in the qualification worktree;
- not weaken any gate;
- not silently rerun after patching;
- open/preserve an evidence-only failure record;
- return the exact failure to the coordinator.

The coordinator then diagnoses/repairs prospectively on a new engineering branch.

## 6. PASS handling

If Macha returns a genuine qualification PASS, the coordinator must independently audit it.

A PR #267 qualification PASS means only:
> the hardened future target-discovery value-reading machinery satisfies its engineering/custody qualification and correctly binds the accepted PR #259 V3 evidence.

It does **not** authorize value reading.

After accepting qualification, the next state is:
`QUALIFIED__STOP_FOR_OWNER_DECISION__NO_VALUE_AUTHORITY`

The coordinator must not instruct Macha to run G6/G7 until the owner explicitly authorizes:
`AUTHORIZE_G6_G7_INTEGRITY_ONLY`

That decision must be preserved as an immutable owner-decision record and cryptographically bound into the future runtime authorization.

## 7. If/when owner authorizes G6/G7 later

Only after explicit owner authorization, the coordinator should issue a **new instruction** to Macha that:
- binds exact PR #259 physical receipt SHAs;
- binds exact qualified PR #267 implementation identity;
- binds the immutable owner-decision record;
- keeps biological replay / target selection / TD60 / training false;
- executes G6 first in a fresh immutable namespace;
- requires exact G6 PASS;
- only then permits G7;
- treats mismatch or NOT_ESTIMABLE as non-success;
- preserves all receipts and STOPs for coordinator/owner review.

Do not pre-send that execution instruction now.

## 8. Corrected biological replay later

Even a future G6/G7 PASS is only value integrity/corroboration.

A **second explicit owner authorization** is required before Macha may execute corrected TD56/TD57B/TD57C/TD59 biological replay.

The replay is already prospectively frozen on PR #251.

Macha must not improvise:
- panels;
- donor splits;
- nulls;
- thresholds;
- locality fractions;
- address universe;
- stage order/interpretation.

TD57C's historical FAIL remains immutable.
TD59's original executor remains unrecovered; only the separately validated replay-closure successor is admissible.

## 9. Macha's parallel Bayesian work is a separate lane

Macha has also worked on Bayesian/sampler qualification in a parallel lane.

That lane must remain authority-separated from target discovery.

Known target-discovery-relevant rule:
- PR #249 terminated with `SAMPLER_NOT_ESTIMABLE` and `STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`;
- do not revive/tune that terminated formulation to force a historical answer;
- any later Bayesian repair/qualification must be audited on its own merits;
- no Bayesian PASS, sampler recovery or posterior result grants target-discovery value-read, biological-replay, target-selection or training authority;
- do not mix Bayesian results into PR #259/PR #267 gate interpretation.

If Macha returns Bayesian work together with target-discovery work, the coordinator must adjudicate the two sections independently.

## 10. Coordinator response pattern after each Macha return

For every Macha report:

1. verify exact branch/head before reading conclusions;
2. separate target-discovery evidence from any parallel Bayesian evidence;
3. inspect committed receipts/logs rather than relying on prose summary;
4. verify all exact hashes and schemas relevant to that gate;
5. verify no forbidden downstream action occurred;
6. state the narrowest valid interpretation;
7. update PR #247 and PR #251;
8. issue Macha's next instruction only after that audit.

Never tell Macha "continue" generically. Give an exact branch/head, allowed operations, forbidden operations, required evidence and STOP condition.

## 11. Current instruction pointer

Current Macha instruction:
`docs/agent/MACHA_NEXT_INSTRUCTION_PR267_20261011.md`

Current next gate:
**canonical qualification of exact PR #267 head, then STOP.**

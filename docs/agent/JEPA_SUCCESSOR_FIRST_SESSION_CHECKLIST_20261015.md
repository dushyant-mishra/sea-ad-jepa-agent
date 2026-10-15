# JEPA successor first-session checklist — 2026-10-15

Purpose: let a new agent take over this lane without redoing historical archaeology and without accidentally crossing a scientific or custody gate.

## 0. Do not start by auditing the whole project

The durable historical audit already exists. Read the handoff and custody surfaces first and treat settled work as settled unless exact bytes, authority context or a concrete defect changed.

Read in this order:

1. this file;
2. `docs/agent/JEPA_LANE_TAKEOVER_HANDOFF_20261015.md` on PR #323;
3. PR #322 `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md`;
4. PR #322 `results/target_discovery/unified_qualification_v1/JEPA_LANE_TAKEOVER_STATE_V1_20261015.json`;
5. PR #322 `results/target_discovery/unified_qualification_v1/INDEPENDENT_REVIEW_CUSTODY_INDEX_20261015.json`;
6. PR #322 `docs/agent/TASK3_REJECTED_LINEAGE_CUSTODY_HAZARDS_20261015.md`;
7. Task 3 independent review at exact review head `869ca777a498181c519ccfc04b8bf5db0f2888c7`;
8. only for future Task 4 planning, PR #322 `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`.

## 1. Establish the authority snapshot before editing anything

Frozen accepted authority:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`

Rejected/open:

- Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`, PR #392
- Macha review: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- verdict: `REJECT_UNIFIED_TASK3`
- gate: `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Binding global state:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

If live GitHub differs from this snapshot, do not silently reconcile it. Record the changed head/diff in PR #322 and classify whether it is expected history, an unauthorized mutation or a prospectively authorized repair.

## 2. First mutation: neutralize T3-B6

Before pushing any new Task 3 RED or repair code:

1. preserve rejected `851544e8...` unchanged;
2. cut/use a focused repair branch;
3. remove or neutralize all Task 3 self-mutating GitHub workflows with `contents: write` + auto-commit/push behavior;
4. convert any needed workflow to read-only verification or manual-only tooling;
5. add a regression/policy check that qualification workflows cannot auto-rewrite RED tests or production registry code;
6. enumerate all Task 3 commits authored/committed by `github-actions[bot]` and map each exact SHA to its workflow and patch script in PR #322 custody.

Known bot commit already identified:
`9052e3ce32f7f8b84d7445e3ec81826c79b6960d` (`task3 GREEN6: migrate actor-bound registry fixtures`).

Do not assume it is the only bot-authored Task 3 commit.

## 3. Preserve Macha's rejection as RED

Turn the exact Macha attacks into tests before production changes.

Required blockers:

- T3-B1: `UNIT:<id>` / `NO_TRAINING_AUTHORITY` cannot promote into training stages; every promotion uses frozen Task 1 authority validation.
- T3-B2: closed per-stage evidence requirements; unavailable Task 4/5 evidence means promotion refuses rather than fabricating placeholders.
- T3-B3: actors come from a frozen identity-bound registry with strict ASCII canonical IDs and permitted roles; reject unknown, lookalike and self-minted actors.
- T3-B4: no caller-controlled positive verification cache; cache is internal/context-bound and cannot survive resolver/dependency changes as authority.
- T3-B5: append-only replay from fixed registry genesis + externally anchored current head; deleted revocation or fabricated history cannot restore readiness.
- T3-B6: write-capable auto-repair workflows cannot mutate qualification RED/code history.

Also preserve actor alias attacks exactly: whitespace variants, case variant and fullwidth-colon lookalike.

Expected first repair run is RED. If it is green before production repair, the tests do not reproduce Macha's findings or the wrong code is under test.

## 4. Repair minimally; do not rebuild known-good Task 3 mechanics

Macha already confirmed these mechanics work and should remain intact unless a blocker forces a local change:

- one-stage promotions;
- refusal of non-ACTIVE units;
- re-identification resets stage/lineage;
- successor identity on supersession;
- cycle detection;
- stale/revoked/insufficient prerequisites block;
- missing or boolean dependency resolver blocks;
- unresolved prerequisites remain visible;
- exact Task 2 execution-row binding;
- population authority consistency;
- `FIXTURE_UNBOUND` blocked at real-reference readiness;
- pooled-only claim limit under the accepted five-fold design.

Remove dead `asserted_ready` and `prerequisite_evidence_verifier` arguments so they are not mistaken for authority-bearing interfaces.

## 5. Task 2 residuals remain blockers, not documentation

R1: real process isolation before `HUMAN_EXECUTABLE`.
R2: substantive contract validation with authorized validators.
R3: fixture authority cannot become current-TD authority.
R4: persistent ledger + signing-key custody before cross-process receipt use.
R5: pooled donor-level five-fold claims only; no per-fold source-stratified claims.
R6: internal/context-bound recursive verification caching.

Hand-written yes/no dictionaries do not satisfy R1/R4.

## 6. Exact verification required before Macha

On one immutable repair head, require:

1. focused Task 3 B1-B6 suite;
2. all Task 3 tests;
3. full `tests/v5/td_unified` regression;
4. frozen Task 2 workflow/regression;
5. frozen Task 1 workflow/regression;
6. inherited unified synthetic integration;
7. diff audit proving frozen Task 0-2 production files are untouched unless explicitly authorized;
8. hostile owner self-audit after GREEN.

Record exact run/job IDs and the exact candidate SHA in PR #322 and #323.

Then ask Macha for a focused recheck of B1-B6 only. Do not request a full historical re-audit.

## 7. Task 4 remains blocked

The Task 4 design is already settled enough for launch after Task 3 acceptance. Do not spend time redesigning it unless Task 3 repairs change a dependency interface.

Do NOT before Task 3 freeze:

- write Task 4 production custody logic;
- generate final challenge secrets, roots, nonces or worlds;
- create an execution RED branch that could be mistaken for prospective Task 4 authority;
- open protected biological values.

After Task 3 independent acceptance:

1. freeze accepted Task 3 exact head in PR #322/#323;
2. derive/review the implementation plan from the controlling Task 4 spec;
3. create Task 4 RED-only branch from frozen Task 3;
4. preserve all 13 historical custody attacks plus the expanded 36-attack matrix;
5. proceed iteratively and obtain independent Macha review before Task 5.

## 8. Historical work not to redo

Do not restart audits for repaired TD units G8/G6/G9-S1-S2/R1/G2/G7/R4-C6-C4/C4→C6/G12/system battery, PR #349 population census/support registry, old canonical/custody substrate at `ff597faf...`, Task 0-2 rejection→repair→acceptance histories, or previously audited downstream optimizer/EMA/checkpoint/RNG/packing/support mechanics unless changed input/interface or a concrete defect demands requalification.

Use the no-repeat classes:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

## 9. Data/file custody

Large/private project files are listed by exact hash/size/path in the PR #322 local artifact custody manifest. Do not copy them into Git merely for convenience and do not infer scientific authority from their presence. Match bytes to an authenticated provenance/receipt before use.

Protected validation/oracle biological values remain closed.

## 10. Every working session must leave a handoff trail

Before ending a substantive session:

- update PR #322 with exact new audit/custody facts;
- update PR #323 with compact current state/next action;
- preserve RED heads, repair heads, exact CI evidence and independent review heads;
- classify new work under no-repeat framework;
- record unresolved questions rather than silently choosing favorable assumptions;
- carry this iterative/no-repeat requirement into the next agent handoff.

The successor's immediate mission is not 'finish JEPA'. It is: **repair Task 3 B1-B6 without damaging the frozen Task 0-2 authority or reopening settled historical audits.**

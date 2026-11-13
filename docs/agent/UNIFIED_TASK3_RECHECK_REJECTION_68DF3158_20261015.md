# Unified Task 3 focused re-check rejection — 2026-10-15

Controlling independent re-check verdict: `REJECT_UNIFIED_TASK3`.

Reviewed exact code candidate:
`68df31584d17f91da2635cdf8e03bbe93695f9d1`

Independent review branch/head:
`review/macha-task0-independent-review-20261014` at `6825f53d`.

PR #392 head at review was `0a25f72cdf5ab408c8ed08878636bb3ba3467151`; commits above the reviewed code candidate were documentation-ledger only and do not change the reviewed code bytes.

## Closed blockers

- T3-B1 authority scope/stage bypass: CLOSED.
- T3-B4 verification cache trust: CLOSED.
- T3-B6 self-mutating qualification CI: CLOSED.

## Still blocking

### N1 — CRITICAL — frozen Task 2 binding absent
Task 3 does not apply frozen Task 2 `manifest_v1` / population validation. A forged 104-donor access policy and a minimal fake manifest can be accepted as `AUTHENTICATED_READER_SPLIT` and promoted to `REAL_REFERENCE_READY` even though frozen Task 2 rejects them.

Required repair: call frozen Task 2 validators, including `validate_manifest(raw_resolver=...)`, at relevant RRR/HUMAN_EXECUTABLE gates and fail closed without a real raw resolver.

### N2 — CRITICAL — qualification can be declared at genesis
`KNOWN_TRUTH_QUALIFIED` cannot be reached by promotion, but can still be declared when registry/custody state is first constructed. That declared stage can then flow onward and bypass the sealed-challenge evidence that Task 4 is meant to provide.

Required repair: cap admissible custody genesis below `KNOWN_TRUTH_QUALIFIED` (review recommends `SAME_CODE_PATH`) and require sealed-challenge evidence before accepting that stage.

### B3-V — IMPORTANT — validator identity not actor-bound
Content validators are checked by role/object shape but not resolved through the closed actor registry. Producer-as-validator can pass.

### B3-E — IMPORTANT — evidence issuer not actor-bound
Human-execution/process-isolation/ledger evidence can be supplied without a registered issuer. Self-authored evidence remains possible.

### B3-R — IMPORTANT — actor registry itself is unanchored
A producer can construct a new actor registry containing self-minted controller/reviewer identities and then qualify under it.

### B5-F — IMPORTANT — revocation custody can be reset
A fresh custody object can forget an earlier revocation and re-qualify the same unit identity. Same-custody deletion/fabrication attacks are fixed, but cross-custody reset remains open.

## Task 2 residual state after re-check

- R1 OPEN
- R2 OPEN
- R3 OPEN via N1
- R4 OPEN
- R5 PASS
- R6 CLOSED

## Carry-forward hardening items

These remain non-closed even after the focused repair:

- actor identity hashes are public identifiers, not credentials; human execution ultimately needs signed or harness-attested approvals;
- custody object state remains editable in-process;
- `registry_v1_legacy.promote_unit` remains a public custody-free route and must not become an alternate authority path;
- `RegistryUnit` construction should enforce frozen Task 1 authority law;
- `.github/workflows/unified-task3-registry.yml` should declare `permissions: contents: read` explicitly.

## Verification evidence

Hostile focused re-check: 38 checks total; 31 expected, 7 bad, 4 notes.

Local unified suite: 177 passed through a wrapper that forces the repository `tests` package ahead of an unrelated installed PyMC `tests` package; this is local evidence, not CI evidence, and the wrapper changed no repository file.

## Next repair scope

Do not reopen already-closed B1/B4/B6. First add the independent probes as RED tests, then repair only:

`N1, N2, B3-V, B3-E, B3-R, B5-F`

After repair, a focused independent re-check of exactly those six items is sufficient unless changed bytes expose an equivalent new authority/custody defect.

## Gate

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This record supersedes any prior statement that candidate `68df3158...` was internally GREEN in a way sufficient for freezing. It was only implementation-green against the then-current tests; the independent re-check found unresolved authority defects.
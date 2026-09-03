# CURRENT SUPERSESSION MAP — JEPA v4

Date: 2026-09-02

Purpose: prevent stale historical PASS/STOP artifacts from being mistaken for the live authority. Historical bytes remain preserved for provenance and reproducibility.

| Historical/current item | Status now | Superseded/controlled by |
|---|---|---|
| Exact hidden-gene reconstruction objective | CLOSED / not current objective | Current biological-program/state objective in `CURRENT_AUTHORITY_INDEX.md` |
| Signed-V2 target branch | CLOSED | Contextual Target V1 line |
| Operator-subtraction branch | CLOSED | Current Contextual Target V1 semantics |
| Arithmetic block-mean target | CLOSED | Current query-addressed contextual target semantics |
| Generic `D_shared` rescue / later-D re-entry | CLOSED at `TEACHER_BIOLOGY_LIMIT`, `D_shared=null` | No re-entry without explicit future authority |
| Historical F1 decision-v1 | FROZEN HISTORICAL ARITHMETIC; not sole current decision authority | decision-v4 plus accepted additive repair layers; currently evidence-slope repair gate |
| Historical F1 decision-v4 | FROZEN CURRENT-BASE DECISION; contains open evidence-slope defect | Future superseding evidence-slope-repaired decision layer after external review |
| 15A3 HC3 frontier | INVALID / superseded | Complete 15A4 frontier |
| 15A4 complete HC3 frontier | ACCEPTED / CLOSED at scope | Selected triple `(5,0,4)` and 15B/15C descendants |
| 15B selection/provenance repair | ACCEPTED / CLOSED at scope | Current selected design authority |
| Historical 15C local integration PASS-awaiting-review | NOT an external PASS by itself | HC3 numerical-robustness repair + external review |
| `STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED` | RESOLVED | `PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW` on repair commit `5e8127d360d1effd0867a73c2bb007ddffb2c901` |
| Normal-equations conclusion-bearing HC3 route in historical v1 | HISTORICAL ONLY for HC3 conclusion | Accepted additive reduced-QR HC3 repair; independent SVD validation |
| Historical 15C independent normal-equations validator | HISTORICAL / insufficient independence | Accepted thin-SVD independent validator in HC3 repair |
| Old live gate in `F1_HC3_15C_EXTERNAL_REVIEW_20260902.md` | HISTORICAL STOP / resolved | New HC3 repair external review and `NEXT_ALLOWED_ACTION.json` |
| Current evidence trend using v1 float-centered `evidence_slopes()` | OPEN DEFECT / blocks real F1 | Next superseding evidence-slope numerical repair |
| Reader/forward/executor preflight | FUTURE / not yet authorized | Only after evidence-slope repair passes external review |
| Real F1 sweep | FORBIDDEN CURRENTLY | Requires reader/forward/executor preflight and later explicit authority |
| Training / finetuning / EMA | FORBIDDEN CURRENTLY | Requires later explicit authority after F1 feasibility gates |

## Current live chain

`F0 PASS`
→ frozen F1 design
→ `15A4 PASS`
→ `15B PASS`
→ historical `15C local PASS-awaiting-review`
→ HC3 numerical independence STOP
→ HC3 numerical robustness repair
→ **HC3 external PASS**
→ **current: evidence-trend numerical repair STOP**
→ future evidence-trend external review
→ future reader/forward/executor preflight
→ only then possible real F1 authorization.

## Rule for agents

When two artifacts disagree, prefer in order:

1. `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`
2. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
3. controlling current external review named there
4. `docs/agent/memory-os/ACTIVE_STATE.md`
5. this supersession map
6. selective historical evidence.

Never use Git commit date alone to infer original historical chronology for recovered/backfilled artifacts.

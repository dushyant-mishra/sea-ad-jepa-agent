# JEPA continuity contract — historical chronology **and** implementation progress (2026-11-02)

**Status:** `BINDING_SUCCESSOR_WORKFLOW__NON_AUTHORIZING`. This supplements the original [`JEPA_ITERATIVE_OWNER_AUDIT_AND_CUSTODY_PROTOCOL_V1_20261015.md`](JEPA_ITERATIVE_OWNER_AUDIT_AND_CUSTODY_PROTOCOL_V1_20261015.md), which **already required** durable evidence updates after every meaningful implementation, audit, acceptance and rejection. This update fixes its historical PR #323 successor pointer: **PR #322 is the audit/custody branch; PR #460 is the active operational handoff. PR #323 is history only.** Do not start a parallel chronology.

**Binding status at creation:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`. Nothing in this document authorizes access, biological target selection, protected outcomes, Stage4 or training.

## Mandatory on every new-agent takeover

1. Verify **live exact heads** of [audit PR #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) and [handoff PR #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460). Historical snapshot SHA strings describe earlier heads and are not automatically current.
2. Read the *latest* top-of-file supersession in `docs/agent/JEPA_NEW_AGENT_LIVE_POINTER_20261029.md` on #460, then the current audit corrections on #322: `JEPA_20261102_QUALIFICATION_HANDOFF_RECONCILIATION.md`, `JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md` and the source-index JSON companion. Use the original architecture ledger and frozen source files for deeper history; **do not recrawl/re-execute settled work**.
3. Read the existing `JEPA_ITERATIVE_OWNER_AUDIT_AND_CUSTODY_PROTOCOL_V1_20261015.md`, accepted unified Task 0–3 identities, current implementation/hostile-review PRs, and source/role restrictions. Do not treat PR #460 as a fork of executable audit or model code.
4. Classify every proposed task by: `ALREADY_AUDITED`, `CLOSED_REJECTED`, `SUPERSEDED`, `OPEN_NEW_WORK`, or `CHANGED_SOURCE_REQUIRES_REQUALIFICATION`. Before calling work “missing,” search both the June–August Graph-JEPA scientific chronology and September–November implementation history.
5. Verify exact input data and reviewer rights. Real/scientific execution is separately authorized; user/project handoff scope is not an authorization token.

## Mandatory progress publication — including **implementation**, not only history

**Do not end a meaningful implementation, experiment, bug repair, reviewer adjudication, source audit or decision cycle without updating these durable surfaces in order:**

A. **Owner implementation branch/PR:** Keep production code, RED-before-GREEN tests, original hostile probes, exact producer commit, input/output hashes, scope labels, review verdicts and workflow receipts on the actual implementation PR. Preserve unsuccessful attempts; do not overwrite frozen heads. The project may work on several PRs in parallel, but no PR's accepted state may be inherited from another without exact qualifying evidence.

B. **Canonical audit PR #322:** Append a dated, uniquely named science/engineering delta under `docs/agent/` and (where meaningful) a machine-readable receipt under `results/target_discovery/unified_qualification_v1/`. Add an event to `JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1.json`. Minimum event fields:
   - `date_utc`, `workstream`, `implementation_pr`, `implementation_head` (or `null` if no implementation), `source_inputs` (paths, hashes and source roles), `change_type` (scientific experiment / implementation / hostile review / repair / acceptance / rejection / source custody / chronology correction), `what_already_existed`, `new_work_or_result`, `negative_or_counterfactual_evidence`, `test_review_scope`, `independent_review`, `authority_before`, `authority_after`, `open_specific_deltas`, `historical_supersession`, `evidence_links`.
   - For a source-linked **actual run**, specify exact cohort/donor/assay context, executed versus fixture-only, outcome visibility, experiment reuse rights and scientific scope. For a repair, preserve original RED and distinguish author-green from independent accept. Never invent reviewer approval or “scientific PASS” from CI.
   - **Never edit hash-pinned October 28 frozen files** or their freeze manifests to add history. If a file is pinned by any validator, use an additive delta and link it from a nonfrozen current pointer. A failing historical freeze must be restored, **not repinned to new bytes**.

C. **Audit verification:** Re-fetch the audit head, verify all added files/links and run corresponding validators. Inspect PR-scoped GitHub Actions after the final commit. Record observed states **success/failure/pending** with exact head and workflow run IDs; do not label pending green. New scientific authority requires explicit independent review and the appropriate issuer, not merely a successful workflow.

D. **Active handoff PR #460:** Update the **top** of `docs/agent/JEPA_NEW_AGENT_LIVE_POINTER_20261029.md` with a dated delta, explicitly naming the *verified audit head*, the live implementation/reviewer PRs, what completed, inherited past work, exact unresolved defect(s), owner/review boundary, and next lawful implementation action. Preserve older first-session instructions lower in the file as **historical/superseded**, not as a concurrent queue. This handoff branch is a **pointer**, not duplicated implementation code.

E. **Handoff verification:** Verify exact #460 head plus pointer contents and its own CI. If the audit head later moves, the pointer is stale **until it is synchronized**. If a later implementation changes source bytes/reviewer verdict while an agent works, redo the narrow drift check before claiming completion. Never report a future CI result as already obtained.

**Completion invariant for every turn:** new implementation result or consequential new scientific finding -> current exact implementation evidence -> updated #322 progress/historical index -> verified audit checks -> updated #460 current pointer -> verified handoff checks. Where a task cannot finish all writes, explicitly identify the last committed SHA and the unsynchronized surface. A successful future handoff cannot skip this disclosure.

## Historical chronology to carry forward unchanged unless new evidence contradicts it

The complete historical scientific record begins with the early Graph-JEPA V1/V2/V3 program: donor-heldout disease-state scores and graph-specificity controls, Stage27C internal lock, small Stage35C graph result, Stage39D and Stage41C promising but non-locking scores, Stage36–49 candidate/methods/manuscript work, Stage53–71 rare/high-tail and regional evidence (Stage69 positive, Stage70 lock refused), Stage72–75F TF-region-gene hypotheses, Stage76–79 *executed* frozen-GeneJEPA perturbation/latent/graph-control path, then Stage81A0→Stage81A2R Foundation identity. September–November developments include physical FULL104, R5/V44/C2, cross-modal/source qualification, V72–V80 synthetic, unified Tasks0–8, JEPA post-TD, source rights and V2C security. The source-pinned chronology is in `JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md`; the existing original ledger and no-repeat index remain independently authoritative at their frozen scope.

**Name collisions:** old `Stage79 F13` is not synthetic `V79`; unified sealed-custody Task4 is not production-synthetic V3.1.1 biological-generator Task4; dataset scientific counts are not adapter counts; measured zero is not unmeasured; positive internal prediction is not a production biological winner.

## Moving from historical audit to forward implementation

After this chronology repair, spend no further time on broad archaeology without a real evidence trigger. Work on the **already specified, latest exact-head implementation queue** (e.g., independent V2C #514 security review/source isolation, constrained source issuer, PS Tasks1–3 dependency scope/T2-D, cumulative Unified Task4, V3.1.1 biological generator under its authorized STOP order) **only after rechecking current statuses, assignments, and existing accepted subparts**. Each completed incremental deliverable must publish its progress event and handoff pointer **before starting the next substantial change**. A reviewer-author conflict cannot be cured by self-review.

**Source restrictions:** NPH52 excluded/protected expression remains off-limits; seven reader-fit derivatives have an older physical firewall; source row/feature alias, donor/specimen, D1 depth, HVS deposited UMI and SEA-AD sample_id constraints remain source-specific. Historical pathology-linked V3 data are research evidence with exposure constraints, never pristine untouched prospective target truth.

**Terminal:** `CONTINUOUS_CHRONOLOGY_AND_IMPLEMENTATION_CUSTODY_ACTIVE__NO_SCIENTIFIC_PROMOTION`.

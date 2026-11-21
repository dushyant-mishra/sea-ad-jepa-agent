# Unified lane chronology and the planned downstream work: what to do next — 2026-11-04 (Macha, for Sol)

**Why this exists.** The owner asked for the unified lane to be traced end to end so Sol can find the next step. This is the lane that merged the synthetic and target-discovery work on 2026-10-14. Everything below is cited to PRs, heads and verdict comments re-read on 2026-11-04.

**Main conclusion.** The lane is **mid-way through its own plan.** Tasks 0–3 are accepted, and Tasks 4 and 5 are accepted only in pieces. Tasks 6–12 have not started, apart from fixture stubs. The recent side work is useful but sits around this spine, not on it: TD60 (#540, now closed), history reconstruction, synthetic diagnostics. **The next actions are the planned Tasks, in their planned order.**

## 1. What the unified lane is (controlling sources)
- **Architecture:** `docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1.md` plus the v1-1 hostile-review amendment (acceptance comment 6174861625), on the accepted #379 architecture (`3064ca54`).
- **Plan:** PR **#380** (`5b6bf07e`): `docs/superpowers/plans/2026-10-14-unified-td-qualification-downstream-custody-v1-implementation.md` plus the Task-0 migration amendment.
- **Goal:** one authenticated **producer → artifact → executor** chain, shared by known-truth (synthetic) certification and sealed human TD execution. It emits an immutable Target Qualification Bundle and certifies exact downstream consumption.
- **Dependency order:** `TD_EXECUTION_MANIFEST_V1 → TD_QUALIFICATION_REGISTRY_V1 → KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1 → TARGET_QUALIFICATION_BUNDLE_V1 → DOWNSTREAM_CERTIFICATION_CONTRACT_V1`.
- **Method:** a fresh independent review after every task, and a final whole-branch hostile audit.
- **Owner stops:**
  - **U1** before a sealed final known-truth exposure;
  - **U2** before `KNOWN_TRUTH_QUALIFIED`;
  - **U3** before `REAL_REFERENCE_READY`;
  - **U4** before any human candidate execution;
  - **U5** before `TRAINING_ELIGIBLE`. `TRAINING_AUTHORIZED` is a separate owner decision.

## 2. Chronology by task
| Task (plan) | PRs, in order | Current state |
|---|---|---|
| **0** Pre-merger migration and custody audit | #381 → Macha REJECT B1–B5 (#383) → repair #384 | **Accepted and frozen** at `e37a22b8` (2026-10-15) |
| **1** Canonical identity and authority model (A1, A9) | #385 rejected `86fa996f` → #386 | **Accepted** at `799d2e23` (10-15). Later #461 RED (numpy dtype, metaclass, int domain) → #463 → #466 RED → **#467 `ACCEPT_INCREMENTAL_WITH_LIMITATIONS`** (10-27, `180b550e`) |
| **2** `TD_EXECUTION_MANIFEST_V1` and population access law (A4) | #387 RED → #388 rejected `2c391137` → #389 RED → #390 | **Accepted** at `c7dfff1c` (10-15). Carry-forwards R1–R6; R1 says in-process producers can reach the harness key |
| **3** `TD_QUALIFICATION_REGISTRY_V1`, revocation, independence, prerequisite graphs (A2, A5, A6) | #391/#392 → rejections, #393–#399 → #401 | **Accepted and frozen** at `117dd51d` (10-16). Binding carry-forwards C1–C9 |
| **4** Sealed qualification-challenge custody (A3) | Design #402 (C1–C9) → #403–#427 (many attack/repair rounds; Macha rejections #421, #427) → Macha-authored #428 (T4-B1R) → #429 RED → `c8331e37` → cumulative finding #435 → #436/#445 (Macha `REJECT_INCREMENTAL_MECHANICS`) → #452 RED → #454 X2–X7 → #459 X1 → #462 RED → **#465 X1-S1/S2** (GPT `ACCEPT_INCREMENTAL_WITH_LIMITATIONS`, `3b86b946`) | **Accepted only in increments. No cumulative Task 4 acceptance.** Task 4 V1 `replay` always reports `authoritative=False` |
| **5** `KNOWN_TRUTH_CASEBUNDLE_V1` / `TRUTH_BUNDLE_V1`, mode equivalence (A7) | #440 (fixture code, 26 tests) → #444 integration with the post-TD harness (Macha REJECT as claimed) → #450 RED → **#451** Macha bridge repair (GPT `ACCEPT_INCREMENTAL_TASK5_FIXTURE_BRIDGE_MECHANICS_WITH_LIMITATIONS`, 6426554595) | **Fixture-only.** `casebundle_v1.py` (`23bbdcfc`) checks digest format only; `externally_authenticated=False`. Full A7 is not done. |
| **6** Register current repaired TD units at demonstrated authority | #447 `gate_registration_v1` stubs (`729a0b4c`) | **Not started.** All units `NOT_REGISTERED`; producer, executor, metric and reference identities unavailable |
| **7** `TARGET_QUALIFICATION_BUNDLE_V1` | #447 `target_bundle_v1` stubs | **Not started**, beyond a fixture TARGET=NONE path |
| **8** `DOWNSTREAM_CERTIFICATION_CONTRACT_V1` (A8) | #447 `downstream_contract_v1` stubs (53 fixture tests) | **Not started**, beyond fixture abstention |
| **9** Reusable known-truth challenge families A–I | — | **Not started as a task.** Raw material exists: #318→#321 relational families (test-of-test independently audited, #336 `PASS_PHASE2_EXECUTION_AND_CUSTODY`); #328 world; V80 benchmark; PS V3.1.1 |
| **10** Full TD known-truth rehearsal through registered production units | #469 ran PR328 → Task 5 fixture → planted labels (no authority) | **Not started.** E41: no producer → registered gate → hidden controller truth → separately learned recovery demonstrated |
| **11** Finalization, generated receipts, unified CI | — | Not started |
| **12** Whole-pipeline hostile review before any human execution plan | — | Not started |

### Streams that feed the unified lane
- **Post-TD harness (#332/#351):** the training-side contract that consumes Task 7.
  - Reviewed through #517 (GPT RED) → #525 → Macha #527/#530/#532.
  - **#525 at `b493efc3` awaits Macha's fresh-head review.**
- **Observation/student boundary:**
  - **#474/#479/#502–#511:** q-excluded depth, private physical library versus D1, V2B, D1-only student source;
  - **#514/#515 → main #522 (`e4925cff`), #523 (`971ec6a1`), #524 (`28cbe3b2`):** D1/V2C fixture law accepted (scoped);
  - **#538 (`b901d3fe`, CI 3/3):** conservative alias-query refusal at D1/V2C. Review owed.
- **Real evidence rights, G7 E3:** #433 → #446 REJECT → #470 REPAIR_REQUIRED → #476/#489/#497/#500. Increments accepted with limits; **physical-trust REDs R1/R1D/R2 still open.**
- **Source qualification:** #509 → #513 → #528 (`1a4fda75`, R01/R02 accepted). Public sources resolved (#528 erratum). Alias restrictions adopted 10-30 (`457b689b`); first enforcement is #538.
- **Production synthetic V3.1.1 (#344/#356):** PS Tasks 1–3 accepted in increments only (#477, #486, #498, #499, #501). The latest Task 3 line (#437) is `REPAIR_REQUIRED`. **PS Task 4 (biology) not started.**
- **Synthetic diagnostics:**
  - #469 (fixture integration);
  - #526 → #531 (support-semantics correction; **owner accepted the five-rule amendment as the future contract**);
  - #534 (**CI RED**, V80 identity mismatch; **V80 originals expire on Nov 13**);
  - #536 (C3 measured producer; awaiting review);
  - #537 (GPU run; awaiting the no-repeat check and owner authorization).

## 3. Planned downstream route
From the #447 mapping (2026-10-27), updated with later owner rulings.

The 2026-10-27 mapping (comment on #447) listed **seven properties** the downstream must enforce for real:
1. authenticated evidence, not PASS strings;
2. a first-class TARGET=NONE;
3. support and estimability scope;
4. exact producer and executor identities;
5. no teacher-to-student leakage;
6. a real C4→C6 dependency;
7. training refused without a qualified target and a separate authorization.

It also gave a dependency order. Each step is listed with its update:

1. **Task 4 cumulative acceptance.** Assemble one cumulative candidate from the accepted increments (#428/`c8331e37`, #454, #459/#465), rebased on the Task 3 freeze, and get a non-author cumulative review.
   - **Update (owner, 11-03/11-04):** a hardware signing key is optional hardening. The trust requirement is now **consumer re-verification**: replay, revocation check and registered-unit re-derivation. Property 1 no longer waits for an external signer.
2. **#351/#525 review.** Macha's review of `b493efc3`.
3. **Full Task 5 (A7)** on accepted Task 4. Unify the two TARGET=NONE types (the #451 bridge dict and the #447 digest-bound bundle).
   - **Update (owner ruling 2):** no new Level-4 read into a real CaseBundle until a frozen experiment needs one. The real-path successor stays specified.
4. **Task 6 unit registration** (property 4): G8, G7 E3, G2, R4 and the relational units, at demonstrated authority only.
5. **Task 7 bundles** (properties 1, 2, 3, 6): `verify_selected_target_bundle` and `verify_target_none`; distinct C6 and C4 bundles; a support scope per block.
6. **Task 8 certification plus `derive_student_input_set`** (property 5). It must refuse WITHHELD, STRUCTURAL and COLLISION scalars and teacher outputs as student inputs, and use exact `int`. It folds in the D1 law (`edee1b8a`), #538 alias refusal and the **L04 decision** (whether a SHARED teacher may see the query within a query presentation).
7. **Trainer entry check** (property 7): a verified Task 7 bundle, a Task 8 `DOWNSTREAM_CERTIFIED` receipt, **and** a separate owner training authorization.

**Then the plan's remaining tasks:**
- **Task 9:** register the challenge families from existing assets (#321 relational, #328 under the #531 contract for any successor, V80), and **add the missing wrong-query family**.
- **Task 10:** a **development** known-truth rehearsal through the registered units, with right- versus wrong-query, program versus matched-null and donor isolation. A sealed final exposure needs **owner STOP U1**.
- **Tasks 11–12**, then U2–U5.

## 4. Next actions: who does what
**Actionable now; no data, no training, no new authority needed:**
1. **Macha:** fresh-head review of #525 `b493efc3`; review #538 (alias enforcement) and #536.
2. **Sol:** build the **cumulative Task 4 candidate** (step 1). **Macha** reviews it.
3. **Sol:** decide on **#534** before the **Nov 13** V80 artifact expiry: pin the platform, or compare against the original artifacts.
4. **Sol:** full Task 5 / NONE-type unification (step 3), then Task 6 registration (step 4). **Macha** reviews each, RED-first.
5. **Sol and owner:** the **L04** policy rule, needed for step 6.

**Needs an owner decision:**
- **#537:** GPU learned run, after Sol's Stage81B no-repeat comparison.
- **STOP U1:** before any sealed known-truth exposure.
- **#533:** the 207-row versus 291-row ruling.
- **PS V3.1.1 Task 4:** whether production-synthetic biology is still wanted, given the owner's "no new synthetic world now" ruling.

**Do not restart:**
- TD60 (closed #540);
- completed Macha reviews (event 56);
- Level-4 reads;
- PR328 world generation;
- historical reconciliation.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

# TD corrected replay (TD56 → TD57B → TD57C → TD59): rebuilt launch package for re-audit

Date: 2026-10-12. Prepared by Macha (Claude Code) after the external audit of PR #307.

**Prior audit terminal:**
`NOT_ACCEPTED_FOR_EXECUTE_ONCE__SOURCE_QUALIFICATION_AND_SOURCE_HETEROGENEITY_MUST_BE_SEPARATED__ONE_SHOT_ATTEMPT_UNSPENT`.

**No corrected replay has been run:**
- no corrected value has been opened;
- no start marker or attempt ledger exists;
- the namespace `D:/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1` does not exist;
- the one-shot attempt is unspent.

**Status:** `QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN`. Execution additionally requires the owner's ratification and your launch-audit acceptance. Neither has been created.

## 1. Commits

| role | branch | commit |
|---|---|---|
| implementation | `feat/td-corrected-replay-turnkey-20261012` | `7819aabd9a4c7adbd494445bb989c44e9b7cfa11` |
| authority (launch root) | `authority/td-corrected-replay-launch-7819aabd-20261012` | `69240132383d92911ddb360660c810b585813f1f` |
| this evidence package | `evidence/td-corrected-replay-launch-package-7819aabd-20261012` | the head of the PR carrying this file |

The authority commit is the implementation plus the equivalence receipt and the three authority records. `git diff 7819aabd 69240132 -- scripts/v5 target_discovery/iterations/corrected_replay_20261012` is empty.

**Superseded and preserved exactly as audit evidence** (not rewritten, not spent):
- implementation `f5673f9b`;
- authority `23b81f11` (branch `authority/td-corrected-replay-launch-f5673f9b-20261012`);
- evidence `cf4cba90` (PR #307);
- contract `46e4e7ad…`, code `4544200c…`, equivalence `18c05fe7…`;
- QUALIFY `51120497…` (`launch_QUALIFY_20261012T162204Z`).

`7819aabd` is a child commit of `f5673f9b` on the feature branch; no commit was rewritten. The gate refuses the superseded authority, because it binds the old contract (negative cases N3 and N4).

## 2. What changed, and what did not

**Unchanged (replay fidelity):**
- the TD56, TD57B, TD57C and TD59 computations;
- the frozen executors (archive bytes and TD59 `870ddea0`);
- the adapter and bootstrap, which are byte-identical to `f5673f9b` (`617efe42…`, `d322da01…`);
- source order, thresholds, panels, nulls, stopping rules, the stage outcome mapping, the launcher and the gate;
- routing V2 and V4 (frozen);
- `detected_field` remains proposed as `detected_corrected`.

**Changed: interpretation only.** The files are `td_corrected_replay_execute_v1.py`, `td_corrected_replay_evidence_v1.py`, the contract builder and contract, and the tests.

| concept | revised definition |
|---|---|
| `universal_qualification` (per stage, descriptive) | `ESTABLISHED__EVERY_PLANNED_SOURCE_AND_PANEL_OBSERVED_PASS` only when every planned source/panel was observed and passed its frozen per-source gate. `NOT_ESTABLISHED__AN_OBSERVED_EXECUTION_FAILED_ITS_FROZEN_GATE` when an observed execution failed. Otherwise, the stage status. |
| source-order censoring | Source/panels not run because of the frozen sequential stop are listed as `UNOBSERVED__NOT_RUN_UNDER_THE_FROZEN_SEQUENTIAL_STOP`. This is missing evidence, never agreement and never disagreement. |
| threshold discordance | A PASS and a FAIL on the same stage and panel is recorded as failure to establish universality (`THRESHOLD_DISCORDANCE_OBSERVED__UNIVERSALITY_NOT_ESTABLISHED`). It adds a descriptive `UNIVERSALITY_NOT_ESTABLISHED__CROSS_SOURCE_THRESHOLD_DISCORDANCE` qualifier to the frozen interpretation. |
| `source_heterogeneity` | `UNRESOLVED__NO_PROSPECTIVELY_FROZEN_DIRECT_BETWEEN_SOURCE_TEST` for every stage. Pattern G is never assigned. |
| routing V2 `universal_source` input | FAIL is reserved for formally established heterogeneity, so it is never produced. The input is NOT_ESTIMABLE if any stage is NOT_ESTIMABLE, otherwise PASS. Routing V2 rules 1 and 9 therefore never change a route: **the route is exactly the frozen TD56 → TD57B → TD57C → TD59 stage hierarchy, a function of the four stage statuses only.** |
| source averaging | No pooled or averaged statistic exists. A stage PASS needs every planned source/panel to PASS. |

The bundle receipt now carries these fields:
- `universal_qualification`, per stage: observed outcomes, unobserved list, discordance;
- `source_heterogeneity`;
- `routing_universal_source_input`.

The evidence validator recomputes all of them from the stage receipts.

## 3. Old (f5673f9b) vs new (7819aabd) routing over the complete outcome space

Artifacts are in `routing_enumeration/`:
- `enumerate_source_rule_routes_v2.py`;
- `ROUTING_ENUMERATION_SUMMARY.json`;
- `ROUTING_CHANGED_COMBINATIONS.csv`, listing all 11,734 combinations whose biological state changes;
- `REPRODUCE_AND_DUMP_SHA256.txt`.

**How the old and new routes were computed:**
- The old routes were computed by the `f5673f9b` code.
- The new routes were computed by the `7819aabd` code.
- The new rule was also re-implemented independently in the script. **The `7819aabd` code matches that prototype in all 15,379 combinations**, and its routing input is never FAIL.

The outcome space is 7 × 13³ = 15,379 combinations: each invocation PASS, FAIL or NOT_ESTIMABLE, with the frozen sequential stop. These are logical possibilities, not probabilities.

**V4 relational status, old → new:**

| old → new | count |
|---|---|
| FAIL → FAIL | 7,641 |
| **FAIL → NOT_ESTIMABLE** | **4,984** |
| **FAIL → PASS** | **4** |
| NOT_ESTIMABLE → NOT_ESTIMABLE | 2,748 |
| PASS → PASS | 2 |

No PASS→FAIL, NOT_ESTIMABLE→FAIL, NOT_ESTIMABLE→PASS or PASS→NOT_ESTIMABLE transitions occur. The biological state label changes in 11,734 combinations and is unchanged in 3,645. Every change replaces `SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED` with the frozen stage-hierarchy state.

**Candidate routes:**

| candidate | old → new | count |
|---|---|---|
| C2 | ELIMINATED → UNRESOLVED | 4,984 |
| C2 | ELIMINATED → ACTIVE | 4 |
| C2 | ELIMINATED → ELIMINATED | 7,641 |
| C2 | UNRESOLVED → UNRESOLVED | 2,748 |
| C2 | ACTIVE → ACTIVE | 2 |
| C4 | BLOCKED → UNRESOLVED_CONSTITUENT | 4,984 |
| C4 | BLOCKED → ACTIVE_SUBJECT_TO_C2_C3 | 4 |
| C4 | BLOCKED → BLOCKED | 7,641 |
| C4 | UNRESOLVED → UNRESOLVED | 2,748 |
| C4 | ACTIVE → ACTIVE | 2 |
| C6 | `ACTIVE_SUBJECT_TO_C1_C3` → same | 15,379 (all; relationally independent by construction) |

**What changed, explained:**
- **The 4,984 FAIL → NOT_ESTIMABLE combinations.** An upstream NOT_ESTIMABLE (or a TD57C divergence) was previously overridden by a later same-panel straddle. It now stays NOT_ESTIMABLE (audit item 8b).
- **The 4 FAIL → PASS combinations.** These are exactly the TD57C P0 or P1 straddles (HVS PASS then NPH52 or SEA_AD FAIL) with TD56/TD57B/TD59 all PASS. The old rule eliminated C2 only because it treated the straddle as heterogeneity. Under the revised rule they route to BROAD_MESO (Pattern A), exactly like a TD57C failure at HVS. The straddle is recorded and the universality qualifier attached; heterogeneity is unresolved.
- **This is the one place the revision is more permissive.** I flag it rather than leave it implicit.

### Source-order dependence (audit item 7)

**(a) Observed space.** For each combination, I moved a stage's first non-PASS to a different source in the same panel (same outcome type) and checked whether the biological state changed:

| rule | order-sensitive combinations |
|---|---|
| f5673f9b | 8,591 |
| **revised** | **0** |
| alternative U1 (below) | 6 |

**(b) Latent truth.** I assigned PASS/FAIL/NOT_ESTIMABLE to every planned invocation (27 × 729³ = 10,460,353,203 configurations, counted with multiplicities) and observed each under all 6 source orders:

| rule | state order-sensitive | V4 / C2 / C4 order-sensitive |
|---|---|---|
| f5673f9b | 8,985,454,482 | 6,130,506,828 |
| **revised** | 4,827,920,844 | 4,827,831,468 |
| alternative U1 | 4,827,921,012 | 4,827,831,636 |

**Every one of the revised rule's order-sensitive configurations has a stage that flips between FAIL and NOT_ESTIMABLE.** This residual comes entirely from the frozen first-non-PASS stage rule: when one source would FAIL and another would be NOT_ESTIMABLE, whichever runs first sets the stage status. That is replay fidelity and is unchanged. The revised interpretation adds no order dependence of its own. A uniform latent count heavily over-weights NOT_ESTIMABLE, so these counts are not frequencies.

**Considered alternative U1, not proposed.** U1 would treat discordance as `universal_source = NOT_ESTIMABLE`, i.e. unresolved. It differs from the revised rule only in the same 4 TD57C combinations (V4 PASS → NOT_ESTIMABLE). But it makes those routes depend on which source fails first: TD57C failing at HVS gives BROAD_MESO, while HVS passing and then NPH52 failing gives unresolved. That is 6 order-sensitive combinations in the observed space. It would turn the historical source order into a biological hierarchy (audit item 6). If you prefer U1, it is a one-function change and requires a rebuild.

## 4. Contract and code (SHA-256 at `7819aabd`)

| file | SHA-256 |
|---|---|
| **contract** `target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json` | `720809582fc36ac9138ca69b6c1fc79d373a6ff38952a8f51af1db680f4c2096` |
| **aggregate code identity** (`gate.code_identity`, 11 files; identical on Windows and WSL) | `dd7ee4bb4a7e3fe471eb30569535ff3252ec60e3bb7703b341f0ef22ab177a5f` |
| launcher `scripts/v5/run_td_corrected_replay_once.sh` (unchanged) | `f05e70b6011714fa9e0e08589572ee9e06bc705fd7cdb1da82c1f610912a0b81` |
| qualification/check script (gate) `scripts/v5/td_corrected_replay_gate_v1.py` (unchanged) | `4a300272eec40f6836aa27ed0580d198e71e0c45b14d028aed9cde1716aff83f` |
| post-marker orchestrator `scripts/v5/td_corrected_replay_execute_v1.py` | `07c26acdb2b5637d4a0223dbef29b914b93cfce41ccbb75c8ab6efd781e0fa3e` |
| evidence-package validator `scripts/v5/td_corrected_replay_evidence_v1.py` | `f1625263429698f3ebe4dc0ebd717a7bf44f36b39ec51d2551275dd459edb9ce` |
| adapter / bootstrap (unchanged) | `617efe42…` / `d322da01…` |
| contract builder `scripts/v5/build_td_corrected_replay_contract_v1.py` | `9e6fc39db9010c2c2b9d8688ff9b8017a6f6919773b4d3fc61cd212def708512` |
| tests `tests/v5/test_td_corrected_replay_turnkey_v1.py` | `4d6ee85e19cec411160031f6dc27d439b40240bc9adf4a0972d11b2564e2e794` |
| prerequisite amendment / environment lock (unchanged) | `4c5fefeb…` / `d63150da…` |

The contract regenerates byte for byte, and every package file is LF-only.

In the contract, `decisions_requiring_owner_ratification.routing_input_rule` holds:
- the revised definitions;
- worked examples;
- the residual order dependence;
- `amended_after`, citing the PR #307 audit terminal and the superseded rule.

## 5. Tests (local execution evidence, not CI)

| environment | turnkey file | with routing V2 + V4 tests |
|---|---|---|
| Windows `td-replay-hist` | 106 passed | 120 passed |
| WSL `td-replay-hist` (pinned replay env) | 104 passed, 2 skipped | 118 passed, 2 skipped |

The 2 WSL skips need the archive at its Windows path; the real QUALIFY covers them.

**New tests for audit item 8:**

| requirement | tests |
|---|---|
| PASS/FAIL threshold discordance is not labelled formal source heterogeneity | `test_threshold_discordance_is_failure_to_establish_universality_not_source_heterogeneity`, `test_td57c_threshold_discordance_routes_exactly_like_a_first_source_failure[0,1]` |
| an upstream NOT_ESTIMABLE is not strengthened by a later straddle | `test_an_upstream_not_estimable_is_not_strengthened_by_a_later_straddle`; plus the exhaustive `test_over_the_whole_outcome_space_the_route_follows_only_the_frozen_stage_hierarchy` (all 15,379 combinations: routing input never FAIL, a decisive NOT_ESTIMABLE always gives V4 NOT_ESTIMABLE, C6 constant, route a function of the stage statuses only) |
| source-order censoring is missing evidence, not agreement | `test_source_order_censoring_is_missing_evidence_not_agreement` |
| downstream target/TD60/Stage 4/training authority stays false | the exhaustive test (routing authority flags on every combination); bundle and evidence downstream-flag checks |
| no source averaging rescues a failed universal qualification | `test_no_source_averaging_rescues_a_failed_universal_qualification` (5 of 6 source-panels PASS still FAIL) |

The evidence tamper tests now include the new fields `universal`, `heterogeneity` and `qualification`. Every earlier negative test is retained: stale authority, wrong hashes, missing or wrong-class diagnostic, altered executor identity, reused namespace, TD60/training authorization, and G7 relabelled PASS.

## 6. Historical-fixture equivalence (bound to the new implementation)

- **Where it ran:** WSL, from the clean detached checkout `D:/jepa_wt_td_replay_canon_7819aabd`, verified clean before and after.
- **Result:** **16/16 cases exactly equal**; the TD57C P0 HVS historical FAIL was reproduced.
- **Time:** 283.5 s.
- **Values:** historical only (`corrected_values_read: false`).
- **Receipt:** `custody/target_discovery/corrected_replay_20261012/TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1.json`, SHA-256 **`9b02c126244aec00b4dcfed13f4c35ce19cec20fde04835537ec1b207175ef16`**.

## 7. Fresh replay-only authority (at `69240132`)

| record | SHA-256 |
|---|---|
| `TD_CORRECTED_REPLAY_OWNER_DECISION_V1.json` | `f3f20773762ace43b5a5ec8658fd696bb1c1aa280fa6c45b2fe0a98f7c739979` |
| `TD_CORRECTED_REPLAY_RUNTIME_AUTHORIZATION_V1.json` | `f59f51712c0222c65b07de5c12b2315bee0d061f5818c473f2a28907e3ffac8d` |
| `TD_CORRECTED_REPLAY_OPERATIONAL_AUTHORIZATION_V1.json` | `fac62caea5dca118c6e55e460d6bf740f1158d03ed1da19974e56dd863ad2ef2` |

**What the records bind:**
- contract `72080958`, implementation `7819aabd`, code `dd7ee4bb`;
- equivalence `9b02c126`, lock `d63150da`;
- namespace `REPLAY_OUT_V1`;
- a single attempt.

Every downstream flag is false.

## 8. Real-file QUALIFY and launcher negative cases

**QUALIFY:**
- **Where it ran:** the clean launch root `D:/jepa_wt_td_replay_launchroot_69240132`, clean before and after.
- **Command:** `bash scripts/v5/run_td_corrected_replay_once.sh QUALIFY 69240132383d92911ddb360660c810b585813f1f fac62caea5dca118c6e55e460d6bf740f1158d03ed1da19974e56dd863ad2ef2`.
- **Exit 3**, terminal `QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN`.
- **Record:** `launch_QUALIFY_20261012T173346Z`, copied byte-exact under `qualify_record/`.
- **Receipt SHA-256:** **`f7c881143f9b3891b257db71133bc36d4773dc04fe1ab78e471ecbc1c52bf5ed`**.

**What QUALIFY checked:**
- **Contract and executors:** PASS.
- **Equivalence:** 16 cases at this commit.
- **Predecessors:** G6 accepted; G7 NOT_ESTIMABLE, never PASS; the diagnostic; the spent record.
- **Structural estimability** (metadata only): donors with a stratum of at least 4 cells were HVS 39, NPH52 16, SEA_AD 46. The structure equals the historical td50 for each source.
- **Support bundle:** `07748d5b`, member `852cb3ec`.
- **Namespace and attempt ledger:** both absent.
- **Authority:** PASS.
- **Recorded flags:** `corrected_values_opened: false`, `replay_kernels_run: false`, `start_marker_created: false`.

**Launcher negative cases** (`LAUNCHER_NEGATIVE_CASES.txt`, recorded at run time against the real launcher): **11/11 refused with exit 64, and the run-base listing was unchanged.**

| case | attempted |
|---|---|
| N1 | bad mode |
| N2 | wrong operational SHA |
| N3 | superseded operational SHA `75f7d0af`, from f5673f9b |
| N4 | superseded authority commit `23b81f11` |
| N5 | implementation commit used as the authority commit |
| N6 | too few arguments |
| N7 | nonexistent acceptance commit |
| N8 | acceptance absent |
| N9 | nonexistent ratification |
| N10 | ratification absent |
| N11 | malformed commit |

N7 and N8 stop at the ratification pin, which runs before the acceptance pin. As before, the acceptance pin itself cannot be exercised until a real ratification exists.

## 9. Pending decisions, residuals and templates

**For owner ratification** (QUALIFY passes only with an exact match):
- `detected_field = detected_corrected`;
- `routing_input_rule` as section 2 and the contract state it.

Ratification can accept only the proposed options.

**Residuals**, unchanged from the previous package unless noted:
- **Pattern F:** any corrected TD59 PASS is flagged for your judgment, and the HVS TD59 case margins are reported.
- **TD56 with zero measurable donors** crashes in the frozen executor and becomes IMPLEMENTATION_FAILURE.
- **NPH52 is G6's historical pass-through,** so it is not an independent corrected replication. It also gives a free post-run adapter check.
- **The structural floor is looser than the executors' own rule.**
- **The environment lock** covers `pip freeze` only.
- **One-shot guards are filesystem tripwires**; the committed evidence is the durable record.
- **Scope:** TD56/57B/57C/59 only. TD57A, TD58 and the 353-gene check are excluded.
- **New:**
  - The residual FAIL-vs-NOT_ESTIMABLE source-order dependence from the frozen stopping rule (section 3).
  - The 4 TD57C-straddle combinations that move from FAIL to PASS (section 3).

**Templates** (I create neither):
- **Ratification**, at `custody/owner_decisions/20261012/TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1.json`: `{"schema": "JEPA_TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1", "contract_sha256": "720809582fc36ac9138ca69b6c1fc79d373a6ff38952a8f51af1db680f4c2096", "ratified": {"detected_field": "detected_corrected", "routing_input_rule": <exactly the contract's proposed object>}}`.
- **Launch-audit acceptance**, at `custody/owner_decisions/20261012/TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1.json`: `{"schema": "JEPA_TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1", "disposition": "ACCEPT_TD_CORRECTED_REPLAY_LAUNCH_PACKAGE__EXECUTE_ONCE", "scope": "CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY", "contract_sha256": "720809582fc36ac9138ca69b6c1fc79d373a6ff38952a8f51af1db680f4c2096", "implementation_commit_sha": "7819aabd9a4c7adbd494445bb989c44e9b7cfa11", "code_sha256": "dd7ee4bb4a7e3fe471eb30569535ff3252ec60e3bb7703b341f0ef22ab177a5f", "operational_authorization_sha256": "fac62caea5dca118c6e55e460d6bf740f1158d03ed1da19974e56dd863ad2ef2", "corrected_replay_execution_authorized": true, "g6_execution_authorized": false, "g7_execution_authorized": false, "target_selection_authorized": false, "td60_authorized": false, "stage4_authorized": false, "training_authorized": false}`.
- **The single execution,** from the clean launch root: `bash scripts/v5/run_td_corrected_replay_once.sh EXECUTE_ONCE 69240132383d92911ddb360660c810b585813f1f fac62caea5dca118c6e55e460d6bf740f1158d03ed1da19974e56dd863ad2ef2 <acceptance commit> <acceptance SHA-256> <ratification commit> <ratification SHA-256>`.

STOP. EXECUTE_ONCE will not be run, and no ratification will be created, until external re-audit accepts this exact package.

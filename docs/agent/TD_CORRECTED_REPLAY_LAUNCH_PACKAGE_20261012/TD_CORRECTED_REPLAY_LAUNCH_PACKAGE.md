# TD corrected replay (TD56 → TD57B → TD57C → TD59): launch package for audit

Date: 2026-10-12. Prepared by Macha (Claude Code) at the owner's instruction.

**No corrected replay has been run.** No corrected value has been opened, and no start marker or attempt ledger
exists. The namespace `D:/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1` does not exist.

**Status:** `QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN`.
- Every QUALIFY check passed on the real files.
- Two things are outstanding:
  1. the owner's ratification of two proposed decisions (section 8, which includes a routing disclosure the owner should read first);
  2. your launch-audit acceptance.
- EXECUTE_ONCE refuses to start without both.

## 1. Commits

| role | branch | commit |
|---|---|---|
| implementation | `feat/td-corrected-replay-turnkey-20261012` | `f5673f9b5c8a02d14ed1a82afb8a1ce144283f5f` |
| authority (launch root) | `authority/td-corrected-replay-launch-f5673f9b-20261012` | `23b81f11c7e573014938274fae0ae4167b32c6d1` |
| this evidence package | `evidence/td-corrected-replay-launch-package-f5673f9b-20261012` | head of the PR carrying this file |

The authority commit is the implementation commit plus two additions:
- the equivalence receipt;
- the three authority records.

`git diff f5673f9b 23b81f11 -- scripts/v5 target_discovery/iterations/corrected_replay_20261012` is empty. The launcher refuses to run otherwise.

**Superseded and void.** None of these was accepted or executed:
- implementation `f74632ed`, authority `635f9f00` (operational `da58136a…`), contract `f45f9f0d…`, and QUALIFY record `launch_QUALIFY_20261012T150923Z`;
- implementation `a9b923d4`, contract `bb6bc298…`, and equivalence `cb3655ca…`. Its authority drafts were never committed.

The gate refuses superseded authority because it binds an old contract SHA (negative cases N3 and N4).

## 2. Frozen contract and code (SHA-256 at `f5673f9b`)

| file | SHA-256 |
|---|---|
| contract `target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json` | `46e4e7ad30f5e18197a377066a16de9047582dafb1ccbb837769e92b5ac92061` |
| prerequisite amendment `…/TD_CORRECTED_REPLAY_PREREQUISITE_AMENDMENT_20261012.json` | `4c5fefeb39de6a607266cf2ae3de96d25673cbf2b92c1af6992210d1f5fb7d2f` |
| environment lock `…/TD_REPLAY_ENV_WSL_PIP_FREEZE.txt` | `d63150da91e13066ddc169d670695ec936b29770ca150969bb7e30e207c6d80c` |
| **launcher** `scripts/v5/run_td_corrected_replay_once.sh` | `f05e70b6011714fa9e0e08589572ee9e06bc705fd7cdb1da82c1f610912a0b81` |
| **qualification/check script (gate)** `scripts/v5/td_corrected_replay_gate_v1.py` | `4a300272eec40f6836aa27ed0580d198e71e0c45b14d028aed9cde1716aff83f` |
| post-marker orchestrator `scripts/v5/td_corrected_replay_execute_v1.py` | `e883676fcd72797051c2439def1ec7bcab5dc033172d8d0ffecbbe4dded68a3c` |
| **evidence-package validator** `scripts/v5/td_corrected_replay_evidence_v1.py` | `45a46088cbc7cf7e50f395e9bfbd87281087efff9b30666664e8de8b39278c59` |
| adapter `scripts/v5/td_corrected_replay_adapter_v1.py` | `617efe4279aaab28a5ea8e8df01b8c920bf1b19d97efa1acc2b0508f3ee7d9fc` |
| exact-bytes bootstrap `scripts/v5/td_corrected_replay_exec_bootstrap_v1.py` | `d322da0188a877d3138bc92c56f117ffa9f3ffe4da0a2c1c18a23b4ff9c4ce53` |
| equivalence runner `scripts/v5/td_corrected_replay_equivalence_v1.py` | `8303061c2a39a704421a531eab8eb2d486ac5a82121a75dc642d8ab02c77551b` |
| contract builder `scripts/v5/build_td_corrected_replay_contract_v1.py` | `f46bd83b0459ee3318cde6ebb941980c62075b566f821e602bdd2c42998dae13` |
| routing V2, unchanged and frozen (`scripts/v5/td_corrected_replay_routing_v2.py`) | `c0a7605e3eefbdcae67e11169fd56ae610078a3dfc85c8caaf5ed189360b3540` |
| tests `tests/v5/test_td_corrected_replay_turnkey_v1.py` | `38e8e5eac7fdeaf442a40b85f0974f0ec02365f9a4e8fade1f366f14aa082ea5` |
| aggregate code identity (`gate.code_identity`, 11 files) | `4544200cbc72b3b47eeab8efbb500ef7147e2ec0bff1159984a3dd582393b389` |

- The contract regenerates byte for byte (`build_td_corrected_replay_contract_v1.py --check`).
- Every package file is LF-only, so the code identity is the same on Windows and in WSL.

**Executors.** These are unchanged and are resolved by their bytes:
- TD56: `run_td56_hvs.py`, `run_td56_nph.py`, `run_td56_sea_fast.py`;
- TD57B: `td57b_fixed_relational_recurrence.py`;
- TD57C: `td57c_three_view_local_geometry.py`;
- TD59: successor `870ddea0…`.

**Predecessor facts.** QUALIFY verifies these rather than trusting them:
- G6: producer `ff4a21f9`, acceptance `89932183`, receipt `2edaa2d2`, values `fdc13516`, metadata `bd3a494b`.
- G7: implementation `8d41fb98`, marker `2579b9a6`, receipt `47f9be6e`. The terminal must be exactly `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` and is never PASS.
- Diagnostic: `0b50938e`, classification `GENUINELY_DISJOINT_NATURAL_CELL_SETS`. Its transforms (`f7378b2a`) and result document (`208684bc`) are pinned by SHA.
- Spent G7 authorities are refused.

## 3. Independent pre-launch reviews and dispositions

Two read-only independent reviews were run. Neither ran EXECUTE_ONCE or opened corrected values.

**Review 1 (of `f74632ed`): CONCERN.**
- It confirmed the core design:
  - the executors get exactly what they historically saw;
  - redirection is complete;
  - the float32 cast is lossless;
  - the marker precedes the values;
  - the equivalence is real.
- It found 7 defects, fixed in `a9b923d4`:

| # | finding | fix | key tests |
|---|---|---|---|
| 1 | `universal_source` routed a TD57C P0 source disagreement to PASS (BROAD_MESO) but the same disagreement in P1 to SOURCE_DISAGREEMENT | The proposed rule now compares sources on the same stage and panel. The contract states the reading and examples. | `test_universal_source_compares_sources_on_the_same_panel`, `test_a_td57c_source_disagreement_routes_to_source_disagreement_in_either_panel[0,1]` |
| 2 | The evidence validator accepted a falsified namespace | Every outcome is recomputed from its exit code and the executor's own result. The validator checks the stdout, stderr and output SHAs, the executor identity, the planned counts, the input record and the ledger, and reproduces the bundle and routing input. | `test_evidence_tampering_is_detected[...]` |
| 3 | `detected_field` was scraped by `sed`; the support bundle was checked only after the marker | The orchestrator reads the ratification as parsed JSON. The support bundle `07748d5b` and member `852cb3ec` are checked in QUALIFY and again before the marker. | `test_ratification_is_parsed_not_scraped`, `test_support_bundle_is_checked_by_bundle_and_member_sha` |
| 4 | The runtime equivalence and lock bindings were never checked | Both are now checked. | `test_stale_or_widened_authority_is_refused[…]` |
| 5 | Deleting the namespace re-enabled EXECUTE_ONCE | An exclusive attempt ledger sits beside the namespace. QUALIFY, the orchestrator and the launcher all check it. | `test_begin_attempt_…`, `test_second_attempt_is_refused_even_after_the_namespace_is_removed`, `test_qualify_refuses_a_spent_attempt_ledger` |
| 6 | Exit 2 was read as a scientific FAIL (Python also exits 2 on argparse errors) | Exit 0 or 2 counts only if the executor's written result says so for that source and panel. | `test_outcome_classes_follow_the_frozen_mapping`, `test_an_implementation_failure_is_preserved_and_never_routed[ARGPARSE]` |
| 7 | Running the orchestrator directly bypassed every guard | `preflight_execute` runs before the marker. | `test_the_orchestrator_cannot_be_run_around_its_gates_and_spends_nothing[…]` |

**Review 2 (of `a9b923d4`): CONCERN, with nothing blocking.**
- It confirmed all 7 fixes, checking finding 6 against the real executors.
- It found no defect that would crash or misroute the real run after the marker.
- Its new findings were fixed in `f5673f9b`:

| # | finding | fix | key tests |
|---|---|---|---|
| A | **Bug introduced by fix 5.** The launcher wrote `RUN_RECORD.txt` before calling the orchestrator and refused any later launch once it existed, so a harmless pre-marker stop blocked the replay permanently. | After the orchestrator returns, the launcher records `attempt_spent=yes\|no` from the ledger and refuses only on `yes`, the ledger or the namespace. | `test_launcher_records_whether_the_attempt_was_spent_and_passes_the_authority_bytes` |
| B | The routing rule's consequences were not shown to the ratifier | Disclosed in the contract and in section 8. I reproduced the enumeration independently. | n/a (owner decision) |
| C | A ledger without a marker was reported as "no attempt" | It is now reported as a spent attempt, or INVALID if namespace files exist. | `test_a_spent_ledger_without_a_marker_is_reported_as_spent` |
| D | A completed result could be passed off as a crash | Unrecorded files and stage directories after a missing receipt are flagged. Against the launch record, an orchestrator exit 0 with incomplete evidence, or a bundle summary that differs from the one printed at run time, is INVALID. | `test_a_completed_result_cannot_be_passed_off_as_a_crash_against_the_launch_record`, `test_the_printed_stage_summary_is_checked_against_the_bundle` |
| E | In a direct run, input SHAs were checked only after the marker | The orchestrator hashes the archive, G6 values and metadata, and the sample freeze before the marker. These are bytes only; nothing is decoded. | `test_input_bytes_are_hashed_before_the_marker` |
| 7′ | Preflight trusted the launcher's check record | Preflight re-validates the owner, runtime, operational and acceptance bytes and the equivalence receipt itself. | `test_preflight_revalidates_the_authority_bytes` |
| 2′ | A fully consistent rewrite was accepted | Each module result must equal the payload the executor printed and follow from its own cases, and a TD56 PASS must match its printed PASS flag. The run-time printed summary sits outside the namespace. | `test_evidence_tampering_is_detected[printed, cases, td56_flag, stray_*, executor_copy, later_stage_dir]` (19 attacks in total) |

**What remains true.** The validator checks self-consistency, not authorship. Someone with write access to both the namespace and the launch record can still produce a consistent forgery. The durable custody of the result is committing the evidence promptly after the run.

## 4. Tests (local execution evidence, not CI)

| environment | turnkey file | with routing V2 + V4 tests |
|---|---|---|
| Windows, `td-replay-hist` (Python 3.13.5) | 100 passed | 114 passed |
| WSL, `td-replay-hist` (the pinned replay env) | 98 passed, 2 skipped | 112 passed, 2 skipped |

The 2 WSL skips need the archive at its Windows path: one rebuilds the contract byte for byte, the other runs `validate_contract` on the real archive. The real QUALIFY covers both.

**Negative tests, by the categories you named:**
- **Stale authority:** `test_stale_or_widened_authority_is_refused` (11 cases: contract, implementation, equivalence and lock bindings, scope, namespace, single attempt) and `test_preflight_revalidates_the_authority_bytes`.
- **Wrong hashes:** `test_spent_authority_and_wrong_shas_are_refused`, `test_predecessor_attacks_fail_closed[g6_file, acceptance, g7_receipt, diag_result]`, `test_validate_contract_refuses_altered_or_ambiguous_executor_bytes`, `test_validate_contract_refuses_a_changed_environment_lock`, `test_equivalence_receipt_is_required_exactly`, `test_input_bytes_are_hashed_before_the_marker`.
- **Missing diagnostic:** `[missing_diagnostic]`. **Wrong diagnostic class:** `[wrong_class]` and `[diag_authority]`.
- **Altered executor identity:** `test_validate_contract_refuses_altered_or_ambiguous_executor_bytes`, `test_bootstrap_refuses_altered_bytes_and_paths_outside_mnt_data`, `test_evidence_tampering_is_detected[executor_copy]`.
- **Reused namespace:** `test_begin_attempt_is_exclusive_and_spends_the_namespace`, `test_second_attempt_is_refused_even_after_the_namespace_is_removed`, `test_qualify_refuses_a_spent_attempt_ledger`.
- **Attempts to authorize TD60 or training:** `test_stale_or_widened_authority_is_refused[td60_authorized, training_authorized, g6_execution_authorized, target_tournament_authorized]`, `test_contract_refuses_any_weakening`, and the downstream flags checked by the evidence validator.
- **G7 relabelled PASS:** `test_g7_relabelled_pass_is_refused_even_with_matching_hashes`.

## 5. Historical-fixture equivalence (adapter qualification)

- **Rerun for `f5673f9b`.** The receipt is bound to the implementation commit, so it was rerun even though the adapter and bootstrap are byte-identical to `a9b923d4`.
- **Where.** WSL, from the clean detached checkout `D:/jepa_wt_td_replay_canon_f5673f9b`. Immediately before the run, Git Bash verified HEAD and that `status --porcelain --ignored` was empty; the check was repeated after the run.
- **Result: 16 of 16 cases exactly equal.** The TD57C P0 HVS historical FAIL was reproduced. Run time: 258 s.
- **Values.** Historical values only (`corrected_values_read: false`).
- **Receipt.** `custody/target_discovery/corrected_replay_20261012/TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1.json`, SHA-256 `18c05fe705374a01dc47e62bd3ee1412089bd95589d383bb7638ad950b1513bf`.

## 6. Fresh replay-only authority (at `23b81f11`, in `custody/owner_decisions/20261012/`)

| record | SHA-256 |
|---|---|
| `TD_CORRECTED_REPLAY_OWNER_DECISION_V1.json` | `02caebae0a83dc2bf73976cea21fcd9a06bfdd948b28e59ca3867ac18bfd9522` |
| `TD_CORRECTED_REPLAY_RUNTIME_AUTHORIZATION_V1.json` | `d716eda760689d3bf00d5c34e8fba67d0f57fd34f76c9edd2b7e378522d82fb4` |
| `TD_CORRECTED_REPLAY_OPERATIONAL_AUTHORIZATION_V1.json` | `75f7d0afb0c8aeeae1ddc43429cbf751c10949fa504a80e028db7b933750cc93` |

**What they bind:**
- contract `46e4e7ad`, implementation `f5673f9b`, code identity `4544200c`;
- equivalence `18c05fe7`, lock `d63150da`, amendment `4c5fefeb`;
- namespace `D:/jepa_td_corrected_replay_20261012/REPLAY_OUT_V1`;
- a single attempt, with scope `CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY`.

Every downstream flag is false: G6, G7, target selection, TD60, Stage 4 and training.

I prepared these records at the owner's instruction. Execution additionally needs two records I do not create: the owner's ratification and your launch-audit acceptance.

## 7. Real-file QUALIFY (no replay)

- **Where it ran:** the clean launch root `D:/jepa_wt_td_replay_launchroot_23b81f11`, checked out at the authority commit. It was clean, including ignored files, before and after.
- **Command:** `bash scripts/v5/run_td_corrected_replay_once.sh QUALIFY 23b81f11c7e573014938274fae0ae4167b32c6d1 75f7d0afb0c8aeeae1ddc43429cbf751c10949fa504a80e028db7b933750cc93`.
- **Record:** `D:/jepa_td_corrected_replay_20261012/launch_QUALIFY_20261012T162204Z`, copied byte-exact under `qualify_record/` with `SOURCE_SHA256.txt`.
- **Receipt:** `QUALIFY_RECEIPT.json`, SHA-256 `51120497a2d3d80a21f6ac2bacd92846254b81eea423ea3afa31550ef0ce93a0`.
- **Exit 3**, terminal `QUALIFIED_EXCEPT_PENDING_OWNER_RATIFICATION__NO_BIOLOGICAL_REPLAY_RUN`.

**What passed:**
- **Contract:** science references, executors resolved from the archive bytes, the TD59 successor, the lock file.
- **Equivalence:** 16 cases, at this commit, with this adapter and bootstrap, in the Linux env.
- **Predecessors:** the five G6 files plus the acceptance; G7 zero-overlap NOT_ESTIMABLE; the diagnostic transforms and result; the spent record.
- **Structural estimability:** metadata only. donors with a >= 4-cell donor x operator stratum HVS 39 / NPH52 16 / SEA_AD 46 (cells 1,129 / 1,310 / 22,561). The G6 structure equals the historical td50 per source.
- **Support bundle:** `07748d5b`, member `852cb3ec`.
- **Freshness:** the namespace and the ledger are both absent.
- **Authority:** PASS.

The receipt records `corrected_values_opened: false`, `replay_kernels_run: false` and `start_marker_created: false`.

**Launcher negative cases.** I ran these against the real launcher in the clean launch root and recorded them as they ran (`LAUNCHER_NEGATIVE_CASES.txt`). **11 of 11 were refused with exit 64, and the run-base listing was unchanged:**

| case | attempt |
|---|---|
| N1 | bad mode |
| N2 | wrong operational SHA |
| N3 | superseded operational SHA `da58136a` |
| N4 | superseded authority commit `635f9f00` |
| N5 | implementation commit passed as the authority |
| N6 | EXECUTE_ONCE with too few arguments |
| N7 | EXECUTE_ONCE with a nonexistent acceptance commit |
| N8 | EXECUTE_ONCE with the acceptance absent at the given commit |
| N9 | nonexistent ratification commit |
| N10 | ratification absent at the given commit |
| N11 | malformed commit |

N7 and N8 were refused at the ratification pin. It runs before the acceptance pin, and there is no committed ratification. So the acceptance pin itself cannot be exercised on the real launcher until a real ratification exists, which I do not create. Its position before any filesystem change is covered by `test_launcher_orders_pure_checks_qualify_and_marker_correctly`.

## 8. Decisions for owner ratification, residuals and limitations

The contract proposes two decisions. QUALIFY passes only on an exact match.

1. **`detected_field`:** proposed **`detected_corrected`** (the alternative is `detected_historical`). This chooses which G6 detected count feeds the executors' td50 `detected` field, which is used by the depth/detection null blocks.
2. **`routing_input_rule`:**
   - The stage inputs are the frozen stage statuses. An IMPLEMENTATION_FAILURE yields no routing input.
   - `universal_source` is FAIL if, in any stage and panel, one source PASSED that panel's invocation and another FAILED it. Otherwise it is NOT_ESTIMABLE if any stage is NOT_ESTIMABLE. Otherwise it is PASS.
   - A universal PASS means only that no disagreement was observed under the frozen sequential order. Sources after a stage's first failure never run, so an "SEA_AD PASS, HVS FAIL" disagreement can never be seen.

**Disclosure the owner should read before ratifying (re-review finding B; I reproduced it independently).** Routing V2 is frozen and checks `universal_source` before everything else. Combined with this rule, that has three consequences:
- **A source disagreement overrides an upstream NOT_ESTIMABLE or a TD57C divergence.** Example: TD56 NOT_ESTIMABLE plus TD59 P0 "HVS PASS, NPH52 FAIL" routes to `SOURCE_DISAGREEMENT` (V4 FAIL, which eliminates C2), not to `NOT_ESTIMABLE__TD56` (V4 NOT_ESTIMABLE).
- **Which source fails first can decide the route.** In that same state, a TD59 P0 HVS FAIL (nothing runs after it) leaves V4 NOT_ESTIMABLE, while HVS PASS followed by NPH52 FAIL gives V4 FAIL.
- **How often the rule changes the route.** I enumerated all 15,379 outcome combinations the frozen order allows; these are logical possibilities, not probabilities. A universal FAIL changes the V4 route in 4,988 of them:
  - 4,984 change NOT_ESTIMABLE to FAIL;
  - 4 change PASS to FAIL, all through a TD57C source disagreement. For example, TD57C P0 "HVS PASS, NPH52 FAIL" with TD59 PASS gives `SOURCE_DISAGREEMENT`, not `BROAD_MESO`.

The enumeration script and its output are in `routing_enumeration/`.

Ratification can accept only the proposed options. A different choice requires a rebuilt contract and a new package.

**Residuals (documented, not mechanized):**
- **Pattern F** ("materially narrow HVS margins") has no frozen threshold. Any corrected TD59 PASS is flagged for your judgment, and the HVS TD59 case margins are reported.
- **TD56 with zero measurable donors** crashes inside the frozen executor (`np.min([])`) before it saves anything. That gives IMPLEMENTATION_FAILURE, which routes nothing, rather than NOT_ESTIMABLE. The SEA_AD script tolerates up to 3 non-finite nulls. This is frozen behaviour and was not altered. Structurally, every source has at least 16 donors with a stratum of at least 4 cells.
- **NPH52 is G6's authenticated historical pass-through.** It is therefore not an independent corrected replication. It does provide a free post-run adapter check: if `detected_corrected == detected_historical` on the NPH52 rows, the corrected NPH52 outputs should equal the historical ones exactly, apart from `input_sha256`. This check is available to the outcome audit but is not a gate.
- **The gate's structural floor is looser than the executors' own measurability rule**, which applies after the marker. The structural counts are well clear of it: for TD57C/TD59, the structurally eligible donors (HVS/NPH52/SEA_AD) are 17/16/46 and 29/16/46.
- **The environment lock is the full `pip freeze`.** Non-Python libraries such as BLAS are not covered; exactness is established empirically by the 16/16 equivalence run.
- **The one-shot guards are filesystem tripwires:** the ledger, the namespace, and `attempt_spent=yes` run records. The committed outcome evidence is the durable record that the attempt was spent.
- **Scope:** TD56, TD57B, TD57C and TD59 only, as instructed. TD57A, TD58 and the 25K contract's 353-gene check are not part of this package.
- **Hard boundary:** no path in the package can reach a G6 or G7 rerun, the target tournament, TD60, Stage 4 or training.
- **Handoff note:** the handoff in PR #304 still points to `f74632ed`. The live implementation head is `f5673f9b`.

## 9. What acceptance would look like (templates only; I did not create these)

Owner ratification, at `custody/owner_decisions/20261012/TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1.json`:

```json
{"schema": "JEPA_TD_CORRECTED_REPLAY_DECISION_RATIFICATION_V1",
 "contract_sha256": "46e4e7ad30f5e18197a377066a16de9047582dafb1ccbb837769e92b5ac92061",
 "ratified": {"detected_field": "detected_corrected",
              "routing_input_rule": <exactly contract.decisions_requiring_owner_ratification.routing_input_rule.proposed>}}
```

Launch-audit acceptance, at `custody/owner_decisions/20261012/TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1.json`:

```json
{"schema": "JEPA_TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1",
 "disposition": "ACCEPT_TD_CORRECTED_REPLAY_LAUNCH_PACKAGE__EXECUTE_ONCE",
 "scope": "CORRECTED_TD56_TD57B_TD57C_TD59_REPLAY_ONLY",
 "contract_sha256": "46e4e7ad30f5e18197a377066a16de9047582dafb1ccbb837769e92b5ac92061",
 "implementation_commit_sha": "f5673f9b5c8a02d14ed1a82afb8a1ce144283f5f",
 "code_sha256": "4544200cbc72b3b47eeab8efbb500ef7147e2ec0bff1159984a3dd582393b389",
 "operational_authorization_sha256": "75f7d0afb0c8aeeae1ddc43429cbf751c10949fa504a80e028db7b933750cc93",
 "corrected_replay_execution_authorized": true,
 "g6_execution_authorized": false, "g7_execution_authorized": false, "target_selection_authorized": false,
 "td60_authorized": false, "stage4_authorized": false, "training_authorized": false}
```

The single execution, run from the clean launch root in Git Bash:

```
bash scripts/v5/run_td_corrected_replay_once.sh EXECUTE_ONCE 23b81f11c7e573014938274fae0ae4167b32c6d1 75f7d0afb0c8aeeae1ddc43429cbf751c10949fa504a80e028db7b933750cc93 \
  <acceptance commit> <acceptance SHA-256> <ratification commit> <ratification SHA-256>
```

STOP. Corrected TD56/57B/57C/59 will not be executed until this exact package is audited and accepted.

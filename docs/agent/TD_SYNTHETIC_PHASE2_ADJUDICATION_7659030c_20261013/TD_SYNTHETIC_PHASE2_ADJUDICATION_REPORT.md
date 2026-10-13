# TD synthetic phase-2 adjudication — repaired head 7659030c (executed once)

**Terminal:** `PHASE2_ADJUDICATION_COMPLETE__RECEIPT_FROZEN__STOP_FOR_INDEPENDENT_AUDIT`

**Emitted:** qualification `QUALIFIED`; readiness `READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY`. These are reported exactly as emitted, without interpretation.

**Authority:** fresh one-shot phase-2 authorization from Dushyant (controller), delivered in the Macha session and recorded before execution in PR #330 comment 6156119102. The procedure follows packet `docs/agent/TD_PHASE2_EXECUTION_PACKET_20261013.md` @ `cde596530d126795ab9421416af58f144b2ab41e`, with the TD checkout replaced by the controller-accepted repaired head (PR #330 comment 6154482286).

Packaging note: this report and `SOURCE_SHA256.txt` were assembled after the run. Every file under `record/`, `input/` and `output/` is a byte copy of what the run and its checks wrote.

## 1. Checkout

`7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606`, a fresh detached worktree at `D:/jepa_wt_td_synth_phase2_7659030c`. It had 0 tracked, untracked or ignored changes before and after the run (`record/CHECKOUT_PRE.txt`, `record/POST_RUN_STATE.txt`).

## 2. Inputs (all verified before use; new phase-2-only workspace `D:/jepa_td_synthetic_phase2_7659030c_20261013`)

| input | identity | result |
|---|---|---|
| run | `38438433970` | — |
| pre-fit artifact `11834580081` zip | `97c89d0e1781b7fe8a3a0e4c5b84bcf181e7e1636cbcb0f81a2679a3dc076798` | = GitHub digest |
| controller artifact `11833833421` zip | `8e796017c01e50fd483278d0eec6f94513e949324665c84b877ae4b7cd621364` | = GitHub digest |
| pre-fit archive | `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`, 7,018,400 B | MATCH |
| controller archive | `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`, 2,028 B | MATCH |
| binding | `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44` | MATCH |
| package root | `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115` | MATCH |
| fit-view NPZ files | 9, each named by its content SHA | 9 ok |
| controller manifest (raw) | `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9` | MATCH (hash only) |
| controller realization receipt | `531966f132f7d1127d7aff586eba5452d6650e115b840193082fef8db2feb255` | hash only |
| frozen V4 receipt (byte copy from `a1aed169`) | `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`, 328,351 B | MATCH |

The 12 package files and 3 controller files are identical, as sets, to the prior attempt's record (`1850b5f8` `INPUT_VERIFICATION.txt`). All of them were unchanged after the run.

**Pre-open checks:**
- **Code order** (`record/AUTH_ORDER_CHECK.txt`): `authenticate_blinded_phase_inputs` (line 159) checks the receipt SHA (line 136) and the 8 fit-engine hashes (lines 106–107). Only after that does `V3._read_controller_json` run (line 167).
- **Reader preflight** (`record/READER_PREFLIGHT.json`, tool SHA `e472857383ce52ea885a62e19b107fec7066e47af8663ef0a5fc2adf36b09341`): `READER_ACCEPTED`; 9 + 45 profiles; engine identity match; re-serialization byte-identical. The controller folder was not accessed and the sentinel did not fire.
- **No phase-1 rerun** (`record/NO_PHASE1_RERUN_CHECK.txt`): the only phase-1 evidence is `a1aed169`.

## 3. Environment

Python 3.11.15 and NumPy 2.4.6 (`sea-ad-jepa-v3`, the same as phase 1). The full freeze is in `record/PHASE2_ENVIRONMENT.txt`.

## 4. Command (run once; `PYTHONDONTWRITEBYTECODE=1 -B`)

The full text is in `record/ADJUDICATE_RUN_RECORD.txt`. The command was `python scripts/v5/td_relational_successor_disk_runner_v4.py adjudicate`, with the packet's arguments and `--output <workspace>/output/TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json`. It ended at 2026-10-13T22:06:37.679Z with exit 0.

## 5. Output streams

stdout (83 B): `QUALIFIED` / `READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY`. stderr was empty.

## 6–7. Adjudication receipt

`output/TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json`, 20,982 B. Independently recomputed SHA-256: **`5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b`**. Schema `JEPA_TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4`. It binds blinded receipt `e67aace8…` and package `0977c30f…`, and its fit-engine identity equals the identity bound in the phase-1 receipt.

## 8. Statuses as emitted

- `qualification.status` = `QUALIFIED`; `missing_requirements` = `[]`
- `gate_qualification`: gate `R_RELATIONAL_SUCCESSOR_TEST_OF_TEST_V2`, candidate `C2_RELATIONAL_SHARED`, `qualification_status` = `QUALIFIED`, `failure_scope` = `TEST_QUALIFICATION_ONLY`
  - executor `feebb8a3a779689617eae82c7f751a213af1b0326a88f8c4ee62fa72669dc5d7`
  - estimand `f9ac86510ce2fd07167cbc42ccfbe5a16b4f62a1e5a8775ecf45d4707515caa1`
  - decision rule `ddca01e1dbf87fceb138fe536dee286ae22c1e3a0dfffd6dbbbdd9d5fddc3d8a`
- `readiness.status` = `READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY`; `readiness.qualification_status` = `QUALIFIED`

| capability | semantic class (controller) | expected | observed | matched |
|---|---|---|---|---|
| REL_BROAD_MESO_POSITIVE | POSITIVE_TRUTH | PASS | PASS | true |
| REL_FINE_RECURRENT_POSITIVE | POSITIVE_TRUTH | PASS | PASS | true |
| REL_RARE_LOCAL_ISLAND_POSITIVE | POSITIVE_TRUTH | PASS | PASS | true |
| REL_MULTI_ISLAND_POSITIVE | POSITIVE_TRUTH | PASS | PASS | true |
| REL_DONOR_RESTRICTED_POSITIVE | POSITIVE_TRUTH | PASS | PASS | true |
| REL_SOURCE_VISIBILITY_STRESS | STRESS_TRUTH | PASS | PASS | true |
| REL_TECHNICAL_TWIN_NEGATIVE | NEGATIVE_TRUTH | FAIL | FAIL | true |
| REL_NULL_NEGATIVE | NEGATIVE_TRUTH | FAIL | FAIL | true |
| REL_UNDERPOWERED_POSITIVE | UNDERIDENTIFIED_TRUTH | NOT_ESTIMABLE | NOT_ESTIMABLE | true |

Rare-increment receipts are present for REL_DONOR_RESTRICTED_POSITIVE, REL_MULTI_ISLAND_POSITIVE, REL_RARE_LOCAL_ISLAND_POSITIVE and REL_TECHNICAL_TWIN_NEGATIVE.

## 9. Authority (all false)

- Receipt `authority`, `qualification.authority` and `readiness.authority`: real_execution, target_selection, td60, stage4 and training are all `false`.
- `gate_qualification.authority`: real_tournament, target_selection, td60, stage4 and training are all `false`.
- `readiness.real_execution_authorized` = `false`.

No authority exists anywhere in the receipt for representation selection, architecture/EMA selection, multimodal training, JEPA training or continuation.

## 10. Downstream execution

None. No real TD run, no target or representation selection, no TD60, no Stage 4, no EMA selection and no training. Phase 1 was not rerun. No adjudication rerun. Controller truth was not modified, and its files were not committed (hashes only).

## Scope note (from the packet's interpretation firewall)

This qualifies the TD test against sealed known truth. It does not select a human biological target.

STOP.

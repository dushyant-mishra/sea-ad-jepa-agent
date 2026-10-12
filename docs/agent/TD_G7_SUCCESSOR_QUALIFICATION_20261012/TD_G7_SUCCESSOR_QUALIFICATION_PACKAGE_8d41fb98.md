# TD G7 successor: qualification package for the external auditor

Date: 2026-10-12

Terminal: `TD_G7_SUCCESSOR_QUALIFIED_AT_8d41fb98__GLOBAL_ROW_AND_ACCEPTED_G6_BRIDGE__REAL_PREMARKER_GATE_PASS__NO_G7_RUN__NO_AUTHORITY_CREATED__EXTERNAL_AUDIT_REQUIRED`

This package is qualification only. G7 was not run. No G7 start marker, receipt or output exists. No owner
decision, runtime authorization or G7 operational authorization was created. G6 was not rerun. No H5AD expression
or count array was reread. None of TD56/57B/57C/59/TD60 or training was touched. `training_authorized=false`.

The failed pre-marker G7 evidence commit `9ab5421169971012f0c358bc3c714e6afcabfca2` is not modified.

## 1. Identities: two separate things

| identity | value |
|---|---|
| **Successor implementation commit** (qualified head; `code_identity` binds HEAD, so an owner decision must name exactly this) | `8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27` |
| branch | `fix/td-g7-global-row-and-g6-bridge-20261012` (branch point `ff4a21f9`) |
| successor G7 `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py` | `275dad00c6bd37ef11a34a376c703b4433ed40eae8d087c4d8f9535f88170412` (was `f8e52710…`) |
| common `scripts/v5/td_relational_value_read_v2_common.py` | `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`, **unchanged** |
| G6 `scripts/v5/materialize_td_relational_corrected_sampleA_v2.py` | `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`, **unchanged** |
| real gate `scripts/v5/qualify_td_g7_real_sample_a_premarker.py` | `4a2e2783f293a4060685ba0bf613f90f5a1a8f0ec3f43bba3b03021817801304` |
| **G6 producer (pinned in `ACCEPTED_G6_PREDECESSOR`, immutable)** | commit `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`; owner decision `3d457d4d…`; runtime authorization `28b3a0c8…`; common `23be96f8…`, G6 `8e6504e0…`, G7 `f8e52710…` |
| G6 external acceptance | `89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb` (`ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY`) |
| G6 artifacts | start `49bdff31…`, receipt `2edaa2d2…`, manifest `4fbc14ce…`, values `fdc13516…`, metadata `bd3a494b…` |

For every SHA above, the raw, LF-canonical and git-blob values are identical (`qualification_8d41fb98/QUAL_06_changed_files_and_hashes.txt`).

Commit chain:

| commit | role |
|---|---|
| `9a87cc8e` | RED |
| `8eef3c15` | GREEN |
| `04b6d1c0` | real gate and runner |
| `5f2532c6` | independent-review fixes |
| `8d41fb98` | runner RED-reason fix |

Changed files since `ff4a21f9`: 10 files, +1026/−13.

| status | file |
|---|---|
| M | `.gitattributes` (fixtures `-text`) |
| M | `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py` |
| A | `scripts/v5/qualify_td_g7_real_sample_a_premarker.py` |
| A | `docs/agent/TD_G7_SUCCESSOR_QUALIFICATION_20261012/qualification_runner.sh` |
| A | `tests/v5/fixtures/td_g7_successor/` (byte-exact `3d457d4d`, `28b3a0c8`, `89932183`) |
| M | `tests/v5/td_g6g7_synthetic_world.py` |
| M | `tests/v5/test_td_g7_g6_artifact_semantics.py` |
| A | `tests/v5/test_td_g7_successor_global_row_and_g6_bridge.py` |

## 2. What changed in G7

1. **Historical-row binding.** `select_sample_a()` now binds `global_row` exactly as the accepted G6 does:
   - It requires the same eight freeze columns.
   - When there is no physical `global_row` (the real freeze), `global_row` is the original freeze-file row position, assigned before filtering or sorting.
   - An explicit `global_row` must be unique, nonnegative integers.
2. **Accepted-predecessor bridge.** `load_accepted_g6_predecessor()` runs these checks, in order:
   1. The acceptance record must have exactly the pinned bytes and the accepted content, including disposition, producer commit, five artifact hashes, the PASS terminal and `g7_may_receive_fresh_operational_authority`. It must also carry no replay, target, TD60 or training authority.
   2. The namespace must hold exactly the five pinned files.
   3. The existing full G6 prerequisite runs against the producer's own authority trace. This covers linkage, coverage and structural validation of the values and metadata NPZ against the frozen Sample-A rows.
   4. The bytes validated must equal the pins. A byte-identical relocated copy is accepted, because provenance is content-addressed.
3. **Producer-code continuity.** `require_g6_producer_code_continuity()` requires that the successor's common and G6 are byte-identical to the producer's.
4. **`main()` wiring.**
   - The successor's own authority is unchanged: `bind_execution`, `expected_authority_trace`, and `common.load_runtime_authorization` bound to this HEAD and these code hashes.
   - A new `--g6-acceptance` argument is required.
   - The start marker and receipt record a `g6_predecessor` block next to the successor's own `authority_trace`.

## 3. Qualification results (canonical run, local evidence, not CI)

The run used a fresh detached worktree at `8d41fb98`, clean with no untracked files, on Windows with Python 3.9.7, numpy 1.24.2, pandas 1.5.3, h5py 3.2.1 and pytest 6.2.4. Logs are in `qualification_8d41fb98/` (source copies: `D:/jepa_td_real_g6_20261011/qualification_g7_successor_8d41fb98/`, SHA-256s in `SOURCE_SHA256.txt`). Runner exit: 0.

| check | result |
|---|---|
| full focused suite (13 existing G6/G7 files + successor file) | **250 passed** (219 existing + 31 new) |
| G7 global-row RED, from an archive of RED `9a87cc8e` (its G7 is `f8e52710`) | 4/4 fail with exact per-test reasons from JUnit: 2 × `KeyError: 'global_row'`, 2 × `DID NOT RAISE` |
| the same four tests, GREEN at head | **4 passed** |
| successor bridge and authority file | **31 passed** |
| real G7 pre-marker gate | **PASS** (below) |
| PR #259 real-receipt compatibility (`test_td_relational_pr259_real_receipt_compat.py`) | **1 passed** |
| accepted G6 namespace before = after | identical |
| G7 output directories under `D:/jepa_td_real_g6_20261011` | none |
| tracked owner decision or authorization binding `8d41fb98` | none |

**Real G7 pre-marker gate** (`QUAL_04_real_g7_premarker_gate.json`):
- **Freeze.** The authenticated freeze `79eb005c…` (50,000 rows) has **no physical `global_row`**. G7's own selector derives `global_row` 0..24999 for 25,000 Sample-A rows (HVS 1,129, NPH52 1,310, SEA_AD 22,561), identical to the accepted G6 selector on all 8 columns.
- **Inputs.** G7's own `load_inputs` runs with every pinned real metadata input: replay `4bde5f80…` (9,216 addresses), provenance `df0cb60f…`, collision ledger `f6909f81…`, Macha freeze `240b2b71…`.
- **Code continuity** holds at the clean committed tree.
- **Bridge.** G7's `load_accepted_g6_predecessor` on the real `G6_OUT_ff4a21f9` namespace and acceptance `89932183` gives `PASS_TD_G6_SOURCE_LIBRARY_EXACT`. All five bytes match the pins, and the NPZ structure is validated against the real Sample-A rows.
- **Negative probes:**
  - **N1.** Old authority `28b3a0c8`/`3d457d4d`, with the real PR #259 receipts and the successor code, is refused: "owner-decision qualified implementation commit does not match the executing code".
  - **N2.** The `G6_OUT_fafd4309` namespace (start marker only) is refused.
  - **N3.** The old G7 (`f8e52710`) on the same freeze and the accepted metadata reproduces the real failure: `AttributeError: 'DataFrame' object has no attribute 'global_row'`.
  - **N4.** The spent G7 operational authorization `19a50126` binds `ff4a21f9`/`f8e52710` and cannot release the successor.
- **No side effects.** h5py was never imported, and no marker or authority was created.
- **Not exercised:** the one pre-marker step not covered is `bind_execution()`, because it needs the owner's fresh successor authority.

**Superseded run, preserved** (`superseded_runner_failure_5f2532c6/`). The first canonical run at `5f2532c6` exited 1 on the runner's own RED-reason rule only; every other check passed.
- The RED failures had exactly the expected reasons.
- The rule grepped for a " - reason" suffix that pytest 6.2.4 does not print on summary lines. The pattern had not been checked against real output.
- Fix (`8d41fb98`, runner only): the reasons are now read per test from JUnit, which is stricter.

## 4. Independent review (read-only subagent, on `04b6d1c0`): VERDICT CONCERN, no blocker

**Confirmed by the reviewer:**
- common and G6 are byte-identical to the producer;
- every pin matches the fixtures and the real namespace (sha256sum only);
- the producer trace equals the real G6 receipt, manifest and marker traces;
- the check order before the marker is correct;
- the old authority cannot release the successor;
- no existing test lost coverage;
- the corrected "another historical G6 receipt" test is honest and sufficient. Its RED version produced a byte-identical deterministic duplicate, which the bridge correctly accepted. The fix runs the second G6 under its own owner decision and authorization.

**Fixed in `5f2532c6`:**
- **Distinct authorities had never been exercised.** Two tests were added:
  - G7 runs under its own commit `b*40` with a fresh synthetic authority while the producer stays `a*40`.
  - The producer authority cannot run successor code.
- **Mutation check.** Rewiring `main()` to the ff4a21f9 design, which validates G6 against the successor trace, leaves the shared-gate tests green and fails the new test.
- **Runner hardened:**
  - the RED tree must hold G7 `f8e52710`, and the RED failure reasons are checked;
  - untracked files are refused;
  - an authority scan checks that nothing binds the head.
- **Gate docstring corrected:** N3 writes a temporary directory.

## 5. Decisions and residuals for the auditor (not changed here)

- **R1. Successor authority scope (decision needed).** Under the unchanged V2 schema (`AUTHORIZE_G6_G7_INTEGRITY_ONLY`; token `…VALUE_MATERIALIZATION…`), a fresh owner decision and runtime authorization for `8d41fb98` would also satisfy G6's `bind_execution`. So it would permit a G6 rerun at the successor commit, which rereads real H5AD.
  - The bridge would refuse any such output, and nothing else consumes G6 output. But the scope leak is not code-enforced, and closing it needs a common or G6 change, which this task forbids.
  - Options:
    - (a) procedure only: create the authority just in time, and have the launcher invoke only G7;
    - (b) a G7-side requirement that the successor owner decision and authorization carry `"g6_execution_authorized": false`. Common already tolerates such keys. This makes the scope explicit but does not stop G6.
  - Pre-existing: `28b3a0c8` can still rerun G6 at `ff4a21f9`.
- **R2. Checks after the marker.** G7 still runs these after its marker:
  - the G1b git load;
  - S174 cache hash verification;
  - the matrix → stem → shard join.
  - The real gate does not cover them. The previous launcher's pre-start step 8 did, and passed: 35 shards, 34 matrices. A successor launcher must repeat it.
- **R3. Launcher inputs.**
  - Add `--g6-acceptance`, materialized from its immutable commit `17a68667` (bytes `89932183`, identical to the test fixture).
  - Keep `--g6-receipt D:/jepa_td_real_g6_20261011/G6_OUT_ff4a21f9/G6_RECEIPT.json`.
  - Use a fresh output directory.
- **R4. Explicit `global_row` truncation.** An explicit value of `"1.5"` would be silently truncated to 1, identically in G6. The real freeze never takes this path.
- **R5. Small hardening items.**
  - `begin_g7_attempt(g6_predecessor=None)` is optional, though `main()` always passes it and a test asserts it reaches the marker.
  - There is a small time-of-check/time-of-use window between pin hashing and the JSON reread inside the existing prerequisite.

## 6. What a G7 run at this successor would need (not created; owner and auditor decision)

1. An owner decision whose `qualified_implementation_commit_sha` is `8d41fb98…`.
2. A runtime authorization bound to that decision and to code identity common `23be96f8`, G6 `8e6504e0`, G7 `275dad00`, and commit `8d41fb98`.
3. A G7 operational authorization, plus the R1 scope decision.
4. A launcher that repeats the R2 pre-start check and passes R3's arguments.

STOP. Returned to the external auditor.

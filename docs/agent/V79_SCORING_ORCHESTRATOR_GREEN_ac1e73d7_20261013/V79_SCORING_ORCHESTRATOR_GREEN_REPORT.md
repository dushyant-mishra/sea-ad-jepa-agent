# V79 V2_CORE physical scoring orchestrator — GREEN, awaiting fresh scoring authorization

**Terminal:** `ORCHESTRATOR_GREEN_AT_ac1e73d7__NO_SCORING_RUN__NO_TRUTH_OPENED__FRESH_AUTHORIZATION_REQUIRED__STOP`

**Head to authorize:** `ac1e73d79489438634aaeeca035d229875f3186a`. Branch `feat/v79-v2-core-scoring-orchestrator-tdd-20261013`, built on scorer head `d4e10c82`. No PR has been opened (see §9).

Packaging note: this report was assembled after the runs. The logs, JUnit XML and mutation JSON under `record/` are the bytes the runs wrote, and `tool/` holds the exact mutation runner.

## 1. Commits since `d4e10c82`

| commit | content |
|---|---|
| `d4ac75bd` | RED suite (38 tests) and synthetic universe |
| `a00cfd62` | custody tightening in `v79_v2_core_score_authority.py`; V2 run receipt in `run_v79_v2_core_scoring.py` |
| `54a64362` | new `scripts/v79/run_v79_v2_core_scoring_orchestrator.py` |
| `08848fa9` | unit tests aligned to the frozen campaign binding; TOCTOU test |
| `add80e28`, `107bd7c5` | synthetic-only CI workflow; the scorer workflow extended to the orchestrator |
| `97146378` | CLI refuses unless the executing code is loaded from the authorized checkout |
| `ac1e73d7` | every failure-mode test names the exact refusing step |

**Unchanged (blob-identical to `d4e10c82`):**
- every scoring primitive: `v79_v2_core_score.py`, `_score_truth`, `_score_quantities`, `_score_evaluate`, `_score_descriptive`, `_score_oracle`;
- `v79_v2_core_fit_surface.py`, `v79_v2_core_qualification_custody.py`, `run_v79_v2_core_qualification.py`, `v79_v2_core_launch.py`;
- all of `results/`, including the contract and the realization package.

No statistical model, gate, estimand, threshold, prior, convergence rule or world construction was changed.

## 2. Frozen input bindings (full values, recovered from durable evidence)

| identity | value | source |
|---|---|---|
| campaign receipt | `a0065925789c58409a85ccbf72d24f5c7b1be142a4d17eddc434babdf0d0e340` | `445f61bf` receipts/ and local result dir |
| campaign code head | `a61437ba284e9e75b0557157ad68e56eacd8f8fe` | campaign receipt `code_sha` |
| custody receipt | `c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63` | campaign receipt; `record/CUSTODY_RECEIPT_SHA256.txt` |
| result-file ledger | `d467bb9b51336278ee46566173148a4f112eaa79cf578b8bbfae502cb4388b89` (2,113 files) | `445f61bf` (both copies) and local `record/continuation/` |
| Contract V2 | `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26` | `results/v79/v2_core_qualification/` |
| root manifest | `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de` | realization package (hashed, never parsed) |
| blinded index | `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40` | realization package and fit custody |
| realization audit receipt | `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3` | `results/v79/v2_core_realization_audit_freeze_v1/` |
| realization ledger | `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65` (498 files = 3 top-level + 145 blinded + 350 truth) | realization receipt `complete_ledger_sha256` |
| world-set directory digest | `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286` | realization receipt |
| committed package | 366 files | realization receipt |
| NOT_DIAGNOSED fits | `09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6`, `6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43`, `ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5` (opaque world `ee384a29a9fc`) | `final_diagnosis` in the hash-verified fit records |

**Production linkage pre-checked with paths and hashes only.** No truth file was read or hashed.
- The fit-custody `blinded_fit_inputs` is exactly the 145 blinded ledger entries, with 0 hash mismatches.
- The committed package is exactly 366 files, with 0 non-truth mismatches.

**Identities that were only syntactically validated are now equality-checked:**
- `load_completed_campaign`: the expected receipt, `code_sha` and the custody receipt;
- `validate_scoring_authorization` and `build_adjudication_receipt`: the campaign receipt;
- the result ledger, realization ledger and digest, and the custody executor head (orchestrator);
- after the barrier, truth-manifest `blinded_fit_manifest_sha256`, `pairing_amendment_sha256` and `generator_bundle_sha256` against the blinded index.

Other truth-manifest fields are fixed transitively by the byte-level ledger binding. `scorer_code_sha` remains a runtime value: it is bound by the authorization and by the CLI's clean-HEAD and executing-code checks.

## 3. Orchestrator behaviour

**Authentication, in frozen order.** Each step is recorded by a `TruthBarrier`, which refuses an out-of-order step:
1. `output_guard`: output must not exist and must not sit inside any input authority; it is created exclusively.
2. `authorization`
3. `contract`: `require_launch_authority` and `gate_authority`.
4. `campaign_receipt`
5. `result_ledger`: exact 2,113-file set, with sizes and hashes.
6. `custody`: executor head = `a61437ba`.
7. `fit_identity_set`: campaign IDs equal the independently derived 1,056-fit queue, in order.
8. `fit_records`: hash-first, plus the campaign runner's own per-record validator with frozen seeds and code head.
9. `campaign_reconstruction`: the campaign receipt equals the deterministic rebuild.
10. `not_diagnosed_set`: exactly the 3 frozen IDs; everything else `COMPLETE`.
11. `realization_authority`: receipt, ledger, digest, partition, and the committed non-truth bytes.
12. `blinded_inputs`
13. `truth_tree`: all 350 truth files, hash-only, against the ledger.

**Truth-open-last barrier (executable).**
- From the start of the run until the barrier is crossed, a process audit hook refuses every `open()` under `package/controller_truth/` and of the unblinded root manifest. The only exception is `hash_only_sha256`.
- `load_truth_after_barrier` refuses unless the barrier was crossed after all 13 steps.

**After the barrier:**
- truth is loaded with `load_truth_set`, and a truth ↔ blinded cross-identity check follows;
- every one of the 1,056 fits is scored in queue order through `score_gene_quantities`;
- all 292 gates are evaluated and bound with the frozen first-hard-fail and LIMIT semantics;
- the held-out oracle runs for every fit;
- the five descriptive families and the adjudication are computed;
- invariants: the scored NOT_DIAGNOSED set must equal the frozen set; the failing convergence gates must be exactly the world/part groups holding those fits; and their summed `not_diagnosed_count` must be 3.

**Outputs.** Every output is written with exclusive create (`open(..., "xb")`):
- `V79_V2_CORE_SCORED_ROWS_V1.json`
- `V79_V2_CORE_GATE_SCORE_TABLE_V1.json`
- `V79_V2_CORE_HELDOUT_ORACLE_SET_V1.json`
- `V79_V2_CORE_DESCRIPTIVE_METRICS_V1.json`
- `V79_V2_CORE_QUALIFICATION_ADJUDICATION_V1.json`

Every input is then re-verified. Only after that is `V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2.json` written. The receipt carries:
- all input identities, the scorer head and the authorization SHA;
- the ordered authentication steps and the five output hashes;
- `qualification_scoring_run=true`, `real_train_posterior_authorized=false`, `factorial_science_authorized=false`, `training_authorized=false`.

**Failure handling.** Any custody refusal is reported as `REFUSED V2_CORE scoring orchestrator at <step>: …`, and no receipt exists.

## 4. Proof of truth-open-last

1. **Unit:**
   - the guard blocks `read_bytes` and `np.load` of a protected file while armed, allows only the hash-only reader, and stops blocking once disarmed;
   - the barrier refuses an out-of-order step, an incomplete crossing, and a truth load before crossing.
2. **Executable:** an authentication-phase bug that calls `np.load` on a truth file (injected into the custody step) is blocked by the hook. The run raises `TruthBarrierRefused` and no receipt exists.
3. **Sentinel:** every pre-truth failure test spies on `load_truth_set`, `load_truth_world` and `TruthWorld.load`, and asserts **zero** truth-loader calls.
4. **Complete run:** every truth-loader call is recorded with the barrier already crossed. The receipt records all 13 steps and `barrier_crossed_after_all_steps=true`.
5. **Mutation (§6):** disabling the guard, or letting the loader ignore the barrier, is detected.

## 5. NOT_DIAGNOSED frozen treatment

**Contract text:**
- `inference.recovery_path.otherwise`: "NOT_DIAGNOSED -> the world fails CONVERGENCE_ALL_FITS_DIAGNOSED".
- That gate is RULE/FAIL for all 24 world/parts.
- `terminal_logic.terminal_lock`: the first FAIL-class failure locks the terminal at `V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED`.

**Consequence (factual, not an interpretation).** With the 3 frozen NOT_DIAGNOSED fits, the scoring terminal is already determined by fit-side data to be `NOT_QUALIFIED`. Scoring will establish:
- which gate is the first hard fail (it may be in an earlier world);
- the post-terminal diagnostic map;
- the descriptive families.

**Tests:**
- Dropped, reclassified (either direction) and refit cases each refuse at their exact step.
- The complete synthetic run preserves the three fits verbatim and fails exactly their world/part convergence gate with `not_diagnosed_count=3`.
- The three real full IDs are pinned as frozen constants.

## 6. Test evidence

| evidence | where | result |
|---|---|---|
| RED, pre-commit working tree, `sea-ad-jepa-v3` py3.11.15 | local | 38 failed for expected reasons (`record/RED_precommit.xml`): 32 module missing, 3 constants missing, 1 tightened check absent, 1 V2 receipt API absent, 1 trust-domain test (corrected then re-run RED: orchestrator file absent) |
| full V2_CORE suite at `ac1e73d7`, `v79-bayes` py3.11.17 (frozen V79 environment: jax 0.4.35, numpyro 0.15.3, numpy 2.0.2) | local, clean detached worktree, 0 status lines before/after | **252 passed** (`record/FINAL_LOCAL_SUITE_ac1e73d7.*`) |
| `v79-v2-core-scoring-orchestrator-synthetic.yml` run `38482198047` @ `ac1e73d7` | **CI** | success. Windows: 126 passed. Ubuntu: 125 passed, 1 deselected (`test_builder_regenerates_final_and_draft_byte_for_byte`, Windows-only as in the scorer workflow). Orchestrator 40/40 on both. Trust-domain audit PASS. |
| mutation pass 1 @ `add80e28` | local | 11/12 killed; `fit_identity_set_removed` **survived** because the test accepted any of three steps. Fixed in `ac1e73d7` by naming the exact step in every test. |
| mutation pass 2 @ `ac1e73d7`, 13 mutations | local | **13/13 killed** (`record/MUTATION_RUN_ac1e73d7.log`, `record/MUTATION_RESULTS_ac1e73d7.json`; runner SHA `b437b56b…`) |

**Excluded from all local runs** (they read real truth or unblinding content; not run by Macha):
- `test_v79_v2_core_score_truth.py`
- `test_v79_v2_core_score_quantities.py`
- `test_v79_v2_core_realization_audit_freeze.py`
- `test_v79_v2_core_seed_ledger.py`

Two tests were added during GREEN after self-review:
- `test_input_changed_during_scoring_prevents_the_final_receipt`
- `test_cli_refuses_when_executing_code_is_not_the_authorized_checkout`

Both are verified to fail with their safeguard removed.

## 7. Custody disclosure

The earlier `git grep -l` event is classified `NON_CONTENT_PATH_NAME_EXPOSURE__NO_TRUTH_VALUE_EXPOSURE`. See `V79_SCORING_CUSTODY_DISCLOSURE_20261013.md`.

## 8. Fresh authorization required

The existing authorization (`6beedf51…`, bound to `d4e10c82`) remains **valid but unused**. It cannot be used here: it binds a different scorer head, and the orchestrator refuses it.

**Requested:**
- a controller scoring authorization, schema `V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_V1` (unchanged), bound to scorer head **`ac1e73d79489438634aaeeca035d229875f3186a`**;
- `AUTHORIZATION_TEMPLATE_ac1e73d7.json` holds the exact canonical bytes the orchestrator accepts (762 B, SHA-256 `4793d8f9024891a6572337246c76dea871b65ebde476d8f3983c483498b80337`);
- the template differs from the original only in `scorer_code_sha`. It is a template; it carries no authority until the controller issues it.

**Invocation after authorization (not run).** Run it from a clean detached checkout of `ac1e73d7` with the `v79-bayes` interpreter:

```
python scripts/v79/run_v79_v2_core_scoring_orchestrator.py \
  --repo-root <clean checkout of ac1e73d7> \
  --campaign-result-dir D:/jepa_v79_qualification_world1_a61437ba/result \
  --result-ledger D:/jepa_v79_qualification_world1_a61437ba/record/continuation/RESULT_FILE_LEDGER_SHA256.txt \
  --custody-dir D:/jepa_v79_qualification_world1_a61437ba/fit_custody \
  --authorization <issued authorization path outside the checkout> \
  --authorization-sha256 <issued authorization SHA-256> \
  --output-dir <new, nonexistent directory outside every input>
```

## 9. Controller decisions requested

1. **PR/CI policy.** Opening a PR on scorer files triggers the existing `v79-v2-core-controller-scorer.yml`. By its pre-existing design, it runs `score_truth`, `score_quantities` and `realization_audit_freeze`, which load committed real truth. Decide whether that is acceptable before a PR is opened; the branch is currently pushed without a PR.
2. **Optional pre-barrier dry run.** You may first want to run steps 1–12 against the real campaign inputs. That would hash the root manifest only and read no truth bytes, and it would rule out a mechanical defect of the kind that consumed the first TD phase-2 authorization. It needs either a narrow authorization or an explicit preflight mode; neither exists yet.

STOP. No scoring was run. No controller truth was opened or hashed by this work, and no downstream authority was exercised.

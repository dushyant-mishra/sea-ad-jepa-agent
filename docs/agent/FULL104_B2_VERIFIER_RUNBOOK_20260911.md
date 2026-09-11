# FULL104 / B2 Production Verifier Runbook — 2026-09-11

Status: `GPU_LAPTOP_RECEIPT_OR_VERIFIER_RUNBOOK__NO_TRAINING_AUTHORITY`

## Purpose

Use this runbook only on the GPU-enabled laptop / attached hard-drive environment where the >30GB FULL104 / Phase2 substrate is available. Do not attempt to upload the full substrate into the ChatGPT environment.

The task is **receipt-first production expression closure**, not dataset rediscovery and not training.

## Frozen verifier lineage to inspect first

Repository:

`dushyant-mishra/sea-ad-jepa-agent`

Verifier lineage used for this runbook:

`planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

Production verifier:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Regression test:

`tests/test_bind_full104_expression_blocks_v4.py`

Do not substitute the older `build_full_reader_expression_identity_closure_v3.py` to certify FULL104 from TRAIN-row space.

## Exact production constants in the verifier

The V4 binder hard-codes the following production authority values:

- block-manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- materialization-contract SHA-256: `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`
- materialization-audit SHA-256: `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`
- selection SHA-256: `edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b`
- selection-manifest SHA-256: `3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e`
- cells: `4,553,407`
- donors: `104`
- operators: `42`
- matrices: `42`
- blocks: `8,915`
- addresses: `41,238`
- sources: `HVS`, `NPH52`, `SEA_AD`
- block rows: `512`
- sample level: `4`
- partition: `reader_fit`

The full-reader metadata SQLite SHA-256 is intentionally supplied at runtime through `--expected-metadata-sha256`; **do not guess it**. Recover it from the already-authenticated full-reader metadata receipt / lineage on the GPU laptop and verify the file independently before invoking the binder.

## Expected contract semantics

The binder requires the materialization contract and audit to report schema:

`full104-phase2-expression-materialization-v1`

and status:

`PASS_PHASE2_EXPRESSION_MATERIALIZED`

It also requires:

- raw integer counts + full-source library with downstream `log1p(raw*10000/library)` applied exactly once;
- identity used as audit metadata, not model input;
- original mixed NPH denied;
- no validation/oracle/DEV/SEALED/pathology access;
- no optimizer/EMA/lambda/query-schedule/GPU-mechanics/training authority;
- corresponding audit flags all false.

Do not edit a contract or audit to make hashes/semantics fit. A mismatch is a STOP.

## Step 1 — receipt-first search

Before running anything heavy, search the hard-drive project/evidence locations for an already-produced receipt whose JSON status is exactly:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

If found, authenticate it against the exact V4 inputs and constants above. Do not accept a prose mention of the PASS terminal as the receipt itself.

If no authentic receipt exists, continue below.

## Step 2 — checkout and verify the verifier

Use an isolated clean checkout/worktree at the exact lineage first:

```bash
git fetch origin --prune
git worktree add ../jepa-full104-bind-verify 1de20b1c222c7fb27fcef5ec1a4b798d5b26a534
cd ../jepa-full104-bind-verify
python -m py_compile scripts/v5_anticheat/bind_full104_expression_blocks_v4.py
python -m pytest -q tests/test_bind_full104_expression_blocks_v4.py
```

Expected: compile PASS and regression test PASS with zero skipped. A test PASS is mechanics/guard evidence only; it does not itself close FULL104.

## Step 3 — identify the exact hard-drive inputs

Set paths only after locating and hashing the real artifacts:

```bash
BLOCK_MANIFEST=/absolute/path/to/the/8915-block/manifest.csv
MATERIALIZATION_CONTRACT=/absolute/path/to/materialization_contract.json
MATERIALIZATION_AUDIT=/absolute/path/to/materialization_audit.json
BLOCK_ROOT=/absolute/path/to/full104/phase2/expression/root
METADATA_SQLITE=/absolute/path/to/authenticated/full_reader_metadata.sqlite
EXPECTED_METADATA_SHA256=<from-authenticated-full-reader-metadata-receipt>
SCRATCH_DIR=/absolute/path/to/fast/local/scratch
OUTPUT=/absolute/path/to/FULL104_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE_RECEIPT.json
```

Before invocation:

```bash
sha256sum "$BLOCK_MANIFEST" "$MATERIALIZATION_CONTRACT" "$MATERIALIZATION_AUDIT" "$METADATA_SQLITE"
```

Required first three hashes are exactly the constants above. The metadata SQLite must match the separately authenticated runtime value supplied to the verifier.

## Step 4 — run the exact V4 binder

```bash
python scripts/v5_anticheat/bind_full104_expression_blocks_v4.py \
  --block-manifest "$BLOCK_MANIFEST" \
  --materialization-contract "$MATERIALIZATION_CONTRACT" \
  --materialization-audit "$MATERIALIZATION_AUDIT" \
  --block-root "$BLOCK_ROOT" \
  --metadata-sqlite "$METADATA_SQLITE" \
  --expected-metadata-sha256 "$EXPECTED_METADATA_SHA256" \
  --scratch-dir "$SCRATCH_DIR" \
  --output "$OUTPUT"
```

The scratch directory should be on fast storage with sufficient free space for the temporary SQLite identity cross-check.

## Step 5 — accept only the exact production terminal

The receipt must report:

```text
schema = JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4
status = PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE
cells = 4553407
donors = 104
operators = 42
matrices = 42
blocks = 8915
addresses = 41238
cross_ledger_identity_mismatches = 0
cross_ledger_missing_cells = 0
test_fixture_mode = false
synthetic_data_used = false
pathology_used = false
checkpoint_outcomes_used = false
training_authorized = false
```

Then hash the receipt itself and preserve the exact command line, verifier commit SHA, input hashes, output hash, host/runtime metadata, and stdout/stderr.

## Important fail-closed behavior

Examples of STOP classes enforced by the V4 binder include:

- block-manifest SHA mismatch;
- materialization-contract SHA mismatch;
- materialization-audit SHA mismatch;
- metadata SQLite SHA mismatch;
- contract/audit schema or semantics mismatch;
- geometry mismatch;
- selection binding mismatch;
- normalization semantics mismatch;
- access-firewall mismatch;
- block manifest row/cell/operator/matrix/source/NNZ mismatch;
- missing block files;
- block file hash mismatch;
- malformed or non-positive block metadata values;
- duplicate selection row or canonical cell ID;
- incomplete selection-row closure;
- cross-ledger cell/source/donor/matrix/operator identity mismatch.

On any STOP, preserve the exact error and do not patch around it in the production run.

## Red-team notes

- A 4,726-row corrected TRAIN cache cannot satisfy this verifier.
- A 50K subset cannot satisfy this verifier.
- A synthetic fixture cannot satisfy this verifier; production output must have `test_fixture_mode=false` and `synthetic_data_used=false`.
- A PASS from the test file is not production closure.
- A prose report containing `4553407`, `8915`, or `FULL104` is not a production receipt.
- Do not use validation/oracle/DEV/SEALED/pathology data to resolve a missing materialization input.
- Do not change the hard-coded production constants merely to fit a different artifact.

## What to return to the project

Return only review-safe evidence, not the >30GB substrate:

1. exact branch/commit used;
2. verifier SHA-256 or Git blob identity;
3. exact command;
4. hashes of the three fixed authority inputs plus metadata SQLite;
5. output receipt JSON;
6. output receipt SHA-256;
7. test pass/skip count;
8. exact PASS terminal or exact STOP terminal;
9. confirmation that no protected source or training path was opened.

## Authority boundary

Even a valid FULL104 expression closure receipt closes only the expression block/identity substrate blocker. It does **not** by itself authorize S0-S4, fresh confirmation, V21 freeze, V5 training, optimizer steps, EMA updates, or production training checkpoints.

Terminal for this runbook remains:

`FULL104_RECEIPT_OR_EXACT_STOP_ONLY__NO_TRAINING_AUTHORITY`

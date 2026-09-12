# V5 FULL104 current-byte rebind work order — 2026-09-12

Status: `READY_TO_RUN_ON_MACHINE_HOLDING_FULL104__NO_TRAINING_AUTHORITY`

## Goal

Produce one compact, content-addressable receipt proving that the exact current FULL104 reader-fit expression blocks and identity ledger close on the machine that actually holds the >30 GB substrate.

This is **not** training. It opens no protected partition, pathology, checkpoint outcome, reader-validation or reader-oracle data.

## Exact producer

Use only:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

from the exact V5 branch/head being qualified. Before execution, record:

```bash
git rev-parse HEAD
git status --short
sha256sum scripts/v5_anticheat/bind_full104_expression_blocks_v4.py
```

Do not substitute a synthetic fixture, a corrected TRAIN cache, the historical 20,804-row T0 substrate, or a filtered block manifest.

## Inputs required

The command requires the physical paths to:

- complete block manifest;
- Phase2 materialization contract;
- Phase2 materialization audit;
- root directory containing all materialized block payloads and metadata sidecars;
- authoritative metadata SQLite;
- externally known SHA-256 of that metadata SQLite;
- scratch directory with enough space for the temporary identity-check SQLite;
- output JSON path.

The producer itself binds the following immutable expected identities/geometry:

- block manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- materialization contract SHA-256 `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`
- materialization audit SHA-256 `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`
- selection SHA-256 `edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b`
- selection-manifest SHA-256 `3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e`
- 4,553,407 cells
- 104 donors
- 42 operators
- 42 matrices
- 8,915 blocks
- 41,238 addresses
- HVS / NPH52 / SEA_AD
- block row target 512
- sample level 4
- partition `reader_fit`.

## Command template

Replace only the filesystem placeholders and metadata SQLite SHA. Do not change scientific/geometry constants in the producer.

```bash
python scripts/v5_anticheat/bind_full104_expression_blocks_v4.py \
  --block-manifest "/ABS/PATH/TO/block_manifest.csv" \
  --materialization-contract "/ABS/PATH/TO/materialization_contract.json" \
  --materialization-audit "/ABS/PATH/TO/materialization_audit.json" \
  --block-root "/ABS/PATH/TO/block_root" \
  --metadata-sqlite "/ABS/PATH/TO/foundation_metadata.sqlite" \
  --expected-metadata-sha256 "<64-HEX-SHA256>" \
  --scratch-dir "/ABS/PATH/TO/scratch" \
  --output "/ABS/PATH/TO/V5_FULL104_CURRENT_BYTE_BINDING.json"
```

## Required successful receipt

The output must contain exactly the production terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

and must also show:

- `cells = 4553407`
- `donors = 104`
- `operators = 42`
- `matrices = 42`
- `blocks = 8915`
- `addresses = 41238`
- `cross_ledger_identity_mismatches = 0`
- `cross_ledger_missing_cells = 0`
- `test_fixture_mode = false`
- `synthetic_data_used = false`
- `pathology_used = false`
- `checkpoint_outcomes_used = false`
- `training_authorized = false`.

Any STOP is evidence and must be preserved; do not patch around a mismatch on the data machine.

## Return package

Only a compact package is needed back in GitHub/chat:

1. `V5_FULL104_CURRENT_BYTE_BINDING.json`
2. `sha256sum` of that JSON
3. exact Git commit SHA used
4. exact producer source SHA-256
5. metadata SQLite SHA-256 supplied to the command
6. stdout/stderr transcript
7. `git status --short` before and after

Do **not** upload the >30 GB block substrate.

## What happens after PASS

A PASS closes only the physical-byte/identity prerequisite. The next stage is to instantiate and validate a V5 FULL104 execution-plan receipt under `scripts/v5_anticheat/validate_full104_execution_plan_v1.py`, then obtain a separate explicit bounded qualification-run authority before any learned FULL104 run.

No production training, TD60, relational-target activation, pathology, reader-validation or reader-oracle access is granted by this work order.

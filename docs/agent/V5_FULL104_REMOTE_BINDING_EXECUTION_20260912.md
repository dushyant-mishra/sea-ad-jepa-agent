# V5 FULL104 remote binding execution — 2026-09-12

Status: `REMOTE_EXECUTION_CONTRACT__FULL104_PHYSICAL_STORE_REQUIRED__NO_TRAINING_AUTHORITY`

This is the exact remote/GPU-laptop procedure for closing the physical FULL104 reader-fit expression substrate. It does not authorize training, dimensions, TD60, or protected-data access.

## Required repository branch

Use the exact reviewed successor lineage:

`planning/v5-dataset-first-production-closure-20260912`

Before execution:

```bash
git fetch origin --prune
git checkout planning/v5-dataset-first-production-closure-20260912
git pull --ff-only
git rev-parse HEAD
```

Record the returned HEAD in the receipt. Do not run from uncommitted source modifications.

## Immutable FULL104 expectations

- reader-fit cells: `4,553,407`
- donors: `104`
- operators / matrices: `42 / 42`
- Level-4 blocks: `8,915`
- addresses: `41,238`
- nominal block rows: `512`
- sample level: `4`
- sources: `HVS`, `NPH52`, `SEA_AD`

Frozen parent hashes:

```text
block manifest              66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
materialization contract    612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17
materialization audit       9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf
selection                   edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b
selection manifest          3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e
metadata SQLite             a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913
```

The committed historical block manifest is:

`docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv`

The historical materialization manifest records the physical parents as:

```text
outputs/full104_v014_20260826/03_phase2_state_derivation_v1/_staging_expression_level4/MATERIALIZATION_CONTRACT.json
outputs/full104_v014_20260826/03_phase2_state_derivation_v1/_staging_expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json
```

The historical Level-4 block root is:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

## Metadata location rule

The metadata SQLite location is machine-specific. Set `FULL104_METADATA_SQLITE` to the physical file whose SHA-256 is exactly:

`a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Do not infer authority from a filename. Verify the bytes first:

```bash
sha256sum "$FULL104_METADATA_SQLITE"
```

If the file is absent or the digest differs, STOP. Do not rebuild, substitute, or use a smaller cache under this contract.

## Exact preflight

```bash
set -euo pipefail

BLOCK_ROOT='outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'
STAGING='outputs/full104_v014_20260826/03_phase2_state_derivation_v1/_staging_expression_level4'
BLOCK_MANIFEST='docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv'
OUT_DIR='outputs/v5_full104_binding_20260912'

: "${FULL104_METADATA_SQLITE:?set FULL104_METADATA_SQLITE to the authenticated metadata SQLite}"

test -d "$BLOCK_ROOT"
test -f "$BLOCK_MANIFEST"
test -f "$STAGING/MATERIALIZATION_CONTRACT.json"
test -f "$STAGING/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"
test -f "$FULL104_METADATA_SQLITE"

printf '%s  %s\n' '66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29' "$BLOCK_MANIFEST" | sha256sum -c -
printf '%s  %s\n' '612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17' "$STAGING/MATERIALIZATION_CONTRACT.json" | sha256sum -c -
printf '%s  %s\n' '9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf' "$STAGING/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json" | sha256sum -c -
printf '%s  %s\n' 'a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913' "$FULL104_METADATA_SQLITE" | sha256sum -c -

mkdir -p "$OUT_DIR"
```

Any failure above is the terminal for this attempt. Do not continue to the binder.

## Exact binder invocation

```bash
PYTHONPATH=src:. python scripts/v5_anticheat/bind_full104_expression_blocks_v4.py \
  --block-manifest "$BLOCK_MANIFEST" \
  --materialization-contract "$STAGING/MATERIALIZATION_CONTRACT.json" \
  --materialization-audit "$STAGING/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json" \
  --block-root "$BLOCK_ROOT" \
  --metadata-sqlite "$FULL104_METADATA_SQLITE" \
  --expected-metadata-sha256 a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913 \
  --scratch-dir "$OUT_DIR/scratch" \
  --output "$OUT_DIR/V5_FULL104_EXPRESSION_BLOCK_BINDING_V4.json"
```

The only accepted production terminal is:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

A fixture-mode result, synthetic result, TRAIN-cache result, 50K result, recomputed different-byte store, validation/oracle data, DEV, SEALED, or pathology data cannot satisfy this terminal.

## Seal the exact dimension-input artifact

Only after the real binder PASS:

```bash
PYTHONPATH=src:. python - <<'PY'
import json
from pathlib import Path
from sea_ad_jepa.v5.full104_dimension_interface_v1 import seal_full104_dimension_input

out_dir = Path('outputs/v5_full104_binding_20260912')
receipt_path = out_dir / 'V5_FULL104_EXPRESSION_BLOCK_BINDING_V4.json'
sealed_path = out_dir / 'V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json'
receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
sealed = seal_full104_dimension_input(receipt)
sealed_path.write_text(json.dumps(sealed, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(sealed['artifact_sha256'])
PY
```

The sealing function independently rejects fixture/synthetic receipts and binds the projected FULL104 payload to the exact block-manifest, materialization-contract, materialization-audit, metadata-SQLite, selection, and selection-manifest hashes.

## Compact return receipt

Do **not** upload or duplicate the >30 GB block store. Return only:

```bash
git rev-parse HEAD
sha256sum scripts/v5_anticheat/bind_full104_expression_blocks_v4.py
sha256sum src/sea_ad_jepa/v5/full104_dimension_interface_v1.py
sha256sum "$OUT_DIR/V5_FULL104_EXPRESSION_BLOCK_BINDING_V4.json"
sha256sum "$OUT_DIR/V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json"
python - <<'PY'
import json
from pathlib import Path
p = Path('outputs/v5_full104_binding_20260912')
r = json.loads((p/'V5_FULL104_EXPRESSION_BLOCK_BINDING_V4.json').read_text())
s = json.loads((p/'V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json').read_text())
print({
    'terminal': r.get('status'),
    'cells': r.get('cells'),
    'donors': r.get('donors'),
    'operators': r.get('operators'),
    'matrices': r.get('matrices'),
    'blocks': r.get('blocks'),
    'addresses': r.get('addresses'),
    'cross_ledger_identity_mismatches': r.get('cross_ledger_identity_mismatches'),
    'cross_ledger_missing_cells': r.get('cross_ledger_missing_cells'),
    'test_fixture_mode': r.get('test_fixture_mode'),
    'synthetic_data_used': r.get('synthetic_data_used'),
    'dimension_input_artifact_sha256': s.get('artifact_sha256'),
    'training_authorized': r.get('training_authorized'),
})
PY
```

Expected semantic result if and only if the real substrate closes:

```text
terminal = PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE
cross_ledger_identity_mismatches = 0
cross_ledger_missing_cells = 0
test_fixture_mode = false
synthetic_data_used = false
training_authorized = false
```

The FULL104 PASS closes data-byte/identity authority only. It does not choose `D_shared`, `D_private`, `D_total`, `D_obs`, locality, triplet budget, training horizon, checkpoint, or training authority.

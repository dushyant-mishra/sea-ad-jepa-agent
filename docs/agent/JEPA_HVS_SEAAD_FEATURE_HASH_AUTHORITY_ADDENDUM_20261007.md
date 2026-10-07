# JEPA HVS/SEA-AD feature-hash authority addendum — 2026-10-07

Status: `METADATA_AUTHORITY_RECOVERED__MATRIX_RECOMPUTE_STILL_REQUIRED__NO_EXPRESSION_VALUES_OPENED`

## Purpose

This addendum narrows one previously open part of `JEPA_HVS_SEAAD_PHYSICAL_AXIS_REPAIR_CONTRACT_20261007.md`: the exact Stage81A2 ordered-feature hashing rule and the frozen expected feature-universe hashes for the 35 HVS/SEA-AD H5AD matrices in repair scope.

It does not authorize expression-value access, rematerialization, Stage A, target replay, training, TEST, Morabito, pathology, Stage 4, or 500K.

## Recovered primary authority

The frozen Stage81A2 producer at commit `808ce4f170055c5568cc5c1e0e3a56415b52f908` defines:

```python
def stable_hash(*parts):
    return sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()

def source_hash(values):
    return stable_hash(*list(values))
```

Therefore the ordered feature-vector hash is exactly:

`SHA256("|".join(ordered_matrix_native_feature_ids).encode("utf-8"))`

The hash is over the matrix-native ordered identifier strings exactly as read by the Stage81A2 audit. Ensembl version stripping occurs later for canonical identity pairing and is not part of the feature-order hash.

## HVS authority

For every one of the 24 HVS matrices:

- count slot: `raw/X`
- native ordered stable-ID vector: `raw/var/_index`
- paired symbol vector: `raw/var/feature_name`
- expected width: `18,736`
- frozen Stage81A2 feature-universe hash:
  `4c1e94c02df22d936270bd82e5229efa81af156c4666ad95849eeabea2e21788`

The Stage81A2 producer required all 24 HVS partitions to share exactly one feature hash and failed closed otherwise.

## SEA-AD authority

For every one of the 11 SEA-AD RNA matrices:

- count slot: `layers/UMIs`
- native ordered stable-ID vector: `var/gene_ids`
- paired symbol vector: `var/index`
- expected width: `36,601`
- frozen Stage81A2 feature-universe hash:
  `b034585d654b46da4d26cc0cbcaf1e4ace12fa93ab9b55dd4182dd882ae966c7`

The Stage81A2 producer required all 11 SEA-AD matrices to share exactly one feature hash and failed closed otherwise.

This `b034585d...` authority supersedes use of the older `a7391464...` pre-Stage mapping-sidecar hash as the expected physical feature vector for this repair. The older sidecar remains historical mapping evidence only.

## Exact matrix inventory

The complete 35-matrix scope is frozen in:

`docs/agent/JEPA_HVS_SEAAD_PHYSICAL_AXIS_MATRIX_INVENTORY_20261007.csv`

with 24 HVS rows and 11 SEA-AD rows.

Every row remains:

`METADATA_BOUND__MATRIX_VECTOR_RECOMPUTE_REQUIRED`

until the exact local H5AD is opened metadata-only and its native vector reproduces the expected width and hash.

## Metadata-only verifier

The prospective verifier is:

`scripts/v5/verify_hvs_seaad_physical_axis_metadata.py`

It is intentionally limited to:

1. opening the exact H5AD;
2. reading only the native feature-ID and symbol metadata vectors;
3. verifying the expected width;
4. recomputing the frozen Stage81A2 ordered-feature hash;
5. confirming the declared raw-count slot exists without reading its values;
6. writing a machine-readable receipt.

It does not read the count matrix values.

Synthetic TDD coverage is in:

`tests/v5/test_verify_hvs_seaad_physical_axis_metadata.py`

Focused local synthetic result before commit: `3 passed`.

## Qualification boundary

A matrix that reproduces its metadata vector and expected hash may advance from:

`METADATA_BOUND__MATRIX_VECTOR_RECOMPUTE_REQUIRED`

to:

`PHYSICAL_FEATURE_VECTOR_AUTHENTICATED`

for the feature-order layer only.

That is still not sufficient for:

`PHYSICAL_AXIS_IDENTITY_QUALIFIED_FOR_REPAIR`

The later qualification additionally requires canonical identity join proof, collision handling, sentinel value equality under separately authorized real-RNA access, and decoder cross-check where covered.

## Current state

`35_MATRIX_SCOPE = FROZEN`

`HASH_ALGORITHM = RECOVERED_FROM_PRIMARY_STAGE81A2_CODE`

`HVS_EXPECTED_FEATURE_HASH = 4c1e94c02df22d936270bd82e5229efa81af156c4666ad95849eeabea2e21788`

`SEA_AD_EXPECTED_FEATURE_HASH = b034585d654b46da4d26cc0cbcaf1e4ace12fa93ab9b55dd4182dd882ae966c7`

`REAL_RNA_VALUES_OPENED = NO`

`REAL_RNA_REPAIR_EXECUTION = NOT_AUTHORIZED`

`STAGE_A_EXECUTION = NOT_AUTHORIZED`

`TRAINING = OFF`

# B3 blocked — the RNG V3 builder and the parameters authority disagree on one key name

Date: 2026-09-22
Branch: `gpu/v5-full104-metadata-receipts-20260921` at `ebae1f9667a6e483ec35a6918234c40b99ae9ea2`

```
STATUS  B3_RNG_V3_REAL_RECEIPT = BLOCKED
        MASKING_RNG_REPLAY_AUTHORITY_V3.json NOT PRODUCED
        Task 4 (non-executable Audit-B V1 parent contract) is gated on B3 and is
        therefore also not produced.
```

**Nothing was patched to get past this, and no RNG authority was produced by any
other route.** A `global_seed` is the root of every mask the project will ever
draw; one manufactured through a script I had edited myself would carry my
workaround in its provenance rather than the builder's.

## What happens

```
$ python scripts/agent/build_full104_rng_replay_authority_v3_20260921.py \
    --registry <stage81a2r_foundation_molecular_address_registry_candidate.csv> \
    --split-receipt <full104_split_receipt_v1.json> \
    --parameters-authority <MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3.json> \
    --burden-ladder-authority <MASKING_BURDEN_LADDER_AUTHORITY_V2.json> \
    --out <MASKING_RNG_REPLAY_AUTHORITY_V3.json>

MaskingQualificationParametersAuthorityV3 digest mismatch
```

## The cause: a key name, not a wrong value

The builder validates each input authority with a helper that compares a declared
digest field against the recomputed canonical digest:

```python
# scripts/agent/build_full104_rng_replay_authority_v3_20260921.py:88-92
parameters = typed(
    parameters_payload,
    MaskingQualificationParametersAuthorityV3,
    "authority_sha256",          # <-- this key does not exist in that payload
)
```

The only producer of that authority writes the digest under a different name:

```python
# scripts/agent/build_full104_masking_parameters_authority_v3_20260919.py:149
"parameter_authority_sha256": authority.canonical_digest(),
```

Measured, not inferred:

```
dataclass has an authority_sha256 field?        False
payload has authority_sha256 key?               False
payload has parameter_authority_sha256 key?     True
dataclass fields absent from payload:           []          <- nothing is missing
recomputed canonical_digest:                    e942c1253ea71e08f50196fbfe28b7eadc1c5757971094673bce75fe6b1436c1
payload["parameter_authority_sha256"]:          e942c1253ea71e08f50196fbfe28b7eadc1c5757971094673bce75fe6b1436c1
VALUES AGREE:                                   True
```

So the authority is correct and its digest is correct. The builder simply reads
the wrong key and therefore compares `None` against the digest.

## Which side is wrong: the RNG builder

`parameter_authority_sha256` is the established convention, with five independent
witnesses on this head:

| consumer / producer | key used |
|---|---|
| `build_full104_masking_parameters_authority_v2_20260918.py:125` | `parameter_authority_sha256` |
| `build_full104_masking_parameters_authority_v3_20260919.py:149` | `parameter_authority_sha256` |
| `build_full104_masking_run_contract_v4_20260918.py:218` | `parameter_authority_sha256` |
| `build_full104_nonlinear_capacity_model_authority_v1_20260918.py:34` | `parameter_authority_sha256` |
| `tests/test_v5_full104_masking_gpu_preflight_v1.py:74,179` | `parameter_authority_sha256` |
| **`build_full104_rng_replay_authority_v3_20260921.py:91`** | **`authority_sha256`** ← sole outlier |

The run-contract V4 builder is the closest analogue — it validates the *same
dataclass* through the *same `typed()` helper* — and it passes
`"parameter_authority_sha256"`.

The likely mechanism is a copy of the adjacent call. Twelve lines below, the same
script validates the **burden ladder**, which genuinely does write
`authority_sha256`, and that call is correct:

```python
burden = typed(burden_payload, MaskingBurdenLadderAuthorityV2, "authority_sha256")  # correct
```

Confirmed that no newer parameters builder exists that would emit the other key:
`scripts/agent/` contains only the V2 and V3 builders, on both this head and the
scientific integration head `3bf6b659`.

## The fix

One token, in the RNG builder:

```diff
 parameters = typed(
     parameters_payload,
     MaskingQualificationParametersAuthorityV3,
-    "authority_sha256",
+    "parameter_authority_sha256",
 )
```

This is preferable to changing the parameters builder, because that would alter
the parameters JSON's bytes and therefore its file hash, breaking anything that
already binds it.

I have not applied it. It is a change to a committed builder on the integration
lane whose output is a freeze root, so the decision is the owner's. On
instruction I can apply it and rerun; everything else B3 needs is already
verified and staged, so the rerun is immediate.

## Everything else B3 requires is verified and ready

| input | state |
|---|---|
| canonical registry | **VERIFIED** `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`, 41,238 rows, 24,946,770 bytes |
| four-fold split receipt | **VERIFIED** canonical `5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4`, schema V1, 4 folds, 104 donors |
| masking parameters authority V3 | **BUILT** — `e942c1253ea71e08f50196fbfe28b7eadc1c5757971094673bce75fe6b1436c1` |
| burden ladder authority V2 | **BUILT** — `85148fdf9be2bdd655ec601c4d26870f47f6885ce83d93b6e5c7ff8046d32685` |

Both newly materialized authorities are committed alongside this note. Neither
was substituted from an older V1/V2 parameter authority: the parameters file
carries schema `V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3` and the ladder
carries `V5_MASKING_BURDEN_LADDER_AUTHORITY_V2` with terminal universe 17,186.

The registry was located by **role**, then confirmed by hash — the registry
authority records `path_is_not_identity: true`, so the path
(`results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv`, in
the main working tree rather than this one) is informative only. It is not
committed here: at 24.9 MB it is an existing tracked artifact elsewhere in the
project, and duplicating it would serve no purpose.

```
AUDIT_B_N1                    = UNOPENED
TERMINAL_MASKING_OUTCOMES     = UNOPENED
MASKS_EXECUTED                = NONE
BURDEN_CALCULATION            = NOT RUN
TRAINING_OFF
```

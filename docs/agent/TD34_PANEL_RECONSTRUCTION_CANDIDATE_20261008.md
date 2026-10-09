# TD34 panel reconstruction candidate — 2026-10-08

Status: `CANDIDATE_EQUIVALENT_SUPPORT_VECTOR__NOT_YET_FINAL_GENEALOGY_CLOSURE`

This record follows physical recovery of the authenticated Sept. 7 target-discovery ZIP and exact recovery of the original TD34 producer. It records a candidate route to reconstruct the four historical TD34 panels without the original `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` bytes.

## Primary recovered producer

Recovered producer:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

SHA-256 of original recovered archive bytes:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

The producer defines:

```python
common = np.where((states == 1).all(0))[0]
ordered = np.array(
    sorted(common, key=lambda x: hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),
    dtype=np.int32,
)
panels = [ordered[i*512:(i+1)*512] for i in range(4)]
```

## Candidate equivalent support vector

Recovered authenticated archive file:

`evidence/td_iteration21b_estimability_sweep/TD21B_GENE_MEASUREMENT_RELIABILITY.csv`

Archive/file SHA-256:

`da8aaedf38045b47d85fb219ccca4fa8c9709d06e74dd76d108d746ea0e2222c`

Columns include `broad_class` and `gene_index`. Inspection found two broad-class blocks:

- `Neuronal: GABAergic`
- `Neuronal: Glutamatergic`

Each block contains exactly `17,186` unique `gene_index` values, and the sorted integer address vectors are byte-identical between the two blocks.

The adjacent authenticated summary:

`evidence/td_iteration21b_estimability_sweep/TD21B_SUMMARY.json`

states:

`"common_scalar": 17186`

and the recovered Sept. 7 handoff states that the corrected cross-source common scalar comparison space is 17,186 Molecular Ledger addresses scalar-measured in all 42 operators.

Therefore the TD21B `gene_index` set is a strong candidate for an authenticated equivalent copy of the exact common-scalar support universe consumed by TD34. This is not yet promoted to final equivalence because the original support NPZ bytes have not been compared directly.

## Deterministic reconstruction results

Sorted common-support vector representation used for this audit:

- dtype: `numpy.int32`
- count: `17186`
- sorted-vector SHA-256 over raw `int32` bytes: `a4095c0e70141cacbcb940a2455480e9666452de4d41875360e9b4573c05a4f4`

After applying the authentic `SHA256("TD25|<address>")` ordering rule:

- ordered 17,186-vector SHA-256 over raw `int32` bytes: `48b311c8abe1c25912277c2c4aaafb595035649ab7e3929bed5655167bd8a310`

Candidate panel hashes over raw ordered `numpy.int32` bytes:

| panel | count | SHA-256 |
|---:|---:|---|
| 0 | 512 | `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976` |
| 1 | 512 | `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44` |
| 2 | 512 | `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56` |
| 3 | 512 | `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5` |

A chat-local exact CSV containing all 2,048 candidate panel addresses was generated as:

`/mnt/data/TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv`

- rows including header: `2049`
- bytes: `25033`
- SHA-256: `c3d706e62b7de5eec67a2aa78f91e376df976038ce7dfc3b6b1106bf39aced2c`

The CSV is a derived candidate artifact, not historical primary evidence.

## Cross-check required before final closure

Promote this reconstruction to `REPRODUCED` only after at least one independent historical cross-check binds these panel identities, ideally one of:

1. original `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` recovered and common set matches exactly;
2. historical TD41/TD43 panel or pair manifest includes panel membership/hashes that match these vectors;
3. historical producer output or other frozen artifact preserves all four exact panel address lists;
4. an independently reconstructed TD41 fixed-pair manifest from these panels yields exact historical pair hashes/results under the frozen hashing rule.

Until then, classification is:

`PRIMARY_TD34_PRODUCER_RECOVERED__CANDIDATE_EXACT_PANEL_RECONSTRUCTION_FROM_AUTHENTIC_DERIVED_COMMON_SUPPORT__DOWNSTREAM_CROSSCHECK_PENDING`

This analysis is read-only/custody-only and confers no target, training, Stage 4, TEST, Morabito, representation, or production authority.
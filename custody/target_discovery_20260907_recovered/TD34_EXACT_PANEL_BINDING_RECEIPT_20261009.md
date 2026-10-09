# TD34 exact historical panel binding receipt — 2026-10-09

Status: `TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__NO_TARGET_AUTHORITY`

This is a custody/provenance closure only. It does **not** create a production target, representation, training, Stage 4, TEST, Morabito, or multimodal authority.

## 1. Historical producer identity

Recovered primary producer:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

SHA-256 of the recovered original Sept. 7 archive bytes:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

This exactly matches the producer digest recorded by the historical TD30–TD36 closure.

The producer reads:

`FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

and defines panel membership by:

```python
states = np.load(SUP, allow_pickle=False)["states"]
common = np.where((states == 1).all(0))[0]
ordered = np.array(
    sorted(common, key=lambda x: hashlib.sha256(f"TD25|{int(x)}".encode()).digest()),
    dtype=np.int32,
)
panels = [ordered[i*512:(i+1)*512] for i in range(4)]
```

## 2. Physical upstream substrate recovered and authenticated

Physical archive inspected in the project environment:

`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`

- bytes: `410278055`
- SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

That is the established canonical Aug-24 calibration-bundle identity used elsewhere in the project.

Exact ZIP member consumed by the recovered TD34 producer after extraction:

`FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

- uncompressed bytes: `227532`
- SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

NPZ contents under `allow_pickle=False`:

| key | shape | dtype |
|---|---:|---|
| `states` | `(42, 41238)` | `uint8` |
| `matrix_id` | `(42,)` | `<U61` |
| `operator_index` | `(42,)` | `int32` |
| `molecular_address_index` | `(41238,)` | `int32` |
| `state_names` | `(3,)` | `<U29` |

No substitute support artifact was used in this reproduction.

## 3. Exact common-support reproduction

Applying the historical producer's exact predicate:

`np.where((states == 1).all(0))[0]`

yields:

- count: `17186`
- minimum address: `0`
- maximum address: `40475`
- dtype used for hash comparison: `numpy.int32`
- sorted common-support vector SHA-256 over raw int32 bytes: `a4095c0e70141cacbcb940a2455480e9666452de4d41875360e9b4573c05a4f4`

This exactly matches the independently reconstructed TD21B common-support vector previously recorded in `docs/agent/TD34_PANEL_RECONSTRUCTION_CANDIDATE_20261008.md`.

Applying the producer's historical `SHA256("TD25|<integer-address>")` ordering gives:

- ordered 17,186-vector SHA-256 over raw int32 bytes: `48b311c8abe1c25912277c2c4aaafb595035649ab7e3929bed5655167bd8a310`

This also exactly matches the prior independently derived candidate ordering.

## 4. Exact four-panel membership hashes

Slicing the authenticated ordered vector exactly as the producer does yields:

| panel | count | SHA-256 over raw ordered `numpy.int32` bytes |
|---:|---:|---|
| 0 | 512 | `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976` |
| 1 | 512 | `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44` |
| 2 | 512 | `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56` |
| 3 | 512 | `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5` |

The concatenated first 2,048 ordered addresses have SHA-256 over raw int32 bytes:

`13616d28a3e0c1e517b8b465e19e4ce7d209fc9e796391c041519fdcf1542b12`

The previously preserved exact CSV representation of those same 2,048 addresses remains:

`TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv`

with SHA-256:

`c3d706e62b7de5eec67a2aa78f91e376df976038ce7dfc3b6b1106bf39aced2c`

Its four per-panel hashes are identical to those reproduced directly from the canonical NPZ above.

## 5. Closure logic

The prior candidate record explicitly required, as its preferred closure condition:

> original `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` recovered and common set matches exactly

That condition is now satisfied by the authenticated canonical calibration archive and its exact support member.

The chain is now:

`historically recorded producer digest`
→ `exact recovered producer bytes`
→ `canonical calibration ZIP identity`
→ `exact observation-state NPZ member identity`
→ `17,186-address all-operator common support`
→ `historical deterministic TD25 hash ordering`
→ `four exact 512-address panel vectors`
→ `independently preserved candidate CSV and matching panel hashes`.

No conflicting historical panel membership or panel hash was identified in the audited repository/custody surfaces.

## 6. Current classification

The old statuses:

- `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`
- `PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`
- `PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__CANDIDATE_MEMBERSHIP_CROSS_CONSISTENT__EXACT_HISTORICAL_PANEL_BINDING_STILL_OPEN`

are superseded for the narrow TD34 genealogy question.

Current custody classification:

`TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__SELECTION_RULE_HASH_BOUND__NO_TARGET_AUTHORITY`

This closes exact TD34 panel genealogy. It does **not** convert TD34/TD41/TD43 into a production target, does not repair or replay later historical target-discovery stages on corrected S174 substrate, and does not alter any current training or Stage-4 boundary.

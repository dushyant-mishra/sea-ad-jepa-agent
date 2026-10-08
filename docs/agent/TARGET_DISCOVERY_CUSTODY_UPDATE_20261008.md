# Target-discovery custody update — 2026-10-08

Status: `DOCUMENTATION_AND_PRIMARY_CUSTODY_ONLY__NON_AUTHORIZING`

This record updates the target-discovery lane after physical recovery of the historical Sept. 7 target-discovery handoff ZIP in the current ChatGPT environment. It must be read together with `TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md` and the final takeover handoff.

## 1. Recovery event

Recovered file:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Recovered chat-local path:

`/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Authenticated identity:

- bytes: `1664383`
- SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- historical expected SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- verdict: `EXACT_MATCH`
- extracted files: `97`

Recovered embedded handoff:

- path: `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.md`
- SHA-256: `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`
- historical expected SHA-256: same
- verdict: `EXACT_MATCH`

## 2. TD34 producer recovered

Recovered original producer:

`scripts/td_iteration34_state_geometry_globalrow.py`

SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

This exactly matches the producer digest preserved in the Oct. 6 TD34/S149 genealogy audit.

Durable takeover copy:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

Therefore the old statement `ORIGINAL_TD34_PRODUCER_BYTES_NOT_RECOVERED` is superseded.

## 3. Exact recovered panel-selection rule

The authentic producer performs:

```python
states = np.load(SUP, allow_pickle=False)['states']
common = np.where((states == 1).all(0))[0]
ordered = np.array(
    sorted(common, key=lambda x: hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),
    dtype=np.int32,
)
panels = [ordered[i*512:(i+1)*512] for i in range(4)]
```

Thus historical TD34 panel membership was defined by:

1. the common scalar-support universe from the observation-state array;
2. deterministic SHA-256 ordering of integer molecular addresses using the literal prefix `TD25|`;
3. four consecutive 512-address slices.

The recovered producer contains no panel-selection ranking by outcome, pathology, covariance, observed HVS/SEA-AD agreement, expression magnitude, topology, or target result.

This materially narrows the S149 genealogy concern raised when the producer bytes were unavailable.

## 4. What remains unresolved for TD34

The ZIP does not contain the producer's upstream support file:

`FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

and no standalone four-panel membership manifest was located by filename inspection in the recovered archive.

The exact panel vectors should therefore not yet be called independently reproduced from takeover custody alone.

Current classification:

`PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`

Next closure path:

- recover/hash-bind the exact historical observation-state NPZ, or an authenticated equivalent containing the same common-support address vector;
- reproduce the common-support set;
- apply the authentic deterministic hash rule;
- persist the four 512-address vectors with hashes;
- compare any downstream TD41 panel/pair manifests against those reconstructed vectors.

## 5. Durable custody added to PR #237 branch

Directory:

`custody/target_discovery_20260907_recovered/`

Primary records:

- `README.md`
- `td_iteration34_state_geometry_globalrow.py`
- `RECOVERED_PACKAGE_SHA256_MANIFEST.csv`

The checksum manifest binds all 97 extracted archive files by relative path, byte count and SHA-256. The binary ZIP itself is not copied into Git because the connected GitHub write interface accepts UTF-8 text rather than arbitrary binary payloads. Its exact SHA-256 and byte count are recorded above and in the custody README.

## 6. Defect -> repair -> verification -> supersession state

| Lane | Old finding | Repair/recovery | Verification | Current state |
|---|---|---|---|---|
| S174 HVS/SEA-AD feature axis | historical positional feature-axis defect | prospective physical gene-ID rebuild at `cf4d4708...` | corrected replay lineage, including `46d8eaa8...`; live branch newer | `FIXED_AND_REPLAYED`; use successor branch |
| TD34 producer custody | producer hash known; bytes absent from repository audit | Sept. 7 ZIP physically recovered | ZIP, embedded handoff and producer all exact historical hash matches | `PRODUCER_RECOVERED`; upstream support binding remains |
| TD34 four panels | exact manifests not repository-resident | authentic deterministic producer rule recovered | not yet independently reconstructed because support NPZ not recovered here | `UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING` |
| G2 / `PIPELINE_ARTEFACT_m` | positive-control execution not recovered by Oct. 6 audit | successor history must be checked | pending archaeology | `DO_NOT_CARRY_RED_FORWARD_WITHOUT_SUCCESSOR_CHECK` |
| Nott/liftover | artifacts not mirrored into takeover | historical V64 successor/contract branches located | pending exact source/checksum/liftover chain reconstruction | `HISTORICAL_GIT_START_POINT_FOUND` |
| SCENIC+ | artifacts not mirrored into takeover | recovery and V69 branches located | pending producer/input/region/exposure reconstruction | `HISTORICAL_GIT_START_POINT_FOUND` |
| NIH-CARD Stage 3/4 | design/control lineages found; later execution package not independently located | historical branches identified | pending exact execution-output recovery | `PARTIAL_PROVENANCE_RECOVERED` |

## 7. Required continuation method

For every target-discovery or external-evidence claim use:

`old defect/finding -> exact repair/recovery commit or primary artifact -> exact verification receipt/result -> explicit superseding conclusion`

Do not:

- freeze an old RED audit as permanent truth;
- call a later prose handoff a repair without primary evidence;
- search PR #237 alone when the locator points to historical branches;
- infer absence merely because an artifact is not on the current branch;
- promote TD34/TD41 or later target stages to production authority from this custody recovery alone.

## 8. Hard boundaries

This recovery does not authorize real-data training, Stage A, Stage 4, TEST, Morabito use as pristine validation, target freeze, representation freeze, production EMA selection, or multimodal training.
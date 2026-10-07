# JEPA TD34 S149 genealogy closure — 2026-10-06

Status: DOCUMENTATION/AUDIT ONLY. Training remains OFF. Stage 4 remains NOT AUTHORIZED. No protected outcome opened.

## Authentication

User-supplied `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip` was hashed locally before inspection.

- bytes: `1664383`
- SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- historical expected SHA-256: exact match

The ZIP contains the original TD34 producer:

- `scripts/td_iteration34_state_geometry_globalrow.py`
- SHA-256: `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`
- historical expected producer SHA-256: exact match

The authenticated calibration bundle supplied the measurement-support state and address namespace used to reconstruct the panels:

- `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- `address_namespace.csv` was used only to map molecular-address indices to IDs/symbols after reconstruction.

## Exact panel-construction rule recovered from primary code

TD34 does **not** select genes from pooled RNA covariance, study/source topology, outcomes, pathology, recurrence scores, or any TD34 result.

The code does exactly this:

1. Load the 42 x 41,238 operator-by-address observation-state matrix.
2. Keep addresses with state `1` in **all 42 operators**.
3. This yields exactly **17,186** common scalar-measured addresses.
4. Deterministically order those addresses by `SHA256("TD25|<molecular_address_index>")`.
5. Take four consecutive blocks of 512 addresses.

Thus panel membership is fixed entirely by universal measurement support plus a deterministic hash ordering.

## S149 adjudication

All four historical TD34 panels are now classified:

`S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`

Reason: selection never uses pooled cell composition or pooled expression topology. The inclusion criterion is the intersection of scalar measurability across all 42 operators, followed by outcome-blind hash ordering. This can bias the panels toward broadly measurable features, but it cannot create the S149 failure mode where source/study composition itself selects genes through pooled covariance/topology.

This classification applies to **panel genealogy only**. It does not automatically validate TD41/TD43 biological conclusions; their downstream estimands and observation-process handling still require S149-aware review.

## Reconstructed panel fingerprints

For each panel below, the index fingerprint hashes the comma-separated ordered molecular-address indices. The ID fingerprint hashes the newline-separated ordered molecular-address IDs after mapping through the authenticated namespace.

- Panel 1: 512 addresses; index SHA-256 `3f76aa8ace61ff527ee9bdcad6afeec2dd15c320d7eb4aa34d114bc6c5190a26`; ID SHA-256 `1e98c95615b06b492f914acfd717531b9ff6ad08f99d1dd854527518aa7d568a`
- Panel 2: 512 addresses; index SHA-256 `d78f49fbdec32e826400fe77bcafeed5c48a442b2847415e799c83022f09565e`; ID SHA-256 `1a08f21bfe7b6d2de1ea88950cc8ef821fc41bf84831942161cd0761de792f2c`
- Panel 3: 512 addresses; index SHA-256 `cba9a855cae491b9be2406c68874559221de596ccd438b06e9d3ddc6fb159044`; ID SHA-256 `5870153179f8cd20f9fbad76b1f05bcd9055a8ca7c41e20e152cb007424d2918`
- Panel 4: 512 addresses; index SHA-256 `904939f2a18a0e2768074cb1246105a327b5591089dcc162d21104cb77ccefee`; ID SHA-256 `3ac777f005df7aef58349983a6e49443d61782190de0d51ae2b83858b2e643e0`

All 2,048 selected addresses map to source-family provenance `HVS|NPH52|SEA-AD` in the supplied namespace. The panels are not restricted to protein-coding genes; this is consistent with the producer, which selects universal molecular addresses rather than a protein-coding-only subset.

A locally reconstructed 2,048-row manifest had SHA-256 `5c1f51c37974df62ef74889c2464bb0c1d87017bbf6e286fb5da8167f9ee23b9`, but it is **not** being committed here because a first large-text transfer into GitHub failed self-audit and was immediately deleted. The compact fingerprints above are the authoritative durable record for this audit checkpoint; exact membership is reproducible from the authenticated producer + support matrix.

## Historical-spillover correction

Prior audit state classified all four panels as `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`. That classification is superseded by this authenticated recovery.

Do not revive the old indeterminate classification after this checkpoint unless one of the authenticated inputs above is itself invalidated.

## What this now permits

The upstream TD34 panel-selection blocker for S149-aware TD41 review is closed. The next scientific step may inspect historical TD41/TD43 **without changing the panel membership**, but must still ask whether the downstream statistic is donor-level, source-stratified/transported appropriately, and free of pooled observation-process confounding.

This does not authorize new training, Stage 4, TEST, Morabito opening, or target promotion.

# TD38S — Rotation-Invariant Split-Ledger Dependence Energy screen result

Status: `TD38S_SURVIVES_NECESSARY_CONDITION__NO_TARGET_AUTHORITY`

Prospective freeze commit: `601b9270f50dca28b423ef0ccd8250d56ff5c1a6`

## Result

The predeclared source-survival rule required all 8 cases per source:
2 independent hash-fixed 512-gene panels × 2 donor splits × 2 donor halves.

All three source families survived.

### HVS — 8/8 PASS

| panel | split | half | observed E | null p95 |
|---|---:|---:|---:|---:|
|0|0|0|118.8047|116.6429|
|0|0|1|132.1855|130.1225|
|0|1|0|116.8012|114.8201|
|0|1|1|134.6083|133.1982|
|1|0|0|120.9409|119.4924|
|1|0|1|133.2317|130.8936|
|1|1|0|119.5169|118.0788|
|1|1|1|134.0943|131.3899|

### NPH52 — 8/8 PASS

| panel | split | half | observed E | null p95 |
|---|---:|---:|---:|---:|
|0|0|0|117.1725|115.4734|
|0|0|1|93.9168|92.1360|
|0|1|0|100.3385|99.1255|
|0|1|1|109.9506|108.3666|
|1|0|0|113.4044|112.3387|
|1|0|1|89.8979|89.7032|
|1|1|0|96.0112|95.4059|
|1|1|1|107.6012|106.8633|

### SEA_AD — 8/8 PASS

| panel | split | half | observed E | null p95 |
|---|---:|---:|---:|---:|
|0|0|0|13.8576|10.2180|
|0|0|1|12.5851|8.7146|
|0|1|0|14.9962|11.0270|
|0|1|1|11.6744|8.0148|
|1|0|0|13.5060|10.1897|
|1|0|1|12.5923|8.9399|
|1|1|0|14.4829|10.8043|
|1|1|1|11.5113|8.2916|

Total: **24/24 PASS**.

## Interpretation boundary

This establishes only a necessary condition: paired disjoint gene views contain rotation-invariant linear dependence above the donor/operator/depth/detection matched broken-pairing null in all three source families.

It does NOT establish:
- a per-cell target;
- cross-source numerical comparability;
- biological sufficiency;
- explanation of TD34;
- production dimension/threshold;
- JEPA training authority.

The HVS/NPH52 margins are materially smaller than SEA_AD's and require stronger per-cell/donor-heldout attacks before interpretation.

Predeclared screen terminal:
`TD38S_SURVIVES_NECESSARY_CONDITION__FREEZE_FULL_TD38_BEFORE_ANY_CROSS_SOURCE_ANALYSIS`.

No labels were opened.

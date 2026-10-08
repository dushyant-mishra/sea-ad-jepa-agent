# TD59 — nearest-half mesoscale relational locality-frontier gate

Status: `PROSPECTIVE_FALSIFICATION_SCREEN__NO_TARGET_OR_TRAINING_AUTHORITY`
Date: 2026-09-08

## Predecessor state

TD57B established donor-recurrent, scale-free relational ordering across two independent disjoint molecular panels and all three source families: 24/24 donor-half cases PASS.

TD57C then tested a much harder three-view local claim. An independent Z view selected the nearest one-third neighborhood and independent X/Y views had to reproduce distance ordering inside that neighborhood. HVS Panel 0 failed 2/4 donor halves. The exact same TD57C X/Y genes passed 4/4 when localization was removed, so the failure is specifically attributable to aggressive nearest-third localization rather than a bad molecular panel.

TD59 does not reopen or rescue TD57C.

## Scientific question

**Does a broader, prospectively fixed nearest-half neighborhood retain donor-recurrent relational ordering on completely fresh molecular views?**

This is a bounded locality-frontier test, not a search over neighborhood fractions.

## Anti-fishing rule

TD59 evaluates exactly one new locality fraction: **nearest 1/2**.

The fraction is not selected from new expression outcomes. It is the next wider fraction already present in the metadata-only TD57C feasibility grid (1/4, 1/3, 1/2), where nearest half structurally supported 29 HVS donors.

To prevent post-hoc scale tuning:

- TD59 uses completely fresh gene-ranking positions beyond all positions allocated through TD57C;
- no 1/2 result has been opened on these genes;
- no 2/3, 3/4, adaptive-k, or other locality fraction will be tried on the 50k archive after TD59;
- if nearest half fails, pilot locality-fraction tuning stops and only unrestricted/global relational geometry remains supported on the 50k archive;
- if nearest half passes, the pilot supports a frontier bracket: nearest one-third failed while nearest one-half survives. This bracket is not a production neighborhood size.

## Inputs and firewalls

Use `A_NATURAL_MIXTURE` only: global expression rows 0..24,999.

Expected source rows:
- HVS: 1,129
- NPH52: 1,310
- SEA_AD: 22,561

No pathology, reader-validation, reader-oracle, DEV, SEALED, external holdout, or biological annotation is used.

The executor reads only the lawful metadata fields needed for donor/operator blocking and technical matching:
- sample identity/order;
- source;
- operator index;
- donor ID;
- stable key;
- source library size.

Detected-gene count is derived from the exact sparse expression row support (`indptr[r+1]-indptr[r]`).

Input bindings:
- 50k expression member arrays:
  - `data.npy` `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
  - `indices.npy` `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
  - `indptr.npy` `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
  - `shape.npy` `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`
- discovery metadata ZIP: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- sample-freeze member: `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- 42-file operator-metadata manifest root: `c7433480da3caad38238aaead0726ce37197e84b1342b92193a3776ee2aae3b5`
- calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- operator-address observation-state member: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

The all-42-operator common-scalar intersection must remain exactly 17,186 Molecular Ledger addresses.

## Fresh three-view panels

Use the exact TD56 gene ranking:
`SHA256("TD56S|gene|<address>")`.

Positions 0..6143 are treated as previously allocated/opened-or-frozen history and are not reused.

### Panel 0
- selector Z: positions 6144..6655
- tested X: positions 6656..7167
- tested Y: positions 7168..7679

Frozen gene/pair hashes:
- Z gene SHA `f09455c4f5c120785608eda0c870bb299951814e895bbb7ff9d4dcf94b5680b2`
- Z pair-address SHA `806553cdacc4d1e3214a2d61880b8795ca4a0637f3762280750cfb502dcd36ed`
- X gene SHA `a365be9aa9ccfc80adddfeb080f8fc6b0c0bc515554bace7076b5cf31a990ae5`
- X pair-address SHA `5d9f539d723117bffebfbcd57feefb9b880c50bc4c0aaab55dc9c9f9411a99fd`
- Y gene SHA `124246edc85f082477fb354f6f20c09752a08a1e079c509a6f94648658b31bd3`
- Y pair-address SHA `eb6182759465df0e719bc793781ce0964e9a766761508ebe7bb192eda05defad`

### Panel 1
- selector Z: positions 7680..8191
- tested X: positions 8192..8703
- tested Y: positions 8704..9215

Frozen gene/pair hashes:
- Z gene SHA `2e1b171e833e248c9107b3f619df66f8ea33677bec7832aad58c6885ba4ae7be`
- Z pair-address SHA `960741f9b74118e8991cb859e3f044176afa8151eed3dace3f7b98102198db84`
- X gene SHA `8ef683be715f471f2a0f95531183416d75613eac43c745aa0ab10c7b59db6fa5`
- X pair-address SHA `d28d1bd09181bbfd24ca3d737a95a6d911ace6906a5e94d6bbdf133bbc33e0da`
- Y gene SHA `e3dc6ad8c685155458c978d7c5127f26536098a88a10a5d87a6ac127b1689959`
- Y pair-address SHA `bc81c334afdcf169a0e4636ec5f76da51e248b4ac35821e26b2a71b8dbe4599f`

All six views contain 512 genes and are mutually disjoint by ranking position.

## Pair coordinates and distance

For each panel/view, enumerate all unordered address pairs and sort by:
`SHA256("TD59|panel|<P>|view|<ZorXorY>|g0|<min>|g1|<max>")`.

Retain the first 2,048 pairs.

Pair sign is tie-aware `{-1,0,+1}`.

For cells a,b:
- a coordinate is informative if at least one cell is nonzero/resolved at that pair coordinate;
- require >=256 informative coordinates;
- concordance distance is mean absolute sign difference divided by 2.

The 2,048 width and 256 measurability threshold are inherited continuity values for falsification only and cannot become production constants.

## Independent nearest-half selector

Within each structurally eligible donor×operator stratum and for each anchor i:

1. compute Z distances from i to every other cell;
2. retain finite/measurable Z candidates;
3. sort by `(Z distance ascending, global_row ascending)`;
4. with M finite candidates, retain exactly `ceil(M/2)` candidates;
5. form all unordered comparison pairs j,k inside that fixed Z-selected candidate set.

Z selects locality only. Z never defines the tested X/Y relation.

Boundary distance ties are handled only by the prospectively frozen global-row tie break and are reported in output telemetry.

## Structural eligibility

Metadata-only pre-outcome calculation uses, per donor×operator stratum of n>=4 cells:
- structural candidate count `ceil((n-1)/2)`;
- structural local-triplet population `n*C(k,2)`;
- cap 64 sampled triplets/stratum.

A donor is structurally eligible if capped triplets across its operators total >=20.

Frozen metadata-only result:
- HVS: **29** structurally eligible donors;
- NPH52: **16**;
- SEA_AD: **46**.

For both panels and both deterministic donor splits, half sizes are therefore:
- HVS 15/14;
- NPH52 8/8;
- SEA_AD 23/23.

## Deterministic local-triplet sampling

Within a donor×operator stratum, flatten anchor-specific local pair populations in global-row anchor order.

If total population <=64, use all. Otherwise select 64 unique flat indices with modulo-unbiased SHA256 rejection sampling:
`TD59|tripletsample|panel|<P>|source|<S>|donor|<D>|operator|<O>|counter|<c>`.

Comparison cells j,k are canonicalized by global row.

## Tested relation

For each sampled local triplet:
- `q_X(i;j,k)=sign(d_X(i,j)-d_X(i,k))`
- `q_Y(i;j,k)=sign(d_Y(i,j)-d_Y(i,k))`.

Nonmeasurable distances or exact distance ties make that view unresolved.

The base set is determined by Z selector eligibility plus X measurability/non-tie only.
Observed Y and every null-permuted Y independently earn Y measurability/non-tie.
Conditioning null support on observed-Y support is forbidden.

## Donor recurrence

For panel P, split s in {0,1}, and source S, order structurally eligible donors by:
`SHA256("TD59|panel|<P>|split|<s>|source|<S>|donor|<D>")`.

Alternate into halves.

Per donor:
- pool eligible triplets across operator strata;
- require >=20 observed resolved X/Y relations;
- donor statistic = fraction with q_X=q_Y.

Each half requires >=4 measurable donors.
Half statistic = median donor agreement.

## Matched Y-cell null

Use the inherited TD37A/TD56 depth/detection block construction within donor×operator.

For q=0..63, keep X and the Z-selected triplet population fixed and reassign only Y identities by a deterministic nonzero cyclic shift inside each matched block:
`TD59|null|panel|<P>|q|<q>|source|<S>|split|<s>|half|<h>|donor|<D>|operator|<O>|block|<b>`.

Each null donor independently requires >=20 resolved relations.
Each null half requires >=4 donors.
All 64 null statistics must be finite.

`null_p95 = sorted(null_values)[60]`.

## PASS / sequential stop

A half passes iff:
- observed median donor agreement >0.5; and
- observed > null_p95.

A source-panel passes only if all four donor halves pass.

Execution order:
`Panel0 HVS -> Panel0 NPH52 -> Panel0 SEA_AD -> Panel1 HVS -> Panel1 NPH52 -> Panel1 SEA_AD`.

Stop at the first source-panel failure.

Full survival requires 24/24 cases.

PASS terminal:
`TD59_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PILOT_FRONTIER_BRACKETED_BETWEEN_ONE_THIRD_AND_ONE_HALF__NO_TRAINING_AUTHORITY`

FAIL terminal:
`NO_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE__TD59_FAIL__STOP_LOCALITY_FRACTION_TUNING_ON_50K`

A mechanics/support failure is `NOT_ESTIMABLE` and cannot be treated as PASS.

## Interpretation boundary

PASS would support a **pilot mesoscale locality frontier**: the deepest tested nearest-third region is not uniformly recurrent, while a broader nearest-half region is. It would support a future global+mesoscale or affinity-weighted relational objective family, not a hard production k/fraction.

FAIL would mean the 50k archive supports unrestricted/global relational ordering but not a hard nearest-half-or-tighter locality objective. No further fraction tuning is permitted on the pilot.

Neither outcome establishes learned EMA-teacher geometry, heterogeneous partial-evidence student predictability, full-reader production locality, a final relational loss weight, or training authority.

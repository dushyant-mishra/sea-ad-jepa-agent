# TD59 result — nearest-half mesoscale relational recurrence survives

Status: `TD59_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PILOT_FRONTIER_BRACKETED_BETWEEN_ONE_THIRD_AND_ONE_HALF__NO_TRAINING_AUTHORITY`
Date: 2026-09-08

Prospective freeze:
`864651fbe56b973f6645866624513e827c2c54da`

Pre-outcome binding:
`f3eb86d26a306fe99ae2848dca89e9f2e9e25207`

Panel-0 preservation commit before Panel-1 opening:
`4a27575bb2bc37617624a266b888f8ec0d36080c`

Frozen local executor SHA-256:
`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`

Case table:
`target_discovery/iterations/td59_mesoscale_half_locality/TD59_CASE_TABLE.csv`

Local case-table SHA-256:
`be3518fa63f99a13bf25fc218b993a99de8e4f91e781f5e98bc898d8b9713cf1`

## Prospective question

TD57C established that a completely independent Z-selected **nearest one-third** neighborhood is not uniformly donor-recurrent in HVS. The exact same TD57C X/Y genes recover unrestricted relational order, so TD57C is a genuine localization failure.

TD59 prospectively asked one and only one wider locality question on completely fresh molecular views:

**Does a Z-selected nearest-half mesoscale neighborhood retain donor-recurrent X/Y relational ordering?**

The anti-fishing rule was frozen before outcome: no additional locality fraction will be tried on the 50k archive after TD59 regardless of result.

## Result

TD59 passes the complete frozen screen:

- Panel 0: HVS 4/4, NPH52 4/4, SEA_AD 4/4
- Panel 1: HVS 4/4, NPH52 4/4, SEA_AD 4/4
- total: **24/24 PASS**

Every case satisfies the prospectively frozen criterion:
1. observed median donor local-order agreement > 0.5; and
2. observed > the 64-null p95, defined as sorted null index 60.

The weakest observed-minus-null-p95 margin is:

`+0.0011566307718604563`

at Panel 0 / HVS / split 1 / half 1:
- observed `0.5484625668449198`
- null p95 `0.5473059360730593`

This is deliberately recorded as a **narrow** HVS survival, not a large-margin result.

## Stronger-than-required null-max diagnostic

TD57B had the unusually strong property that every case also beat the maximum of 64 matched nulls.

TD59 does **not** fully reproduce that stronger property:

- **22/24** TD59 cases beat null max;
- two Panel-0 HVS cases do not.

The most negative observed-minus-null-max margin is:
`-0.02518822680587396`
at Panel 0 / HVS / split 0 / half 1.

This does not alter TD59's prospectively frozen PASS rule, which is p95-based, but it materially limits the strength of the claim.

## Exact first-run result SHA-256

Panel 0:
- HVS: `72fd84c60f96ec7ad07b0039efc46bb049778b2e54190056afd84cdc83d54df6`
- NPH52: `dbf5570164aa686d1ded67ac408c354e543680cf0ffa76ddac2279a49eb4d6ba`
- SEA_AD: `5601bc1f788b1cb5b9eb060d984bea22a86a20af7d014bf98e0b7b34a978727c`

Panel 1:
- HVS: `72feba792c3bd1bf7c28ca7fa49d80edbf21825b0553a1811fbc3af050a4c66d`
- NPH52: `bf867da0446a3311d4118ddef7f784f6c94be680b32f0aa58c8f4dffd064214a`
- SEA_AD: `070f1bf8fc224d1dbef6b617749544cc7e854b157843a640e2347a160e4cc5df`

## Independent replay / mechanics audit

All six source-panel executions were independently rerun after the full outcome was known.

Every replay is **byte-for-byte identical** to its first-run JSON and reproduces the exact SHA-256 above.

The optimized concordance-distance kernel independently compares to the direct/naive definition with maximum absolute difference **0.0** in every source-panel run.

Selector-cutoff tie telemetry:
- Panel 0 HVS: 0 / 530 selectable anchors
- Panel 0 NPH52: 0 / 1,262
- Panel 0 SEA_AD: 44 / 22,561
- Panel 1 HVS: 0 / 530
- Panel 1 NPH52: 6 / 1,262
- Panel 1 SEA_AD: 69 / 22,561

All ties are resolved only by the prospectively frozen global-row tie break.

Observed and null measurable-donor counts are identical in every case:
- HVS halves: 15/14
- NPH52 halves: 8/8
- SEA_AD halves: 23/23

## Scientific interpretation

TD59 changes the locality conclusion in a bounded way.

Supported on the 50k falsification archive:
- TD57B: unrestricted/global-to-mesoscale relational ordering is donor-recurrent across independent molecular views;
- TD57C: concentrating entirely on the nearest one-third local neighborhood fails the frozen HVS donor-half gate;
- TD59: a broader nearest-half Z-selected mesoscale region survives two completely fresh molecular panels and all three sources under the frozen p95 criterion.

Therefore a future relational objective may legitimately retain **broad/mesoscale affinity or relation matching**. The evidence does not support making the deepest local neighborhood the primary loss.

### Important non-equivalence

TD57C and TD59 intentionally use different prospectively frozen molecular views. Therefore the pair of experiments does **not** estimate a precise monotone transition point at exactly one-third versus one-half.

The lawful conclusion is an operational pilot bracket:
- nearest-third was falsified on its frozen views;
- nearest-half was independently supported on fresh frozen views.

It is not a production k/fraction, and it is not proof that every neighborhood wider than one-third must pass.

## Anti-fishing closure

Per the pre-outcome TD59 contract, **locality-fraction tuning on the 50k archive is now closed**.

Do not run:
- 2/3;
- 3/4;
- another nearest-half panel chosen after outcome;
- adaptive k selected from these outcomes;
- any other 50k fraction intended to choose a winning locality.

Production locality/weighting, if needed, must be newly derived on the complete lawful 4,553,407-cell reader-fit population under its own prospective authority.

## Next scientific gate

The next gate is no longer another fixed-concordance locality experiment.

Freeze the **TD56/TD57B-style learned-teacher continuity test**:

1. hold a learned teacher state fixed;
2. encode the same cells under prospectively frozen disjoint lawful molecular views;
3. compute learned latent relational geometry separately;
4. require donor-primary recurrence above matched wrong-cell nulls;
5. require source replication;
6. do not allow optimization success, variance, covariance, or effective rank to substitute for this continuity result.

Only after learned-teacher geometry earns continuity should partial-evidence student relational predictability become the next qualification gate.

## Authority boundary

TD59 is a falsification-screen success only.

It does **not** authorize:
- a production nearest-half neighborhood;
- a relational loss weight;
- learned EMA-teacher geometry;
- successor-u1 training;
- full-reader training;
- pathology;
- DEV/SEALED;
- reader-validation/oracle;
- modification of the frozen Teacher/Student V3 mechanics branch.

Frozen terminal:

`TD59_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PILOT_FRONTIER_BRACKETED_BETWEEN_ONE_THIRD_AND_ONE_HALF__NO_TRAINING_AUTHORITY`

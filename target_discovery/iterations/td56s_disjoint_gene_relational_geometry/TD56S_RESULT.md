# TD56S result — disjoint-gene within-donor relational geometry survives all three sources

Status: `TD56S_DISJOINT_GENE_RELATIONAL_GEOMETRY_SURVIVES__NO_TARGET_AUTHORITY`

Prospective freeze:
`d257fd3cf4957ecbb1ab3f03a06e54d043a1326f`

## Primary frozen screen

Two disjoint 512-gene views were defined from the 17,186 all-operator common-scalar addresses.
Each view used 2,048 fixed hash-ranked within-view gene-pair order coordinates.
Cell-pair geometry was evaluated strictly within donor×operator strata.
Donor was the primary aggregation unit.
The matched Y-view null reassigned Y-cell identities only within donor×operator depth/detection blocks.

### HVS
- sampled cell pairs before measurability filtering: 1,689
- measurable donors: 30
- observed median-Fisher donor correlation: **0.7975611**
- matched-null median: **0.4989747**
- matched-null p95: **0.5541568**
- matched-null max: 0.5738782
- PASS

### NPH52
- sampled cell pairs before measurability filtering: 2,541
- measurable donors: 16
- observed: **0.8007195**
- matched-null median: **0.5611960**
- p95: **0.5990585**
- max: 0.6187037
- PASS

### SEA_AD
- sampled measurable cell pairs: 21,365
- measurable donors: 46
- observed: **0.8782250**
- matched-null median: **0.7441524**
- p95: **0.7526606**
- max: 0.7546258
- PASS

The SEA_AD null used an algebraically exact precomputed distance-matrix implementation. Deterministic comparison against the naive per-cell-pair distance formula gave **max absolute difference 0.0**.

Frozen screen terminal:
`TD56S_DISJOINT_GENE_RELATIONAL_GEOMETRY_SURVIVES__FREEZE_DONOR_BLOCK_AND_CROSS_SOURCE_SCALE_GATE_NEXT`.

## Adversarial hash-ordering audit

The prospective wording says "unordered gene pairs" but does not explicitly state whether g/h in the pair-hash preimage follow view position or canonical numeric Molecular Ledger address order.

The complete screen was rerun with canonical numeric address ordering in the pair-hash preimage.

- HVS observed **0.8171162**, p95 **0.5610813** -> PASS
- NPH52 observed **0.8070469**, p95 **0.5984434** -> PASS
- SEA_AD observed **0.8783750**, p95 **0.7578417** -> PASS

Thus the pair-preimage ordering ambiguity is non-material to the terminal.

Pair sign orientation itself cannot alter the distance because flipping one pair coordinate's sign for every cell leaves absolute pairwise sign differences unchanged.

## Independent pair-subset robustness

To test whether the first 2,048 fixed pairs were an unusually favorable hash subset, the entire screen was repeated using the **next non-overlapping 2,048 hash-ranked pairs in each molecular view**.

- HVS observed **0.8208022**, p95 **0.5810706** -> PASS
- NPH52 observed **0.8158430**, p95 **0.6230301** -> PASS
- SEA_AD observed **0.8780424**, p95 **0.7525642** -> PASS

The result is therefore not dependent on one favorable 2,048-pair sample.

## Interpretation

This is the first current Target Discovery candidate to establish, label-free and donor-wise, that:

1. two **disjoint Molecular Ledger gene sets** encode strongly concordant within-donor cell–cell relational geometry;
2. the correct-cell alignment matters beyond a donor/operator/depth/detection-preserving wrong-cell null;
3. the effect reproduces in HVS, NPH52, and SEA_AD;
4. no latent-axis transfer, gene–gene dependency replication, clustering, state matching, graph matching, biological labels, or hidden-gene scalar reconstruction is required.

This is not yet a Foundation target.

TD56 does **not** establish:
- donor-block recurrence under held-out donor subsets;
- cross-source distance-scale comparability;
- partial-evidence / student-to-teacher predictability;
- production pair width;
- target dimensionality;
- JEPA training authority.

## Local artifact identities

Primary scripts/results:
- HVS script SHA-256: `a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43`
- SEA_AD exact fast script SHA-256: `c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866`
- HVS result SHA-256: `ac6dd050689952698ffd18a5bffcf0251132508e20f695eb675b5e7ddc246c4a`
- NPH52 result SHA-256: `caa190e708b632b106250f9d27272f1d3f32a88520539bcf9451ee8b9ee07be7`
- SEA_AD result SHA-256: `ec57015dbc1b1c0dab30ffd3429b8e400898402408868f1641e431beef14157b`

No biological labels were opened for TD56.
No target authority or JEPA training authorization.

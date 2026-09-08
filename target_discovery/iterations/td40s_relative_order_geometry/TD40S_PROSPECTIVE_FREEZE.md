# TD40S — Within-Cell Relative-Order Geometry validation screen

Status: FALSIFICATION_VALIDATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical check

This is not a return to PCA/REP, Signed-V2, same-gene dependency modules, source-specific subspaces, clustering, diffusion, or canonical axes.

The materially new object is a fixed within-cell ordinal relation over Molecular Ledger addresses. No loading, module membership, state label, cross-source map, graph alignment, or fitted coordinate system defines the feature.

Historical Signed-V2 is treated as a distinct learned/signed target family; no recovered historical artifact establishes that a pure within-cell relative-expression-order target was previously qualified.

## Candidate object

On any fixed set G of scalar-measured Molecular Ledger addresses for one cell, replace expression values by within-cell average ranks:

R_g = average rank of x_g among {x_h : h in G}.

Tied values, including measured zeros, receive the average tied rank.
Normalize ranks to [0,1] by (R_g-1)/(len(G)-1).

This preserves measured zero as evidence and uses only common-scalar addresses.
It is invariant to any strictly monotone cell-wide transformation of expression values and requires no source-specific axis.

The production candidate, if ever qualified, would be an address-resolved ordinal/relative-order object. The 512-gene panels below are validation probes only and cannot define production dimension.

## Validation panels

Use exactly the four deterministic 512-gene TD34/TD25 common-scalar panels:
sort the 17,186 all-operator common-scalar addresses by SHA256("TD25|<address>") and take consecutive blocks 0..511, 512..1023, 1024..1535, 1536..2047.

These panels were hash-defined, not outcome-selected, and permit direct comparison to TD34 on identical genes.

## Row binding and labels

Use B_COVERAGE_DISCOVERY with explicit global rows 25000..49999.
Never use B sample_row or a reset DataFrame index for CSR addressing.

The rank target definition and panels are frozen before opening native_class/broad_class.
After this freeze, labels may be opened for validation only.

## Exact TD34 validation scaffold

Use the already-frozen outcome-blind TD34 state rule:
native class present in HVS and SEA_AD with >=20 B-sample donors in each source; expected 19 states.

For each source/state/panel:
1. compute within-cell normalized rank vectors;
2. average within donor;
3. average donor means to obtain donor-balanced state centroid.

Compute the same standardized-gene Euclidean state-distance vector and HVS<->SEA_AD graph correlation used by TD34.

Run:
- RAW_RANK
- STATE_DEPTH_DET_RESID_RANK, using the same per-state median log1p(source_library) and log1p(detected_genes) residualization as TD34.

Subsets:
ALL19, GLUT, GABA, NONNEUR when >=4 states.

## Null

For each panel/preprocess/subset, repeat the complete SEA_AD state-label permutation null exactly 1000 times as in TD34. No state matching/search occurs.

## Fast survival rule

The simple rank-order target survives this validation screen only if:
- RAW_RANK GLUT graph correlation exceeds its own null p95 in all four panels; AND
- STATE_DEPTH_DET_RESID_RANK GLUT graph correlation exceeds its own null p95 in all four panels.

All19/GABA/NONNEUR are descriptive secondary validation and cannot rescue GLUT failure.

If either primary condition fails:
NO_RELATIVE_ORDER_GEOMETRY_EXPLANATION_OF_TD34__TD40S_KILL

If both conditions pass:
TD40S_RELATIVE_ORDER_GEOMETRY_SURVIVES__FREEZE_LABEL_FREE_MEASUREMENT_AND_DONOR_QUALIFICATION_NEXT

No label result can choose genes, pairs, thresholds, panel size, or production dimension.
No training authority.

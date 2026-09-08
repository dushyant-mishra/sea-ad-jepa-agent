# TD57C pre-freeze locality feasibility audit

Status: `METADATA_ONLY_PRE_OUTCOME_DESIGN_AUDIT`
Date: 2026-09-08

Purpose: choose the tightest local-neighborhood fraction that remains structurally estimable in HVS before any new TD57C expression outcome is opened.

Only A-sample donor/operator cell counts were used. No expression geometry, labels, pathology, or protected populations were inspected.

For a donor×operator stratum of n cells and neighborhood fraction q, the structural upper bound uses:
- candidate count `ceil(q*(n-1))`;
- anchored local triplet population `n * C(candidate_count,2)`;
- cap 64 sampled triplets/stratum;
- donor structurally eligible if the sum of capped triplets is >=20.

Results:

| q | HVS structurally eligible donors | NPH52 | SEA_AD |
|---|---:|---:|---:|
| 1/4 | 7 | 15 | 46 |
| 1/3 | 17 | 16 | 46 |
| 1/2 | 29 | 16 | 46 |

Nearest quarter cannot support a donor-half gate in HVS with >=4 donors/half.
Nearest third is the tightest tested fraction that can.

Therefore TD57C primary local selector fraction is prospectively fixed to **1/3** for the 50k falsification screen.

This is not a production k/fraction and cannot be carried into the 4,553,407-cell run without full-reader derivation.

To avoid learned-teacher circularity, TD57C will use a third **disjoint fixed concordance view Z** only to select the local candidate neighborhood. Two other disjoint views X and Y must then agree on distance ordering *inside* that Z-defined neighborhood.

No TD57C gene-view expression result has been opened.

Terminal:
`TD57C_LOCALITY_FRACTION_FROZEN_AT_ONE_THIRD__NO_TARGET_AUTHORITY`

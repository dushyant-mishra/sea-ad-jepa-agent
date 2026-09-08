# TD57B local execution binding

Status: `FROZEN_BEFORE_REAL_OUTCOME`
Date: 2026-09-08

Prospective screen:
`target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_PROSPECTIVE_SCREEN.md`

Repository implementation reference commit:
`ae18a2224cecb73daa3e4c748195dbde7c8f6b4f`

The exact local executor to be used for the decision-bearing 50k run is:

- path: `/mnt/data/td57b_fixed_relational_recurrence.py`
- SHA-256: `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`

No real TD57B Panel-0 or Panel-1 outcome was opened before this binding.

Synthetic pre-outcome checks on these exact local bytes:
- vectorized concordance distance vs naive formula: max absolute difference `0.0`;
- unordered-pair unranking exhaustive for sizes 2..11: PASS;
- anchored-triplet flat enumeration uniqueness for sizes 4..9: PASS;
- deterministic rejection sampler: exactly 64 unique in-range indices: PASS;
- all four new 512-gene views mutually disjoint: PASS;
- all four views disjoint from TD56/TD57A ranking positions 0..1023: PASS.

Pre-outcome pair-address array SHA-256 values:

Panel 0:
- X: `f0869188d5858777196896c98075907096ad6af9f98fead8a5692d57c57f6f13`
- Y: `ca01396a8214bafd2bddb4f1899427867401a04a86f347a3e738512918c2db6d`

Panel 1:
- X: `3e2ea8760b270a9a4b83104dea1d651bff49d6e6de45bf0c6d301b1cd191acd2`
- Y: `02f7059b1ec72908c369ca95acf00d58ae42249cdc1df99e935d7f2dc408000d`

Execution order remains:
P0 HVS -> P0 NPH52 -> P0 SEA_AD -> P1 HVS -> P1 NPH52 -> P1 SEA_AD.

Any failure stops subsequent execution.

No target or training authority.

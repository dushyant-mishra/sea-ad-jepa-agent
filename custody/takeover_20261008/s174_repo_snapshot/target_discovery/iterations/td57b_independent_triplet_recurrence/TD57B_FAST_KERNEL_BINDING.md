# TD57B exact fast-kernel binding before SEA_AD

Status: `FROZEN_BEFORE_SEA_AD_OUTCOME`
Date: 2026-09-08

Base local executor:
- `/mnt/data/td57b_fixed_relational_recurrence.py`
- SHA-256 `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`

Fast wrapper:
- `/mnt/data/td57b_fast_wrapper.py`
- SHA-256 `808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70`
- repository freeze commit `dfc08d570c29e76c5e3d58d593575a3ba8240f04`

The wrapper changes only the internal category-count matrix multiplication used by `distance_matrix`:
- frozen base uses int16 matrix multiplication;
- wrapper uses float32 GEMM followed by exact rounding to integer counts;
- all category counts are <=2048 and are exactly representable in float32.

No scientific choice, gene/pair/triplet selection, donor split, null, support rule, threshold, or PASS rule changes.

Pre-SEA equivalence checks:
- synthetic sign matrices at n=4,17,64,255: max distance difference `0.0`;
- HVS Panel 0: complete JSON equality with base executor;
- NPH52 Panel 0: complete JSON equality with base executor.

The first two base-executor attempts on SEA_AD timed out before producing an output file/result. No SEA_AD TD57B outcome was observed before this acceleration freeze.

The fast wrapper is therefore permitted for the remaining TD57B execution with identical scientific semantics.

No target or training authority.

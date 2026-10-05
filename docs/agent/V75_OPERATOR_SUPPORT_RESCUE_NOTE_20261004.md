# V75 operator-support rescue

Purpose: restore the V73 stress-twin zero-quota operator-support rescue that was lost in V74 calibration closure, without changing calibrated observation semantics.

## TDD evidence

1. **RED** — commit `a86bcc28a122bde1840c782a48327c948ef6269b` added the focused regression lane and the 2K invariant. GitHub Actions run `37261351716` failed in the pytest step after setup and compilation succeeded.
2. **GREEN** — commit `9e0ea8c0b6184a050149a42398c602f9e3e097f8` restored only the zero-quota support rescue in `scripts/v64/v73_full104_population_geometry.py`.
3. **Focused regression** — GitHub Actions run `37261417238` passed. Coverage includes 2K and 10K all-42/minimum-1 support, 100K minimum 4, 500K minimum 20, and FULL104 minimum 179 plus exact FULL104 triplet/count reconstruction.
4. **Inherited stress/calibration lane** — GitHub Actions run `37261417217` passed compilation, shard-invariance and empirical-calibration tests, and the 2,000-cell calibrated smoke/readiness step. The readiness gate remains limited to `100K_STRESS_ONLY`; it does not authorize 500K, FULL104, or training.

## Scope audit

Relative to V74, the production change is nine added lines in `scripts/v64/v73_full104_population_geometry.py`. The other changes are regression tests, focused CI, and this note. No calibrated RNA-QC authority, observation model, latent biology, source counts, or training authority changed.

No training authority is created by this repair.

# V26 independent reader-fit development proposal integration — CPU only

Date: 2026-09-25. **SYNTHETIC_TESTED_ONLY until exact frozen pass1 is physically presented; NO TRAINING AUTHORITY.**

## Why this narrow connection

Current V5's inactive one-update mechanics runner takes frozen `stable_cell_keys`, operator-homogeneous update cell selections and externally supplied scientific weights. PR #130 authenticated the frozen fit roster (104 donors, 4,553,407 cells) against the SHA-verified Aug24 bundle. PR #132 already implements an exact-byte frozen pass1 `cell_donor`/ `duniq` histogram cross-asset check, but not the update-level selection/proposal handoff. This adds **only** that handoff. It never loads an expression matrix or selects a target/mask.

`reader_fit_development_sampler_v1.py` **first executes the PR132 physical frozen-pass1/metadata bridge** (not a caller-supplied mock receipt), then rehashes and rereads the frozen pass1 through a single descriptor and revalidates the archived fit count map. The proposal draws each donor slot uniformly across 104; for each donor, draws distinct selection rows without replacement within a single update, keeping every presentation's **unconditional marginal** probability `q_i = 1/(104*n_d) = p_i`. Thus marginal importance `p_i/q_i = 1`. The joint slots are dependent, unlike IID replacement sampling; do not relabel the proposal IID. If a donor has more requested slots than eligible cells, **STOP** rather than silently redrawing donors, varying q or introducing duplicate stable cell keys. The existing V5 reference runner rejects duplicate stable keys, so this is a functional integration boundary, not a tuning choice.

Every draw is keyed by a SHA-256 over explicit `run_seed`, `update_index`, the frozen pass1 root and proposal ID, using NumPy PCG64. No historical seed, 128x8 geometry, EMA value, target, mask, source mass or operator mass is inherited. `presentations` is REQUIRED, not defaulted. The result gives selection-row identities, corresponding donor codes, explicit q vector, unit p/q vector and an unbound NONTRAINING receipt; actual expression/model consumers require independent FULL104 per-cell lineage, current target/visibility and training source authority.

**Scope of proof:**

- PR132 frozen pass1 hash: `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`.
- PR130 Aug24 calibration ZIP hash: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- Frozen population: 104 reader_fit donors, exactly 4,553,407 cells; reader_validation 22 and reader_oracle 23 excluded by exact roster check.
- `selection_rows` come from the genuine hash-pinned pass1 `cell_donor` and must be subsequently authenticated against original Level-4 metadata by the **existing** `verify_pass1_against_physical_full104`. The sampler does not certify that physical link. It does not read Level-4 blocks or run N1.
- No protected expression, foundation validation/holdout, pathology, Siletti, D_shared, or historic 94-donor Layer-2 artifacts opened. No V4 `production_update` and no training/model defaults.

**Red-team self-check:** The first proposal draft sampled cells *with replacement* and could yield duplicate `stable_cell_keys` in one update, which the existing V5 inactive reference explicitly rejects. Corrected to donor slots with replacement, cells within donor **without** replacement, with a hard oversubscription stop and adversarial tests. Its numeric per-presentation marginal remains donor-uniform, and the returned receipt explicitly identifies the dependence. That correction is necessary before any end-to-end V5 diagnostic integration.

Run synthetic test suite in `.github/workflows/v26-reader-fit-development-proposal.yml`; CI rejects skipped/missing positive and negative controls. A physical CPU selection operation on the GPU laptop remains a separately scheduled read-only execution using actual frozen source paths after all roots match. Even physical success is a **proposal/sample receipt**, not authorization to train JEPA or claim biological results.

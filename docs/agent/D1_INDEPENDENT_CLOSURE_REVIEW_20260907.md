# D1 Independent Closure Review — 2026-09-07

Base implementation candidate: `566079ad2ef4a1e99efff77bfc0bdb79559b77b7`

Status: `INDEPENDENT_REVIEW_IN_PROGRESS__NO_REAL_D1_EXECUTION_AUTHORITY`

This review is outcome-blind. No healthy trained teacher exists, no D1 production value has been emitted, and no protected population/pathology access is authorized.

## Review invariants

- Preserve the frozen D1 scientific authority unless an explicit prospective clarification is required.
- Do not use synthetic, historical 4,540-cell, or 50k auxiliary outputs to choose production values.
- Do not open reader-validation, reader-oracle, development, sealed, external, or pathology data.
- Keep the full real discovery population at the frozen reader_fit geometry when real D1 later becomes legal.
- Separate implementation repair from scientific authority changes.

## Independent defects found against 566079a

### D1-R1 — readout gate cannot ever open without editing implementation

`resolve_teacher_readout()` enumerates candidate readouts but sets
`unique_authorized_cell_level_state = False` unconditionally.
`resolve_production_readout()` unconditionally raises.

Therefore adding a future frozen representation/readout authority and healthy checkpoint cannot unlock D1 without changing source after outcomes/training exist. The implementation needs an external immutable readout contract parser/resolver.

### D1-R2 — healthy checkpoint is not actually bound to the exact readout contract

`load_teacher_qualification_authority()` accepts any 64-character
`readout_contract_hash`; it does not compare that hash to the selected canonical readout authority. `resolve_teacher_readout()` then promotes the checkpoint based only on checkpoint digest membership.

This contradicts the implementation claim that health is qualified under the exact readout contract.

### D1-R3 — current readout hash is the wrong object and creates a circular binding

The current `readout_contract_hash` is a hash of the dynamic resolver report, which itself includes checkpoint/qualification state. A checkpoint qualification is supposed to reference the readout contract hash, while that qualification state changes the resolver-report hash.

The canonical readout contract must be a separate immutable artifact whose hash is independent of checkpoint qualification.

### D1-R4 — Monte Carlo precision gate is not the frozen authority rule

`derive_D_end_to_end()`:
- checks precision only on null spectrum component 1;
- measures the width of the underlying null distribution rather than Monte Carlo endpoint error;
- does not check precision of D_PA-relevant component envelopes, real stability lower bounds, null stability upper bounds, or eigengap endpoints;
- proceeds even when the maximum replicate ceiling is reached without precision.

The authority requires deterministic sequential doubling until decision-bearing CI endpoints/subspace summaries meet the fixed computational precision target, otherwise `INSUFFICIENT_MONTE_CARLO_PRECISION`.

### D1-R5 — resampling path is not production-feasible as written

Every null replicate and donor-bootstrap replicate repeatedly calls `source.load()` for all lawful strata. If the production readout performs model forwards this re-forwards 4,553,407 cells for every replicate. Even if states are read from disk, the current design repeatedly rereads/recomputes cell-level moments instead of reusing frozen state materialization and donor sufficient statistics.

A production D1 path needs a one-time, hash-bound canonical teacher-state materialization plus reusable stratum/donor moment summaries, and incremental resampling that does not recompute prior replicates on every doubling step.

### D1-R6 — D1 downstream atlas is not end-to-end assembled

The commit assembles production D derivation, but required downstream discovery outputs remain isolated primitives or absent:
- full cell/program ranking orchestration;
- donor recurrence;
- source/operator heterogeneity;
- molecular-effect uncertainty;
- multi-axis block outputs;
- final ranked hypothesis catalog;
- end-to-end provenance tying those outputs to D/readout/checkpoint roots.

D1 cannot be considered implementation-closed until these are wired into a fail-closed post-D derivation driver.

### D1-R7 — old F1-u0 precision is incorrectly treated as a D1 readout authority dependency

The resolver treats historical F1 float32/autocast-off mechanics as a conflict that a future D1 readout must reconcile. The D1 authority requires an exact canonical readout seam; it does not authorize the historical u0 F1 execution root to define the future trained-teacher D1 representation.

The V2 canonical readout precision must be prospectively frozen independently. Future F1 can separately bind that same seam or define a tested parity bridge.

## Degeneracy clarification under review

The existing D1 authority says both:
1. near-degenerate axes form a joint subspace and individual axes inside the block are not identified; and
2. D is the largest leading rank whose stability remains separated for every leading rank 1..d.

Prospective clarification under review: evaluate the prefix rule only at admissible degeneracy-block boundaries, but preserve prefix monotonicity across those boundaries. A larger boundary may not rescue an earlier failed admissible boundary. This preserves the original fail-closed leading-prefix rule while avoiding tests inside an unidentified block.

No production outcome has been inspected; this can still be frozen prospectively.

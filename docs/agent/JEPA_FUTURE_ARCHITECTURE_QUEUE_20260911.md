# JEPA Future Architecture Queue — Observation Operators and Uncertainty

Date: 2026-09-11
Status: `FUTURE_ARCHITECTURE_QUEUE__NOT_PART_OF_T0_V2_EMERGENCY_REPAIR__NO_TRAINING_AUTHORITY`

## Purpose

This note preserves the high-value architecture ideas from the local project note `WSL execution issue.txt` without mixing them into the current T0 V2 / V21-T1 emergency repair closure.

The current T0 V2 work remains narrowly scoped to a review-ready repaired candidate: authority API restored, effect transport still open/fail-closed, no S0-S4 execution, no AT8, no validation/oracle opening, no freeze claim, and no training.

## Queue items

### 1. Technology as observation operator

Treat technology/assay context as an observation process `O_t`, not as a free biological covariate or unrestricted dataset embedding.

Conceptual direction:

```text
z_biology --O_t--> X_observed
q(z_biology | X_observed, O_t)
```

Allowed `O_t` features should have physical/experimental meaning: scRNA/snRNA, platform/chemistry, measured vocabulary, sequencing depth, detected-gene profile, count-split noise properties, and documented acquisition characteristics.

Forbidden as free observation identity shortcuts: donor ID, arbitrary matrix ID, unrestricted dataset embedding.

### 2. Invariance versus legitimate biological change

Do not make the state invariant to everything. It should be approximately invariant to measurement realization, sequencing noise, technical replicate variation, and irrelevant assay differences, but sensitive/equivariant to real cell state, cell type, tissue environment, brain region, donor biology, age biology, and genuine molecular context.

Avoid the crude objective “make technology impossible to predict.” Prefer: after controlling for comparable biology, measure how much unnecessary technology information remains.

### 3. Basis/subspace stability before freezing coordinate uncertainty

Before treating the 160-D state axes as coordinate-specific biological uncertainty channels, audit basis stability across donor-balanced resamples / leave-donor-group-out fits:

- principal angles between subspaces;
- canonical correlations;
- Procrustes-aligned similarity;
- coordinate stability;
- eigenvalue gaps.

If the subspace is stable but axes rotate, report uncertainty over stable blocks/subspaces rather than pretending each coordinate is independently meaningful.

### 4. Evidence-response curve for biological uncertainty

Define biological uncertainty by how inferred state changes as more molecular evidence becomes available, not by a single arbitrary mask.

For evidence fraction `p`, track:

```text
z_i(p)
C_i(p) = ||z_i(p) - z_i(100)||
Delta_i(p -> p') = ||z_i(p') - z_i(p)||
```

This supports panels, spatial assays, different technologies, and future multimodal evidence.

### 5. Separate measurement-depth response curve

For the same biological evidence, vary measurement depth/quality and track:

```text
z_i_depth(p)
```

Use this to separate biological uncertainty from measurement uncertainty.

### 6. Information efficiency

Future metric: minimum evidence required for a cell’s state to enter a stable neighborhood of its high-evidence reference. This may identify cells whose molecular state is redundantly encoded versus cells that require much more evidence.

### 7. Held-out dataset family and technology transfer

Beyond held-out donors and matrices, add held-out dataset/study and held-out technology tests where scientifically possible. A state that transfers to an unseen dataset family is stronger evidence of a reusable biological coordinate system.

### 8. Separate biological novelty from measurement/domain shift

Track at least two domain-support axes:

```text
D_measurement
D_biological_support
```

This avoids incorrectly dismissing rare but well-measured biological states as technical outliers.

### 9. Preserve donor variability

Do not automatically remove donor imprint. Some donor variation is nuisance, but some may be the biological signal of interest. A good model should distinguish unusual-but-well-measured biology from measurement/domain concern.

### 10. Hierarchical production sampling

Before real training, use a bounded hierarchical sampling design over dataset → donor → cell. Avoid uniform cells, where giant datasets dominate, and uniform datasets, where tiny datasets become overrepresented. Predeclare the weighting exponent or rule rather than tuning it on biological outcomes.

### 11. Keep the molecular ledger as the high-resolution escape hatch

The 160-D global state should be an accountable global coordinate system, not a replacement for all molecular detail. Preserve the 4096/address-resolved Molecular Ledger as fine molecular state.

### 12. Shared/context latent split only if evidence demands it

Potential future extension:

```text
z = (z_shared, z_context)
```

Do not add this preemptively. Only consider it if domain-direction analysis shows that real biology and technical acquisition cannot be adequately represented by the current single global state plus observation process.

## Priority order after T0 V2 repair closure

Very high:

- observation-process/operator abstraction;
- donor/matrix-balanced reproducible basis;
- basis/subspace stability audit;
- evidence-vs-depth convergence curves;
- conditional technology-imprint analysis;
- held-out dataset/technology transfer.

High:

- QC must earn measurement-channel access;
- separate biological novelty from measurement OOD;
- hierarchical production sampling before real training.

Do not implement yet:

- new nonlinear architecture;
- shared/context latent split;
- pathology-guided design.

## Boundary

This queue is **not** authority to alter T0 V2/V21-T1 repair, run S0-S4, open protected partitions, open reader_validation/oracle, train V5, or modify production biological semantics. It is preserved for planning after the repair candidate and its external review close.

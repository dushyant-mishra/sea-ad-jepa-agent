# JEPA Macha/V77 — S157 Phase-5 multimodal handoff audit

Date: 2026-10-06
Parent audit head before write: `858f0e888b657d23c4351c73b48bb68007d8cbd2`
Macha head audited: `b1d8ca9fb0f1d03102c8e117e2792b0e3b100326`
Status: `DOCUMENTATION_ONLY__REQUIREMENTS_ONLY__NO_OBJECT_SELECTED`

## What is sound

The Phase-5 handoff correctly treats multimodal evidence as a way to challenge explanations that RNA alone cannot distinguish. It also correctly preserves important boundaries:

- Morabito remains PROTECTED;
- SCENIC+ built from the same RNA is explicitly treated as circular rather than independent truth;
- Nott/ATAC/motif/perturbation/spatial/genetics/protein are candidate evidence objects, not selected winners;
- donor is the biological replicate;
- each evidence object must characterize its own measurement nuisance;
- no object, target, estimand, weighting or threshold is selected.

## Spillover correction: T2 is not removed by raw identity

The table says the operator-linked capture twin is `Removed only by raw dataset identity ... or a measured capture covariate`.

The S157 score receipt does not support `removed`.

Raw identity reduces operator-latent recoverability from about R2 0.872 to about 0.374, while the preregistered context-share statistic becomes separable. A substantial nuisance signal remains.

Correct wording:

`T2 IS CONTEXT-SEPARABLE_AND_SUBSTANTIALLY_REDUCED_BY_RAW_IDENTITY__NOT_ELIMINATED`

A measured capture covariate has not yet been demonstrated in this challenge, so it should be described as a prospective requirement, not a proven remover.

## Causal qualification: lawful observable is not automatically safe adjustment

Visible library size is lawful to observe, but it is jointly caused by biology and measurement. A real biological program can change total RNA/count depth. Therefore conditioning on library size can remove or distort biological signal as well as technical signal.

Similarly, measurable-address count is a legitimate measurement fact but identifies operator for 95.6% of test cells in the current challenge.

Thus future multimodal/measurement-context design must distinguish:

- observable provenance variables;
- causal technical measurements;
- downstream mixed biology+technology quantities;
- near-deterministic dataset-identity proxies.

Do not equate `lawful context` with `safe nuisance covariate`.

## Quantitative matching caveat for TWIN_OPERATOR

The BIO program is tied to a state containing 366 cells. The operator set selected prospectively reaches 571 cells because whole operators are added until the target count is crossed.

This obeys the preregistered construction and is not post-outcome tuning, but BIO and TWIN_OPERATOR are not tightly matched in affected-cell prevalence. Their quantitative R2 values therefore should not be interpreted as a clean effect-size comparison between equally strong biology and nuisance.

The exact twin does not have this problem and remains the stronger identifiability control.

## Evidence-object interpretation

Phase 5 should remain a requirements document, not a ranking. In particular:

- same-nucleus ATAC can help only if shared nuclear quality/capture is controlled;
- separate-nucleus/donor-level chromatin has stronger measurement independence but weaker cell-level attribution;
- Nott physical contacts establish possible wiring, not state activity or causality;
- motif evidence is sequence-level support, not proof the motif is active;
- SCENIC+ is only independent when constructed on data independent of the RNA being explained and still requires motif/annotation controls;
- perturbation needs demonstrated target engagement and lineage relevance;
- direct capture measurements would address T2 most directly but may not transfer gene-specifically.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.

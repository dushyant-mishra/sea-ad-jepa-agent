# Independent V7 teacher-fidelity gate red-team — 2026-09-27

Reviewed **committed** implementation/protocol at `b2ce421622ebe56d34155b11739f26840798abb7`, plus Claude's supplied same-mechanism eight-thousand-nucleus diagnostic. This audit has **not** run the forthcoming gate v3, has **not** opened real expression or protected readouts, and does **not** imply training authorization.

## What the evidence actually establishes

The previously constructed shams derive their capture dependence from observed `D`. In the reported simulation, the true program retains partial correlation with latent log-capture after conditioning on log D (+0.4437), whereas the two historical shams do not (+0.0031/+0.0092). A synthetic sham generated through the **same latent-capture mechanism**, with its own independent biological latent, resembles the real null-program amplitude in one seeded 8,000-nucleus diagnostic (partial residual readout association 0.1970 versus 0.1939; partial log-capture correlation 0.4410 versus 0.4520). That supports the mechanism-specific explanation, **not** proof of full exchangeability across donors, stratification, capture regimes or all model outputs.

### Finding V7-R1 (high) — present positive arms validate amplitude, not biological composition

In `scripts/v5/teacher_fidelity_synthetic_gate_v1.py`, `counts4(z)` assigns the SAME rate `base * exp(0.5*z) * cap` to all four partners. `zP` affects their common abundance; latent partner proportions are 1/4 each for every cell. In POS-1/POS-2, `zQ` correlates with `zP`, so positive outcomes can be explained by `log1p(sum(P))` alone. The observed sparse CLR carries sampling/pseudocount effects but has **no injected true compositional state**.

Therefore a future gate using this generator can demonstrate sensitivity to amplitude association, not sensitivity to a genuine four-partner-composition association. Preserve the frozen primary gate and state the limitation honestly; if composition-specific sensitivity is required, add a separate predeclared diagnostic with gene-specific log-ratio perturbations at fixed or explicitly controlled total abundance. Do not retrospectively attribute success to CLR.

### Finding V7-R2 (high) — model fallback must fail closed or be symmetrically predeclared

In `src/sea_ad_jepa/v5/teacher_fidelity_core_v1.py`, `_fit_nb` catches every exception and silently fits Poisson. It can disguise an NB convergence/design defect, change real/sham model families asymmetrically, and turn missing model evidence into green status. Record successful NB fits, alpha, convergence and exception provenance; treat unintended fallback as an explicit failing test, or prospectively declare and identically apply a bounded fallback before running any real outcome. Include a forced-NB-failure negative fixture and verify the pipeline refuses rather than certifies.

### Finding V7-R3 (high) — real-gene shams require independently validated nuisance exchangeability

Real genes from the same nuclei are sensible candidate nuisance controls, but being real does NOT guarantee matching gene-specific capture efficiency, dropout, ambient contamination, cell-type program covariance or relation to Q. Matching abundance, sparsity and within-quadruple coherence alone cannot guarantee equivalence of *residual capture information conditional on the fitted controls*.

Run the complete unchanged v7 statistical pipeline using generative real/sham nulls through the **same** latent capture mechanism and repeat calibration across the four frozen regimes and independent datasets. Then challenge it with **gene-specific** capture heterogeneity and ambient perturbations that were not used to choose the sham. Report the actual false-qualification rate and uncertainty. A partial-correlation match on one pooled simulation is not a substitute.

### Finding V7-R4 — selection and empirical-sham p-values need exact lineage

- Freeze the real-sham candidate pool and outcome-blind matching algorithm before looking at held-out Q outcomes. Use only fitting-donor expression/covariates and external prior biological exclusions for candidate ranking; don't use the held-out Q readout to choose shams.
- Record every candidate quadruple, per-gene availability, its cell/donor support and exclusion rationale. Additional real-gene extraction expands beyond the 29-address artifact and requires authenticated decoder paths for every newly consumed gene.
- `p=(1+#sham>=real)/(1+B)` requires an empirically justified null/reference distribution. Non-exchangeable or highly overlapping quadruples and outcome-aware candidate selection can invalidate its nominal p-resolution, even for B=999.
- The assertion that Q-related shams are always conservative is not established. A Q-related sham could make the test insensitive, and biased selection of anti-associated Q shams could make the observed statistic look anomalous. Measure these cases during null simulation and avoid universal claims.

### Decision and sequencing

Preserve `b2ce4216` and v1–v6 historical freezes. Finish gate v3 as planned with the same-mechanism sham and all four regimes; **the gate remains CLOSED unless calibrated NEG arms stay near nominal and POS arms retain sensitivity in independent datasets**. Do not tune negative-test thresholds, shams, or control definitions on real outcomes. If the frozen stopping rule fails, record `COUNT_READOUT_INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE` and separately prepare a composition-readout experiment with sparse-count and capture-specific validation. This is a statement about the validation method, not absence of the per-nucleus biological state.

No neural EMA training; no released protected readout; exact static-audit scope only.

# JEPA Macha/V77 — Background V2 S149 spillover audit

Date: 2026-10-06
Parent audit head before write: `ab8e2db1877ca080886832a2da3d7f8008c0dcfc`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

`v77_background_v2.py` was explicitly designed to imitate the old pooled real RNA dependence topology.

Its motivating targets include pooled values such as:

- expression median |corr| about 0.329;
- fraction |corr| > 0.3 about 0.562;
- top-10-PC variance about 0.509;
- mean degree about 1686;
- largest-community fraction about 0.824;
- transitivity about 0.860;
- substitute fraction about 0.198;
- T5 about 1.012.

S149 later showed that pooled topology is strongly entangled with study/coverage composition and is not a biological calibration target.

Therefore Background V2 cannot currently be called a qualified `realistic biological background` merely because it approaches those pooled numbers.

Current classification:

`BACKGROUND_V2 = S149_CONTAMINATED_AS_BIOLOGICAL_CALIBRATION__HISTORICAL_SYNTHETIC_GEOMETRY_EXPERIMENT_ONLY`

## Biological meaning

Background V2 teaches the simulator how to make a dense, highly connected gene-correlation graph. But the graph it was taught to imitate contains a large measurement/study component.

So matching that graph can bake the confounding into the simulator instead of reproducing biology.

## T5-specific spillover

The Background V2 comments treat pooled T5 ≈1.012 as evidence that real covariance is equally strong within classes and pooled.

The later within-cohort analysis gives materially different within-cohort T5 values (roughly 0.77–0.81 in eligible cohorts), and the current audit already classifies those as class-associated structure whose biological versus technical cause remains unresolved.

Thus pooled T5≈1.012 must not remain a biological target for background design.

## What survives

Background V2 remains useful as an engineering demonstration that broad/mid/narrow factors and substitute-like groups can change synthetic graph geometry.

That is simulator-mechanism knowledge, not real-biological calibration authority.

## Current S157 challenge is not invalidated by this finding

The S157 challenge builder uses the observer with `--background v1`, not Background V2.

Therefore the exact BIO/TWIN_EXACT identifiability result does not depend on the S149-contaminated Background V2 calibration.

## Future rule

Any successor background should separate:

- biological within-observation-process structure;
- measurement/coverage structure;
- donor variation;
- class-associated structure;

and should be calibrated prospectively to a selected estimand rather than to the historical pooled graph.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.

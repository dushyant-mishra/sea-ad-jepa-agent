# Independent gene-dependency recheck — 2026-09-08

Status: `FALSIFICATION_ONLY__NO TARGET OR TRAINING AUTHORITY`

Historical gate: `docs/history/foundation_target_discovery_prior_20260907/HISTORY_GATE.md`

Durable predecessor: `target_discovery/iterations/td19_claude_followup/TD19_DECISION.md`

## Conflict reconciliation

A local, non-durable artifact named `TD19_PSEUDOBULK_DEPENDENCY_REPLICATION.csv` reported HVS↔SEA_AD edge correlations about 0.33–0.51. Its exact SHA-256 is:

`e413fee49ee73247f4daaf58c5a786ab0f9ccc0a6c1bcd686c14aa49bc95ca30`

That result is **quarantined as unreproduced**.

The durable branch TD19 artifact,
`target_discovery/iterations/td19_claude_followup/TD19_PSEUDOBULK_DEPENDENCY.csv`
(blob `3dfa1e17ef5ea288adc164ec858a735e3d7a7ea8`), reports the opposite: cross-source dependency correlations approximately -0.0055 to +0.0070 while within-source reliability is positive. It is the historical source of truth.

Independent re-analysis was therefore performed from the frozen 50k archive rather than choosing between the two summaries.

## Independent checks

### Across-donor pseudobulk dependency after nuisance/composition attacks

Four independent common-scalar panels were tested in shared HVS↔SEA_AD Glutamatergic/GABAergic broad classes and in outcome-blind exact-native classes (L2/3 IT and Vip). Donor depth, detected-gene count, and operator composition were residualized.

Median cross-source edge correlations remained approximately zero and did not clear a gene-identity permutation null matched on mean expression/detection.

Decision-table SHA-256:
`895043fcb059068afd811ab9299bc8af8d1dd765ebc1b34c826d77225db92e71`

### Measurement-estimability sweep

The 17,186 all-42-operator scalar addresses were stratified only by within-source split-cell donor-pseudobulk gene reliability. Even the top 10% reliability stratum (median per-gene reliability roughly 0.72 HVS / 0.67 SEA_AD for Glutamatergic) retained donor-block dependency structure within each source but cross-source edge correlation remained approximately zero.

Summary SHA-256:
`78de9d711f303db9bbde37e71ebd84b76322c1a89157344a0b8d2e1b3df0d72c`

### Within-donor between-cell Pearson dependency

To avoid the across-donor cohort-covariance estimand entirely, correlations were computed within donor, then Fisher-z averaged with equal donor weight. Top-quartile jointly detected common-scalar genes, broad classes, and exact-native classes were tested. A within-donor nuisance model removed source-library depth, detected-gene count, and operator one-hot effects.

Cross-source geometry again remained approximately zero despite positive donor-block recurrence inside source and did not clear matched gene-identity nulls.

Summary SHA-256:
`fa86bae4fe03e7e6384f21750c2b2255579bcf3aa3b97d44b47e92d8fba242d8`

### Within-donor Spearman dependency

The same design was repeated with within-donor Spearman correlations to allow arbitrary per-gene monotone capture transformations. Broad Glutamatergic donor-block reliability was about 0.53 HVS / 0.70 SEA_AD, yet median HVS↔SEA_AD edge correlation was only about 0.02 and did not clear the matched null. Other strata were similarly null.

Summary SHA-256:
`ad0e0a65a92a74e0446f108e1b893c3ac274e0441b4b2b478cb1aba95c9173ea`

## Current adjudication

These independent checks reproduce the durable TD19 conclusion rather than the conflicting positive local artifact.

`UNIVERSAL_SAME_GENE_DEPENDENCY_GEOMETRY_NOT_ESTABLISHED`

This does not prove that no source-specific module is biologically useful. It does block promotion of a module target whose cross-source qualification requires the same gene-gene dependency geometry or same transferred module membership.

The next prospective branch hypothesis remains the already-declared:

`TD28_LABEL_FREE_RELATIONAL_ALIGNMENT`

State discovery must be label-firewalled. Graph matching must be repeated inside every null. Common-scalar addresses only. Depth/QC pseudo-state geometries are mandatory competing nulls. Any later taxonomy opening is interpretation-only.

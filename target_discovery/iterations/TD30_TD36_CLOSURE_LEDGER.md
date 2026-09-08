# TD30–TD36 closure ledger

Status: `FALSIFICATION_ONLY__NO_TARGET_AUTHORITY`

## TD30 — diffusion/heat-signature label-free alternative
Coordinate-free donor×operator geometry did not qualify.
- HVS↔NPH52 trace p=1.0, assignment p≈0.970.
- HVS↔SEA_AD assignment p≈0.0303 but trace p≈0.970 and depth trace was better; insufficient.
- NPH52↔SEA_AD fails.
- Within-source donor-half trace/assignment does not beat null p05 for HVS, NPH52, or SEA_AD.

Decision:
`NO_VALID_LABEL_FREE_DIFFUSION_TARGET_ESTABLISHED`.

Local hashes:
- script `bcc824c499e92c2d98dce9b71d7d313ae0dc86aa199676757e01204432614adc`
- cross CSV `e7b44382f5cd047fdcd4063738c1bf51e00cdfd9df2bcc3276610b965f9958ae`
- within CSV `70a1ca2688a67a6af8c473f0d2babdbe456f4351778db672306adc662da3b788`

## TD31A/31B/32 — invalidated apparent positives
These runs appeared to show large source-internal donor-half/count-split subspace recurrence. They were later found to belong to the reset-index B-row failure family: after a pandas merge, reset DataFrame indices 0–24,999 were used as CSR rows instead of global B rows 25,000–49,999.

They are retained only for forensic traceability and are not positive evidence.

## TD33 — global-row binding guard
B rows = 25,000; global row range 25,000–49,999; sample_row range 0–24,999.

Global-row inverse-log1p integer recovery:
- fraction <1e-8 residual = 1.0
- maximum residual = 3.55e-15

Reset alias:
- fraction <1e-8 = 0.0002
- median residual = 0.2523

Decision:
`PASS_GLOBAL_ROW_BINDING__RESET_INDEX_FORBIDDEN`.

Local script SHA:
`0c3907c0a91a0d72056f068769891fe786062001967accae98de05bae0f21190`.

## TD34 — global-row-guarded annotated state geometry
Four 512-gene common-scalar panels, 19 outcome-blind pathology-blind states shared by HVS/SEA_AD with >=20 B-sample donors/source.

Median r:
- RAW ALL19 0.9016
- RAW GABA 0.7835
- RAW GLUT 0.9161
- STATE_DEPTH_DET_RESID ALL19 0.7141
- residual GABA 0.7428
- residual GLUT 0.8603

All exceed state-label permutation nulls.

Classification:
`ANNOTATED_RELATIONAL_SCAFFOLD_REPRODUCES__VALIDATION_ONLY`.

Script SHA:
`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`.

## TD35 — corrected source-wide source-conditional subspace
Correct global rows + independently fit preprocessing per donor half.

Median overlaps:
- HVS rank2/4/8 0.1691 / 0.1265 / 0.1883
- NPH52 0.1329 / 0.1507 / 0.2387
- SEA_AD 0.1572 / 0.1685 / 0.1968

Most ranks fail the all-splits null criterion; principal angles are large.

Classification:
`NO_ROBUST_SOURCE_GLOBAL_SUBSPACE_TARGET_ESTABLISHED`.

Script SHA:
`cfcd15a34c9db3b369e6bcd35a580629d7232175c4fd0176bcca66334294104b`.

## TD36 — class-conditioned source-specific subspace
Top three abundant B-sample native classes/source among classes with >=20 donors.

HVS: L2/3 IT, Oligodendrocyte, L4 IT.
SEA_AD: L2/3 IT, Astrocyte, L4 IT.

Across ranks 2/4/8 and four donor splits, no class/rank summary has `all_gt_all_null=True`. Typical median overlaps are ~0.01–0.16 with principal angles ~85–90 degrees.

Classification:
`NO_SOURCE_CONDITIONAL_CLASS_SUBSPACE_TARGET_ESTABLISHED_IN_CORRECTED_50K_PILOT`.

Script SHA:
`022f1eb39e6b37d8af875540c5dc58e740d3f72f326a94b1d48286d13c02e308`.

## Overall terminal after TD36
`NO_VALID_TARGET_ESTABLISHED_YET__ANNOTATED_RELATIONAL_SCAFFOLD_REPLICATES_BUT_NO_LABEL_FREE_OR_SOURCE_CONDITIONAL_TRAINABLE_OBJECT_QUALIFIED`

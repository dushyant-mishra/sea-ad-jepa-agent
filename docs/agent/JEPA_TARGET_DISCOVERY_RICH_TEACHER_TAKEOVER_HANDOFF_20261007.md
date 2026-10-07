# JEPA target-discovery / rich-teacher takeover handoff — 2026-10-07

Status: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__TRAINING_OFF__REAL_RNA_STAGE_A_NOT_AUTHORIZED`

This is the controlling handoff for the target-discovery / teacher-target scientific lane. It records current conclusions, supersessions, local file custody, exact historical artifact locations, and the next work order. Historical methods may remain useful even when later provenance findings invalidate their biological numerical conclusions.

## 1. Hard boundaries

- Training OFF.
- Stage-A real-RNA execution OFF until current expression authority is semantically qualified.
- Multimodal training OFF.
- 500K NOT AUTHORIZED.
- Stage 4 NOT AUTHORIZED.
- NIH-CARD real biological correspondence remains unopened.
- TEST/SEALED remains sealed.
- Morabito protected.
- TARGET_WINNER = NONE.
- REPRESENTATION_WINNER = NONE.
- Current Phase-A eligible population authority = 13,510 cells; historical 4.55M reader-fit104 is not current Stage-A population authority.
- Do not use pathology, DEV, SEALED, reader-oracle, or protected external outcomes to tune target design.
- Runtime/interface reconciliation is a separate active lane; do not collide with it or merge old runtime branches wholesale.

## 2. Most important current correction: HVS / SEA-AD physical feature-column defect

Immediately before this handoff the audit branch was at `be522a911002f53f0f225f602e125cbeb29eca37`, containing:

`docs/agent/JEPA_FULL104_HVS_SEAAD_FEATURE_AXIS_SEMANTIC_INVALIDATION_20261007.md`

The late V46 provenance audit establishes that historical `HVS_COMMON` and `SEA_AD_COMMON` provenance `source_feature_index` is an Ensembl-harmonized rank, not the physical H5AD matrix column index. Historical HVS/SEA-AD Level-4 materializers used sparse H5 `indices` (physical columns) to index that mapping directly. A canonical address could therefore receive counts from the wrong physical gene while every downstream positional/hash check still passed.

Current classification:

`FULL104_HISTORICAL_MIXED_SOURCE_BIOLOGY_NOT_REQUALIFIED__HVS_SEAAD_LEVEL4_FEATURE_AXIS_INVALID`

The historical `TEACHER_BIOLOGY_LIMIT / D_shared = null` is now a procedural historical result only; its scientific terminal requires corrected feature-axis replay. This does not imply that the result will reverse after repair.

NPH52 is a separate lineage and is not invalidated by this specific HVS/SEA-AD finding.

## 3. Critical retraction from this chat: 50K discovery expression is not fully requalified

Recovered source:

`foundation_materialize_discovery_expression.py`
SHA-256 `ede646be8030ef1644d27496a98eb4661e1c95e4043bc44a6d520e81b7d0228f`

It reads:

`results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`

and for HVS/SEA-AD constructs:

`source_feature_index -> molecular_address_index`

then indexes that mapping with raw sparse H5 `indices`.

Therefore the same semantic defect plausibly affects the HVS/SEA-AD portions of the historical 50K discovery NPZ. The earlier chat classification `DISCOVERY_EXPRESSION_ADDRESS_AXIS_PRIMARY_SOURCE_VERIFIED` is superseded for HVS/SEA-AD.

New conservative classification:

`DISCOVERY_50K_NPH52_AXIS_PRIMARY_SOURCE_VERIFIED__HVS_SEAAD_PHYSICAL_COLUMN_BINDING_NOT_REQUALIFIED`

Do not use TD34/TD41 mixed-source numerical biology as decision-grade evidence until HVS/SEA-AD 50K expression is rematerialized or independently proven against physical feature order.

NPH helper:

`foundation_materialize_nph_discovery_sample.R`
SHA-256 `c463688e87cbac14ad0ebd07716d160256ff1347731896e7945963f3a3d2f611`

uses a separate NPH source-count matrix path and was not implicated in the HVS/SEA-AD H5 physical-column defect.

## 4. Local/runtime custody and large-file policy

A top-level custody manifest and a ZIP-member custody manifest are preserved under:

`docs/agent/archive/chat_runtime_20261007/`

Large binary bytes are not inserted into ordinary Git history. Their exact size/SHA-256 and archive-member inventories are preserved. Do not claim a large binary is physically in GitHub merely because its hash is recorded.

Key current runtime files:

### Historical 50K expression

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
  - 303,979,881 bytes
  - SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
  - 303,979,880 bytes
  - SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- checksum manifest SHA-256 `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356`
- reassembled ZIP identity previously verified: 607,959,761 bytes, SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- contained historical NPZ: 50,000 x 41,238 CSR, SHA-256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

Exact custody is proven; HVS/SEA-AD column semantics are not.

### Discovery audit / lineage

- `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` SHA-256 `c0f1f68fd3af9b95479fdc05536533481bd42710bc67a94a1c4996d4e4fe3b39`
- `FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json` SHA-256 `223b9deec03767d9bb260f530717803fed20e67d737d99107efbb731886abe48`
- `expression.zip` SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`

These bind historical execution and payload reproduction, but do not rescue a wrong physical feature lookup.

### Checkpoints

- `checkpoints.zip` SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`; includes u0 and u205.
- `t1_checkpoint_u0200.zip` SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`; includes u10/u25/u50/u100/u200.

### Other high-value custody files

- Nott Table S5 `NIHMS1066836-supplement-Table_S5.xlsx`, 36,876,140 bytes, SHA-256 `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`.
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`.
- `v77-suite-junit.zip` SHA-256 `bdcbfb1e4a468801f9e4e6ca4b71cd2987ee57f84de2ae2d10c3be437d8eed62`.

## 5. TD34 / TD41 genealogy and exact locations

### Sept-7 target-discovery archive

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

- SHA-256 `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- 97 members.

Contains the original producer:

`scripts/td_iteration34_state_geometry_globalrow.py`

SHA-256 `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

It also contains actual TD23-TD36 scripts/results: row-alias forensic, corrected depth attack, TD25 state geometry, TD29A falsification, TD30 diffusion, TD31A/B source-conditional work, TD32 count split, TD33 global-row guard, TD34 state geometry, TD35 source conditional, TD36 class-conditioned subspace.

Historical terminal remained `NO_VALID_TARGET_ESTABLISHED_YET`.

### TD34 panel selection

Recovered TD34/TD41 code shows panel membership came from the strict common scalar universe across 42 operators, yielding 17,186 addresses. Four 512-address panels were deterministic blocks after SHA-256 ordering of `TD25|<molecular_address>`.

Independent reconstructed membership hashes:

- A `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- B `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- C `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- D `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

Panel selection itself is largely independent of RNA values. Numerical TD34/TD41 biology is not.

Current classification:

`TD34_PANEL_SELECTION_GENEALOGY_RECOVERED__HVS_SEAAD_EXPRESSION_VALUE_BINDING_REQUIRES_REQUALIFICATION`

## 6. TD41-TD58 working archive

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

- 92,478,083 bytes
- SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`
- 155 members.

Important members include:

- `repro_td41.py`
- `exact_kendall_state.py`
- `TD43_RECONSTRUCTED_24_CASES.csv`
- `run_td51s.py`, `td51s_result.npz`
- `run_td55s.py`, `td55s_result.npz`
- TD56 HVS/NPH52/SEA-AD scripts and NPZs
- TD57/57A scripts and NPZs
- `td57b_fixed_relational_recurrence.py` and p0/p1 JSONs
- `td57c_three_view_local_geometry.py` and post-failure forensic JSON
- `run_td58_source.py` and TD58 source result NPZs.

Historical audit interpretation:

- TD55 query-specific proxy selection did not transport cleanly to NPH52; do not promote.
- TD56-TD58 repeatedly recovered donor-level relational geometry across independent gene views and partial RNA.
- TD57C primary failure remains a failure; its post-failure forensic diagnostic cannot rescue it.
- TD56-TD58 support the existence of shared/predictable relational structure, not full rich-teacher identifiability.
- Because HVS/SEA-AD discovery expression is now semantically suspect, mixed-source quantitative conclusions require corrected replay. NPH-only subresults may be separately salvageable after exact dependency review.

## 7. Core rich-teacher / partial-student scientific rule

The project is building a world model of cellular molecular state, not hidden-gene imputation.

Keep separate:

1. teacher fidelity: the teacher may use the richest lawful biological evidence needed to construct a faithful state;
2. student withholding: the student receives partial lawful evidence and query identity;
3. shortcut prevention: withheld information must not leak through values, normalization, QC descendants, copied embeddings, or observation metadata.

A deterministic student cannot be expected to reproduce teacher-private information. For squared error, the best possible deterministic student is conceptually `E[z_teacher | student_evidence, q]`, not the exact realized rich-teacher vector when the latter contains information unavailable to the student.

Therefore every target component should eventually be classified as one of:

- `RECOVERABLE_FROM_VIEW`
- `PARTIALLY_RECOVERABLE_FROM_VIEW`
- `NONRECOVERABLE_FROM_VIEW`
- `NOT_IDENTIFIED`

A biologically meaningful nonrecoverable component is not automatically model failure. It should be excluded from deterministic point-matching or represented through uncertainty/distribution/abstention.

## 8. Historical branches and what they actually established

### T1 / contextual mechanism

Important historical mechanism result:

- u0 already contained useful correct-cell/query-aware contextual biology.
- T1 training lowered its mathematical loss while eroding fine query-local/contextual geometry.
- a later large contextual predictor run over 4.785M queries showed real donor-reproducible latent improvement, but ~95% of correct-memory advantage was cell-global; attention entropy ~0.998, query routing cosine ~0.991, program-matched memory enrichment ~1x.
- all four adjudicators denied promotion.
- strict donor-cross-fitted residual-target rescue was later executed and did not rescue protected biology.

This is strong evidence that lower teacher-matching loss can coexist with worse biology.

### FULL104 D_shared / D_private

Historical FULL104 shared-state branch ended at `TEACHER_BIOLOGY_LIMIT`, `D_shared = null`. That branch was explicitly closed at the time. Now, because its deciding mixed-source expression substrate includes semantically invalid HVS/SEA-AD Level-4 values, its biological terminal is additionally not decision-grade pending corrected replay. Do not use it as evidence that the corpus lacks shared biology.

### CONTEXTUAL_TEACHER_TARGET_V1

Historical definition:

`T_q(c)=LayerNorm(H_T_safe(c,q)-mean(H_T_safe(c,rich eligible context)))`

`S_q(c)=LayerNorm(H_S_safe_partial(c,q)-mean(H_S_safe_partial(c,visible eligible context)))`

F0 implementation/leakage mechanics passed. Real F1 did NOT run in the recovered Sept-3 lineage. Historical state explicitly says real reader/forward authority was not frozen and training was not authorized. Do not revive the planned 474,188-forward F1 unchanged, especially because its FULL104 HVS/SEA-AD substrate is now invalidated.

### R5 measured-target work

Project Library file: `JEPA_TOURNAMENT_R5_TEACHER_TARGET_REPORT_20260926.md`.

R5 made a key conceptual correction: the teacher used genuine richer same-cell measurements, while the student received complementary RNA and q identity. The measured target was an eight-other-gene same-cell q-context, not the queried scalar itself.

But it remains developmental only. Historical decision record says:

- APOE complementary-RNA predictability was encouraging in one disjoint-reference diagnostic (heldout R² ~0.355 vs technical ~0.088), but prespecified separate RNA readouts were not successfully predicted in R7;
- P2RY12 and HLA-DRA did not consistently outperform technical baselines;
- no program passed independent chromatin/protein fidelity;
- normalization remained an unresolved scientific estimand/leakage route.

Current classification: `MEASURED_TARGET_DEVELOPMENTAL_ONLY__NEURAL_TARGET_UNQUALIFIED`.

## 9. Multimodal implication

ATAC, SCENIC+, and other modalities may improve teacher fidelity and should not be discarded merely because the student lacks them. But teacher-only evidence must not automatically become a deterministic student regression target.

Ask separately:

- what richer biological components are faithfully represented by the teacher?
- which are conditionally predictable from partial RNA?
- which are teacher-private and therefore should appear as uncertainty / conditional distribution / abstention?

The project contains uncertainty concepts (evidence-response curves, depth-response curves, biological vs measurement uncertainty, abstention), but this audit did not recover a qualified foundation predictor distribution head for `p(z_teacher | partial RNA, q)`. Historical foundation objectives were still primarily deterministic latent matching.

## 10. Current V3 premise contract: correct science, incomplete machine enforcement

The current V3 premise work correctly distinguishes target meaning from recoverability and explicitly allows partial/nonrecoverable components. It also distinguishes preservation failure, inference limitation, and uncertainty failure.

Audit gap: machine enforcement is still primarily top-level. It does not require an end-to-end per-component recoverability ledger. Before Stage A, mixed rich-teacher targets should be required to expose component-level recoverability so a biologically important nonrecoverable component cannot be averaged away behind a family-level PASS.

## 11. S149 / Macha still constrains all target work

Historical pooled topology was strongly confounded by study/source composition; the S149 audit found the null edge density was ~88.85% of observed and within-source structure was much weaker. Historical within-cohort bootstrap was also cell-weighted rather than a selected donor-level estimand.

Therefore:

- pooled source topology is not target biology authority;
- do not simply regress out study and claim closure;
- select/freeze a donor-level population estimand prospectively;
- source/operator should be support/observation structure, not a free biology identity shortcut.

## 12. Eligible-donor estimator bundle

`TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_20260909.zip`

SHA-256 `206e11c606fc8631c1e527549655fb0f21087cb31e54320ce026d5e2f04fa3c7`, 25 members.

Useful principle: equal donor mass and no exclusion merely for cell count/source size. Not current Stage-A population authority; it belongs to historical reader-fit104. Reuse the weighting principle, not the 4.55M population.

## 13. Runtime/interface lane: do not collide

Separate active work includes PR #223 shared qualification interface, PR #222 runtime safety, and the canonical V5 successor branch. Canonical runtime ordering remains:

`authenticated/q-safe 41K input -> encoder -> predictor -> EMA teacher -> loss -> backward -> CurrentTrainingAuthorityV2 -> OptimizerGuardV4 -> guarded step -> completion assertion -> EMA -> authority-bound checkpoint -> deterministic reload`

Target archaeology does not authorize training or runtime mutation.

## 14. Exact next work order

### P0 — repair expression semantics before real target execution

1. Recover/authenticate matrix-specific physical feature order for every HVS and SEA-AD matrix used in current Stage-A, historical 50K, and FULL104.
2. Build exact mapping: `canonical molecular address -> source feature identity -> matrix-specific physical column -> raw count slot -> canonical output column`.
3. Never use `HVS_COMMON` / `SEA_AD_COMMON` harmonized-rank `source_feature_index` as H5AD physical column.
4. Exhaustively verify all decision-bearing addresses; spot checks are insufficient.
5. Re-materialize affected HVS/SEA-AD expression under new hashes/roots. Preserve historical invalid bytes; do not overwrite them.
6. Independently reconstruct sampled rows/genes from the source to prove semantic correctness.
7. Recompute only results whose deciding numerical inputs actually changed.

### P1 — build a target-evidence supersession table

For TD34, TD41-TD58, T1, contextual V1 F0/F1, R5-R8, FULL104 D_shared, V61 and V77 target-related work, classify:

- substrate valid / invalid / unaffected;
- target meaning valid / developmental / invalid;
- student recoverability tested / untested;
- query leakage closed / open;
- estimand current / historical / invalid;
- current decision authority YES/NO.

### P2 — repair Stage-A target governance

Add machine-readable component-level recoverability states (`RECOVERABLE`, `PARTIAL`, `NONRECOVERABLE`, `NOT_IDENTIFIED`) and freeze the biological estimand/donor weighting before outcomes.

### P3 — prospective target families after P0/P2

No winner now. Compare only prospectively:

1. measured/query-local contextual state;
2. donor-balanced global/program state;
3. structured combination only if it adds independent information;
4. rich multimodal teacher components, first for teacher fidelity and only then for RNA conditional predictability.

Every family must beat appropriate query-only, generic-cell, technical, wrong-cell/matched-null controls and must separate biological fidelity from student recoverability.

### P4 — replay only decisive historical probes after corrected data

- minimal TD34/TD41 checks;
- decisive TD56-TD58 relational probes;
- keep NPH-only evidence separate from mixed-source evidence;
- do not replay the entire historical zoo.

### P5 — external biological fidelity after mechanics pass

Use RNA/ATAC/SCENIC+ assets under exposure constraints. Nott is same-study specificity/prevalidation, not independent AD replication. Morabito exposure history must be honored. NIH-CARD protected Stage 3/4 remains unauthorized unless current authority explicitly changes.

## 15. First files for the successor to read

On `handoff/jepa-20261006-macha-audit-successor`:

1. `docs/agent/JEPA_FULL104_HVS_SEAAD_FEATURE_AXIS_SEMANTIC_INVALIDATION_20261007.md`
2. this handoff
3. `docs/agent/archive/chat_runtime_20261007/CHAT_RUNTIME_FILE_CUSTODY_20261007.csv`
4. `docs/agent/archive/chat_runtime_20261007/CHAT_RUNTIME_ZIP_MEMBER_CUSTODY_20261007.csv`
5. archived `foundation_materialize_discovery_expression.py`
6. archived `foundation_materialize_nph_discovery_sample.R`
7. archived `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`
8. archived `FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json`
9. archived `td_iteration34_state_geometry_globalrow.py`

Then historical Library/GitHub:

- `JEPA_SCIENTIFIC_DECISION_RECORD_20260926_V2_CORRECTED_MORABITO.md`
- `JEPA_TOURNAMENT_R5_TEACHER_TARGET_REPORT_20260926.md`
- `JEPA_DETAILED_NEW_CHAT_HANDOFF_20260825_1534.md`
- `JEPA_DETAILED_NEW_CHAT_HANDOFF_V015_20260826(1).md`
- `JEPA_FORENSIC_MATHEMATICAL_ENVIRONMENT_HANDOFF_V3_20260902*.md`
- Sept-7 target-discovery handoff / `target_discovery/HANDOFF_CURRENT_20260907.md`
- current V3 premise qualification design/state/Stage-A gate on `main`
- current S149/Macha audit checkpoints.

## 16. Do not conclude

Do not say the target is fixed; TD41 is qualified; D_shared failure proves no shared biology; the teacher must be impoverished to match the student; the student should reproduce teacher-only multimodal evidence exactly; HVS/SEA-AD 50K or FULL104 gene columns are currently semantically qualified; real F1 passed; Morabito is pristine independent validation; Nott validates AD biology; or training is authorized.

## 17. Current scientific state in one sentence

Let the teacher use the richest lawful biological evidence to construct the best state we can justify; then identify which components are conditionally recoverable from partial RNA and train the student only against those components, while representing teacher-private information as uncertainty/abstention rather than as an impossible deterministic matching error — but first repair the HVS/SEA-AD physical feature-axis binding and make component-level recoverability machine-enforced.
# Stage81A2R/A3R Full-Transcriptome Microqualification Readout

**PROVISIONAL DEVELOPMENT EVIDENCE - NOT FROZEN**

## Scope And Chronology

This successor experiment starts from checkpoint `63a29ed74af4bb624e9a574b404692f091b6f13f` on branch `stage81a2r-a3r-microqual-20260813`. It does not rewrite the frozen Stage81A2 contract or any historical Stage81A3 evidence. The frozen 4,096-gene result remains valid evidence about the architecture actually tested; it is not treated as a biological saturation result. This microqualification decouples `G`, `d_gene`, and global-state resolution and stops before any freeze or production trajectory.

## A2R Candidate Registry

- Maximal exact stable-ID address space from authorized frozen source metadata: **37,346 genes**.
- Source feature decisions: **299,775** total; **193,646** exact retained; **106,118** ambiguous unresolved.
- Stable Ensembl IDs with source-release symbol conflicts: **535**. The stable identity was retained and the display-symbol preference was documented; no fuzzy lookup or arbitrary identity tie-break was used.
- Candidate semantic hash: `d9d8b08bcf8e88b73d2f5483b573767c49b47ff661da57b99c5b5aab828aa8a2`.
- No biological top-K was used.

### Measurement support

The complete support table has 42 matrix contracts and 1,568,532 matrix-gene rows. A measured zero is always distinct from a structurally unmeasured gene.

- `HVS_COMMON`: 24 matrix/matrices, 18,717 measured genes per matrix
- `NPH52::Astro_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 19,769 measured genes per matrix
- `NPH52::Endo_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 19,143 measured genes per matrix
- `NPH52::ExN_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 20,403 measured genes per matrix
- `NPH52::InN_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 20,044 measured genes per matrix
- `NPH52::MG_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 19,432 measured genes per matrix
- `NPH52::OPC_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 19,412 measured genes per matrix
- `NPH52::Oligo_data_arranged_updatedId_final_batches.qs`: 1 matrix/matrices, 20,121 measured genes per matrix
- `SEA_AD_COMMON`: 11 matrix/matrices, 36,571 measured genes per matrix

## Full-G Token-Preserving Mechanics

- `G=37,346`, `d_gene=160`, six blocks, four heads, FP16 CUDA autocast, gradient checkpointing.
- Three bounded probes: microbatch 1, 8, and 16. All completed two finite optimizer plus EMA updates.
- Selected practical microbatch: **16**.
- RTX device: `NVIDIA GeForce RTX 3080 Laptop GPU`; peak allocated/reserved at selected probe: **9.73/10.18 GiB**.
- Selected-probe step times: 2.551s and 2.377s.
- Finite outputs/losses: `True`; optimizer state: `True`; EMA update: `True`; Pearson graph invoked: `False`.
- Classification: **MECHANICALLY FEASIBLE**. **`d_gene=160`: FULL-G MECHANICALLY FEASIBLE; CONTEXTUAL CAPACITY UNRESOLVED.** No supported contextual-state capacity failure was demonstrated, so no width-256 comparison was authorized or run.

## Molecular Ledger And Synthetic Biology

The candidate package explicitly retains canonical IDs, normalized observed expression, measurement support, and contextual gene states. Therefore complete-Ledger molecular recoverability equals raw normalized-RNA recoverability by construction; contextual states alone are not mislabeled as the complete Ledger.

- **overlapping_programs:** global-preserved `broad, broad`; global-attenuated `subtype, subtype, state, state, fine, rare, donor`; raw-data-limited `none`.
- **rare_tail_difficult:** global-preserved `broad, broad`; global-attenuated `subtype, subtype, state, state, fine, donor`; raw-data-limited `rare`.

No raw-recoverable factor was lost from the complete Ledger package. Several subtype, state, fine, rare, and donor factors were attenuated in the unsupported 16-D candidate view. Those rows are retained as negative diagnostic evidence, but the global-resolution interpretation is **UNADJUDICATED** because no stable hierarchy was earned. They are not demonstrated encoder failures. Rare-classification samples were very small and remain data-limited.

## Accountable Global State

- **overlapping_programs:** one-SE cross-view candidate `k=16`; ordinary/weighted donor-basis median canonical correlation `0.0192/0.0227`; ordinary/weighted projected-state similarity `0.5172/0.5632`; final supported prefix `0`; `AUDIT / FIXTURE LIMITATION - ordinary PCA and weighted basis both donor-unstable`.
- **rare_tail_difficult:** one-SE cross-view candidate `k=16`; ordinary/weighted donor-basis median canonical correlation `0.0187/0.0285`; ordinary/weighted projected-state similarity `0.4828/0.5293`; final supported prefix `0`; `AUDIT / FIXTURE LIMITATION - ordinary PCA and weighted basis both donor-unstable`.

Both hard fixtures nominally favored 16 dimensions under the cross-view one-SE calculation, but this is **not a supported global dimension**. Ordinary PCA and the weighted basis were both donor-unstable, so the original hierarchy and residual decisions are **UNADJUDICATED**. In particular, failure to include a residual block is not evidence that residual biology does not exist.

### Stability-audit repair

The method-independent calibration fixture validated the machinery at known rank 9: ordinary/weighted basis stability `0.800/0.822`, projected-state similarity `0.997/0.997`, and raw/ordinary/weighted mean factor R2 `0.810/0.717/0.729`.

The hard fixtures then changed sample size only (`192`, `384`, `768`), retaining seeds, factors, amplitudes, prevalence, operators, and thresholds. At the largest level:

- **overlapping_programs, N=768:** ordinary/weighted basis stability `0.0216/0.0862`; ordinary/weighted projected-state similarity `0.2763/0.6268`; raw/ordinary/weighted mean factor R2 `0.601/0.236/0.394`; relative eigengap `0.0018`.
- **rare_tail_difficult, N=768:** ordinary/weighted basis stability `0.0249/0.1528`; ordinary/weighted projected-state similarity `0.2751/0.7486`; raw/ordinary/weighted mean factor R2 `0.550/0.218/0.389`; relative eigengap `0.0031`.

The calibration proves the metric can recover a stable known subspace. The hard fixtures remain unstable at larger `N`, with flat eigenspectra around the tested prefix. Classification: **AUDIT / FIXTURE LIMITATION**. Global-resolution decision: **UNADJUDICATED**. No held-out-family rerun was performed because no hard fixture earned a stable prefix.

### Eigenspectrum and band identifiability

One final method-independent diagnostic retained the existing `N=768` hard fixtures and audited fixed local bands plus cumulative widening from 16 through 96. Around dimensions 12-20, relative eigengaps were mostly about 0.003-0.020, confirming a flat boundary. No weighted cumulative band reached the unchanged 0.50 stability threshold:

- **overlapping_programs, cumulative 1-96:** median canonical correlation `0.0628`; cumulative reproducible variance within audited 96 `1.000`; donor/shared covariance fraction `0.028/0.972`; hidden-factor mean R2 `0.474`; stable `False`.
- **rare_tail_difficult, cumulative 1-96:** median canonical correlation `0.0646`; cumulative reproducible variance within audited 96 `1.000`; donor/shared covariance fraction `0.020/0.980`; hidden-factor mean R2 `0.437`; stable `False`.

Widening across the plateau did not restore donor-refit agreement, yet informative-gene recovery remained substantial (`R2=0.601` and `0.550`), and widening improved hidden-factor recovery. Classification for both fixtures: **DONOR-HETEROGENEITY / COMMON-SUBSPACE UNRESOLVED**. Donor covariance itself was only about 2-3% in the widest audited bands, so donor effects are not shown to dominate; the common-subspace/eigenspectrum issue remains unresolved. No dimension or band was promoted.

## Observation Operators And Uncertainty

- **overlapping_programs:** masked/zero-fill same-cell distance `3.307/3.730`; top-1 retrieval `0.312/0.312`; held-out global/raw-informative upper-bound mean factor R2 `0.197/0.423`; biology R2 before/after unconditional operator-mean removal `0.823/0.586`.
- **rare_tail_difficult:** masked/zero-fill same-cell distance `4.335/5.755`; top-1 retrieval `0.453/0.391`; held-out global/raw-informative upper-bound mean factor R2 `0.159/0.433`; biology R2 before/after unconditional operator-mean removal `0.794/0.575`.

Masked projection reduced same-cell distance in both fixtures and improved top-1 retrieval in one. Held-out measured-panel raw upper bounds were about 0.42-0.43 mean R2, while the unsupported candidate global map yielded about 0.16-0.20. Classification: **DATA/OPERATOR CEILING + UNRESOLVED GLOBAL REPRESENTATION GAP**. The gap is not attributed to weighting or dimension because no stable global prefix was selected. Crude unconditional operator-mean removal reduced legitimate broad-factor recovery, demonstrating why unconditional technology erasure is unsafe. `U_BIO` and `U_MEAS` were implemented as separate evidence and quality perturbations; their per-cell correlations were 0.278 and 0.305. Rare-cell uncertainty comparisons and generic residual OOD remain underpowered and were not promoted.

## Bounded Real TRAIN Audit

Only existing pathology-blind TRAIN-derived summary caches were read: 55,337 H5 gene-stat rows, 38,199 NPH gene-stat rows, and 72 historical count-split rows. No new real RNA values were opened. Those count-split summaries cover the historical 4,096-gene vocabulary, not full `G`, so a real full-G basis was not fit. Classification: **DATA / PROVENANCE LIMITATION, not architecture failure**.

## Governance And Tests

- Pre-change full v4: **754 passed**.
- Focused candidate tests: **33 passed**.
- Post-change full v4: **787 passed**.
- Compileall and `git diff --check`: passed.
- Protected hashes unchanged: **True**.
- DEV RNA accessed: **NO**. SEALED RNA accessed: **NO**. Pathology accessed: **NO**.
- Stage81A3 complete: **NO**. Freeze 1 declared: **NO**. Stage81B/Stage81C started: **NO**.

## Remaining Blockers

1. The accountable global audit did not earn a donor-stable prefix or wider band; common-subspace/eigenspectrum identifiability remains unresolved.
2. Real full-G paired count-split evidence is absent from current bounded caches. Building it requires a separately reviewed TRAIN-only materialization plan.
3. Full-G real masking still needs a scalable non-quadratic engineering contract; the synthetic oracle graph cannot be used as real biological evidence.
4. Rare-program evaluation is underpowered in these bounded fixtures.
5. The 106,118 unresolved source mapping records require pinned authoritative evidence if future exact recovery is attempted.

## Human Decision

**NOT READY - AUDIT INCOMPLETE**

The address-space and full-G mechanics candidates are ready for review, but the global-state audit is unsupported and real full-G reproducibility evidence is incomplete. No freeze is declared.

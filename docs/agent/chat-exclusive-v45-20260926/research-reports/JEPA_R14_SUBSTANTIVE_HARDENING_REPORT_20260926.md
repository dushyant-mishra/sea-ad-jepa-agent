# JEPA Round 14 — executable scientific-fidelity baseline hardening and raw-query leakage counterfactual

**2026-09-26 | LOCAL RESEARCH CODE | NO REAL OR PROTECTED OUTCOMES OPENED | TRAINING OFF**

## Exact task and why it matters

Previous R13 paired-multiome evaluator was a useful synthetic scaffold, but its primary `teacher_plus_same_RNA − same_RNA_linear` comparison used only `pca_components=2` of the reference RNA. A teacher with a *linear copy of a discarded RNA feature* could beat this impoverished comparator without learning an additional biological state. Separately, appending a duplicate teacher feature to a ridge readout changes the effective regularization of that feature; it can produce a numerical gain even if the teacher introduces zero information.

R14 adds an explicitly independent, stronger **full permitted RNA ridge baseline** as well as the older PCA comparator; teacher state is residualized against full same-RNA plus nuisance using **training donors only**, and the direct gain versus full RNA is always separately reported. It refuses underdetermined full-RNA fits instead of silently dropping that baseline. This is an engineering sensitivity test, not proof that residualization solves all fairness, causality, neural-compute or distribution-shift questions. For any real candidate, its source RNA feature panel, ridge regularization, teacher architecture, and outcome definition must be prospectively frozen outside the evaluation cohort and authenticated.

R14 also ships a **raw-count student preprocessor** whose library size, normalized tokens, and QC features use *only the declared permitted student genes*. It provides a function that alters hidden query, teacher partner, and reference counts in the original raw vector, recomputes every student feature and asserts exact invariance. Deliberately unsafe source-library normalization changes visible token values under this intervention, demonstrating detector sensitivity. The richer teacher can independently receive q when its declared research policy permits it. The existing immutable V5 policy is **not changed**.

## Synthesized demonstration (not biological results)

The same 8 donors × 16 synthetic nuclei (128 total), 7 legal RNA features and fixed ridge protocol are used for all four planted scenarios. Effects are donor-equal average heldout-R² *differences* (an R² difference can exceed 1 when its baseline is negative).

| Planted condition | Teacher additional R² over PCA2 | Teacher additional R² over full RNA, unadjusted | Teacher additional R² over full RNA, residualized |
| --- | ---: | ---: | ---: |
| Genuine nonlinear `RNA3 × RNA4` feature | +1.015803 | +1.089722 | +1.089992 |
| Teacher is a copy of one legal RNA gene | +0.700073 | +0.005877 | ~0 |
| Linear RNA feature omitted by PCA2 | +0.702964 | +0.005934 | ~0 |
| Teacher copies technical nuisance | +0.005164 | +0.005804 | ~0 |

These values document detector behavior on planted controls, not any external dataset. The key outcome is categorical: a PCA2 teacher gain of ~0.70 is a false biological inference for a copied RNA gene. The full-RNA+training-fold residualization comparator detects it. If `p >= training nuclei − 1`, R14 blocks the full-RNA analysis rather than letting an interpolating residualizer manufacture a vacuous result.

## Executed verification

- 16 R14 evaluator tests, 14 raw-query firewall tests, and 21 inherited R13 tests: **51/51 PASS**, no skips (the original 21 include 13 evaluator and 8 outcome-blind power tests).
- Three physical mutant controls explicitly flip correct logic to incorrect logic and MUST fail: unsafe full-library denominator, allowed q/student overlap, disabled residualization. All three mutants are rejected by their intended tests; the unmutated complete suite passes.
- The first implementation's `Ridge.predict` for a single teacher feature returned a flat vector and inadvertently broadcast the residualizer subtraction to an `n × n` matrix, repeating the R13 error in a different location. It failed 4/15 initially; fixed by explicit prediction reshaping, then strengthened the zero-copy test because an error tolerance of .015 did not detect intentionally disabled residualization. The raw-q validator also initially used inconsistent category dictionary names; initial 12/14 failures fixed before green. All failures remain documented in this report and source histories of this artifact.

`R14_ALL_TEST_LOG.txt`, `R14_MUTATION_LOG.txt`, and `R14_SYNTHETIC_RESULTS.json` are included. The code uses NumPy and scikit-learn, no network, and does not contain actual human data. The R13 original source and tests are included only to enable exact inherited local reexecution, and are not rewritten in place.

## Explicit limits and realistic integration points

This is **not deployed production V5 anti-cheat**, not a cryptographically authorized external outcome opener and not a clean same-cell biological validation. Even identical nucleus ID strings cannot authenticate a true RNA/ATAC multiome origin; these must be externally authenticated against deposit barcodes, and donor duplication checked. The `synthetic_lineage_token` is a tripwire to prevent *accidental* actual outcome use, not a security defense against malicious callers. Production q-safe preprocessing requires tracing all upstream row/global normalization and every post-token hidden-to-visible data path, including metadata and attention pooling, through the exact V5 reader and tokenizer. The per-view student-library normalization discards global amplitude; preserve overall biological program activity separately on the teacher side and compare against independently specified permitted student normalization strategies before freezing a production estimator.

Do not use this full-RNA direct baseline without a dimensionality rule frozen on external developmental information. An unrestricted 41k-gene readout with fewer training nuclei is underdetermined and R14 deliberately blocks that setup. Likewise, residualizing teacher features by a high-capacity RNA predictor may remove nonlinear RNA biology; R14 residualizes *linearly* and reports the unadjusted comparison as context, but there is no universally unbiased adjustment for all latent-teacher effects. Hyperparameters, matching teacher compute, donor power and independent outcome panels are still open. No result here selects rich vs shared vs specialist teachers.

## Claude integration directives

1. Preserve and cite the existing real V5 normalizer, tokenizer, Stage-A mask, teacher construction and every QC/denominator path by exact source SHA. Run the raw-query intervention **upstream of the earliest normalization** on authenticated developmental counts and audit the entire student tensor and downstream summaries, not merely the R14 standalone implementation. The first allowed difference should be only in the declared teacher q-visible branch; any student-visible difference must block the candidate. Include healthy and planted-unsafe comparators.
2. Apply the improved teacher fidelity comparison only to a legitimately frozen RNA-only actual V5 teacher representation with *matched* full lawful RNA and technical baselines, donor-heldout evaluation, physically authenticated paired nuclei, independently prespecified chromatin endpoint, and independent provenance permission. Under a large p/small n regime, freeze a practicable full-RNA feature panel on separate developmental data, and keep both PCA and complete-frozen-panel direct baselines. Do not quietly interpret a gain over PCA alone as novel biology.
3. Keep heldout ATAC inaccessible to target, threshold, feature or architecture selection. The Agent2 Morabito observed ATAC crosswalk is already exposed, making that cohort conditional secondary evidence. Same-study GSE214637 and GSE214979 are not independent replications; accession and prior-use checks remain open. Full104 TRAINING=OFF until the genuine 33-root scientific closure and separately reviewed governance authority are satisfied.

**Status:** A stronger executable falsification harness, not a qualification of teacher biology.

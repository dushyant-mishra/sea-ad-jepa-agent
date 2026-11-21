# DEV2048 V2: count-noise-vs-rare-biology and joint real/synthetic qualification (SOURCE ONLY)

**New work relative to Events117–122:** an executable, fail-closed **pre-generation metadata gate** lives in `scripts/v79/dev2048_v2_count_null_joint_gate_v1.py`, with inert hostile tests. This is NOT another real-data QC run, another V78/V79 experiment, a fitted count model, a V2 dataset, a JEPA update, a rare-state discovery, or acceptance of the shared non-q C3 panel policy.

## Scientific reason for synthetic data

The original synthetic fixture is a **controlled, known-truth challenge environment** for whether JEPA sees rare/weak/perturbation biology in measured views and query conditions, rather than source, depth, q leakage or technical pseudo-rarity. It must approximate **relevant real RNA measurement distributions and joint structure** without copying human donor-specific rare programs or substituting real protected outcomes for planted synthetic truth. The historical match in sparse nonzero fraction (real 0.111, earlier synthetic 0.105) was inadequate: median absolute HVG correlation differed markedly (real 0.329 versus synthetic 0.068, Event117). Those comparisons are old and version-specific, not DEV2048 V2.

Two questions must be jointly answered:

1. **Realism:** does a future versioned, rights-cleared synthetic realization match authenticated TRAIN-only real source/operator/assay observations in measured support, zero mass, library depths, detected genes, per-gene tails/dispersion, signed conditional gene correlation, broad and within-class structure, donor×class variability and transfer to withheld operators/donors?
2. **Scientific discrimination:** when unusual expression occurs, is a **coordinated, recurrent, multi-gene program** left unexplained by library depth, ordinary count variation, class/source/operator effects and baseline coexpression? Can the same method reject depth-matched technical pseudo-rarity, wrong-query, null-query and deliberately planted synthetic negatives?

**No scalar similarity score is enough.** A marginal RNA PDF or zero-rate match cannot cancel a failed covariance, topology, operator, rare-null or heldout gate. The goal is a finite, predeclared set of scientifically relevant aspects, not promising an impossible literal match to every property of reality.

## Prospective decision sequence (not yet executed)

| Gate | Mandatory check and counterexample |
|---|---|
| G0 | Authenticated issuer, permitted TRAIN-only real donor use, immutable source/gene address, split and human-rights scope. Otherwise **NOT_ESTIMABLE**. |
| G1 | Five physical support states from owner ruling #531 stay distinct. Compare *measured* zeros separately from unmeasured addresses, detection probability, collision-unresolved, rights withheld. Raw UMI count models only if true raw UMI counts exist; log1p(10K) cannot masquerade as integer UMIs. |
| G2 | Match comparable source/operator/depth/class-stratified measured-zero point mass, library-size and detected-gene distributions, per-gene detection and positive-count tails, and overdispersion. Reuse existing V74/V77 summaries when valid; do not re-extract the historical sample. |
| G3 | Match signed conditional gene covariance, eigenspectrum, class/within-class relationships, donor×class variability and source transfer. A sparsity-only pass is **FAIL** here, not near-PASS. |
| G4 | Fit preregistered Poisson and negative-binomial count baselines (e.g. log mean with observed library-depth offset), plus class/source/operator and ordinary-coexpression-preserving empirical controls **only on authorized training donors**. Hold donor data out for predictive calibration. Do not estimate baseline or choose hyperparameters by peeking at the candidate rare outcome. |
| G5 | Score coordinated conditional residual tails across several program genes and views; test against depth/class/source-matched pseudo-rare controls, empirically correlated ordinary-expression nulls, wrong-q and null-q tests, perturbation-specific contrasts and multiple-testing controls. An isolated high count or a library-depth spike is not rare biology. For V2, reserve q RNA and q-locus ATAC from student inputs. |
| G6 | Demand donor-heldout recurrence and, when estimable, independent operator/technology replication; then independent scientific review. If split×source×rare-cell support is insufficient, return **NOT_ESTIMABLE**, not zero effect or PASS. |

**Statistical outline, only after G0 authorization:** for a measured cell/gene, start with `Y[c,g] ~ NB(mu[c,g], dispersion[g])`, with `log(mu[c,g]) = log(library_size[c]) + ordinary_class_source_operator_effects[g,c]`. Compare that model with Poisson and a matched empirical null that preserves ordinary coexpression. A rare-program score tests the **excess coactivity of multiple heldout residuals**, not the extremeness of one gene. Select the gene panels, matching criteria, donor split, test statistic, multiplicity correction, numeric tolerances, model families and finite iteration budget **before** scoring real candidate rare outcomes or tuning the new synthetic world. Gene-level correlation is a key background confound, not an automatic target discovery.

**Known-truth synthetic role:** only after a separately authorized new V2 world, plant and sequester ground-truth rare, weak and perturbation programs and technical pseudo-rarity; then measure the detector's known-truth sensitivity and false discoveries under the frozen controls. This does not authorize JEPA model training and cannot prove a state seen in human RNA is biological. Human discovery requires separate independent donor/operator replication, rights and orthogonal biological checks.

## Implementation / blocked state

- Source-only machine-read contract: `scripts/v79/dev2048_v2_count_null_joint_gate_v1.py`. Every G0–G6 is explicitly **NOT_ESTIMABLE__NO_APPROVED_EXECUTION**; all generator, real-data, fitting, rarity and model authority flags are false. The module reads no RNA and performs no fitting. `validate_manifest` refuses unsupported edits, missing joint gates, self-declared PASS, or an upgraded authority claim even under optimized Python.
- Hostile inert checks: `tests/v79/test_dev2048_v2_count_null_joint_gate_v1.py`; CI uses an exact named file, never directory/test discovery.
- Existing work reused: #205 V74, #239 V77, #242 V78, #265/#533 V79, #348 V80, #344/#356/#379 accepted design and pivot, #493/#598 Task3 audit, #531 support semantics, #541/#549 Task4 HOLD, #547 DEV2048 v1 and #599 role proposal. No duplicate historical study.
- Unresolved: G0 rights+real issuer, trusted physical source semantics and generator parameter binding, independent C3 panel-sharing approval, V2 physical causal remap and V2 generator authorization, signed covariance/realism metrics, donor/source estimability, frozen numeric bands, bona fide rare-null evaluation and heldout confirmation. This manifest is **not a scientific PASS mechanism**; later measurement results must be checked by a separately reviewed, issuer-bound evaluator and independent reviewer.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

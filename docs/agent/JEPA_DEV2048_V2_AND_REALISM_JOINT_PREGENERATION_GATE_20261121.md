# DEV2048 v2 and real-data realism are one qualification objective

**Status: prospective design/source-only preflight. NOT a new world, not realism PASS, not training authorization.** Read with original [PR547](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/547), Macha F1–F4 review/comment 6649187938, and v2 proposal/comment 6649566055. Original 480×48 PR328 and 1,440×2,048 PR547 remain byte-for-byte preserved.

## Purpose

Synthetic RNA is an **independent, known-truth falsification world**. It needs the *relevant real observed distributions and conditional biology* so it is not a toy; and it must retain controllable synthetic rare/weak/local/core+halo and perturbation truth, q-blind controls, donor-held-out and wrong-source/query negatives. Matching real marginals while destroying truth or covariance is **not** success. Matching a real heldout result by retuning a known test is prohibited.

## Concrete source-level finding: current v2 proposal cannot be executed as written

The Macha v2 idea proposed 15 genes per program, four genes in each 512-gene view and three in the tail, with one rare-bearing query per program and >=3 **other** same-program genes in that query's panel. Under v1's **disjoint** view/query/panel convention, that first query alone needs 4 tail members, not 3; three views×4 plus one query and three panel genes need **16 unique program genes, exceeding 15**.

The PR328 actual mechanism uses its first 15 rare-program genes **also as the perturbation response** (source `scripts/v79/unified_synthetic_integration_v1.py:285–297`). A rare-regime-0 query plus two perturbation queries therefore draw on the **same 15 genes**, not an additional independent perturbation program. If each of these three q requires three other unique panel genes and every view holds four, a minimum of **24** members would be needed. Simply assigning "perturbation response genes" separately would change the original planted mechanism.

The new static `dev2048_v2_pregeneration_feasibility_v1.py` checks the original source Git blobs, source-only support/role capacity and these contradictions; it **does not generate a cell, select biology, or update a model**. It does confirm the artificial support table contains enough *distinct measured addresses* for 3×512 views, 8 queries and 8 panels—**not** that rare biology occupies them.

### Narrow design resolution to review before implementing v2

Prefer preserving the original 15-gene mechanisms and explicitly reviewing **controlled reuse of permitted observed panel genes across different query-specific panels**, while never placing *any query address* in the student's inputs or in another q's panel. This may allow more program members in views and prevent a silently new perturbation mechanism, but the exact C3 panel-independence contract and shared-panel leakage must be independently reviewed first. If C3 requires globally distinct panels, instead introduce a separately named prospective biological version with sufficient program size; never silently relabel PR328 as unchanged. Both alternatives require source-level reviewer acceptance and explicit authorization **before any new world is realized**.

The original source/donor support fingerprint, q-locus ATAC proxy and rare-active donor×source×split imbalance must also be tested, as Macha F2–F4 found. The controller alone can open activity truth and must report non-estimability rather than invent rare-active observations.

## One integrated qualification: no shortcut through a "realism" label

Reuse completed V74 sampled operator QC, V77 TRAIN real geometry, S174 corrected references, V78 negative, V79 frozen Q08 failure, V80 benchmark, the #239 class-propagation crosswalk, the #493 Task3 calibration firewall, and owner #531 five-state support/rights ruling. Do not extract the same 50K real data again or rerun old experiments.

Before iteration, freeze a **versioned finite-budget multi-metric decision contract** using lawful TRAIN-only reference statistics, strata (source×operator, donor, broad class), the measured/unmeasured/collision/rights ladder and independent review. It must evaluate **jointly** depth, detected genes, zeros/support, per-gene abundance/detection, count dispersion, signed dependence and T1–T5 topology, eigenspectrum, class-conditioned and donor×class structure, rare/perturb observability, all-view C2 and C3 panel coverage, source-stratified and wrong-q/null tests. Where real evidence or class-specific sample size is unavailable, mark **NOT_ESTIMABLE**, never automatic PASS.

A **prospectively frozen E0–E4 mechanistic family already exists** in `docs/agent/ETL_TO_SYNTHETIC_RECONCILIATION_20261008.md`: class composition, class-shared random program, within-class biology, then donor×class ablation. Reuse it rather than inventing new arms or tuning T5 to the real point. Hold observation model fixed on the first biological comparison. Retune only approved observation-side parameters with actual physical bindings; Task3's seven family names alone are not generator semantics. Version every new generator, reveal no private heldout truth, never post-hoc change gates to fit the current result.

**Prerequisites to qualify:** owner-accepted v2 role+biology contract, independent source tests, authenticated real TRAIN reference/issuer and approved mapping to actual generator, prospectively frozen joint PASS bands/finite iterations, independent held-out evaluation. After a lawful iteration fails, record failure and design the next *new version* without altering that result. None of these is a claim to qualify DEV2048 against all 41,238 human addresses.

No synthetic realization, training, optimiser/EMA, RT1–8, sealed controller, target/representation selection, Stage4, real-RNA training, or production promotion is authorized.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

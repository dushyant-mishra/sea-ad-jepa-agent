# JEPA tiny tournament — historical developmental pilot (26 September 2026)

**Status:** complete, research-only. **No scientifically qualified winner; no production model comparison.**
All four neural arms finished **two** prespecified random donor-group splits; 15 separate local fail-closed and scope checks passed. The two splits are *resamples* of the same 50 donors, not independent external cohorts. An attempted 60/75-epoch extension exceeded the execution time limit and produced no additional scored results; only the fully completed 26/38-epoch trials below are reported. The EMA arm used its own early stopping (up to 45 epochs). No FULL104/N1/protected outcomes were opened.

## Source and biological scope

Original SHA-verified historical discovery archive: split `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` + `.part002`; historical original 50,000 fit-donor cells × 41,238 address CSR. Original exact support map from `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`; row metadata and frozen source selection from `expression.zip`. These are historical *fit-donor developmental* assets, not current V5/FULL104 authority. The analysis uses 1,561 extracted cells: 361 **Microglia-PVM or Microglia-PVMSubclass-labelled** cells across 50 donors plus 1,200 other non-neuronal cells from the same donors. There are 15 distinct measurement operators in this selected subset. Microglia-PVM labels may include perivascular macrophages; no purity claim.

CSR row indices were recovered by an exact `stable_key` one-to-one join across original per-operator metadata, and operator/donor correspondence was checked. Each sparse historical log-expression row proved invertible to integer raw counts by the smallest positive single-count quantum, with maximum numerical rounding error 5.46e-12. This inversion is a *validated historical pilot convenience*, not a sanctioned source replacement for actual production raw counts. Teacher and student are independently re-normalized *after* panel construction/masking. The original full-library denominator is never forwarded to the student. The 700 modeled genes are selected from the **17,757 unambiguously measured addresses across the 15 operators represented in this subset**, not from all 41,238 addresses; genuine operator-native missingness is therefore not tested by these four models. The separate V43 data-contract prototype already covers structural abstention at the unit level.

Two donor-group splits: 34 training donors, 8 validation donors, 8 untouched testing donors per split. Feature/panel selection uses training-donor microglia-labelled cells only. Every model gets the same 400 core + 200 fine + 100 low-prevalence RNA features and 96 completely disjoint held-out RNA evaluation features (selected on training donors only). The low-prevalence 'rare' panel requires at least three TRAINING donors with nonzero observed RNA, but it is **not a validated rare biological state**. Approximately 40% of student features plus one sampled core query are hidden and the visible counts alone determine student normalization. The target is generic full-cell latent state, **not yet a query-conditioned target**; the sampled query is intentionally omitted from student input, but query identity is not passed to these small proxy models.

## Actual pilot tournament

All learned states are 32-dimensional. Neural teachers train with either EMA latent prediction (incumbent proxy) or autoencoder reconstruction (A/B/C), and students train against the learned teacher state. For A/B/C, per-head reconstruction of observed input is an expedient developmental proxy, **not** the approved JEPA objective. Model sizes and training objectives were **not capacity- or compute-matched**. The incumbent proxy is a scaled single-teacher/student EMA mechanism, **not** the actual current V5 production code or current target semantics.

Metric: a *new linear ridge probe* is fitted using training-donor states to predict the **96 genes excluded from all teacher and student inputs**; its test-donor pooled squared-error improvement over the training-donor mean is reported as R². The microglia/PVM-only result restricts the test scoring to annotated microglia/PVM cells while retaining the common training-data probe. This is **same-study withheld RNA recoverability, not independent biological teacher fidelity, perturbation skill, rare state validity or causal prediction**.

| Configuration | Teacher held-out RNA R² | Student held-out RNA R² | Microglia/PVM student R² | Teacher + student parameters |
|---|---:|---:|---:|---:|
| EMA incumbent **proxy** | 0.4668 | 0.4538 | 0.3833 | 187,712 |
| A — single rich frozen-AE teacher | 0.4875 | 0.4630 | 0.3859 | 282,236 |
| B — shared backbone, specialist heads | 0.4822 | 0.4622 | 0.3913 | 247,868 |
| C — independent core/fine/rare teachers | 0.4822 | 0.4606 | 0.3896 | 141,820 |
| Operator-only baseline | 0.0321 | — | — | 0 |
| Random-state negative control | -0.0285 | — | — | 0 |


### Results for the separate splits

| Fold | Configuration | Teacher R² | Student R² | Microglia/PVM student R² | Teacher / student epochs |
|---:|---|---:|---:|---:|---|
| 0 | EMA | 0.4234 | 0.4105 | 0.3518 | 24 / 24 |
| 0 | RICH | 0.4478 | 0.4240 | 0.3529 | 26 / 38 |
| 0 | SHARED | 0.4419 | 0.4226 | 0.3636 | 26 / 38 |
| 0 | TEAM | 0.4442 | 0.4246 | 0.3632 | 26 / 38 |
| 1 | EMA | 0.5103 | 0.4970 | 0.4148 | 25 / 25 |
| 1 | RICH | 0.5272 | 0.5019 | 0.4189 | 26 / 38 |
| 1 | SHARED | 0.5225 | 0.5018 | 0.4189 | 26 / 38 |
| 1 | TEAM | 0.5203 | 0.4966 | 0.4161 | 26 / 38 |


### Interpretation

A, the single rich teacher, has the largest **average teacher** withheld-RNA score (0.4875). B, the shared-backbone multi-head model, has the largest average **microglia/PVM student** score (0.3913); C, the separate teacher team, is very close (0.3896). On all held-out cell types the A student scores 0.4630, B scores 0.4622, and C scores 0.4606. These differences are small compared with the two-fold variation; the specialist teachers have **not established incremental fidelity**. B's microglia student advantage over C is ~0.0017 R², much too small for an architectural decision. No qualified tournament winner is declared.

The operator-only negative baseline averages 0.0321 withheld-RNA R² and a random representation averages −0.0285. This shows all learned models exceed **these two specific simple controls**, not that operator, library depth, source or donor confounding has been eliminated. Teacher scores are systematically higher than student scores, as expected with information asymmetry. Several A/B/C runs hit the 26-epoch teacher or 38-epoch student caps, so relative training convergence is **not** established. An attempted longer run timed out without completed scored folds and is not counted.

### Crucial missing scientific qualifications

1. **Biologically faithful, query-conditioned target:** this round tests generic-cell latent state; target q-value policy and direct-versus-derived q leakage for actual V5 remain unresolved. A sampled masked gene is not equivalent to an authenticated query-specific teacher target.
2. **True rare biology:** the 'rare' head is a low-prevalence expression proxy drawn from common measured RNA. Real rare microglial state and donor-level recurrence need separate biological qualification.
3. **Independent biology:** evaluation genes come from the same RNA study; independently reserved unpaired ATAC may eventually provide a properly designed *population-level* validation, but cannot be combined with separate RNA nuclei as one cell.
4. **Fairness and power:** teacher/student parameter counts and learning objectives differ, several arms hit epoch caps, two donor-resampling splits are not power for tiny differences, and no repeated initialization or independent cohorts were included.
5. **Authentic V5 architecture:** the incumbent is a scaled EMA proxy. The current exact pipeline, remaining-RNA policy, 33 authority roots, optimizer guard and Phase-IV masking are untouched.

## Fail-closed red-team controls

15 local tests passed: all four original source SHA-256 digests; integer-source recovery; explicit genuine structural-missingness distinction; no donor overlap across training/validation/test; **masked-student invariance** when the queried count alone is mutated; a planted full-library-denominator leakage path correctly fails that invariance test; held-out evaluation size; complete 2×6 results; no false query-specificity/production claims; protected/training OFF; fold-specific training-only features; and trained teacher performance above the chosen operator-only baseline. This probes a representative input path, **not** a comprehensive audit of all encoder-visible V5 tensors.

## Proposed second round before changing production architecture

First define a per-head **teacher-only biological fidelity** task and approved query-scalar policy with Claude's #163 proposals versus the existing #152 checker. Use the same authentic training support, matched effective capacities, shared masks and independent initialization seeds for A/B/C plus the exact actual V5 incumbent. Design the core/fine/rare targets *before* comparing performance; include cross-query exchangeability, q-only and generic-state controls; low-prevalence donor recurrence and a shuffled rare expert; and donor-level source/technical adversaries. Reserve independent unpaired RNA/ATAC measurements strictly for predeclared population-level evaluation, without training or selecting on them. Only then compare the predictability of independently faithful teacher states by support-aware students. Until the target and every required current authority root qualify: **TRAINING=OFF; N1=UNOPENED; PROTECTED FULL104 OUTCOMES=UNOPENED.**

## Reproducibility and exact local files

- `JEPA_TINY_TOURNAMENT_PREPARE_20260926.py`: streams the original, original-SHA-checked historical split ZIP and exactly joins per-operator metadata; creates `/tmp/jepa_tour_logexpr.npz` and `/tmp/jepa_tour_meta.csv` locally. It does not publish raw cell data.
- `JEPA_TINY_TOURNAMENT_20260926.py`: recovers counts, selects train-only panels, conducts the full pilot, writes the result JSON. Requires original historical calibration archive and the preparation outputs.
- `JEPA_TINY_TOURNAMENT_REDTEAM_20260926.py`: physical original-SHA and 15 hostile/scope checks.
- `JEPA_TINY_TOURNAMENT_RESULTS_20260926.json`: all two-fold scores, sizes, training epochs and hashed feature/evaluation panel identities, without cell identifiers or original expression arrays.

The original heavy archives are not included. Their roles remain historical and outside current production authorization.

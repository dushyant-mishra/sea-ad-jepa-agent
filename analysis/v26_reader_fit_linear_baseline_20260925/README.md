# Independent parallel lane — new matched 104-reader-fit linear comparator (V26)

**STATUS: IMPLEMENTED AND SYNTHETIC-TESTED ONLY. REAL FULL104 PHYSICAL EVALUATION NOT EXECUTED.** This is a *different, prospectively specified* comparator, not an attempt to reconstruct lost September 15 `bind_population.npz`, `screen_out.npz`, or `final_manifest.csv`. Do not confuse this implementation with historical Layer-2 PR #133 or any future trained JEPA checkpoint. The current GPU diagnostic remains governed by its own named execution authority.

## Independent lane / explicit anti-overlap

Other active PR owners: #129 repairs optimizer chronology, #130 checks reader-fit ZIP metadata, #132 compares frozen pass1 counts, #133 looks for the lost **94-donor historical baseline**, #134 cleanly replays CRISPRbrain reliability, #120 recomputes 104×17,186 raw counts. This branch touches **none of their source files or outputs**. It adds one new evaluator and its independent fixture suite; it does not read protected outcomes, train JEPA, run Audit-B N1, mine Siletti or request a repeat of any other agent's heavy computations.

**Why needed:** the old 94-donor sample and its operator-centered linear R² cannot be honestly compared with a new 104-donor JEPA. If the original scratchpad files are irrecoverable, generate a genuinely new 104-donor baseline *from authenticated surviving original V0/V1 full arrays*, under exactly declared identity/splits/evaluation. It cannot retroactively reproduce the old 94-donor R².

## Computation and estimand

- Input universe: EXACT immutable `V0_full.npy` and `V1_full.npy`, both `(4,553,407, 512)` `float32`, with the full archived SHA-256s. Only columns `0:256` (`VALUE_ONLY`) are read. No `VISIBILITY` channels enter the regression.
- Population: EXACT SHA-pinned frozen pass1 `cell_donor`, `duniq`, and `donor_src`: 104 fit donors, HVS 41 / NPH52 17 / SEA_AD 46, and 4,553,407 rows. Require an **independently reviewed, externally full-SHA pinned** physical pass1→Level4 binding receipt, not just user-provided unsigned JSON. Require an independently documented V0/V1 `selection_row` order attestation before scientific result promotion; the pass1 physical binder alone does not attest VIEW row-order compatibility. Pair with #132 donor-count bridge once physically executed (not required to rerun the costly 8,915-block raw audit).
- Target: same-cell **V1 VALUE_ONLY 256-dimensional molecular view**, features V0 VALUE_ONLY 256. No Braak, AT8, pathology, target identity, perturbation outcomes, or donor label as a model feature.
- For each source separately: leave **one donor completely out** of the linear fit. Source donor counts listed above, no cross-source pooling as the primary claim. Weight train donors equally, each individual cell receiving conditional weight `1/[(D_source-1) × n_d]` in that fold; this is the donor-uniform law conditional on the source and held-out donor.
- Training transform: train-fold weighted X mean and SD, train-fold weighted Y mean. Ridge on standardized X with mean-scaled `lambda=0.01`, mathematically `argmin_Ew ||Y - (X B + b)||² + 0.01 ||B_scaled||²`. All parameters are recomputed from remaining donors; held-out donor means are never used for training. No fitted operator means because the physical **selection-row operator code vector is not bound as an input to the exact frozen pass1**. This makes it a *distinct*, unadjusted baseline rather than the historical operator-centred analysis.
- Scoring: held-out SSE of actual Y against prediction and held-out SST against the **train-side** target mean, avoiding held-out target mean as a denominator tuning step. Report both `cell_pooled_r2=1−ΣSSE/ΣSST` and donor-uniform `1−Σ(SSE_d/n_d)/Σ(SST_d/n_d)`, plus per-donor R² distribution. The numerical results are development evidence and model-selection sensitive if reused for architecture search.
- The script accumulates per-donor sufficient statistics using finite row chunks; it never forms a full combined 4.55M×256×2 in memory. Historical Ridge lambda `0.01*n_train` on a cell-uniform standardized design is **not equivalent** to this source-conditional donor-uniform scientific weighting; labels must stay distinct.

## Exact physical GPU-machine invocation — only after parent authentication

Use a clean worktree at THIS PR's exact live head. Resolve exact paths from PR #120 and the SHA-bound FULL104 asset manifests. Replace `<...>`; do not guess an old T1 reduced file. The physical pass1 source binder receipt must already be independently signed off and its SHA captured *outside this result*, not fabricated locally to pass an argument.

```powershell
python -m pytest analysis/v26_reader_fit_linear_baseline_20260925/tests/test_reader_fit_linear_lodo_v1.py -q

python analysis/v26_reader_fit_linear_baseline_20260925/scripts/reader_fit_linear_lodo_v1.py `
  --pass1 '<SHA_VERIFIED_FROZEN_PASS1_NPZ>' `
  --v0 '<SHA_VERIFIED_V0_FULL_NPY>' `
  --v1 '<SHA_VERIFIED_V1_FULL_NPY>' `
  --physical-receipt '<INDEPENDENTLY_REVIEWED_PASS1_LEVEL4_RECEIPT_JSON>' `
  --physical-receipt-sha '<INDEPENDENTLY_FIXED_SHA256_OF_THAT_RECEIPT>' `
  --out 'D:/jepa_v26_results/linear_baseline_new104_v1/NEW_104_READER_FIT_LINEAR_LODO.json' `
  --chunk-rows 4096
```

This is CPU/Numpy linear algebra; CUDA is not necessary, and it can run alongside actual JEPA GPU training with CPU/disk bandwidth monitored. It will read/hash ~18.7GB of views. Use a new immutable output path. Do not hold off the diagnostic JEPA waiting for the historical scratchpad recovery. The heavy 104-donor physical pass1 binding remains independently owned by Claude's original workstream; **never rescan all 8,915 blocks solely for this comparator** if an authenticated physical binding receipt already exists.

## Fail-closed result promotion and limitations

The evaluator refuses absent or wrong full SHA inputs, invalid donor/source geometry, nonfinite VALUE-only vectors, empty held-out donors, unwarranted reused result paths, missing external physical-binding SHA, and the wrong current 104-reader-fit population. Its receipt marks `NEW_DEVELOPMENT_BASELINE_NOT_HISTORICAL_REPLAY`, no operator centering, and `view_selection_row_lineage=MUST_BE_INDEPENDENTLY_ATTESTED_BEFORE_SCIENTIFIC_PROMOTION`. It does not open any protected partition, infer `q_i`, authenticate donor sex/pathology, establish biology or replace a trained JEPA experiment. A direct head-to-head must evaluate the SAME donor folds, same view target, same nuisance centering, same scorer and same weighting. A 104-donor pretrained JEPA has already seen every fit donor; its frozen encoder evaluated on those donors is **not itself a donor-held-out test**. To make a clean same-population donor-held-out comparison, train separate JEPA fold-specific checkpoints excluding each evaluation donor or use reserved donor populations under their own release rules; never imply the comparator's held-out ridge refits make a full104-pretrained JEPA independent.

## Verification performed in this branch

14 independent tiny-fixture tests of numerical correctness and fail-closed mechanics: compare direct weighted ridge to sufficient stats, direct per-cell SSE/SST vs analytic quadratic scores, both donor-balanced and cell-balanced training, permutation-invariant donor ordering, visibility decoy exclusion, chunk equivalence, duplicate-ID/nonfinite/empty-fold rejection, negative receipt tests and no output overwrite. **No physical FULL104 execution and no scientific R² result** at creation. Any future real receipt must be independently inspected before citing new values.
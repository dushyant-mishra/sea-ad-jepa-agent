# JEPA independent V7 six-directed-comparison CPU red-team

**Date:** 2026-09-28 (US Eastern)  
**Execution boundary:** synthetic input only; no human RNA, reserved outcomes, external ATAC, full Monte Carlo gate-v4 rerun or neural training.  
**Source reviewed:** PR #178 `59e094d32d27c8bc024b94308bbe73bf38225de5`, `src/sea_ad_jepa/v5/teacher_fidelity_core_v1.py` (Git blob `3df54cc718f2b2491ff9bdfc1738f74fddf793d7`); frozen protocol `V29_TEACHER_FIDELITY_FROZEN_PROTOCOL_V7_20260927.md` (Git blob `052cebe1fa4e04b52e73e0557b7e43c0284fb646`). The live branch may have progressed; recheck before implementing corrections.

## What was physically executed here

- A fresh independent Python implementation of the *six-pair verdict algebra*: one frozen set of six directed pairs, 199 sham draws per pair, ties counted as at least as extreme, finite sham-null p-values, source-separated BH at q=0.05, ≥2/3 held-out-donor support, and program qualification only when *both* directed tests pass.
- **41/41 pytest cases passed**, including 16 parametrized adversarial corruption cases, ten BH invalid-input cases, a cross-process `PYTHONHASHSEED` test, and 3,000 seeded comparisons to SciPy's independent BH implementation.
- The previously supplied 21-mutant gate-validator probe passes its **fixture self-check**, including the exact synthetic denominator witness `total_excluding_29=942`, naive `=923`, correct pairwise `=933`. The probe has **not been integrated against Claude's executable gate validator** in this environment; those are separate tools/tasks.
- A separate **300-replicate toy experiment** used nine synthetic donors, 60 synthetic nuclei each, a shared *technical* capture factor, an imperfect observed depth proxy, 199 sham scores, and no shared true biological state. The readout statistic is **within-donor partial Pearson correlation**, *not* the frozen negative-binomial incremental Spearman. With otherwise identical inputs and equal marginal variance:
  - Same capture mechanism real and shams: one-sided nominal rank p≤0.05 in **21/300 (7%)**; exact 95% CI **[0.04385, 0.10501]**.
  - Same marginal variance but sham capture slope 0.25 rather than 1: rank p≤0.05 in **300/300 (100%)**; exact 95% CI **[0.98778, 1]**.
- The six-directed extension used **150 synthetic datasets** with three biologically independent simulated programs, three simulated readouts and shared capture. It applied six-test BH and the ≥2/3 donor rule to the correlation proxy:
  - Same-mechanism shams: at least one false qualification in **3/150 datasets (2%)**, all six false qualifications in **0/150**.
  - Weaker-capture shams with the same marginal variance: at least one false qualification in **150/150**, all six falsely qualified in **150/150**.

**Interpretation:** A null based on real genes cannot be justified solely by abundance, marginal variance or sparsity matching. Gene-specific capture-response and conditional nuisance exchangeability matter. The extreme synthetic contrast is deliberately adversarial; it is *not* a direct estimate of full V7 error rates, an independent recreation of the 960 NEG gate datasets, or evidence about biological effect size. Correlated six-test BH behavior in real sources still needs a dedicated protocol assessment.

## Exact statistical properties confirmed by executed tests

1. A single p=0.01 with five p=1 values does **not** survive BH over six tests at 0.05; two p=0.01 values can survive together because the rank-two threshold is 0.0167. A p=0.005 (minimum for 199 shams) **can** survive at rank one (threshold 0.00833). The v4 synthetic gate's 99-primary-sham, 49-calibration-sham counts should therefore never be silently mistaken for the complete real six-pair analysis.
2. The paired directional results must not be silently merged. In a synthetic fixture where both APOE-directed comparisons pass, APOE qualifies; one passing APOE-directed comparison is **partial** even when it has p=0.005.
3. A strong sham p-value cannot compensate for donor inconsistency: five positive evaluation donors out of nine **fail** the frozen rule; six out of nine pass it.
4. A tie `sham_median == real_median` is counted in `#(sham≥real)`. If all 199 tie the real statistic, sham p=1, not p=0.005.
5. No source pooling, duplicated/missing directional tests, missing/extra shams, nonfinite results, forged summary p-values or donors outside a passed-in evaluation roster were tolerated by this prototype.

## Additional source-inspection risks for the real six-test implementation

These are **not claims that a full real evaluator was run here**. They are interface hazards discovered from `teacher_fidelity_core_v1.py` and the protocol:

- The reusable `benjamini_hochberg(pvals, q)` helper accepts any array length; it does not demand all six predeclared tests or finite inputs. A NaN for one test need not prevent some other tests being marked significant. **The real evaluator must verify all six, all finite, with frozen identities, before calling BH**, as the independent prototype does. A partial test set must yield explicit incomplete/abstention status, not a new six-test decision silently made on five p-values.
- `run_directed_test` accepts `fit_mask` and `eval_mask` but contains no explicit donor-disjoint or row-disjoint assertion. **A future caller must authenticate both masks against the frozen donor split before any fit**; a model trained on evaluation nuclei would invalidate cross-donor evaluation even if the statistic is numerically impressive.
- Its permutation diagnostic ignores a draw when no valid per-donor increment exists but still divides by `n_perm+1`. If this diagnostic is reported, invalid draws must be counted and the complete requested draw census enforced, although permutation is *diagnostic-only* under frozen V7 and must not become the qualifying null.
- The NB convergence check uses `getattr(model, 'converged', True)`: an estimator that does not report convergence inherits an optimistic default. **Fail closed when convergence evidence is unavailable** if a successor changes model objects or solver. The v4 synthetic receipt has a separate model-family check; neither a healthy receiver nor a reported `converged=True` alone attests the whole run.
- This local decision prototype consumes precomputed per-donor increments and sham medians. It cannot verify whether each of 199 sham quadruples is physically distinct, uses genuine eligible genes, shares nuisance sensitivity, excludes all six historical readouts or was selected using fitting donors only. Those require an authenticated, outcome-blind sham-selection ledger on Claude's GPU data.

## Hand-off to Claude: bounded integration requests

1. Keep `TRAINING=OFF`, real-data gate CLOSED and all six historical readout genes reserved with the exact **exposure firewall**, including prior CSF1R value exposure and LPL availability exposure. Reservation is a prospective use restriction, **not** a retroactive claim that no inspection happened. Continue keeping all six excluded from the original denominator.
2. After correcting the synthetic gate's source/receipt validity and complete four-regime/channel enforcement, add a *separate* **six-directed V7 integration test** that physically exercises 199 sham draws, all six finite p-values, BH q=0.05, donor consistency, two-of-two program qualification, and negative controls. The v4 Monte Carlo receipt does not supply this evidence.
3. Make fail-closed input gates around the reusable core: exact six pair census per source, frozen held-out donor roster, row-disjointness, exact requested sham count, numeric/finite fields, proper structural-missingness abstentions, and no fallback or skipped fits. Do not reinterpret previously invalid biological gene-axis results.
4. Use the independent script and pytest suite as **comparison fixtures**, not as proof of full protocol implementation. Before running real genes, make the real-gene sham selection and nuisance-matching criteria outcome-blind and document what evidence cannot establish exchangeability.
5. No global `PASS` from an empty experiment, green CI not actually executing the specific tests, and no claim of a pristine untuned C/D validation (those regimes were viewed during iterative diagnostics).

## Reproduction

```bash
python -m pytest -q -ra test_six_pair_decision_v7_redteam.py
python six_pair_decision_v7_redteam.py --repeats 300 --out results_synthetic_300.json
```

Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 and pytest 9.0.2 were used locally. The full per-pair example and synthetic simulation outcomes, including explicit status caveats, are in `results_synthetic_300.json`. All scripts and their hashes are included in this portable package.

## Independent companion: proposed sham-selection metadata preflight v0

`sham_preflight_v0.py` and `test_sham_preflight_v0.py` are packaged alongside the statistical harness. They add 26 passing targeted schema/adversarial tests (combined **67/67**) and an explicit **non-authorizing** synthetic manifest for 1,194 proposed sham quadruples over six directed comparisons. Read `OUTCOME_BLIND_SHAM_PREFLIGHT_V0_20260928.md`. The structural check cannot validate actual nuisance exchangeability or selection honesty from self-reported boolean fields and hashes; Claude must independently re-derive them from authenticated fitting-donor data before real-data use.

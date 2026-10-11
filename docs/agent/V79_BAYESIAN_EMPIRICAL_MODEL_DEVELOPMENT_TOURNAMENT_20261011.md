# V79 Bayesian Empirical Model-Development Tournament — 2026-10-11

## Purpose

This is exploratory **model development**, not confirmatory Bayesian qualification. It was opened after controller review concluded that the project had repeatedly frozen plausible models before adequately characterizing the TRAIN-like data geometry those models were supposed to explain.

No target-discovery values, pathology, TEST/Morabito, JEPA outcomes or H0-H3 factorial outcomes were used.

## Data scope

The current project mount does not contain the exact corrected S174 4,726-cell / 149-donor Bayesian cache as a directly readable raw-count artifact. It does contain the authenticated auxiliary 50K reader-fit discovery expression archive and metadata covering 104 fit donors and all three sources.

Therefore this tournament is explicitly:

`AUXILIARY_50K_READER_FIT_POPULATION__MODEL_DEVELOPMENT_ONLY__NOT_S174_CONFIRMATORY_AUTHORITY`

The matrix is stored as 41,238-address log1p10k values. Operator metadata carry the original `source_library`. For observed entries, integer counts were reconstructed as:

`count = round(expm1(log1p10k) * source_library / 10000)`

Across 200 checked rows, transforming the reconstructed integers back to log1p10k reproduced the mounted values with maximum absolute error `8.88e-16`. This establishes a numerically exact replay for the observed entries used here.

Input custody:
- `expression.zip`: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- expression part001: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- expression part002: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

## Design

A donor-balanced development sample was created with at most 100 cells per donor:
- 10,379 cells;
- 104 donors;
- HVS 4,100;
- NPH52 1,679;
- SEA-AD 4,600.

Broad biology used the same three-way mapping concept as the Bayesian lane. Ten identity-blind gene-address indices were selected to deliberately span prevalence from approximately 5% to 87% rather than sampling mostly sparse genes.

Evaluation used three held-out-donor folds.

Four simple candidate models were compared:
1. NB2 on all counts with fixed library-size offset + source/broad-class terms;
2. NB2 on all counts with a free log-library slope + source/broad-class terms;
3. explicit logistic detection + discrete-bin lognormal positive magnitude;
4. explicit logistic detection + zero-truncated NB2 positive magnitude.

This is intentionally a simple tournament. It asks what structure the data demand before rebuilding a deep hierarchical Bayesian version.

## Results

Equal-gene mean held-out-donor log predictive density:
- NB2 fixed depth: `-1.43373`
- NB2 free depth: `-1.40428`
- hurdle lognormal: `-1.30285`
- hurdle ZTNB: `-1.30617`

Detection-only held-out-donor log loss:
- NB2 implied zeros, fixed depth: `0.37573`
- NB2 implied zeros, free depth: `0.35608`
- explicit logistic detection: `0.26179`

Thus allowing NB2 a free depth slope improves it, but does not close the gap. Explicit detection improves detection log loss by about `0.0943` versus the fairer free-depth NB2 competitor and is better on all 10 genes.

Relative to free-depth NB2:
- hurdle lognormal mean LPD gain: `+0.10144`;
- hurdle lognormal better on 9/10 genes;
- hurdle ZTNB is also better than the one-piece NB family across the sampled prevalence range.

Positive-family comparison is almost a tie:
- hurdle ZTNB minus hurdle lognormal mean LPD: `-0.00332`;
- per-gene winner count: lognormal 7, ZTNB 3.

That difference is too small and this substrate is too developmental to justify selecting the positive-count family from this tournament alone.

## Scientific interpretation

The correct conclusion is **not** that the failed Bernoulli qualification proved detection is unnecessary.

The empirical tournament says the opposite: a separate detection component carries real held-out-donor predictive information that a one-piece NB2 model does not reproduce, even after the NB model is allowed a free depth slope.

What failed was the **specific deep hierarchical Bernoulli parameterization and its posterior geometry**, not the biological/statistical idea that detection should be modeled separately.

The next Bayesian generation should therefore retain a two-part architecture but simplify and empirically regularize the detection component before any new confirmatory freeze. Candidate simplifications include fewer weakly identified random-effect levels, partial pooling informed by observed crossing/information per level, and only those source/operator/donor-class components demonstrably estimable from development data.

The positive-magnitude family remains unresolved. Lognormal and ZTNB should continue as development competitors until a broader corrected-TRAIN comparison supplies a defensible separation.

## Controller ruling

- Bernoulli/detection V2 remains `NOT_QUALIFIED`; this tournament does not rehabilitate it.
- Gaussian/lognormal/ZTNB confirmatory S0-S5 campaign remains on methodological hold.
- Do not spend compute running the queued 18 fits under the old freeze.
- Use this tournament as development evidence to design a simpler next-generation two-part model.
- Before the next confirmatory qualification, replay the development tournament on the exact corrected S174 cache and expand the identity-blind gene sample.
- Only after development should a new candidate be frozen and challenged on untouched synthetic worlds.

No posterior parameter export, H1/H2 update, factorial execution or JEPA training is authorized.

Terminal:

`EMPIRICAL_DEVELOPMENT_TOURNAMENT_COMPLETE__TWO_PART_MODEL_SUPPORTED__OLD_BERNOULLI_PARAMETERIZATION_REMAINS_FAILED__POSITIVE_FAMILY_UNRESOLVED__NEW_MODEL_DEVELOPMENT_REQUIRED__TRAINING_OFF`

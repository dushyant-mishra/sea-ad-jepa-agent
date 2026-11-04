# JEPA cross-lane audit — Macha V77 canonical-universe correction — 2026-10-06

## Superseding synthetic-lane commit

`6821f164c571aa38f32d45cba3e2894706742a79`

This supersedes the earlier cross-lane interpretation of `c4f12597...` wherever the two conflict.

Lane status remains:

`SUPPORTED_FOR_NEXT_STAGE__ISSUE_1_NARROWED__PROMOTION_NOT_YET_QUALIFIED`

No Stage A, production-world rebuild, training, optimizer/EMA mutation, checkpoint authority, or protected-data execution is authorized.

---

## 1. Audit verdict

The correction is valid and material.

The previous near-exact topology claim must be treated as retracted. Per-arm prevalence filtering changed the graph vertex set between candidates and produced an upward bias by hiding canonical-gene loss.

On the frozen `TRAIN_PREVALENCE05_19569` universe, the deterministic arm is not close enough to the real target to support the earlier headline:

| metric | old per-arm | corrected canonical | real |
|---|---:|---:|---:|
| frac `|corr| > .3` | 0.6154 | 0.5208 | 0.6148 |
| transitivity | 0.8238 | 0.7645 | 0.8871 |
| mean degree | 1846 | 1561.8 | 1843.8 |
| abundance max/median | 2908.1 | 7625.8 | 1976.6 |

The deterministic arm has only 9,605 nonzero-variance genes on the 19,569-gene canonical universe, i.e. 9,964 canonical genes are lost.

The abundance-recovery claim is also not established: deterministic max/median is 7625.8 and Poisson max/median is 26753.4, both outside the frozen `[1804.75, 2187.67]` envelope.

---

## 2. What survives and is now stronger

The realization isolation is now promotion-grade as a **diagnostic comparison**, because both arms use the same:

- frozen generator;
- latent abundance/rate field;
- capture propensity;
- cell state;
- seed;
- canonical 19,569-gene evaluation universe;
- executor and command;

with realization mode as the single intended variable.

Under this isolation:

- deterministic transitivity: `0.76455`;
- Poisson transitivity: `0.35546`;
- deterministic mean degree: `1561.76`;
- Poisson mean degree: `8.36`.

So stochastic counting alone destroys most of the recovered dependence topology under the current fixed rate field.

This supports the revised causal wording:

> With the current fixed generator and the current independent-capture Poisson observer, introducing counting noise destroys the recovered dependence topology. This is consistent with insufficient latent rate dynamic range and makes generator dynamic range the next falsifiable target.

Do not upgrade this to exclusive generator causality.

---

## 3. Important correction to the proposed sequencing language

The statement that Poisson is "the only realization regime that keeps the gene universe intact" is too strong.

The **evaluation universe** is intact by construction in both arms because both are scored on the frozen 19,569 canonical genes.

What differs is how many canonical genes retain nonzero variance:

- deterministic: `9,605` nonzero-variance genes; `9,964` lost;
- Poisson: `18,372` nonzero-variance genes; `1,197` lost.

So the correct statement is:

> Poisson preserves substantially more of the canonical universe as nonzero-variance observed genes than deterministic thresholding, while deterministic thresholding collapses more than half of the canonical genes to zero variance.

That makes deterministic thresholding a poor candidate production observer at the current parameters.

---

## 4. Next experimental target

Dynamic-range experiments should primarily target the **Poisson realization regime**, because:

1. it is the biologically relevant stochastic-counting regime among the two current realizations;
2. it preserves far more canonical genes as nonzero-variance observations;
3. it is exactly where current dependence topology collapses;
4. therefore a successful dynamic-range repair under Poisson would address the actual stochastic-observation failure instead of optimizing a deterministic diagnostic surrogate.

However, do **not** describe Observer-V2 as globally frozen/qualified. Freeze only the parts needed for a controlled diagnostic:

- independent capture parameterization;
- cell-state parameterization;
- Poisson realization rule;
- canonical evaluation universe;
- seed protocol;
- scoring code and envelopes.

Then vary **generator dynamic range only** in a small predeclared mechanistic family.

The deterministic arm should remain as a diagnostic control, not as the optimization target.

---

## 5. What the next family must measure

For each predeclared dynamic-range candidate, require at minimum:

- canonical genes with nonzero variance;
- canonical genes lost;
- median detected genes per cell;
- abundance max/median on `TRAIN_PREVALENCE05_19569`;
- top-1% count share on the same universe;
- median `|corr|`;
- fraction `|corr| > 0.3`;
- mean degree;
- transitivity;
- sign balance / positive-vs-negative dependence;
- largest-community fraction;
- depth/capture marginals already frozen by the current observer contract.

A candidate that repairs topology by again destroying canonical genes or worsening abundance concentration is not acceptable.

---

## 6. Synthetic-lane disposition

Issue 1 remains narrowed but open.

The project has learned something important and falsifiable:

- per-arm filtering was invalid and is now fixed;
- deterministic thresholding created severe canonical-gene loss;
- Poisson retains most canonical genes but destroys dependence topology under the current rate field;
- abundance concentration is still badly wrong in both realization arms;
- generator dynamic range under Poisson is therefore the next justified experiment, not another broad observer search and not a return to the original 37-generator sweep.

After that, Issue 2 sign/community co-calibration remains necessary, followed by A_REPLICA at promotion.

---

## 7. Runtime-lane effect

None of this reopens completed runtime audits.

Runtime work continues independently at:

- exact historical authority/guard source/test recovery where still missing;
- current V5 optimizer/scaler/EMA/checkpoint/resume mutation-site inventory;
- RED bypass tests;
- minimal authority-bound canonical mutation consumer;
- deterministic authority-bound restart;
- deliberate comparison against post-PR220 `main`.

Training remains OFF.

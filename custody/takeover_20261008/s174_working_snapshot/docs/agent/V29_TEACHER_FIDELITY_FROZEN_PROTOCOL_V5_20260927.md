# Frozen protocol v5 — teacher-only biological fidelity

**Prospectively dated successor to v4
(`0ad1a601`, sha256 `2bb642f792400bf0c17550099596b2c1e5c5847cf1986697fa33a672b2efb8ff`).**
v1–v4 preserved unedited as historical record. v5 is the sole execution
authority.

**Frozen 2026-09-27, before the synthetic gate is run and before any control
gene is extracted.** Three implementation defects were found in review; all
three are specification errors, none depends on data.

## What changed from v4

### A. The response is never centered — model space and evaluation space separated

v4 said "leave-one-out within-stratum centering of every predictor **and of the
readout**" while also specifying a negative-binomial GLM whose response is the
readout count. **A centered count can be negative and cannot be an NB
response.** The two requirements were mutually impossible.

Resolved by putting each transformation in its own space:

> **Model space.** The NB GLM is fitted to the **original nonnegative counts**
> with the frozen `log D` offset. Nothing about the response is centered,
> residualised or rescaled. The count likelihood is untouched.
>
> **Evaluation space.** Prediction performance is computed **within stratum**
> from the fitted model's predicted means against the observed counts.

### B. Outcome centering is a no-op for the statistic, so it is removed

Within a stratum, leave-one-out centering maps each observation to
`x·n/(n−1) − S/(n−1)` with `n` and `S` shared across that stratum — a positive
affine map, which **preserves ranks exactly**. The primary statistic is a
within-stratum Spearman correlation, which is a rank statistic. It is therefore
**invariant** to the centering.

The centering was buying nothing and costing something real: it made the
analysis transductive in the held-out donors' own outcomes, which v4 had to
disclose and defend. **Outcome centering is removed entirely, and with it the
outcome transduction.**

**Predictors are still centered within stratum**, because that is what confines
the comparison to within a donor and region, and it remains a transferable
transformation computable from a held-out donor's own cells. It uses only
predictor values — never the readout — so it is ordinary preprocessing and not
outcome leakage. Leave-one-out is retained there.

### C. The synthetic gate must include the sparse, shared-capture-efficiency regime

CLR is scale-invariant **only without a pseudocount**. With `log(x + α)`,
scaling `x → c·x` does not factor out unless `α` scales too. At high counts `α`
is negligible and the invariance is effectively real. At the counts these
programs actually have — partner medians of **one to four molecules** — it fails,
and capture efficiency leaks directly into a quantity v4 assumed carried no `D`
at all.

The negative control therefore runs in **both regimes**, and passing the
high-count arm alone is not sufficient:

| arm | numerators | shared factor | counts | required verdict |
|---|---|---|---|---|
| NEG-1 | independent | denominator varies | high | no association |
| NEG-2 | independent | **capture efficiency varies** | **sparse, matched to real medians** | **no association** |
| POS-1 | genuinely associated | denominator varies | high | association detected |
| POS-2 | genuinely associated | capture efficiency varies | sparse | association detected |

All four must return their required verdict. NEG-2 is the one that matters: it
is the regime the real data is in, and it is the regime where the CLR invariance
argument breaks.

## 1–2. What is tested, and the six directed tests

Unchanged from v4. R8's measured per-nucleus program state, not a trained
teacher. Six ordered predictor→readout pairs, each program read out by the other
two. All six reported including failures; no program gene predicts itself; no
reserved gene touched.

## 3. Denominator — single frozen authority

Unchanged from v4.

```
EXCLUDED(P,Q) = query(P) ∪ panel(P) ∪ query(Q) ∪ panel(Q)
              ∪ RESERVED 6 ∪ HOUSEKEEPING 8
              ∪ AMBIENT 10 ∪ MYELOID_IDENTITY 6 ∪ MITOCHONDRIAL 3

D_i(P,Q) = total_all_i − Σ counts_i[a]  over a ∈ EXCLUDED(P,Q)
                                         with address_available_i[a] == True
```

An unavailable address is never summed and never treated as a zero. A nucleus is
dropped if `D_i ≤ 0` or if any `panel(P)` or `panel(Q)` address is unavailable
for it; drops are counted and reported. `D` enters only as `log D`, an offset.

## 4. Controls

Unchanged from v4: depth; ambient RNA (10 lineage-foreign genes); generic
myeloid identity (6); mitochondrial (3); query-only; and an abundance-matched
sham program.

## 5. Design

- **Model:** negative-binomial GLM on the **raw readout partner count**, `log D`
  offset. Dispersion and regularisation estimated within fitting donors only.
- **Predictors:** `CLR_P` (primary) and `log1p(N_P)`, plus the controls, each
  **leave-one-out centered within `donor × operator` stratum**. Predictor-only;
  the readout is never centered.
- **Minimum stratum size 20 nuclei**; smaller strata dropped and counted.
- **Split:** held-out donors, two thirds fitting / one third evaluation, by hash
  of the source-specific donor identity. Sources never pooled.
- **Statistic:** within-stratum Spearman between observed count and predicted
  mean; increment from adding `S_P` to the controls; computed per stratum, then
  median across a donor's strata, then summarised across evaluation donors.

## 6. Decision rule and unit of qualification

Unchanged from v4. A directed pair passes if its permutation p-value
(within-stratum permutation of `S_P`, B = 999) survives **Benjamini–Hochberg at
q = 0.05 across the six directed tests**, the increment is positive in at least
**two thirds** of evaluation donors, and the real program **beats the
abundance-matched sham**. A **program qualifies** only if **both** its directed
tests pass; one of two is *partial* and does not qualify it. Primary reporting
unit is the directed pair.

**Gate:** all four synthetic arms in §C must return their required verdict
before any real data is read. **Failure is a result** — no refitting, no changed
controls, no dropped donors, no reporting the better readout.

## 7–8. Interpretation and standing constraints

Unchanged. A pass is preliminary **same-assay program coherence**, not
independent validation, and authorises no training. Reserved and frozen: SALL1,
CTSD, CTSS, LPL, CSF1R, HLA-DMB. HVS excluded from anything requiring observed
LPL. Every input digested in the receipt. `TRAINING=OFF`, protected outcomes
unopened. Scope: audited addresses in candidate myeloid nuclei; the 29-address
repair does not license the general FULL104 reader.

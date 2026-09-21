# Audit D — held-out-donor standardization: what estimand is it?

Date: 2026-09-20
Status: **characterization only. No regime selected. The canonical attacker is
unchanged.**

Produced by `scripts/audit_d_standardization_estimand_20260920.py`.
Evidence: `evidence/audit_d/ATTACKER_STANDARDIZATION_CALIBRATION_RESULTS.json`,
`evidence/audit_d/ATTACKER_STANDARDIZATION_FIXTURE_RESULTS.csv`.

No terminal masking outcome was run under any alternative definition. Everything
below is fixtures.

---

## 1. What the current attacker actually does

From `_standardized_components`, verbatim:

```python
mean_x = st.sum_x / st.n
var_x  = np.maximum(st.sum_x2 / st.n - mean_x * mean_x, 0.0)
sd     = np.sqrt(var_x); sd = np.where(sd > _EPS, sd, 1.0)
gram   = (st.sum_xx - np.outer(st.sum_x, st.sum_x) / st.n) / (sd[:,None] * sd[None,:])
rhs    = (st.sum_xy - st.sum_x * (st.sum_y / st.n)) / sd
```

and in `_source_balanced_prediction_score` these components are taken from
`stats[d]` where `d` ranges over the **held-out** donors.

So each held-out donor's own feature mean and SD are used to standardize its
features before prediction. No held-out **target** label is used, so this is not
classic target leakage. It is **transductive feature adaptation**.

## 2. The exact consequence, measured not argued

If donor *d*'s features are transformed `x → a·x + b` with `a > 0`, centring by
that donor's own mean and dividing by that donor's own SD returns numerically
identical standardized features. So `gram`, `rhs`, and therefore `r`, are
unchanged.

Measured on a fixture, applying an independent random affine transform per donor:

| regime | score before | score after | absolute change |
|---|---|---|---|
| **D1_CURRENT** | 0.8073577812446403 | 0.8073577812446403 | **0.000e+00** |
| D2_TRAIN_ONLY | 0.8084384127206592 | 0.8074883893826963 | 9.500e-04 |
| D3_NO_DONOR_ADAPTATION | 0.8084360557498478 | 0.8073647175956533 | 1.071e-03 |

D1 is invariant to bit-level identity, not approximately. A shortcut living
purely in per-donor feature scale or offset is invisible to this attacker by
construction — not because it is small, but because the estimand cannot express
it.

## 3. The three regimes and what each asks

| regime | standardization | scientific question |
|---|---|---|
| **D1_CURRENT** | each donor's own mean/SD, held-out included | given this donor's internal feature geometry, does the masked representation still predict the target *within* this donor? |
| **D2_TRAIN_ONLY** | mean/SD pooled over training donors, applied unchanged | does a predictor fitted *and scaled* on training donors transfer to an unseen donor? |
| **D3_NO_DONOR_ADAPTATION** | none beyond the frozen production normalization | is the target predictable from absolute normalized values, including donor- and source-level scale? |

These are three different questions, not three implementations of one.

## 4. Fixture results

Source-balanced mean of squared within-donor centred prediction correlation,
unconditional over all four donor-honest folds (every fold in the denominator;
`folds_finite = 4` everywhere).

| fixture | D1_CURRENT | D2_TRAIN_ONLY | D3_NO_DONOR_ADAPTATION |
|---|---|---|---|
| null | 0.001922 | 0.001862 | 0.001862 |
| within_donor_signal | 0.794450 | 0.795496 | 0.795497 |
| donor_scale_nuisance | 0.001922 | 0.001460 | 0.001459 |
| within_donor_signal_plus_donor_scale | 0.794450 | 0.780270 | 0.779460 |
| per_cell_denominator_channel | 0.003063 | 0.003166 | 0.002737 |
| per_cell_denominator_channel_no_target_link *(negative control)* | 0.002635 | 0.002640 | 0.002624 |

## 5. What this corrected

I began this audit expecting to show that D1 suppresses a donor-level shortcut
channel that D2 or D3 would reveal. **The fixtures refuted that**, and the
refutation is the more useful result.

On `donor_scale_nuisance` — where the shortcut lives entirely in per-donor scale
and offset — *every* regime sits at its null floor. D1 gives 0.001922, exactly
its null value. But D2 and D3 give 0.001460 and 0.001459, also at null.

The reason is not the standardization. It is the **score**. The primary score
computes a *within-donor centred* correlation:

```python
yc = yd - yd.mean();  pc = pred - pred.mean()
r  = (yc @ pc) / sqrt((yc @ yc) * (pc @ pc))
```

Centring within the donor removes any donor-level offset from both the target
and the prediction before the correlation is taken, in **every** regime. So
blindness to donor-level channels is a property of the primary score definition,
not of the standardization choice.

**Changing D1 → D2 would therefore not restore visibility of donor- or
source-level shortcuts.** The gap is one level up, at the estimand.

What D1 *does* uniquely provide is exact invariance, and with it robustness: on
`within_donor_signal_plus_donor_scale`, D1 returns 0.794450 — identical to the
clean-signal case — while D2 and D3 degrade to 0.7803 and 0.7795 because they
must fit across heterogeneous donor scales. D1 is not less sensitive to genuine
within-donor signal; it is more robust to donor-scale heterogeneity.

## 6. The per-cell denominator channel

Audit A establishes that the normalization denominator carries a strongly
source-dependent component. Unlike a per-donor offset, it varies **cell to
cell**, so within-donor centring does not remove it.

The fixture models it at real geometry — sparse non-negative counts, ~83%
measured zeros, the frozen `log1p(raw · 10000 / L)` applied literally, and
`L = ledger / (1 − outside)` with the measured source-dependent outside
fractions. The target is itself a normalized address, so it carries the same
denominator. This matters: an **earlier version of this fixture used mean-zero
Gaussian features and detected nothing**, because a linear predictor cannot
express a pure scale change on mean-zero features. That version was not evidence
of absence; it was a fixture that did not match the real geometry. It was
replaced rather than reported.

At real geometry the channel is **present but weak**: 0.003063 against its own
negative control at 0.002635, an excess of about 0.0004. All three regimes see
it about equally, so this channel does not discriminate between them either.

The fixture uses 32 features. The production model sees 17,186 addresses that
all share one denominator, so the channel has far more surface to aggregate over
than this fixture gives it. **That is a reason not to treat 0.0004 as an upper
bound** — but it is also not evidence that the real magnitude is larger. Sizing
it properly needs the real substrate, and that is exactly what Audit A's
per-cell artifact enables later.

## 7. Findings

**D-1. `ATTACKER_D1_IS_EXACTLY_AFFINE_INVARIANT_PER_DONOR` — established.**
Measured change 0.000e+00 under per-donor affine feature transformation.

**D-2. `DONOR_LEVEL_SHORTCUT_BLINDNESS_IS_A_SCORE_PROPERTY_NOT_A_STANDARDIZATION_PROPERTY`
— established, and it corrects the hypothesis this audit started from.**
All three regimes sit at the null floor on a pure donor-scale shortcut, because
the within-donor centring inside the score removes donor-level structure before
the correlation is taken.

**D-3. `G3_DESIGN_BLOCKER__ESTIMAND_CANNOT_EXPRESS_DONOR_OR_SOURCE_LEVEL_CHANNELS`
— OPEN.**
A production JEPA reading absolute normalized values across donors and sources
can use structure this attacker's estimand removes by construction. A
capacity-matched attacker (G3) that inherits the same within-donor centred score
would inherit the same blindness, however much capacity it is given. So G3 must
settle the **estimand**, not only the capacity and functional form recorded in
`J_G3_ATTACKER_CAPACITY_20260920.md`.

## 8. What is not concluded

No regime is selected. The canonical attacker is unchanged. These are fixtures,
not the real substrate, and the fixture magnitudes are not transferable
estimates. Whether the estimand should change is a scientific design decision
that belongs with G3 and G5, and it must not be made by whichever regime happens
to produce a preferred number.

```
REGIME_SELECTED = NONE
CANONICAL_ATTACKER_CHANGED = false
TRAINING_OFF
```

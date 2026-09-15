# V5 Layer-2 cross-view shortcut closeout — 2026-09-15

Package: `analysis/v5_layer2_cross_view_shortcut_20260915/`
Closeout manifest: `V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json`
sha256 `105092b41cd132a6134d548bbba26de05204e04a9af5139aae913d50122741f3`

Scope: **Layer 2 only** — shortcut exposure of the cross-view training objective.
Not Layer-1 substrate qualification. Not Layer-3 downstream inference.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION` · no representation change ·
no operator/source residualization · residual objective specified only, not implemented.

---

## 0. Layer separation

| layer | question | status |
|---|---|---|
| 1 — representation substrate | is VALUE_ONLY a reasonable molecular representation of a cell? | measurement response characterized |
| **2 — training anti-cheat** | **does the V0↔V1 task reward shared technical / context state?** | **this closeout** |
| 3 — downstream inference | is donor-level inference nuisance-robust? | deliberately deferred |

Donor-level work was deferred on the grounds that a model can learn a cell-level shortcut and
still produce stable donor averages; averaging cannot rescue a flawed objective.

---

## 1. Population, folds, model class

BASE_MECHANICS probability sample: 196,817 cells, 94 donors, 42 operators
(HVS 88,015 · NPH52 41,218 · SEA_AD 67,584). Source-conditional stress strata excluded
from all weighting.

Inclusion `q_i = min(12, B_o)/B_o`, whole blocks. Content-independence of the selection hash
is **proven by reproduction**: recomputing the rank from namespace + `block_key` alone
reproduced the frozen 396-block selection exactly (396/396, 0 missing, 0 extra).

Fold identities, binding digest `f0ca25e5e91d2b87991a6ea301d41a4f64d8805519aa39370e29dd43c8635ec0`:

- donor-held-out: `donor_code mod 5` → [39924, 33340, 44759, 39770, 39024]
- cell-held-out: `default_rng(7).integers(0,5)` → [39358, 39351, 39087, 39504, 39517]

Model class: ridge, `lambda = 1e-2 * n_train`; metric total-variance-explained OOF R².
Frozen in `X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json` (`b280a1ed…`) **before** any computation.

---

## 2. Measurement-state shortcut — small

`V0^p → V1^p` is *worse* than `V0^1.0 → V1^p` at every level, both directions
(−0.0018 at p=0.90 to −0.0158 at p=0.25): matching measurement state does not help.

Against the classical attenuation null `C(p_i,1)·C(1,p_j)/C(1,1)`:

| p | observed | null | synergy | % of C(1,1) |
|---|---|---|---|---|
| 0.90 | 0.4519 | 0.4519 | +0.0000 | 0.00% |
| 0.75 | 0.4266 | 0.4264 | +0.0002 | 0.05% |
| 0.50 | 0.3720 | 0.3707 | +0.0013 | 0.27% |
| 0.25 | 0.2882 | 0.2831 | +0.0051 | 1.09% |

The 5×5 matrix is separable to within 1.8% at its most extreme corner.

**Consequence:** the shared-denominator ablation and any measurement-decorrelated objective
are not justified by evidence — eliminating the shared denominator entirely buys ≤0.005 R².

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS` — bounded at ~1%, **not absent**.
A linear probe does not clear a deep encoder trained against this objective.

---

## 3. Context decomposition — independently reproduced

Path A (hand-rolled normal equations, `np.linalg.solve`, manual standardisation, `get_dummies`)
vs Path B (sklearn `StandardScaler` + `Ridge` + `OneHotEncoder` + `r2_score(variance_weighted)`),
identical cells and folds:

| predictor set | PATH A | PATH B | abs diff |
|---|---|---|---|
| Q only | 0.030610 | 0.030610 | 1.0e-14 |
| source only | 0.338003 | 0.338003 | 6.8e-15 |
| operator only | 0.459719 | 0.459719 | 6.8e-15 |
| source + operator | 0.459742 | 0.459742 | 4.7e-15 |
| operator + Q | 0.467122 | 0.467122 | 5.1e-15 |
| V0 only | 0.466622 | 0.466622 | 5.2e-15 |
| operator + V0 | 0.496594 | 0.496594 | 4.7e-15 |
| operator + Q + V0 | 0.498035 | 0.498035 | 4.1e-15 |

Worst disagreement 1.04e-14 against a 1e-4 tolerance declared before the run.
Overlap: unique to V0 +0.0369 · unique to operator +0.0300 · shared +0.4297.
Operator subsumes source (adding source to operator moves R² by 0.00002).

`CONTEXT_SHORTCUT_DECOMPOSITION_INDEPENDENTLY_REPRODUCED`

---

## 4. Estimand sensitivity

| estimand | Kish ESS | ctx R² | V0 R² | both | mol increment | within-donor |
|---|---|---|---|---|---|---|
| unweighted reconnaissance | 196,817 | 0.4671 | 0.4666 | 0.4982 | +0.0311 | 0.1850 |
| empirical / FULL104 structure | 61,374 | 0.2651 | 0.3645 | 0.3858 | **+0.1207** | 0.2182 |
| source-uniform | 96,338 | 0.4715 | 0.4746 | 0.5002 | +0.0287 | 0.1750 |
| donor-primary | 34,726 | 0.4532 | 0.4536 | 0.4855 | +0.0323 | 0.1764 |

Views reported separately, never combined. All qualitative conclusions survive all four.

**Context dominance is substantially an artifact of the reconnaissance sampling distribution.**
Under the population-proportional view the molecular increment is ~4× larger and context R²
falls from 0.467 to 0.265, because the reconnaissance sample over-represents HVS and NPH52 —
the two batch-heavy sources.

`ESTIMAND_SENSITIVITY_CHARACTERIZED`

---

## 5. Variance structure by source

| source | between-operator | donor-within-operator | within-donor |
|---|---|---|---|
| HVS | 0.213 | 0.193 | 0.595 |
| NPH52 | 0.253 | 0.228 | 0.519 |
| SEA_AD | 0.028 | 0.040 | **0.932** |

A partition-granularity explanation for SEA_AD's behaviour was hypothesised and **refuted** by
this decomposition: SEA_AD retains its signal because it has almost no batch structure to
remove, not because its operator partition is coarse.

---

## 6. Within-donor cell-level signal, and what carries it

Donor-centred, cell-held-out. Estimator validated before use (§9).

| source | QC only | V0 only | V0 increment over QC | QC increment over V0 |
|---|---|---|---|---|
| ALL | 0.0208 | 0.1850 | **+0.1668** | +0.0026 |
| HVS | 0.0535 | 0.1906 | +0.1401 | +0.0029 |
| NPH52 | 0.0690 | 0.2646 | +0.1982 | +0.0026 |
| SEA_AD | 0.0575 | 0.2487 | +0.1941 | +0.0029 |

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

This rules out the **measured** `Q_DEPTH`/`Q_DETECT` family as the primary explanation. It does
**not** eliminate unmeasured technical state. The claims `THE_SIGNAL_IS_BIOLOGICAL` and
`THE_SIGNAL_IS_NOT_TECHNICAL` are explicitly **not** made.

### Donor-level recurrence

94/94 donors evaluable (≥30 held-out cells).

| source | donors | min | Q1 | median | Q3 | max | frac > 0 | frac > 0.10 |
|---|---|---|---|---|---|---|---|---|
| ALL | 94 | −0.0224 | 0.1500 | 0.1739 | 0.2050 | 0.2695 | 98.9% | 93.6% |
| HVS | 41 | 0.0758 | 0.1392 | 0.1582 | 0.1810 | 0.2695 | 100.0% | 92.7% |
| NPH52 | 17 | −0.0224 | 0.2016 | 0.2204 | 0.2498 | 0.2695 | 94.1% | 94.1% |
| SEA_AD | 36 | 0.0892 | 0.1614 | 0.1809 | 0.1919 | 0.2379 | 100.0% | 94.4% |

Recurrent across donors, not carried by a small subset. `DONOR_LEVEL_RECURRENCE_CHARACTERIZED`

---

## 7. Donor generalization — leave-one-donor-out, complete refit

Operator means re-estimated and ridge refit from scratch per held-out donor. Fast accumulation
verified against a direct implementation at ≤2.1e-14. Zero sole-donor operators.

| source | donors | pooled LODO R² | min | median | max | frac > 0 | 5-fold (fixed models) |
|---|---|---|---|---|---|---|---|
| HVS | 41 | 0.0451 | 0.0189 | 0.0419 | 0.1363 | 100% | 0.0437 |
| NPH52 | 17 | 0.0546 | 0.0311 | 0.0577 | 0.0940 | 100% | 0.0530 |
| SEA_AD | 36 | **0.2410** | 0.1491 | 0.2408 | 0.2996 | 100% | 0.2402 |
| ALL | 94 | 0.0687 | 0.0026 | 0.0442 | 0.2543 | 100% | 0.0687 |

Full refitting moves nothing — the earlier fixed-model intervals were not understating
uncertainty in a way that mattered. The donor distributions **separate completely**: SEA_AD's
weakest donor (0.1491) exceeds HVS's strongest (0.1363) and NPH52's strongest (0.0940). With
17 NPH52 donors this remains a small-sample claim, but it is not driven by outliers.

`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`
`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`

The negative result is **not** converted into absence.

---

## 8. Loss-geometry proxy

| | raw target | layer-normalised |
|---|---|---|
| context only, donor-held-out | 0.4671 | 0.4683 |
| molecular increment over context | +0.0311 | +0.0432 |
| within-donor molecular | 0.1850 | 0.1960 |

`MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED` — **`MECHANICS_ALIGNED_PROXY_ONLY`.** The real
objective operates on trained-encoder hidden states, which do not exist under `TRAINING_OFF`,
and V5 target semantics are not frozen. Historical V4 semantics were **not** inherited.

---

## 9. Estimator validation and a withdrawn implementation

Any estimator reporting signal *remaining after removing group structure* has a leakage failure
mode that manufactures within-group signal from nothing. The estimator used here was validated
first (`scripts/x6_fixture.py`):

| fixture | truth | raw R² | group-centred R² | |
|---|---|---|---|---|
| operator structure only, zero cell-level signal | 0 | 0.8299 | **−0.0068** | PASS |
| + planted cell latent (0.5 / 1.0) | >0 | 0.876 / 0.904 | 0.233 / 0.595 | PASS |
| no shared structure | 0 | −0.0020 | −0.0020 | PASS |

A first implementation (`withdrawn/x4_within_DEFECTIVE.py`) double-centred training data
inconsistently across folds and reported substantial within-operator signal on the null fixture.
Its outputs were discarded and never entered the evidence record. It is retained so the defect
claim is reproducible.

**Donor-centring under donor-held-out CV is not identifiable** — a held-out donor has no
training rows from which to estimate its mean. It is excluded by construction, not computed and
discarded after inspection.

---

## 10. Corrections to earlier reporting

1. **"~85% of the cross-view signal is operator-level mean structure."** Computed correctly, but
   it conflated between-source pooling inflation with donor-generalisation failure. Pooled raw
   R² is 0.4666 while *within-source* raw R² is 0.21–0.28; the pooled figure is inflated by
   between-cohort contrast. Superseded by §5–§7.
2. **"pair Spearman 0.969 → 0.730 (BASE)."** 0.730 is the STRESS_SEA_AD Euclidean value, not
   BASE. BASE at p=0.25 is 0.8197 (V0) / 0.8010 (V1).
3. **"real pairing minus permutation floor = biological signal."** Withdrawn. The unexplained
   remainder holds unmeasured technical state and representation artifacts, not only biology.
4. A nuisance-matched permutation test was **retired before execution**: exact matching on
   realized `(L_p, detect_p, source, operator)` leaves overwhelmingly singleton strata, and
   coarsening the match after observing that would be threshold-widening after seeing the
   discrepancy.

---

## 11. Residual-over-context — specification only

`Z_RESIDUAL_OVER_CONTEXT_SPECIFICATION.md` (`d088bdef…`).

```
prediction_i = stop_gradient(g_phi(C_i)) + f_theta(V0_i)
loss         = L(prediction_i, T_i)        # complete target, unmodified
```

Nothing subtracted from input or target. Labelled
`PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`, never "biology". **Not implemented.**
Five preconditions listed, including a failure mode of its own: an overfit frozen baseline
understates the increment.

---

## 12. Unresolved

- Non-linear model class untested; a linear probe bounds neither direction.
- Why HVS and NPH52 fail donor generalization while SEA_AD succeeds — cohort heterogeneity is a
  hypothesis, not evidence.
- Whether unmeasured technical state explains part of the within-donor signal.
- Whether the residual construction changes what the molecular pathway *learns* — requires training.
- V5 teacher target undefined, so only a geometry proxy is possible.
- Whether operator identity is admissible as a training-time input — a design decision, not a
  measurement.

---

## Terminals

**Established**

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`
`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`
`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS`
`DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS`
`CONTEXT_SHORTCUT_DECOMPOSITION_INDEPENDENTLY_REPRODUCED`
`ESTIMAND_SENSITIVITY_CHARACTERIZED`
`DONOR_LEVEL_RECURRENCE_CHARACTERIZED`
`MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED`

**Retained**

`BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104`
`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`
`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`
`MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`
`V3_NULL_NOT_YET_FROZEN`
`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
`TRAINING_OFF`

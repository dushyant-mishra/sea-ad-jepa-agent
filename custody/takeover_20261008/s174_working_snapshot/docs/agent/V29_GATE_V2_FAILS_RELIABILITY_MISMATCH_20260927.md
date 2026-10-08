# Gate v2 fails: the sham is matched on marginals, not on reliability

Date 2026-09-27. Receipt `results/v29/TEACHER_FIDELITY_SYNTHETIC_GATE_V2.json`.
**No real expression has been read. No control gene has been extracted.**

## Result

| arm | wanted | increment | sham-null p | donors + | qualifies | verdict |
|---|---|---|---|---|---|---|
| NEG-1 | no | −0.0145 | 0.7750 | 0.36 | no | PASS |
| NEG-2 | no | **+0.0230** | **0.0050** | 0.73 | **yes** | **FAIL** |
| POS-1 | yes | +0.7737 | 0.0050 | 1.00 | yes | PASS |
| POS-2 | yes | +0.2015 | 0.0050 | 1.00 | yes | PASS |

Calibration across 40 independently generated datasets:

- **NEG-2 qualified in 39 of 40 — a false-positive rate of 0.975**
- POS-2 qualified in 40 of 40 — power 1.000

The sham-generated null did not fix the problem. One seed would have shown the
arm failing; only the replication shows it fails essentially always.

## Diagnosis — measured, not assumed

| quantity | real | sham |
|---|---|---|
| mean pairwise Spearman among the four partners | +0.425 | +0.355 |
| amplitude vs log capture efficiency | +0.641 | **+0.657** |
| **amplitude vs the true shared per-nucleus rate** | **+0.853** | **+0.496** |

The sham tracks capture *slightly better* than the real program, so the capture
channel is matched. What is **not** matched is **reliability**.

The real program's four partners share a per-nucleus latent, so its amplitude is
a much less noisy estimator of whatever per-nucleus factor is present. The sham's
partners are conditionally independent given the depth weight, so its amplitude
is noisier. After the controls partial out `log D`, the real state retains more
capture information than the sham purely by being a **better instrument** — not
by carrying any biology.

That is why it beats the sham in 39 of 40 datasets while containing, by
construction, no relationship to the readout whatsoever.

## What this means

Three distinct failure modes have now been found before any real data was
touched, each by the gate:

1. **the permutation null is the wrong null** — permuting the state destroys the
   technical link along with the biological one, so it asks "is there any
   dependence" instead of "is there dependence beyond the technical factor";
2. **a two-thirds-of-donors sham vote is not error control** — with nine
   evaluation donors it fires about 25% of the time under exchangeability;
3. **a marginally matched sham is not a valid null** — matching abundance,
   sparsity and capture sensitivity leaves reliability unmatched, and the more
   reliable instrument wins regardless of biology.

## The fix that follows from the diagnosis

The sham must additionally match the real program's **internal coherence**: its
four partners must share a per-nucleus latent of the same magnitude, drawn
independently of the readout. Then real and sham differ in exactly one respect —
whether their latent relates to `Q` — which is the contrast the test is supposed
to make.

That is implementable: the shared-latent magnitude is estimable from the partner
covariance structure, and a sham drawn with matched shared dispersion,
abundance, sparsity and capture weight would be a null of matched reliability.

## The honest caveat, and why this is reported rather than iterated

Each fix has revealed the next gap. That is the gate working, and it is also a
signal worth stating plainly: predicting one program's **count** from another
program's **state** when both carry a shared per-nucleus nuisance may be close to
unidentifiable by this route, because any statistic that estimates the nuisance
better will win.

A reliability-matched sham is the next prospective revision and it is worth
running. If it also fails, the problem is the **readout construction**, not the
null — and the alternative would be a readout that is nuisance-free by
construction, such as `Q`'s own composition rather than its count, so that
capture largely cancels on the readout side and a better nuisance-meter gains
nothing.

**The real-data gate stays closed.** No control gene extraction, no R7/R8
replay, until a gate passes with a measured NEG-2 false-qualification rate at or
below nominal.

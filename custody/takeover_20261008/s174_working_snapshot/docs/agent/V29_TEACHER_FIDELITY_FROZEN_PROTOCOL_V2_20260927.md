# Frozen protocol v2 — teacher-only biological fidelity

**Supersedes `V29_TEACHER_FIDELITY_FROZEN_PROTOCOL_20260927.md`
(sha256 `5aead8edb9cb25b2fca50dc76fe21e26b4f505e2513513b4a12fe401bb1fc604`,
commit `027866e8`).**

**Frozen 2026-09-27, still before any control gene was extracted and before any
outcome was computed.** That is what makes this a legitimate revision rather
than threshold shopping: no result existed to steer it. Two defects in v1 were
found in review, both structural, neither dependent on data. Everything else —
the readout choice, the controls, the permutation null, the two-thirds donor
criterion, the reserved-gene freeze — is carried over unchanged.

## What changed from v1, and why

### 1. Six ordered tests, not nine

v1 said "all nine program × readout combinations." With each program read out by
the **other two**, there are **6** ordered predictor→readout pairs:

| predictor | readouts |
|---|---|
| APOE_LIPID | P2RY12_HOMEOSTATIC, HLA_DRA_ANTIGEN |
| P2RY12_HOMEOSTATIC | APOE_LIPID, HLA_DRA_ANTIGEN |
| HLA_DRA_ANTIGEN | APOE_LIPID, P2RY12_HOMEOSTATIC |

Three by three counts the self-pairs that v1 had already excluded as circular.
All six are reported, including failures.

### 2. The stratum control must be a transformation, not a fitted effect

v1 listed a "donor × operator fixed effect" among the controls while holding out
whole donors. Those are incompatible: a fitted donor dummy has no coefficient
for a donor never seen, so on a held-out donor it is undefined — it silently
drops the rows or falls back to a baseline that means something else.

The intent was "every comparison sits within one donor and one brain region."
That intent is achieved by a **transformation**, which is computable on a
held-out donor from that donor's own cells and therefore transfers:

> **Leave-one-out within-stratum centering.** For every predictor and for the
> readout, subtract the mean of the nucleus's own `donor × operator` stratum,
> computed *excluding that nucleus*. Fit and evaluate on the centered
> quantities.

Leave-one-out matters: plain stratum centering lets a nucleus contribute to the
mean subtracted from itself, which for a small stratum is a nucleus partly
predicting itself. LOO removes the self-contribution exactly.

**Disclosed transduction.** Centering a held-out stratum uses that stratum's own
readout values collectively to form the mean. This is deliberate and is part of
the estimand — the question is explicitly about *within-stratum* association,
and the stratum mean is a nuisance parameter being profiled out rather than
predicted. No individual nucleus's readout enters its own centering. This is
stated rather than hidden, because it is the kind of thing that looks like
leakage if discovered later.

**Minimum stratum size: 20 nuclei.** Declared now. Below that, a within-stratum
mean is too noisy for the centering to mean anything, and LOO centering on a
handful of cells manufactures anticorrelation. Strata under 20 nuclei are
dropped, and the number dropped is reported per cohort.

## Everything carried over from v1, unchanged

- **What is tested:** R8's measured per-nucleus program state
  `S_P = (activity, CLR composition over four partners)`, not a trained teacher.
- **Readout:** the activity of the other programs; no program gene predicts
  itself; no reserved gene is touched.
- **Shared-denominator fix:** each activity uses a denominator excluding every
  gene of both the predictor and the readout program, rebuilt per comparison.
- **Controls:** depth (`total_all`, `source_library`, logs); an ambient module
  of eleven lineage-foreign genes; a pan-myeloid generic-identity module;
  mitochondrial; and **the queried gene alone**.
- **Split:** held-out donors, two thirds fitting and one third evaluation,
  assigned by a hash of the source-specific donor identity. Sources never
  pooled.
- **Model:** ridge, regularisation cross-validated within fitting donors only.
- **Statistic:** per evaluation donor, the increment in Spearman from adding
  `S_P` to the controls.
- **Decision rule:** pass requires **both** that the median per-donor increment
  exceeds the 95th percentile of a within-stratum permutation null over 200
  permutations, **and** that the increment is positive in at least two thirds of
  evaluation donors.
- **Failure is a result:** no refitting, no changing controls, no dropping
  donors, no reporting whichever readout looked better.
- **A pass is same-assay program coherence, not independent validation.**
- **Reserved and frozen:** SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB. HVS excluded
  from anything requiring observed LPL, enforced by the availability mask.
- **Training stays off;** scope stays the audited addresses in candidate myeloid
  nuclei.

## Input provenance, added in v2

Every input this analysis reads — the masked artifact, the control extraction,
the decoders — is recorded by SHA-256 in the result receipt. This is a direct
response to finding that R7/R8 hashed their own scripts and outputs but not the
development cache that determined their numbers, which is why those results are
now unverifiable.

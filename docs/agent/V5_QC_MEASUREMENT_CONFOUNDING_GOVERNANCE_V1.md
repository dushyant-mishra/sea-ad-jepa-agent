# V5 QC and measurement-confounding governance V1

Status: **PROSPECTIVE GOVERNANCE CANDIDATE. NOT TRAINING AUTHORITY.**

This document records the QC architecture learned from the T0 rare-tail investigation without changing T0 and without choosing any V5 numeric threshold from observed model performance.

## Core rule

A marginal or cross-cell association between candidate biology and a technical variable is **not by itself rejection authority**. Real biology may change RNA content, complexity, detection, support, or related observation variables.

V5 therefore separates three QC layers.

### Layer A — actual bad-cell / invalid-observation QC

This layer may exclude observations only for independently defined evidence of unusable measurement, such as impossible support, empty or near-empty observations, catastrophic damage/failure, corrupted identity, invalid counts, or other explicitly frozen technical-invalidity criteria.

Global depth/detection cutoffs must not be used merely because rare biology occupies their tails.

### Layer B — technical-association diagnostics

Measure association of candidate biology / `z_bio` with technical variables including depth, detection, source, operator, support family, mask identity, evidence fraction, and lawful observation descriptors.

These results are warnings and shortcut diagnostics. They may trigger deeper investigation but cannot alone reject biology or authorize removal/regression of the associated signal.

### Layer C — causal same-cell measurement qualification

Rejection authority belongs primarily here.

For the same underlying cell, perturb only lawful observation conditions while holding biological identity fixed. Required intervention families remain those already encoded by V5 where applicable, including `MEASUREMENT_DEPTH`, `SUPPORT_FAMILY`, `MASK_IDENTITY`, and `EVIDENCE_FRACTION`.

Qualification must test whether `z_bio` and biology-bearing conclusions remain appropriately stable while `z_obs` is allowed to respond to the observation change.

Numeric thresholds are deliberately **not defined here**. They must be derived or frozen prospectively before candidate-model results are inspected.

## Independent biology requirement

A candidate state/neighborhood used for qualification must also be testable through information that did not define/select it. Where the data contract supports it, use held-out genes/features or another pre-separated biological readout.

Validation must not silently reuse the same feature set both to define the state and to prove that state exists.

## Donor-level recurrence requirement

Disease/biology claims must be evaluated across biological replicates/donors. Large cell counts must not substitute for donor recurrence.

Cell-level diagnostics may support mechanism and measurement analysis, but disease-level qualification must use donor-aware inference or an equivalently explicit biological-replicate design.

## What V5 must not require

V5 must not require `z_bio` to be globally uncorrelated with depth, detection, source, or every technical descriptor across real cells. Such marginal independence can erase legitimate biology.

V5 must not blindly residualize Q_DEPTH/Q_DETECT or analogous variables from biology without a prospectively justified estimand and evidence that the operation is not removing the biological signal of interest.

## Relationship to the existing representation firewall

This governance is consistent with `representation_firewall_v1.py`:

- biological objectives consume `z_bio` only;
- technical/observation state has an explicit `z_obs` route;
- source-adversarial erasure is not a default because source can be confounded with legitimate biology;
- same-cell technical interventions are required.

This document clarifies which QC evidence is warning-level versus rejection-capable.

## T0 as a calibration case, not a threshold source

The frozen T0 rare-tail result remains `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`.

T0 may be used as a qualitative/adversarial calibration case showing why cross-cell QC association and same-cell causal measurement sensitivity must be distinguished. T0 outcomes must **not** be used to tune V5 numeric thresholds so that the old tail passes.

## Pretraining blocker

Before V5 production training can be authorized, the project must have explicit closure for:

1. valid-observation / bad-cell QC;
2. technical-association diagnostics;
3. same-cell causal measurement qualification;
4. independent held-out biology validation where applicable;
5. donor-level recurrence / replicate-aware qualification;
6. shortcut, collapse, proposal-weight/packing, and hardware qualification already required elsewhere;
7. exact full-reader data binding and production-dimension authority.

Until those gates close, `training_authorized = false`.

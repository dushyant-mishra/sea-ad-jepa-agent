# JEPA Biological-Evidence vs Measurement-Depth Convergence Protocol — 2026-10-06

Role: `PROSPECTIVE_SCIENTIFIC_GOVERNANCE__PREFREEZE_ONLY`
Status: `NO_EXECUTION_AUTHORITY__TRAINING_OFF`

## Purpose

Separate two different questions:

1. How much does the inferred representation change when the model receives more biologically relevant molecular evidence?
2. How much does the representation change when the same underlying biological evidence is merely measured more deeply?

These must not be collapsed into one generic uncertainty score.

## A. Biological-evidence convergence

For a fixed cell/state and representation extractor, construct lawful partial-evidence views at prospectively fixed fractions such as:

`20% -> 40% -> 60% -> 80% -> 100%`

The fractions are placeholders until an execution authority freezes exact values and construction rules.

The **perturbation itself must remove biological information support, not merely molecules**. Lawful future operators may restrict, for example:

- measured feature/panel support;
- program/pathway support;
- contextual evidence;
- an additional lawful modality or molecular evidence channel.

Count thinning alone is **not** a biological-evidence perturbation. If the same feature/information universe is retained and only fewer molecules are sampled, that belongs exclusively to the measurement-depth axis below.

For each representation family report:

- distance from the 100%-evidence representation;
- incremental representation change between successive evidence levels;
- donor-level distribution of those quantities;
- whether convergence is monotone in expectation;
- whether rare/local/program/query-specific structure converges differently from global structure.

Interpretation:

Large continued state movement as biologically relevant evidence increases means biological state inference remains underdetermined from the lower-evidence view.

This is an uncertainty/readiness diagnostic, not evidence of pathology or novelty.

## B. Measurement-depth convergence

Hold the biological information universe fixed and vary only count/depth realization, for example:

`25% -> 50% -> 75% -> 100%` of counts

Exact fractions and thinning operator remain `UNSET_REQUIRES_APPROVAL` until prospectively frozen.

The feature/panel/context support must remain unchanged across the depth curve. The operator may reduce molecule/count realization, but it may not remove genes, programs, modalities or other biological evidence channels.

Report:

- representation distance to full-depth realization;
- donor-level uncertainty;
- dependence on source/operator/technology;
- whether technically lower-depth observations converge to the same state;
- whether q-safe and normalization rules remain invariant under thinning.

Interpretation:

Large movement under depth-only thinning is measurement uncertainty, not missing biological-state information.

## C. Operator-separation rule

The two curves must use demonstrably different perturbation operators:

- biological evidence: `FEATURE_OR_CONTEXT_SUPPORT_RESTRICTION`;
- measurement depth: `COUNT_DEPTH_THINNING` with the information universe fixed.

A future execution contract must record the exact operator used for each axis. Reusing count thinning for both axes is a contract violation, not a valid estimate of two uncertainties.

## D. Two-axis classification

A candidate may therefore be:

- biologically stable / measurement stable;
- biologically unstable / measurement stable;
- biologically stable / measurement unstable;
- unstable on both axes.

Do not treat these states as equivalent.

## E. Observation-operator interaction

The measurement-depth curve must be reported within the declared observation regime. Cross-technology differences are a separate transfer axis and must not be smuggled into the depth curve.

## F. Information efficiency

A later authority may define the minimum evidence needed for representation stabilization. This can support panel/spatial design, but it is not a production objective or winner-selection metric in this document.

## G. Required controls

- same biological unit wherever technically possible;
- prospectively frozen subsampling seed/rule;
- no q-dependent normalization leakage;
- no post-hoc choice of evidence fractions from deciding outcomes;
- donor-level uncertainty;
- source/operator diagnostics reported separately;
- representation-family comparison remains neutral;
- explicit declaration of the perturbation operator for each uncertainty axis.

## H. Claim boundary

These curves can qualify statements about robustness of an RNA representation to missing biological evidence and measurement depth.

They do not by themselves establish:

- biological truth;
- technology invariance;
- regulatory validity;
- causal/interventional validity;
- biological novelty.

## Protected boundaries

`TRAINING=OFF`; optimizer updates = 0; EMA updates = 0; TEST sealed; Morabito protected; no representation/target/estimand winner selected; numeric decision margins remain `UNSET_REQUIRES_APPROVAL` unless inherited from independent authority.

# Lineage-Composite Production Synthetic V3 — External Audit Corrections V1

Date: 2026-10-14
Status: **PROSPECTIVE CORRECTIVE AMENDMENT — IMPLEMENTATION OFF**

Controls over the prior cross-lane alignment addendum where they conflict.

Base design remains V2 plus the V3 amendment. V79/V80 frozen history is unchanged. No human outcome was opened to make these corrections.

## 1. R1 relational object correction

The prior cross-lane addendum incorrectly described R1 relation identity as a triplet of repaired molecular-address IDs. That interpretation is rejected for production R1 compatibility.

Historical TD57B defines the scale-free relational object on cells:

`q(i;j,k) = sign(d(i,j) - d(i,k))`

where `i` is the anchor cell and `j,k` are comparison cells. Molecular addresses/features define the measured molecular views and the ruler used to compute cell-cell distance `d`; they are not themselves the relational triplet.

Therefore synthetic R1 rehearsal must satisfy:

- relation identity is the prospective anchor/comparison **cell triplet** `(i,j,k)`;
- the molecular ruler is built from repaired canonical 41,238-address-bound evidence/views;
- required molecular ruler coordinates must obey three-state support semantics;
- unsupported or collision-unresolved ruler components are masked/abstained according to the downstream metric contract, never imputed to manufacture a relation;
- measured zero remains measured evidence;
- relation-label nulls must break cell-relational identity while preserving required donor/source/support structure;
- current PR #347 address-triplet semantics are **not** imported as production scientific authority unless the real-TD lane prospectively defines that as a distinct new estimand and separately qualifies it.

Hostile test: mutate a cell-triplet relation into an address-triplet relation and require failure.

## 2. G11/G12 successor semantics — PR #349 or later

The prior addendum's PR #342-style support abstraction is superseded for cross-lane rehearsal.

Synthetic G11/G12 compatibility must target PR #349-or-explicit-successor semantics:

- bind reader partition per stratum (`reader_fit`, `reader_validation`, `reader_oracle`, or explicit successor vocabulary);
- donor transfer cannot be REQUIRED merely because donors exist; it requires supported fit population plus an actual held-out partition under the frozen contract;
- candidate evidence support must use at least the three states:
  - `SUPPORTED`;
  - `UNSUPPORTED_STRUCTURAL`;
  - `BLOCKED_EVIDENCE_CONTRACT`;
- structural absence must remain distinct from unresolved candidate evidence rights;
- frozen population/evidence/support registry precedes downstream outcomes;
- physically supported strata define maximum lawful claim scope;
- unresolved evidence contracts cannot be promoted to support merely because RNA or another broad modality is present;
- post-outcome scope shrinkage is forbidden.

Synthetic worlds may instantiate known-truth analogues of these states, but may not import real human support outcomes as synthetic biology.

Hostile tests must catch: missing held-out partition mislabeled as donor transfer; `BLOCKED_EVIDENCE_CONTRACT` collapsed into `SUPPORTED`; `UNSUPPORTED_STRUCTURAL` collapsed into unresolved evidence.

## 3. TargetPortfolio C4 prerequisite correction

Full synthetic TargetPortfolio rehearsal is externally blocked until the downstream portfolio implementation enforces the scientific prerequisite that a C4 increment is evaluated **only against independently qualified C6**.

Required synthetic-facing semantics:

- C1/C2/C3 remain independently retainable;
- C6 remains optional and cannot rescue failed C1/C3 constituents;
- C4 may be evaluated only when C6 is independently qualified under its own receipt;
- if C6 is absent, failed, or `NOT_ESTIMABLE`, the C4 increment is `NOT_ESTIMABLE`/ineligible under the downstream contract, not a free-standing PASS;
- C4 failure does not delete independently qualified C1/C2/C3;
- composite PASS never rescues failed constituents.

Hard external dependency:

`BLOCKED_DOWNSTREAM_TARGETPORTFOLIO_C4_REQUIRES_INDEPENDENTLY_QUALIFIED_C6`

The synthetic lane may build fixtures/tests for the intended semantics before downstream repair, but may not claim full same-code-path portfolio qualification until the repaired downstream bytes are hash-bound.

## 4. G6 complete margin-bearing rehearsal

The earlier addendum captured evidence-right and matched-search mechanics but not the full substantive decision path.

Synthetic G6 qualification worlds must include known-truth cases that exercise both:

1. teacher-versus-student diagnostic direction under matched model/search rights; and
2. a prospectively frozen **substantive reference margin** representing separately qualified refit and/or measurement variability where the owning G6 contract requires it.

Rules:

- positive teacher advantage/sign alone cannot qualify a full G6 biological-PASS analogue;
- the synthetic known-truth world must distinguish `teacher advantage detectable but below substantive reference` from `teacher advantage exceeds substantive reference`;
- underpowered cases must remain explicit and may be `NOT_ESTIMABLE`;
- synthetic reference magnitudes qualify the test machinery only and never become human thresholds;
- hidden controller factors and expected molecular state remain forbidden teacher inputs;
- exact human teacher target and evidence-right matrices remain owned by the real lane.

If the real G6 substantive-margin contract changes before implementation, same-code-path rehearsal must bind the explicit successor rather than freezing this prose as human authority.

## 5. G8 exact executor pin and calibration resolution

Canonical synthetic G8 same-code-path rehearsal must pin PR #343 exact executor mechanics or an explicitly named successor.

Current frozen mechanics to exercise prospectively:

- nonnegative integer thinning with deterministic namespace-bound RNG;
- disjoint calibration/deciding/null namespaces;
- canonical 25/50/75% depth references where required by the pinned executor;
- two protected endpoints per depth: displacement upper bound and support-fraction lower bound;
- family alpha `0.01` over `3 depths x 2 endpoints`, yielding `alpha_eff = 0.01/6`;
- exact finite-sample minimum of **599 calibration realizations per required depth/reference unit** for that executor;
- insufficient resolution returns `NOT_ESTIMABLE`; alpha/coverage may not be relaxed to force a result;
- measured zero remains measurement; structural/unresolved support remains abstention semantics.

This pins mechanical rehearsal, not human technical tolerances. Human calibration remains a separate real-data requirement.

Hostile tests must fail if 598 realizations are accepted where 599 are required, or if support-fraction protection is dropped.

## 6. Audit-process correction

The prior R4 self-audit reviewed the V3 amendment but not the later cross-lane addendum as a single combined controlling object. Therefore the prior `CROSSLANE_ALIGNED` label was too strong.

A new hostile audit must review together:

- V2 base design;
- V3 amendment;
- cross-lane alignment addendum;
- this corrective amendment;
- live #349-or-successor G11/G12 semantics;
- current G6/G7/G8/R1/TargetPortfolio interfaces.

Until that audit passes, status is:

`V3_EXTERNAL_AMENDMENTS_APPLIED__COMBINED_REAUDIT_REQUIRED__IMPLEMENTATION_OFF`

## 7. Authority boundary

These corrections do not reopen V79 or V80 and do not grant implementation, realization, fitting, scoring, target selection, representation selection, TD60, Stage4, synthetic training, or real training authority.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

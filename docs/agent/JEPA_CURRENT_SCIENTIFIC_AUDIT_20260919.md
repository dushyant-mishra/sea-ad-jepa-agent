# JEPA V5 — scientific legitimacy audit — 2026-09-19

Audited scientific head: `a51cdbe8bbfac1c77980711cca13df8bc58caa1d`

Purpose: determine whether current engineering preserves the scientific meaning of the JEPA experiment rather than allowing storage order, measurement artifacts, authority labels or convenient statistics to stand in for biological meaning.

## Verdict

`SCIENTIFIC_FOUNDATION_SOUND__FULL104_PROVENANCE_GUARDS_WORKING__DOWNSTREAM_AUTHORITY_AND_SIGNAL_PRESERVATION_STILL_OPEN__TRAINING_OFF`

## Positive findings

1. Support semantics are biologically disciplined: unmeasured != zero; common core != biological truth; native support != private biology; collision unresolved excluded from scalar support.
2. Base objective mass is explicit donor-uniform/cell-uniform-within-donor and separated from proposal/packing.
3. Visibility/QC channels are excluded from the primary molecular value route.
4. Hidden-gene scalar reconstruction is forbidden as the JEPA objective; target intent is query-local cellular state.
5. Shared target-address provider avoids a free trainable embedding per address.
6. Physical/runtime anti-spillover and independent rederivation are real; they caught the invalid pass1 before downstream promotion.
7. H3/G5 terminal execution is mechanically locked.
8. Exact-head CI is green with no skipped critical tests.

## Findings requiring action

### AUDIT-1 HIGH — historical pass1 keyed cells by storage order

Confirmed in `analysis/v5_full104_census_20260917/full104_readonly_census_pass1.py`. Per-cell arrays were filled with sequential `pos`, not `selection_row`. Old pass1 is invalid for current role. Build a new physical producer and keep independent verifier unchanged.

### AUDIT-2 MEDIUM — historical masking-feasibility census confused nonzero with measured support

Old pass2 used cell strict-core nonzero count when describing ability to supply measured maskees. Measured zero is still measured evidence. Current target-evidence-budget code repairs this by using strict measured non-target addresses independent of expression value. Quarantine the old interpretation.

### AUDIT-3 HIGH — final closure is stale relative to the hardened masking chain

`current_authority_closure_v2.py` imports older masking authority generations. It does not yet close over current Design V2 / Parameters V3 / Precision V4 / RunContract V4 / Execution V4 / TargetPanel V3 / RNG V2 / physical-pass1 provenance. Rebuild after final scientific schemas stabilize.

### AUDIT-4 HIGH — caller-declared execution PASS still exists in several downstream authorities

Critical-test, remaining-RNA, measurement-robustness, geometry-memorization and runtime-source schemas contain valid-looking result hashes/statuses that are not always physically rederived by the validator. Final closure must derive or independently bind every executable PASS/hash/status from real bytes/logs.

### AUDIT-5 HIGH — biological-state labels are intent, not evidence

`BIOLOGICAL_CELLULAR_LATENT_STATE_V1` and similar enums are semantic constraints. They do not establish that the learned representation is biological. Empirical state-signal preservation, remaining-RNA necessity, measurement robustness and capacity-matched anti-shortcut evidence remain required.

### AUDIT-6 HIGH — query-scalar leakage through precomputed global context is unproven

The target contract says the query scalar is withheld before contextual mixing, but global V0/V1 context is precomputed. There is no current production consumer proving the query scalar cannot influence a route claimed to withhold it. Add a metamorphic query-scalar intervention/invariance test before F13/F15 closure.

### AUDIT-7 MEDIUM — masking robustness estimand differs from base training estimand

Base training is donor-uniform. Masking Precision V4 uses equal aggregation over fixed HVS/NPH52/SEA_AD plus source guardrails. This can be defensible as a robustness/safety constraint, but the distinction must be explicit so source-equal qualification is not silently promoted to the training population estimand.

### AUDIT-8 MEDIUM — target estimability thresholds need rationale/sensitivity

The 30 cells/donor, 20 train donors, 5 validation donors rules are statistical design choices, not biology. Keep them fail-closed, but document prospective rationale and nearby-threshold sensitivity before final target-panel authority.

### AUDIT-9 MEDIUM — burden ladder does not prove biological signal preservation

5/10/15/20/30/50% is a frozen search grid. Lowest qualifying burden minimizes intervention but does not itself prove state information remains learnable. G4 is mandatory.

### AUDIT-10 MEDIUM — governance docs were stale

`START_HERE`, latest pointer, active plan and prior command anchor lagged the actual scientific head. This handoff branch repairs startup routing and records scientific/docs heads separately.

## Open scientific blockers carried forward

- G5 equivalence margin basis — HIGH
- H3 equivalence power/precision panel sizing — HIGH
- H4 all-rung failure interpretation — HIGH
- G2 targeting-complexity materiality — MEDIUM/HIGH
- G3 capacity-matched/deep shortcut attacker — HIGH
- G4 state-signal preservation — HIGH
- F13 representation consumer binding — HIGH
- F14 production dimension/rank/subspace — HIGH
- F15 current teacher/student/runtime — HIGH
- final derive-vs-declare authority repair — HIGH

## Corrected donor-sample interpretation

Independent donor units = 104. Historical Kish ESS≈42 is a descriptive statistic for imbalance in cell-count weights, not donor-level effective sample size under the donor-uniform estimand.

## Current rule

Before any artifact is treated as scientific evidence, ask:

> What biological/scientific entity does each array element represent, and what immutable physical identity proves that mapping?

For cells: `selection_row`.
For donors: canonical donor ID, not first-seen order.
For addresses: canonical 41,238-address registry identity, not inherited column position.
For sources/operators: authenticated physical metadata.
For execution PASS: actual bound result/log bytes, not a declared string.

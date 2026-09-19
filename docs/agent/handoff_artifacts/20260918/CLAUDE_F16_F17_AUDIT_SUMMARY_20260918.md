# Claude F16/F17 audit — consolidated takeover summary

This file records the user-supplied independent Claude audit state. It is review evidence, not scientific authority.

## First audit verdict

`STOP_F16_F17_MECHANICALLY_CLOSED__CEILING_BINDING_AND_SCIENTIFIC_RULE_JUSTIFICATION_OPEN`

Claude independently audited `144873cec377e2cd098ce66220377f10723f413a` and reported 25/25 adversarial attacks behaving correctly. It considered the original F16 float-arbitrariness defect mechanically closed and F17 realized-control-width leakage closed. It independently reproduced 280 passed / 0 skipped and found the spillover scan clean.

Residual findings from that pass:
- G1: null_noise_tolerance_ceiling was not cross-bound to PrecisionAuthorityV4.
- G2: one-total-event targeting-complexity equivalence is exact but scientifically under-justified and scale-dependent.
- G3: ridge and nonlinear shortcut probes use 32 features while production JEPA sees a much richer visible context.
- G4: no biological-signal-preservation / learnability criterion in the masking ladder.
- G5: null-equivalence margin is supplied as a CLI rational without recorded scientific derivation/rationale.
- G6: minimum-intervention selection tends to select nearest the failure boundary.
- G7/G8: strict-common-core and fixed-three-source qualification do not establish broader transfer.

## Deeper audit continuation

Revised verdict:

`STOP_F16_F17_MECHANICALLY_CLOSED__PRIOR_RUNG_BINDING_AND_EQUIVALENCE_POWER_OPEN`

Additional findings:
- H1: prior rung receipts were caller-constructible and could advance the burden ladder without a proven prior execution. Repair required matching ExecutionAuthorityV4 / run contract / failed status.
- H2: rung receipt digest validation accepted any 64-character string rather than lowercase hex SHA-256.
- H3: target-panel sizing currently establishes detection of an intentionally easy planted shortcut with lower bound > 0. That is superiority power, not the equivalence power needed for the terminal residual-within-margin claim.
- H4: no pre-registered feasibility/diagnostic framework distinguishes all-rung failure caused by masking ineffectiveness, a bad margin, irreducible measurement structure, or inadequate equivalence precision.

Claude corrected one of its own earlier suspicions: replay_exact is earned by fail-fast reconstruction/replay rather than a free hard-coded assertion.

## Strategic critique to preserve, but independently re-derive

Claude argued that the project may have an inverted apparatus-to-substance ratio: many authority modules but unresolved executable production representation/dimension/model mechanics. It specifically asked for independent verification of whether VALUE_ONLY_256 is actually consumed in src, whether D_shared/D_private/D_obs exists as an executable pipeline, and whether donor-level confirmation power rather than masking is the true downstream bottleneck.

Do not copy its Kish ESS / rho numbers as authority. Recompute them from current representation/data before prioritization.

## Project-wide rule distilled from F1 -> G1 -> H1

`NO_RECEIPT_FIELD_ACCEPTED_FROM_CALLER_IF_RECOMPUTABLE_FROM_BOUND_INPUTS`

Apply this globally across every current authority and receipt.

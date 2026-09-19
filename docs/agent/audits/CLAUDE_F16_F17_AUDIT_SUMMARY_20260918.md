# Claude F16/F17 and post-repair audit summary — supporting evidence only

Date: 2026-09-18

Role: `SUPPORTING_EXTERNAL_AUDIT_ONLY__NOT_SCIENTIFIC_AUTHORITY`

## Verified strengths reported by the reviewer

- F16 exact target×fold complexity lattice behaved correctly under 25 adversarial attacks at `144873ce...`.
- F17 heterogeneity floor was invariant to admissible realized negative-control interval width and used the frozen margin.
- source-specific harm guardrails and raw evidence digest binding were reported closed.
- DECISION_RULE_ID drift was closed through canonical imports.
- exact-head masking CI was independently reproduced at 280 passed / 0 skipped on the audited pre-PR26 head.
- no Stage81/T1/C2, X_common6000, EMA 0.996, placeholder SHA or historical PASS ingress was found in the audited dependency cone.
- replay, donor coverage, mask reconstruction and one-rung ordering logic were reported strong.

## Reviewer findings subsequently repaired on PR #26

- G1: decision tolerance ceiling not cross-bound to PrecisionAuthorityV4.
- H1: higher burden could be authorized from caller-constructed prior rung receipts.
- H2: rung receipt policy roots accepted arbitrary 64-character non-hex strings.

PR #26 at `72338541...` repairs those items and passes exact-head CI. Independent post-repair re-review remains required.

## Open scientific findings

- G2: one-total-event complexity-equivalence materiality does not scale with panel grid.
- G3: 32-feature attacker is much smaller than the production model's visible context.
- G4: no explicit biological signal-preservation criterion.
- G5: equivalence margin needs prospective scientific rationale/derivation; PR #24 is a candidate freezing mechanism, not automatically the rationale.
- H3: panel sizing currently detects an easy planted superiority effect rather than establishing precision/power for the terminal equivalence question.
- H4: no pre-registered interpretation separating possible causes of complete ladder failure.
- transfer outside strict common core / fixed observed sources remains a separate scope issue.

## Important reviewer self-correction

The reviewer reported that three probes were vacuous on first attempt and produced plausible but meaningless output before being caught. Therefore every finding above must be independently reproduced before promotion to project authority. The audit is valuable adversarial evidence, not a substitute for exact-current code/data verification.

## Structural lesson

Recurring F1 -> G1 -> H1 pattern: values named by a receipt were accepted from callers instead of being derived from bound inputs.

Adopt project-wide:

`NO_CALLER_SUPPLIED_DERIVABLE_RECEIPT_FIELDS_V1`

If a field can be recomputed from bound inputs, recompute it, compare it and fail closed on disagreement.

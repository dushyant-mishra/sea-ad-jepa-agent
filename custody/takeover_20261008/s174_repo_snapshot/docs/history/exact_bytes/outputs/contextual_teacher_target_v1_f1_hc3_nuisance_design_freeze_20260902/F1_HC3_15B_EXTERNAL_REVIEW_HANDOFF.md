# F1 HC3 Command 15B — external-review handoff

Terminal: `PASS_F1_HC3_NUISANCE_DESIGN_FREEZE_AWAITING_EXTERNAL_REVIEW`.

- Authenticated 15A4 manifest and every manifested file reproduced.
- The selection contract was frozen and SHA-bound before frontier application.
- The complete 30-row admissible set has one universal component-wise maximum: `[5, 0, 4]`.
- The selected design has SHA-256 `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`, rank 16, df 88, and zero leave-one-donor rank losses across all 104 donors.
- SVD production leverage and independent pivoted-QR geometry agree; HC3 is estimable without leverage clamping.
- Deterministic synthetic arithmetic and the known NPH52 donor-indispensability attack behave as required.
- Independent selection, reconstruction, exact float64 design bytes, QR geometry, LOO ranks, and synthetic HC3 checks PASS.
- Six targeted review lenses PASS; dissent, if any, is preserved in the review artifact.
- No expression, outcome, model/checkpoint, forward, training, optimizer, or EMA access occurred. No F1 evaluation ran and no production F1 engine was patched.

This freezes only the current F1-104 nuisance design. Current ranks, leverage values, and donor identities must not transfer to a larger cohort; the authenticated 15A4 reusable procedure must be rerun there.

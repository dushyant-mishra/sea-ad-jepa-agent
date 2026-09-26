# V34 final-issuer provenance remediation — non-authorizing

Date: 2026-09-26. Parent: V30 PR #156 at a5af773adfd66d0e727113610f5e62d7353b13b8. Scope: synthetic source/CPU only. Training remains OFF; no B1 scientific approval, no current V5 root closure, no protected outcome, no real training.

## Demonstrated predecessor failure

PR #156's real-issuer test constructed a self-consistent SHA envelope with no representation, support, masking, teacher, geometry, or other actual scientific parents. The original final issuer accepted it: checking a valid SHA-256 digest proves only internal consistency, not execution of the 32-role graph validator.

## Versioned V34 fail-closed boundary

`issue_training_authority_v1` now requires the exact arguments of the real `validate_current_v5_authority_closure_v2` under `closure_inputs`, freshly invokes that validator **inside issuance**, and compares its entire canonical closure output byte-for-byte at the object-value level to the caller's supplied closure before returning an authority. It also requires the critical-test and runtime-source objects supplied to the issuer to be the *identical objects* supplied to the live graph validator; digest agreement between separately constructed objects is insufficient. A legacy caller lacking live inputs is rejected. Existing preexecution binding and target receipt checks remain in place and are executed first.

The production graph validator already checks current typed upstream authorities, exact parent-role links, source/runtime binding claims, and explicit executed-pass predicates for masking, remaining-RNA, measurement and geometry memorization. V34 does not substitute test doubles for that production validator.

## Seven isolated regression assertions

1. V30's exact fabricated envelope now fails when no live graph is supplied.
2. Corrupted receipt digest remains rejected.
3. Corrupted closure digest remains rejected.
4. Incomplete live role set is rejected.
5. Runtime object substitution is rejected even when digests match.
6. Injected failure from a test-only validator spy is propagated, demonstrating call-site invocation.
7. A test-only validator spy returning a different complete closure cannot be accepted.

CI requires exactly seven tests, zero failures/errors/skips, the explicit fabricated-envelope rejection marker, and `set -o pipefail` so a broken pytest behind `tee` does not report success. CI is *mechanics only*. Do not claim that a mocked validator in two negative tests establishes source provenance.

## Residual boundaries / independent review

- No actual graph can currently pass because the project records zero fully closed current V5 upstream authority roots. This branch does not test a real positive B1/B2 issuance. The exact authorized positive control must eventually use **all authentic typed inputs**, not a fake validator.
- A live typed `validate()` graph is not automatically proof that referenced SHA roots bind to original external artifact bytes. Each producing source/runtime authority must independently verify actual file bytes, immutable source roots and executed evidence, with a separate full-chain provenance audit before ever enabling B2.
- The optional `closure_inputs=None` parameter exists to reject old callers with a clear runtime error rather than a signature-time error; it never bypasses validation.
- The V30 diagnostic expectation that a fabricated authority gets issued is intentionally inverted here. Do not run that superseded expectation as a production acceptance gate.
- Do not silently merge this stacked implementation branch into `main`, the independent V32 handoff, or other parallel lanes without reconciliation and a fresh live-head review.

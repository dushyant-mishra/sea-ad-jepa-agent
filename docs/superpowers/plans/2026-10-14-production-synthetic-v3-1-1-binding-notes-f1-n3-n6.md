# Production Synthetic V3.1.1 Implementation Plan — Binding Notes F1 / N3–N6

Date: 2026-10-14
Status: **PLAN-BINDING ADDENDUM — EXECUTION SEMANTICS ONLY**

This addendum binds the accepted implementation plan:
`docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md`

It does not amend V3.1/V3.1.1 scientific design. It records one required plan fix (F1) and four execution-binding notes (N3–N6) from the focused review frozen on the PR #344 audit branch at commit `2507b967`.

Precedence: where this addendum conflicts with the implementation plan, this addendum controls for F1 and N3–N6 only. The V3.1/V3.1.1 controlling specs remain higher authority.

Authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## F1 — full SHA-256 identities are mandatory before Task 12

Task 12 finalizer tests and the immutable receipt must bind the full 64-character SHA-256 values of both controlling specs, in addition to their Git blob identities:

- V3.1 controlling amendment
  - Git blob SHA: `48e71346c74378729e39a4de6b80699d3cb43d15`
  - SHA-256: `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c`

- V3.1.1 erratum
  - Git blob SHA: `977faa75e37c31610122e7ad45d2fc26dac536a3`
  - SHA-256: `ab1ae1bb67765cc025f580205d7c082ee4af470dd39ef23c4f000414e8e9363f`

Shortened display forms are not acceptable to Task 12 tests or receipts.

## N3 — withheld family must not have a unique public code path

The plan's statement that generic mechanism code may be public is valid only when the same code path is exercised by development/fixture realizations independently of the withheld family.

Binding requirements:
- no function/module/branch exists solely for the withheld family;
- if a mechanism implementation would be uniquely exercised only by the withheld family, that implementation stays controller-side/off-repo until reveal rather than being committed publicly;
- the withheld family remains a secret parameterization/composition over code paths already exercised by non-withheld fixture/development worlds, unless the unique mechanism implementation itself is also withheld off-repo;
- no implementer or reviewer subagent receives withheld-only code, parameters, applicability, scoring rules, nonce or preimage;
- Task 2 hostile tests include a dummy unique-code-path leak case and require custody failure when a committed path is uniquely attributable to the withheld family;
- before commitment, the controller's private repository-tree scan verifies both plaintext/preimage absence and absence of a uniquely identifying withheld-only public code path.

The controller, not a subagent, authors the real withheld family.

## N4 — thinning must thin normalization library consistently

Synthetic measurement-depth thinning must alter the stored measured-scalar counts **and the normalization-library quantity derived from those counts under the declared observer**.

Binding requirements for Task 5:
- thinning operates only on `MEASURED_SCALAR` entries;
- randomness is keyed to cell/scientific identity, never storage order;
- `STRUCTURALLY_UNMEASURED` and `MEASURED_COLLISION_UNRESOLVED` states pass through unchanged;
- thinned-to-zero remains `MEASURED_SCALAR`;
- the corresponding per-cell normalization-library size is recomputed/thinned under the same measurement realization so counts and library cannot become inconsistent;
- the thinning API returns/binds both thinned counts and the resulting library quantity or enough immutable information for the reader to derive exactly the same library;
- hostile tests reject a fixture where counts are thinned but the original full-depth library size remains visible.

This is measurement-depth behavior only and cannot be relabeled biological-evidence restriction.

## N5 — PR #343 thinning code is not reusable

No task may import, wrap, copy or treat the PR #343 thinning function as an implementation authority for production synthetic thinning.

Reason for the prohibition:
- its frozen arithmetic is useful historical mechanics evidence;
- its randomness follows storage/matrix position rather than canonical cell identity;
- it cannot distinguish unmeasured entries from measured-scalar entries in the required four-state support model;
- it does not thin/update the normalization library.

Task 5 must implement a prospective production-synthetic thinning operator from the controlling design contract and N4, with independent tests. #343 remains an external mechanics/reference dependency only; no code reuse claim is permitted.

## N6 — PR #353 is not an adversarial R1-control source

PR #353 remains `SEMANTICS_COMPATIBLE_FIXTURE_ONLY`, but it does not supply the adversarial negative worlds required for Task 8.

Task 8 therefore owns a synthetic hostile R1 control family that includes at minimum:
- a **library-size-only negative control** in which library/depth differences are present but the expected-state R1 truth contains no corresponding biological relation signal;
- scoring that treats method success driven by the library-only cue as shortcut failure;
- fit-side custody that does not expose the control role;
- applicability and hard-gate status frozen before downstream exposure.

This control is implemented prospectively in `scripts/production_synthetic/controls_v1.py`; it is not delegated to or inherited from #353.

## Execution implications

- Tasks 1–3 remain authorized for subagent-driven implementation with a fresh implementer and fresh reviewer per task.
- Task 4 may begin only after Tasks 1–3 each clear their per-task reviews, per the accepted amended-plan verdict.
- N3 binds Task 2 and any later task touching withheld-family realization/custody.
- N4 and N5 bind Task 5.
- N6 binds Task 8.
- F1 binds Task 12 and must be tested before any finalizer invocation.
- STOP_A, STOP_B and STOP_C remain unchanged.
- No production realization, sealed qualification, finalization, human gate execution, target/representation selection, TD60, Stage4 or training is authorized by this addendum.

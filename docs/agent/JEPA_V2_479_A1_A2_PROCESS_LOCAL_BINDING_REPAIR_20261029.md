# JEPA V2 #479 A1/A2 fixture consumer repair — 2026-10-29

## Classification

**Incremental synthetic/fixture mechanics only; source rights unauthenticated.**
Source base: PR #479 `ae762d7096a94ac663a0788f6f577ba404e37536`.
A3 prerequisite: PR #495 `d2e430d739e1ef16806120752b867c6aeeba4972`.
Independent original reviewer: Macha PR #481 `957fa4a558ce2bd219b5c2dec6dad8f65dca81ab`.
Original reviewer file blob: `3dda6c2cc9be19d5daececfb07967e94067519f6`.
The reviewer file is copied without modifications for A1–A3 test execution. The inherited #474 A4 RED is explicitly excluded from this **repair-specific** workflow, not erased or accepted.

## Exact proposed fixture behavior

- **A1:** The consumer checks for each cell that `base_rights_normalization_depth` equals the exact sum of `MEASURED_SCALAR` counts in addresses whose producer-bound rights are in frozen base. Non-base scalar counts may be larger than the depth in teacher views; no physical `count <= depth` constraint is added.
- **A2:** Before publishing a view, the fixture producer stores a process-local binding of the published observable digest to the query identity, selected role, full address-to-right roster, base-rights set, and selected view-rights set. This binding contains **no per-cell count values, whole-library totals, teacher digest, private input digest or source artifacts**. The consumer requires that binding; a self-re-signed view, relabeled query, altered right, missing address or extra visible right is refused. Legitimate JSON serialization/roundtripping remains accepted **within the issuing process**.
- **A3:** Carried unchanged from #495: exact type-identity checks in the V2 receipt snapshot preclude payload metaclass `__eq__`.
- **A4:** Inherited upstream #474 `total < 1` / zero-base refusal noninterference remains RED. No claimed repair.

The frozen base rights are supplied by the original upstream fixture call and **are not authenticated human evidence rights**. The process-local binding can be modified by hostile same-process Python and does not survive process restart. It cannot qualify an external independent issuer. A hash is only an observable-content identity; it is not a signature or source attestation.

## Explicit scientific stop

This does **not** accept the proposed `D1 = VISIBLE_BASE_MAPPED_SUM_V1` as a production default; the equality is only the existing conservation-qualified PR #479 fixture law. D2 source residual remains OFF, and the physical total remains private. Existing CaseBundle/G7 V1 physical `library_size` content laws are untouched. A V2/G7 versioned producer/consumer issuer still requires the deciding-lane contract decision and independent review.

Reader-fit mapped-feature/alias closure, QC/selection rights, true physical units, specimens and independent donors remain unresolved. G7 R1/R1D/R2 and production-synthetic T2-D remain RED. Real data, real training, selected target and Stage4 are not authorized.

## Test evidence and required review

- New arithmetic tests deliberately inject a bound but *malformed* receipt, testing the consumer's exact equality rather than obtaining a pass by refusing unknown hashes.
- New rights tests inject non-base count exposure while retaining the original frozen base policy. Orphan JSON and forgery must fail closed.
- The original Macha #481 A1–A3 hostile tests execute byte-identically through the CI `-k red_v2_consumer`; the remaining A4 test is **not included**. Existing 240-world characterizations and original #474 producer regression tests remain available unchanged.
- Matrix: Ubuntu and Windows, pinned Python 3.11, pytest 9.1.1 and NumPy 1.26.4.
- Author-CI GREEN is not independent acceptance. This branch is awaiting hosted test results and outside review.

**Standing scientific authorization:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

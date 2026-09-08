# Teacher/Student V3 external-review terminal bridge V1

Status: `PROSPECTIVE_GOVERNANCE_BRIDGE__AWAITING_EXTERNAL_REVIEW__EXECUTION_UNAUTHORIZED`
Date: 2026-09-08

## Problem

The frozen V3 self-contained review instructions request the active-source PASS terminal:

`PASS_TEACHER_STUDENT_UNIFIED_V3_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`

The already-frozen `HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1` validator accepts an independent-review terminal only if it begins:

`PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW`

Changing the overlay validator would change one of the 20 files in the reviewed V3 source manifest and therefore create a new source root. A hand-written alias is forbidden.

## Resolution

Keep the reviewed V3 source bytes unchanged. Introduce a separate fail-closed governance bridge.

The bridge may emit:

`PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW__V3_SELF_CONTAINED_EXTERNAL_REVIEW_BOUND`

only if all of the following are true:

1. the supplied review package ZIP SHA-256 is exactly `8bcec10f60988df9bb34c23f89c8e0918222776be70dca5bce98156f1c223d98`;
2. the package manifest root is exactly `0720214288dfe0a4446b418bbd8bc6f21b34c54385cec57195371b687e4a1a71`;
3. package metadata binds package commit `76bf7912cc621756fdbbd82218025d8e4c00a057`;
4. package metadata and source authority bind active source commit `8f9c34f18ac7cf43572299901e5e4f5d65cecb24` and source root `cd7faf6dd48f58387597b05f2e143ac629e1b74418d9720c4acdc9fcf4dfb584`;
5. the package manifest rehashes every member exactly and contains no execution-authority file;
6. the external review artifact contains the exact active V3 PASS terminal exactly once and contains no active V3 STOP terminal;
7. the external review separately reports either the relational PASS terminal or one relational STOP terminal;
8. the bridge artifact records the SHA-256 of the exact external-review bytes;
9. `execution_authorized` remains false.

The relational adjunct result is recorded separately. A relational STOP does not convert an otherwise clean active V3 review into an active-source failure, matching the frozen review instructions.

## Overlay use

If and only if the bridge emits PASS, a later execution-binding overlay may set:

- `independent_review.terminal` to the bridge PASS terminal;
- `independent_review.artifact_sha256` to the SHA-256 of the canonical bridge JSON;
- `independent_review.reviewed_commit` to `8f9c34f18ac7cf43572299901e5e4f5d65cecb24`.

The bridge does not create the overlay, materialize u0, authorize u1, authorize u0->u40, or authorize continuation.

## Current state

No external-review result is supplied by this authority freeze. Therefore no PASS bridge artifact exists yet and execution remains unauthorized.

# Claude independent review instructions — Teacher/Student V4 self-contained candidate

Review only the supplied V4 package bytes plus the external ZIP-SHA sidecar. Do not infer authority from older V3 packages, historical continuation checkpoints, or superseded relational V1 files.

The candidate is intentionally **training unauthorized**. A clean review does not authorize successor-u0 materialization or u1.

## Package identity — no self-reference

The package uses two complementary identities:

1. `PACKAGE_ROOT_SHA256.txt` is exactly `SHA256(PACKAGE_MANIFEST.csv)`. Every payload member except `PACKAGE_MANIFEST.csv` and `PACKAGE_ROOT_SHA256.txt` is listed in that manifest.
2. `TEACHER_STUDENT_UNIFIED_V4_SELF_CONTAINED_REVIEW_PACKAGE_SHA256.txt` is an **external transfer sidecar** containing the SHA-256 of the deterministic ZIP. It cannot be embedded as the ZIP's own required hash without circular self-reference.

`REVIEW_METADATA.json` therefore binds the package-build commit, integrated-source commit/root, active-test manifest, and upstream authorities. It deliberately does not claim to contain its enclosing ZIP SHA or package root.

## Required identity checks

1. Hash the supplied ZIP and require equality with the external ZIP-SHA sidecar.
2. Extract the ZIP; rehash every row of `PACKAGE_MANIFEST.csv` and require exact byte/size agreement.
3. Rehash `PACKAGE_MANIFEST.csv` and require equality with `PACKAGE_ROOT_SHA256.txt`.
4. Verify `REVIEW_METADATA.json` is schema `TEACHER_STUDENT_UNIFIED_V4_REVIEW_PACKAGE_SELF_CONTAINED_V1`, has `execution_authorized=false`, and binds:
   - the supplied package-build commit;
   - the integrated-source commit frozen in `TEACHER_STUDENT_INTEGRATION_FREEZE_CANDIDATE_V4.json`;
   - V4 source root `8aae50696124a259bbd89d4a788d0e1cb0f94ee8b7ed13520a2db73138ae6460`;
   - the exact SHA-256 of `TEACHER_STUDENT_ACTIVE_TEST_MANIFEST_V4.csv`.
5. Rehash all rows of `docs/agent/TEACHER_STUDENT_INTEGRATED_SOURCE_MANIFEST_V4.csv`; require `SHA256(manifest)` and `TEACHER_STUDENT_INTEGRATED_SOURCE_ROOT_V4.txt` both equal `8aae50696124a259bbd89d4a788d0e1cb0f94ee8b7ed13520a2db73138ae6460`.
6. Confirm the package contains neither `HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json` nor `HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json`.
7. Confirm the superseded `prospective_relational_teacher_student.py`, its V1 relational test, and its V1 relational design are not review authority and are absent from the V4 package.

## Active mechanics review

Run the exact seven paths in `docs/agent/TEACHER_STUDENT_ACTIVE_TEST_SELECTION_V4.txt`. Independently attack at least:

- C2 mandatory gradient gate: missing/zero/nonfinite gradients;
- all frozen F1-B successor attack findings;
- population firewall and healthy-teacher training contract;
- checkpoint/resume and exact runtime source authority;
- exact V4 review terminal plus package/source-root binding;
- exact decay-only movement adjudication;
- relational target invariance to positive per-cell rescaling;
- reversed relation increases relational loss and student ties are penalized;
- teacher zero-norm/collapse fails closed;
- frozen triplets cannot cross groups, duplicate, or reverse comparator orientation;
- group/stratum IDs are discrete integers;
- evidence levels, seeds, and group-geometry authority values cannot be silently float/string coerced;
- fine-matched null stays within stratum and has no fixed points;
- collapse calibration is external and **every group is adjudicated separately with no pooled rescue**;
- current `production_update` neither imports nor calls the relational target;
- no nearest-third/nearest-half selector is embedded in the target module;
- full-reader group size/locality/threshold/loss-weight values are not invented by the candidate.

## Scientific consistency check

Confirm the candidate target matches `TEACHER_STUDENT_RELATIONAL_TARGET_AUTHORITY_V2.json`:

- TD57B supports scale-free anchored ordering and does not require absolute distance equality;
- TD57C nearest-third locality remains failed;
- TD59 nearest-half is only pilot mesoscale support and cannot become production k/fraction;
- TD60 is still prospective and requires a lawful successor u40;
- V4's relational module accepts externally frozen global/mesoscale triplets but does not select locality itself;
- the relational target is not active in current u0→u40 `production_update`.

## Required terminal

Return exactly one active-source terminal:

`PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED`

or

`STOP_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__<PRECISE_REASON>`

A PASS means only that the supplied V4 package is internally coherent and review-clean. It does **not** authorize successor-u0 materialization, u1, u0→u40, TD60 execution, relational training, protected-population access, or full-reader training.

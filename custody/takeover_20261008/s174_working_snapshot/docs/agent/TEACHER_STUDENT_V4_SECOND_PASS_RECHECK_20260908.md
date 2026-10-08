# Teacher/Student V4 — second-pass independent internal recheck — 2026-09-08

Status: PASS_TEACHER_STUDENT_UNIFIED_V4_INTERNAL_RECHECK__EXTERNAL_REVIEW_STILL_REQUIRED__TRAINING_UNAUTHORIZED

Decision-bearing package identity remains unchanged:
- integrated source commit: 24752e33f5f7a9ff0e8caef733223b8c4c6de5b7
- integrated source root: 8aae50696124a259bbd89d4a788d0e1cb0f94ee8b7ed13520a2db73138ae6460
- package-build commit: 8d92f15f973de06415650f72e63788d255ac833d
- review package root: db162fdf5988d2f7b833ad0a24b1edba2fb3fcf7a6bd0c43cfeda3888329d58a
- review ZIP SHA-256: 17c16eb02103ea8b2df8949d407a82aa8e65302b855f6f06fed91aba0d671d66
- GitHub CI run: 34248656470
- downloaded GitHub Actions outer artifact SHA-256: 33cc302401e28e52ab80a304cd1e06e65d7ee88f24fd98a28b4abfe02cead864

Second-pass package attack:
- supplied ZIP SHA equals external sidecar: PASS
- ZIP entries: 99; duplicate paths: 0
- absolute/traversal paths: 0
- symlink members: 0
- PACKAGE_MANIFEST rows: 97; every byte count and SHA-256 rechecked: PASS
- actual file set equals exactly manifest payload + manifest/root: PASS
- SHA256(PACKAGE_MANIFEST.csv) equals PACKAGE_ROOT_SHA256.txt: PASS
- V4 source-manifest rows: 21; every source byte/size rechecked: PASS
- source manifest SHA and recorded source root both equal 8aae5069...: PASS
- active-test manifest rows: 7; byte/size recheck: PASS
- exact active-test selection equals exact manifest path set: PASS
- REVIEW_METADATA source/test/root/execution bindings: PASS
- execution/continuation authority files absent: PASS
- superseded V1 relational module/test/design absent: PASS

Second-pass executable replay:
- V4 integration freeze audit: PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4
- exact active selection: 98/98 PASS
- unrestricted pytest over the self-contained package: 98/98 PASS
- Python compile: 71/71 PASS
- fresh deterministic rebuild from extracted reviewed bytes: byte-identical ZIP: PASS
- rebuilt ZIP sidecar: byte-identical: PASS
- rebuilt packaging-validation JSON: byte-identical: PASS

Additional adversarial relational checks:
- positive per-cell scaling invariance: 100 randomized seeds PASS
- student gradients finite / teacher detached across 100 randomized seeds: PASS
- fine-matched null: 550 varied size/seed cases, within-stratum and no fixed point: PASS
- triplet enumeration count formula across group sizes 3..9: PASS
- grouped batch contract across multiple externally supplied geometries: PASS
- per-group collapse gate/no pooled rescue across 20 randomized cases: PASS
- current production runtime contains no relational-target import/call: PASS
- exact V4 review terminal is required; legacy V3 terminal is rejected: PASS

Git ancestry/scope:
- legacy V3 package commit 76bf7912... to V4 source commit changes only V4 source authority/overlay surfaces plus the new non-active relational target and V4 source manifest/root; canonical runtime/model/optimizer/EMA/masking/checkpoint mechanics remain byte-unchanged.
- package-build commit 8d92f15f... is a direct successor of frozen source commit 24752e33....
- post-package branch commits before this report changed reviewer status/identity documentation only; no source/test/workflow/package-builder bytes changed.

Immutable input recheck:
- discovery part001 SHA-256 b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e: PASS
- discovery part002 SHA-256 5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875: PASS
- concatenated discovery archive SHA-256 63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7: PASS
- calibration bundle SHA-256 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444: PASS
- historical t1 u0200 archive SHA-256 0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c: PASS

Governance boundary:
- this is an internal recheck, not the independent external review.
- training remains unauthorized.
- successor-u0 materialization remains unauthorized.
- u0->u40 execution remains unauthorized.
- TD60 remains waiting for a lawful frozen successor u40.
- protected-population access remains unauthorized.

Next legal gate remains the exact external terminal:
PASS_TEACHER_STUDENT_UNIFIED_V4_INDEPENDENT_REVIEW__TRAINING_STILL_UNAUTHORIZED

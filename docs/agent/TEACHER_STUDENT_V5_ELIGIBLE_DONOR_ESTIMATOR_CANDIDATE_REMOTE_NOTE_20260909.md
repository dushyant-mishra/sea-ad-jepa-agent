# Teacher/Student V5 eligible-donor + estimator authority candidate — remote note

Date: 2026-09-09
Branch: `planning/teacher-student-v5-dataset-schedule-20260909`

This note records the chat-local candidate package generated after the support-family geometry push at `ce151fa58d42b11f768678556b4baa7a2a064ae7`.

## Candidate package

- Package: `TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_20260909.zip`
- ZIP SHA-256: `206e11c606fc8631c1e527549655fb0f21087cb31e54320ce026d5e2f04fa3c7`
- ZIP bytes: `48170`
- Payload files: `22`
- Payload bytes: `143200`
- Manifest: `docs/agent/TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_MANIFEST.csv`
- Candidate root / manifest SHA-256: `fa5728fb855e3aa90893abd23cad979d730954f89bb27082dc025dc31a597945`
- ZIP integrity: `ZipFile.testzip() == None`

## Local verification

- Full local regression: `232/232 PASS` with `PYTHONPATH=src:. pytest -q tests`.
- Eligible-donor suite: `7/7 PASS`.
- Hardware-boundary suite: `4/4 PASS`.
- Dataset/support/runtime subset: `43/43 PASS` before full suite.

## Candidate semantics

The candidate makes eligible-donor and estimator boundaries first-class without authorizing training or execution.

Eligible-donor authority is derived from the frozen Gate-1 reader-fit donor×operator ledger, not from mechanics fixtures or pathology/outcome fields. Current derived values are 104 reader-fit donors, 104/104 base-teacher eligible donors, 104/104 relationally estimable donors, 1,400 donor×operator groups, 1,361 relationally estimable groups, and 39 small non-estimable groups containing 59 cells. Those 59 cells are excluded only from relational anchors; no donor is removed from the base donor objective.

The base estimator candidate uses exact `p/q` normalization by proposal draws and rejects self-normalized importance weighting. The singleton query precision candidate selects a 21-query total floor by an exact minimax two-family finite-population variance bound, with hardware allowed only to increase the query count while keeping the same allocation rule.

The EMA exposure helper expresses half-life in successful base-cell presentations and provides a donor-level worst-case absence union-bound criterion. The current 1% candidate half-life is 16,249 presentations, but the 1% criterion itself remains pending independent scientific review.

Hardware calibration is firewalled to execution geometry only: microbatch/token/chunk/device choices may not change donor eligibility, target/proposal mass, support-family weights, complete hidden evidence masks, singleton target identity, query allocation, EMA exposure unit, or relational activation.

## Authority posture

This is a candidate package only:

- `training_authorized = false`
- `execution_authorized = false`
- `successor_u0_authorized = false`
- `td60_authorized = false`

Required before any training authority: independent scientific review, independent implementation verification, real CUDA Gate-2 qualification, GPU hardware calibration under the science-neutral boundary, and a combined schedule attack.

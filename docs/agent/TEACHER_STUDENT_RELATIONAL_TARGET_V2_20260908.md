# Teacher/Student Relational Target V2 — Scale-Free Anchored Ordering

Date: 2026-09-08

Status:

`PROSPECTIVE_INACTIVE__SCIENTIFICALLY_ALIGNED_TARGET_MECHANICS__NO_TRAINING_AUTHORITY`

## Why V2 exists

The earlier prospective relational V1 adjunct matched two continuous quantities:

- teacher-normalized within-group Euclidean pair distances; and
- centered-state cosine similarities.

That is mechanically valid but scientifically too strong for the object that survived Target Discovery. TD57B established donor-recurrent **ordering of distances** across independent molecular views. It explicitly removed the need to assert absolute distance-scale equality. TD59 supported a broader nearest-half mesoscale screen on fresh panels, but much more narrowly, while TD57C falsified nearest-third hard locality.

Therefore V2 does not ask the student to reproduce the teacher's absolute distance magnitudes or angles. It asks the student to reproduce the **anchored order relation**.

## Exact representation and distance

Teacher and student use the canonical direct 160-D `cell_state`.

There is no learned relational projection head.

For cells a,b:

`d(a,b) = 1 - cosine(z_a, z_b)`.

The implementation rejects zero-norm or nonfinite cell states rather than silently defining a cosine.

## Exact teacher relation

For an anchor i and comparison cells j,k:

`y(i;j,k) = sign(d_T(i,k) - d_T(i,j))`.

So:

- y=+1 means j is closer to i than k;
- y=-1 means k is closer to i than j;
- y=0 is an exact teacher tie and is unresolved.

Only the sign is teacher supervision. Teacher distance magnitude is not a target.

## Differentiable student loss

For every teacher-resolved triplet:

`m_S = d_S(i,k) - d_S(i,j)`

and:

`L_triplet = softplus(-y * m_S) / log(2)`.

Properties:

- student tie => loss exactly 1;
- correct ordering => loss < 1;
- reversed ordering => loss > 1;
- positive rescaling of any individual cell state cannot change the cosine geometry;
- no teacher distance scale is fitted;
- no learned temperature or margin is introduced;
- absolute teacher distance magnitude and angle are not matched.

The module reports exact order agreement separately from the differentiable loss.

## Group law

Relations never cross a relational group. The intended group key remains:

`canonical_donor_id × operator_id`.

The module can deterministically enumerate all anchor/comparator triplets within an eligible group.

For future mesoscale use it can instead accept an **externally frozen exact triplet list**. It has no function that chooses a nearest-half, nearest-third, k, locality fraction, or winning neighborhood.

## No pilot-derived production constants

V2 intentionally does not freeze:

- a production locality fraction;
- a production k;
- a relational loss weight;
- a collapse threshold;
- a default relational group size/groups-per-batch combination.

A grouped-batch validator exists, but group size and groups per batch must be supplied by a later full-reader schedule authority. The 50k pilot cannot set those values.

## Collapse and fine-structure remain separate

Variance, pairwise spread, and entropy effective rank are anti-collapse telemetry only. Numerical lower ratios require a separate outcome-blind calibration authority.

Passing collapse checks does not establish fine biological structure.

Teacher/student fine-structure qualification must use donor-primary order agreement above a matched wrong-cell/fine-stratum null under a separately frozen evaluation contract.

## Scientific gating

This module is source-frozen mechanics, not an active objective.

Before it can influence an optimizer:

1. produce a lawful successor-bound u0;
2. separately authorize and execute u0→u40 mechanical qualification;
3. freeze u40 before biology;
4. require TD60 learned-teacher continuity 48/48 using the already-frozen TD57B global and TD59 mesoscale molecular views;
5. prospectively freeze and pass the partial-evidence student relational-predictability gate;
6. derive grouped schedule, any mesoscale weighting, collapse thresholds, and loss weight on the complete lawful 4,553,407-cell reader-fit population under separate authority;
7. independently review the resulting execution contract.

Until then, `teacher_student_runtime.production_update` must not import or call V2.

## Frozen implementation

`src/sea_ad_jepa/v4/teacher_student_relational_target_v2.py`

Source commit:

`931520bdbe6ac58b93298b38890bbcb054011648`

V4 source root:

`743347ab176adb8c3b7bd4ec74897d8e223d3ca4de9d78b9e4d398aa90bdedb2`

Terminal:

`TEACHER_STUDENT_RELATIONAL_TARGET_V2_FROZEN_PROSPECTIVELY__NOT_ACTIVE__NO_TRAINING_AUTHORITY`

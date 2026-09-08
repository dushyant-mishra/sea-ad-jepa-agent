# Teacher/Student V5 data-first planning status — 2026-09-08

Status: `V5_DATA_FIRST_PROFILE_AND_PROTOTYPE_PASS__DESIGN_ONLY__TRAINING_UNAUTHORIZED`

Completed:
- exact full reader-fit geometry profile from the frozen calibration-bundle metadata, reader_fit only;
- independent byte-identical profile replay;
- independent direct-SQL cross-check of cells/donors/operators/donor×operator groups;
- qualification-vs-production geometry boundary documented;
- support-aware evidence telemetry prototype;
- ragged donor×operator estimability prototype;
- singleton null strata become explicit NOT_ESTIMABLE rather than global failure;
- finite anchored-triplet capacity computation without exhaustive enumeration;
- deterministic operator-support-aware microbatch planner with no default token budget;
- exact target-element loss weighting for unequal microbatches;
- canonical packed valid-token path prototype;
- dense-vs-packed teacher/student/predictor/block-loss equivalence demonstrated in eval-mode synthetic attack;
- V5 prototype tests: **12/12 PASS**.

Important full-reader findings:
- reader_fit = 4,553,407 cells, 104 donors, 42 operators;
- raw cell mix is 90.44% SEA_AD, while donor mix is only 44.23% SEA_AD: scientific weighting must be explicit;
- 1,400 donor×operator groups, median full-reader group size 228, max 42,209;
- 97.21% groups have >=3 cells and contain 99.9987% of reader-fit cells;
- the 3,292 mechanics inventory spans the same 1,400 groups but samples only 1–5 cells/group, proving mechanics group size is not production geometry;
- historical 40% within-support masking gives 11,242 visible HVS addresses versus 21,046 SEA_AD addresses; evidence needs within-support and universe-relative reporting;
- full-group exhaustive anchored-triplet enumeration is impossible at production scale (median group >5.8M triplets; max group >37T).

Open before V5 can become a review candidate:
1. define/freeze the full-reader scientific sampling estimand (cell-weighted vs donor/source-donor weighting) without letting compute packing choose it;
2. solve deterministic training-mode dropout/RNG semantics for packed execution;
3. integrate exact element-weighted accumulation into a successor runtime and attack gradient/EMA equivalence;
4. define an externally frozen finite relational triplet sampler/budget for training (qualification keeps exact TD57B/TD59/TD60 triplets);
5. GPU-calibrate token/memory budget on actual target hardware;
6. express EMA/training horizon in exposure units as well as update units;
7. build and clean-room review a self-contained V5 package.

No V4 source/review package has been modified. No training, successor-u0 materialization, TD60 execution, or protected-population access is authorized.

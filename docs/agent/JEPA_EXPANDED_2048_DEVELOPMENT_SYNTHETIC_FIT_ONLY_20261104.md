# Expanded 2,048-gene synthetic developmental dataset — NOT production qualification

Date: 2026-11-04. User authorized an expanded synthetic dataset if needed for already designed all-C tests. This is a **development-only FIT dataset**, not production synthetic Task4, sealed withheld-family qualification, model training, a C1–C6 biological PASS, or authorization to cross STOP_A/B/C.

## Why the expansion is justified

Original [#328](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/328) has 480 cells × 48 genes × 16 donors. Its exact original world and fit hashes remain frozen. Original C2 [#316](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/316) uses three disjoint 512-gene molecular views; [#536](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/536) already demonstrated that 48 genes cannot be padded or relabeled as three independent 512-gene views. The original 9/9 independent C2 known-truth test-of-test [#336](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/336) is complete, not rerun.

Real target discovery completed TD57B, TD57C, TD59 and the once-spent corrected replay [#314](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/314); TD60's 48-case learned-EMA teacher plan exists but was not run. Existing [#341](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/341) prospectively resolved the original 13 scientific-gate *design* questions, with implementation and hostile mechanical tests through #369. Original C3 R5 q-excluded eight-*other*-gene comparisons ran; #328's population-mean controller mapping is not their biological target. Original #531 corrected the misleading detection-frequency-as-assay-support interpretation. Production V3.1.1 #344/#356 and Tasks1–3 are also substantially implemented. Do not rebuild or repeat any of this.

## Prospectively frozen development fixture

This code calls the original #328 neutral biology generator unchanged with **1,440 cells, 2,048 gene addresses, 36 donors** and seed **20261104**. The original V79 observation operator simulates counts at seed **20261105**. The three artificial acquisition labels are SYNTH_A/B/C, 12 donors each. The source-dependent capture log means (-0.25,-0.45,-0.65) and SDs (0.15,0.18,0.20) reuse original #328 development conventions.

Unlike original #328's faulty proxy, **assay structural support is chosen without using detection or observed gene values**: an artificial source-specific address is supported iff (gene_index + offset) % 37 != 0, offsets (0,5,11). This is a clearly labeled new *prospective simulation convention*, not empirical HVS/SEA-AD/NPH52 assay calibration, and not a new regulator of latent biology. It is not retrofitted into the old #328 world.

The first three disjoint blocks of 512 common physically supported addresses serve the C2 view *feasibility* check. The next four common addresses are query identities; each has eight other distinct measured-gene addresses, all frozen before candidate outcomes. Student base views exclude all four query addresses and derive depth only from visible base counts. Original synthetic ATAC producer gives both matched same-nucleus ATAC and a separate-nucleus negative.

## Output and protected boundary

GitHub Actions will produce four independent FIT-only arrays and a small receipt. **No hidden truth is exported.**

- teacher_measured.npz — measured synthetic RNA, structural support, matched ATAC.
- student_qexcluded.npz — query-excluded RNA, query-excluded support, projected base-only depth, no original whole-library depth.
- roster_evaluation_only.npz — synthetic donor/source/split and experimental-arm metadata, not student-model input.
- atac_separate_nucleus_negative.npz — separate-nucleus matched-donor negative.
- DEVELOPMENT_RECEIPT.json — original source identity, frozen parameters, all file hashes, specific limits, C1–C6 UNASSESSED and authority false.

The CI-generated artifact has 30-day retention; it is not sealed, qualified, or durable scientific custody. The private original V80 controller is not opened, copied, imported or included.

## Limits and next use

This makes **3×512 C2 views available** without falsifying original measurements, and provides actual multi-query q-excluded and paired/unpaired multimodal observations. It does **not** establish learned EMA geometry, per-cell C3 recoverability, C5 regulatory validation, nonlinear C6/C4 increments, 41,238 real-address transfer or multi-head non-interference. These require prospectively frozen actual candidate-specific learner/scoring controls and separate owner authorization. We must not train on or score using controller truth here.

The expanded fixture is not a substitute for the distinct V3.1.1 production Task4 biological generator, controller-private withheld-family test, authenticated calibration issuer, or any STOP gate. Macha should independently challenge its source invariance, original-hash preservation, detection/structural separation, C2 disjoint views, query-value descendants, source/donor shortcuts and nonpromotion claims before biological use.

Standing lock: TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED.

# V44 tiny historical teacher-team tournament — original-data CPU screen, not an authorized V5 trial

**2026-09-26 | EXPLORATORY ONLY | Stack on [V43 draft PR #176](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/176).** This is the first CPU tournament on authenticated *historical* actual RNA after V43's non-authorizing architecture proposal, NOT a full-size biological validation and **NOT the canonical IPBEncoder/EMA V5 execution**. Earlier Stage69–71 rare-head failures remain historical evidence, not reinterpreted as fresh success. Source of scientific rationale: `docs/agent/JEPA_V43_COMPLEMENTARY_TEACHER_STUDENT_RESEARCH_20260926.md`.

## Actual data and honest experimental unit

- Original discovery expression CSR NPZ, **50,000 × 41,238**, exact SHA-256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`. Original metadata CSV SHA-256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`. Original historical August calibration bundle SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`. Those original binary bytes remain mounted/subject to the V42 18-file custody; **do not upload to public GitHub**. Prepared decoded CSR arrays are independently hashed, too: `data.npy` `0276be05...`, `indices.npy` `f1fc3200...`, `indptr.npy` `58182d0a...`, `shape.npy` `5547a1cd...`. The GitHub rerunner must reject wrong prepared array SHA even if an authentic original NPZ sits beside them; never silently trust a derived array.
- **Only first 2,600 original sample-A natural-mixture cells**, with recorded original T1 sample explicitly excluded. **Three** independently seeded donor splits: seeds 7, 11, 17; **81 training / 20 held-out donors each**, 2,257/343, 2,125/475, 2,029/571 training/test cells respectively; **48 unique held-out donor IDs across all three splits** (some donors recur across seeds). This is a limited historical mixture, NOT a representative current FULL104 104-donor run.
- Exact all-42-operator original common-core support: 17,186 molecular addresses. Gene variance panel selected on each split's training donors ONLY, no peeking at held-out data; 1,600 common-support genes, randomly partitioned with fixed development seed into disjoint 640-gene student C, 768-gene teacher-only T and 192-gene independently withheld RNA Y. APOE index 6186 and P2RY12 index 12469 are **excluded from all views**. Within-view `log1p(10000*ratio/sum_view_ratio)` cancels inherited full-library q and opposite-view denominators algebraically; **this does not demonstrate any q-conditional biology**. Original storage precision and real production raw-block reader still need their own verification.
- Teachers are **train-donor-fitted PCA** (with small training-only projections where specified), student and Y readout **ridge regressions**, common 48-dimensional latent output and fixed alpha 50, same C input for each student. **Parameters and teacher compute are NOT equal**. No neural teacher, EMA or current-V5 optimizer. The rich reference R teacher has **C+T** (more information than other T-only teachers) and cannot win a fair same-teacher-evidence claim. The output Y is disjoint RNA genes from the SAME original cells, not an independent biological assay or unseen modality; all classification labels are RNA-derived.

## Five descriptive tournament arms and observed held-out donor-equal score

The primary statistic is `1 − mean_donor(mean_cell(mean_gene((prediction−observed_Y)^2 / train_gene_variance)))`; higher is greater generalization to independently omitted RNA coordinates. It is a **proxy** for retention of latent molecular information, not proof of biological world-model fidelity. Mean over three splits (see exact 15 rows in `tournament_scores_v1.csv`).

| Arm | Teacher evidence | Held-out donor-equal Y R² | RNA-defined rare subgroup Y R² | Student→teacher latent R² |
|---|---|---:|---:|---:|
| R: V5-*like* single rich PCA proxy, **NOT actual current model** | C+T (unfair informational advantage) | **0.415882** | 0.443839 | 0.712563 |
| A: single complementary teacher | T | 0.402673 | 0.431578 | 0.241531 |
| B: shared PCA trunk + 3 separate projections | T | **0.407823** | 0.432661 | 0.767634 |
| C: independently fitted core/fine/rare PCA components | T | 0.401864 | 0.422060 | 0.648729 |
| D: C's first 2 components + rare-tail-fitted 3rd | T | 0.400415 | 0.416042 | 0.595816 |

**Observed proxy-screen result:** rich R obtained the largest mean when allowed MORE teacher evidence (C+T vs only T). When keeping teacher *information set* fixed at T, B has the largest mean among tested variations, while independently trained C and tail specialist D showed no empirical gain. That is NOT a full tournament winner: architecture parameters, training compute, specialist input semantics, query specificity and independent biology are uncontrolled.

An ordinary direct C→Y ridge comparator averaged around 0.2225 and was not hyperparameter matched; the two-stage bottleneck can regularize it. Do not report this as proof that latent learning or JEPA is inherently better than supervised prediction.

## Red-team of the apparent scores — no false confidence

An independent audit physically re-executed the full producer, reconciled **15/15** scores to the saved result JSON, checked original NPZ and sample CSV hashes and separately retained all per-donor losses. The initial producer's descriptive bootstrap treated **60 donor×split appearances** as exchangeable; because donor IDs repeat, it was too optimistic as an independent-sample approximation. The independent repair first averaged each donor's within-seed paired residual and then resampled **48 unique donor identities** 10,000 times (still exploratory repeated-split analysis, not a preregistered CI):

| Arm minus A | Mean difference in donor-equal Y R² | Descriptive 95% unique-donor bootstrap |
|---|---:|---|
| R (rich-input unfair) | +0.013224 | [+0.010589, +0.015759] |
| B shared multi-head | +0.004755 | [+0.001241, +0.007301] |
| C independent team | −0.001381 | [−0.006243, +0.002032] |
| D rare-tail team | −0.002915 | [−0.008281, +0.001252] |

**Serious falsification gaps:** No actual current IPB/V5 code has run; all five are PCA/Ridge **surrogates**. No q identity enters target or predictor (the two named q IDs are excluded), so query-local fidelity, arguably the most important criterion of OUR project, is **unmeasured**. Native-class rarity is descriptive and derived from the same RNA, not independent rare biological truth. Coarse/global cell-state shortcuts may entirely explain measured cross-view Y. Y's independence is gene-panel nonoverlap, not donor-independent modality validation. Common 48 latent units do not enforce equal parameter counts or compute; R's C+T teacher information is unequal. Cells come from an old 50k sample, not authorized current FULL104. The seeded split and model choices were retrospective development conveniences and MUST NOT become frozen production hyperparameters.

**Tournament conclusion:** no scientifically validated architectural champion. For a subsequent, *genuinely matched-teacher-evidence* neural round, retain R as a historically important **unfair rich evidence upper comparator**, and compare actual current canonical IPBEncoder single-EMA baseline, shared multi-head, and separate core/fine/conditional-rare EMA teachers on exactly matched lawful teacher input, student C evidence and donor exposure. Freeze query-specific held-out biological targets, wrong-query and q-agnostic baselines, genuine rare-donor replication, compute/parameter budgets, copy/shuffle specialist controls and eventual external held-out modality. None of those experiments has been executed by this V44 screen.

## Reproduction, provenance and governance

GitHub `run_historical_tournament_v1.py` is an auditable streamlined producer implementation with **explicit exact prepared-array hashes added after red-team**, avoiding a serious original-NPZ vs decoded-memmap provenance gap. The **exact locally executed** original producer, complete per-donor JSON, original result JSON, 15-row CSV and independent audit script/log are preserved in the locally generated 19,390-byte `JEPA_V44_TINY_TOURNAMENT_PORTABLE_20260926.zip`, SHA-256 `7912918cad795f930b5c0a86a690a902e2126c6fca45fec33d83eced4ffb1daa`. The ZIP's CRC and all nine member checks passed. The exact original producer SHA is `1a3ee7ad900f9da71e287f47bed66850782a5cca0351e8c38390a519546dc342`; original score CSV SHA is `43edc51516ad63bebbba48eb5f98d8c5271f993e7ed4fa6a2a6c716fb518ae26`. The GitHub reimplementation still needs an independent execution on original data before claiming byte-equal replay to the exact original local producer; its added prepared-array hashes are a stricter fail-closed requirement.

Portable is **local-only**, not a public GitHub original-byte custody claim; it contains only source/results, not private large RNA originals. Remote GitHub carries every one of the **15 original result rows**, this complete signed-off descriptive interpretation, an auditable reproducibility implementation and the machine-readable original hash/experimental status. The V42 exact-original inventory remains the owner of the 18 original source files.

No source-branch training gate, original Phase-IV freeze, V42 preservation branch or production module modified. `TRAINING=OFF | AUDIT_B_N1=UNOPENED | D_SHARED_G5=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED`.

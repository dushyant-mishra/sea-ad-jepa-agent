# TD historical PASS test-quality reassessment — 2026-10-12

Status: `READ_ONLY_SCIENTIFIC_REASSESSMENT__NO_HISTORICAL_RELABELING__NO_EXECUTION_AUTHORITY`

Purpose: reassess whether historical Target Discovery PASS/positive results used tests that were too narrow, brittle, or biologically mismatched, especially in light of the TD57C nearest-third failure and the new fine/rare relational successor design. This document does not change any historical PASS/FAIL/NOT_ESTIMABLE label.

## Audit principle

A historical PASS means only that its frozen claim passed its frozen test. It must not be silently expanded into a broader biological claim. A better successor may characterize the same biology more faithfully without erasing the historical result.

Cross-cutting audit questions:
- Was donor the biological replication unit?
- Were sources kept distinct rather than averaged?
- Could common biology dominate a statistic while rare biology was lost?
- Did a single hard threshold/scale define the claim?
- Were failure and success scopes explicit?
- Were matched wrong-cell/technical nulls appropriate?
- Were effect sizes and donor distributions retained rather than only PASS/FAIL?
- Could measurement support or operator effects masquerade as biology?

## TD33 — global-row binding guard

Classification: **ROBUST ENGINEERING PASS; NO BIOLOGICAL REASSESSMENT NEEDED**.

TD33 verified physical row binding and caught the reset-index failure family. It is an integrity guard, not a biological claim. Keep unchanged.

## TD34 — annotated state geometry

Classification: **VALID POSITIVE VALIDATION, BUT TOO LABEL-DEPENDENT FOR TARGET AUTHORITY**.

What it established:
- annotated HVS/SEA state geometry reproduced strongly even after depth/detection residualization.

Limitations:
- labels establish the correspondence;
- only annotated/common states are emphasized;
- rare/private programs can disappear under state averaging;
- not a target-defining test.

Improvement if reused: donor-balanced rare/common and continuous-extreme state stratification, source/operator-aware controls, and source-specific reporting. Do not rerun merely to promote it; it remains validation-only.

## TD41 / TD43 — pair-order geometry and measurement reliability

Classification: **ROBUST SUPPORTING PASS; CLAIM SHOULD REMAIN NARROW**.

Strengths:
- later forensic audit reconstructed TD43 independently: 24/24 PASS;
- weakest observed-minus-null-p95 margin ~0.0856;
- TD41 4,096-pair result converged toward much larger/all-pair representations rather than depending on a lucky pair subset;
- common-scalar support and population-prior attacks were explicitly checked.

Limitations:
- TD41 primarily characterizes pair-order/state geometry, not preservation of rare programs;
- TD43 establishes measurement reliability conditional on resolution, not trainability or target quality;
- state/donor aggregation can still miss rare substructure.

Improvement: retain these as support tests and add rare-program-conditioned measurement reliability when rare biology is tested. No reason to relabel or replace the existing PASS.

## TD56 — disjoint-gene within-donor relational geometry

Classification: **STRONG PASS, BUT BROAD-STATE DOMINATED BIOLOGY WAS NOT EXCLUDED**.

Strengths:
- label-free;
- donor-primary aggregation;
- donor×operator/depth/detection-preserving wrong-cell null;
- all three sources PASS with large margins;
- independent non-overlapping pair subset also PASS;
- pair-hash ambiguity audit did not change the terminal.

Limitations already acknowledged by TD56:
- no held-out donor-block recurrence;
- no locality characterization;
- no partial-evidence/student predictability;
- no rare/common stratification.

Most important reassessment: a strong global relational correlation can coexist with loss of rare-state geometry because common states dominate the cell-pair population.

Improvement: do not rerun TD56 as a replacement. Its donor-block weakness was addressed by TD57B. Add rare/common and continuous-extreme conditioned relational preservation as a successor characterization.

## TD57B — donor-recurrent scale-free relational ordering

Classification: **CURRENTLY THE STRONGEST HISTORICAL RELATIONAL PASS; KEEP, BUT AUGMENT**.

Strengths:
- two fresh disjoint molecular panels;
- donor-primary deterministic splits;
- all three sources;
- 24/24 PASS;
- every case beat the maximum of 64 matched nulls;
- null-specific support/measurability was recomputed;
- no labels/pathology/protected outcomes.

Limitations:
- the estimand is unrestricted/global-to-mesoscale ordering;
- it does not establish fine locality;
- it does not test whether rare programs are preserved rather than averaged away by common biology;
- it does not test learned-teacher continuity or student recoverability.

Improvement: keep TD57B as evidence that broad relational ordering is real. Add program-conditioned donor recurrence and rare/common stratification. A rare-program failure must not retroactively convert TD57B to FAIL; it would show that broad relational order is insufficient for that program.

## TD59 — nearest-half mesoscale recurrence

Classification: **PASS, BUT HISTORICALLY THE MOST FRAGILE DECISION-BEARING POSITIVE TEST**.

Historical weaknesses:
- one fixed nearest-half scale;
- weakest historical observed-minus-null-p95 margin only +0.0011566;
- only 22/24 cases beat the maximum of 64 nulls;
- TD57C and TD59 used different fresh molecular views, so their pair does not estimate a clean one-third-to-one-half biological transition;
- nearest-half cannot be interpreted as a production locality hyperparameter.

Corrected replay materially strengthens the empirical HVS margins, but does not remove the design limitation that only one mesoscale point was tested.

Improvement: the PR #316 successor scale-response profile is warranted. The goal is not to invalidate TD59 but to replace the single-cutoff interpretation with a prospectively frozen scale-response characterization.

## Historical apparent positives that should NOT be revived as PASS authority

### TD17/TD18
Initially strong label-defined relational geometry, later superseded because depth pseudostates reproduced equally strong geometry. Keep as historical evidence only.

### TD20–TD22
SEA residual/subspace signals survived several attacks, but remained source-specific/falsification evidence and never established a universal target. Do not promote them retrospectively.

### TD31A/31B/32
Invalidated by the reset-index B-row defect. Not positive evidence.

These examples confirm that a visually strong or statistically large positive result is not enough; claim scope and falsifiers matter.

## Reassessment summary

| TD | Current assessment | Action |
|---|---|---|
| TD33 | robust integrity PASS | keep unchanged |
| TD34 | valid annotated validation | keep narrow; no target authority |
| TD41/43 | robust supporting PASS | keep; add rare-conditioned successor checks |
| TD56 | strong broad relational PASS | keep; augment rare/common characterization |
| TD57B | strongest relational PASS | keep; augment rare/program-conditioned recurrence |
| TD59 | valid but narrow/fragile historical PASS | replace single-scale interpretation with prospective scale-response successor |
| TD17/18, 20–22 | historical positives, superseded/falsification-only | do not revive |

## Binding methodological correction for future TD work

Future biological TD tests should, where applicable:
1. report donor-level effect distributions, not only binary gate outcomes;
2. preserve source-specific evidence;
3. separate common-state, rare-state and continuous-extreme regimes;
4. use matched technical/operator/wrong-cell controls;
5. characterize scale with a frozen profile when the biology is plausibly multiscale;
6. avoid early stopping when the purpose is biological characterization rather than one-shot gatekeeping;
7. state exactly what PASS establishes and exactly what FAIL may invalidate;
8. never let one narrow subtest discard a dataset or unrelated biology;
9. keep `NOT_ESTIMABLE` distinct;
10. never tune thresholds to reproduce historical outcomes.

## Recommendation

Do **not** blindly rerun every historical PASS. Most of the strongest PASS results remain scientifically useful. The better strategy is:
- preserve TD41/43, TD56 and TD57B;
- reinterpret TD59 only within its narrow historical claim;
- execute the new PR #316 scale-response + rare-state-conditioned successor;
- use the same test-quality rules when materializing PR #313 candidate gates.

Hard authority remains unchanged:
`TARGET_PORTFOLIO_NONE_SELECTED__REPRESENTATION_NONE_SELECTED__TD60_OFF__STAGE4_OFF__TRAINING_OFF`

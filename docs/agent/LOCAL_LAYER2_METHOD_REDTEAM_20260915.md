# LOCAL LAYER-2 METHOD RED-TEAM — 2026-09-15

Authority: `LOCAL_METHOD_VALIDATION_ONLY__NOT_FULL104_V5_PRODUCTION_EVIDENCE`.

Purpose: independently test the statistical logic being used in Claude's live V0/V1 shortcut audit and compare one supporting real-data diagnostic on the local 50K discovery substrate. No D_shared, pathology, protected outcomes, training, or new FULL104 intervention was accessed.

## 1. Fixed-target matched-state test

Controlled simulations confirm the test is a useful **one-way detector**:

- with no shared technical channel, the cleaner predictor beats the matched noisy predictor;
- with a sufficiently strong shared technical channel, matched-state advantage becomes positive;
- with moderate shared technical signal, the clean predictor can still win.

Therefore a positive matched-state advantage is strong evidence of shortcut accessibility at that model class, while a negative advantage is only `SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`.

This supports the terminal semantics already proposed.

## 2. Claude `x4_within.py` is not a valid within-operator estimator as written

The script first cross-fold-centers every row, then re-centers the training rows again inside each fold. Training examples are therefore transformed using a mixture of centering maps from other folds while test examples use the current fold's map. This is not the intended fold-local transformation.

A controlled fixture demonstrates the defect:

| synthetic truth | correct within-operator incremental R2 | Claude x4-style R2 |
|---|---:|---:|
| shared structure = operator only; zero cell-level shared signal | -0.0019 | 0.4819 |
| shared cell biology + operator effect | 0.5737 | 0.5388 |
| biology correlated with operator; no technical batch effect | 0.5774 | 0.7236 |

The first row is decisive: the x4 implementation manufactures substantial apparent within-operator signal when none exists by construction.

`x4_within.py` results should therefore not enter the evidence ledger until reimplemented.

Correct donor-held-out within-operator evaluation must, for each outer fold independently:

1. estimate operator means from that fold's TRAIN donors only;
2. subtract the same TRAIN-derived operator mean from both training and held-out cells;
3. fit the molecular predictor on the resulting training residuals;
4. evaluate on the held-out residuals;
5. measure incremental R2 against the operator-mean-only baseline.

No row should be pre-centered using a different outer fold.

Also: `donor-centred` is not a meaningful donor-held-out diagnostic. A held-out donor has no training-fold donor mean. Falling back to a global mean does not constitute within-donor centering. Do not report it as such.

## 3. Claude's nuisance-only result is important but needs direct verification

Claude observed on the frozen V5 mechanics sample:

- full-depth `V0 -> V1` OOF R2 = 0.4666;
- `Q + source + operator -> V1` OOF R2 = 0.4671;
- combined `Q + source + operator + V0 -> V1` = 0.4982.

If reproduced, this means a coarse operator/source/QC prior can predict as much **total target variance** as the molecular cross-view predictor on this mechanics sample. That is potentially a major anti-cheat finding.

But it must not yet be labeled a pure technical effect because source/operator are biologically confounded in FULL104.

Before interpretation, verify it through a source-distinct code path using direct cross-fitted group means and report separately:

- Q only;
- source only;
- operator only (source is nested in operator, so source+operator is redundant structurally);
- operator + Q;
- V0 only;
- operator + V0;
- operator + Q + V0.

The key quantity is the molecular increment beyond the coarse group prior and the amount of target variance attributable to between-operator means versus within-operator variation.

## 4. Sample-estimand warning

The V5 BASE sample is an operator-stratified whole-block mechanics sample with `q_i = min(12,B_o)/B_o`, spanning ~119x in inclusion probability.

Therefore unweighted nuisance-only R2 is a property of the mechanics sample, not automatically of:

- empirical FULL104;
- source-uniform FULL104;
- donor-primary training/inference targets.

Before using the magnitude 0.4671 to redesign training, repeat the summary under the relevant explicit weighting views when mathematically supported. A positive existence result remains important, but magnitude is distribution-dependent.

## 5. Independent local real-data sanity check

Using the local 50K discovery expression substrate:

- common core recovered exactly: 17,186 addresses;
- exact current partition namespace replay: V0=8,568, V1=8,618;
- each view projected independently with a deterministic 128-d signed CountSketch (`LOCAL_LAYER2_COUNT_SKETCH_V1`);
- evaluation donor-held-out over 104 donors / 42 operators.

Results:

- `V0 -> V1` R2 = 0.47252;
- source-only -> V1 R2 = -0.00009;
- operator-only -> V1 R2 = -0.00093;
- operator+V0 -> V1 R2 = 0.47195;
- correctly computed within-operator V0->V1 incremental R2 = 0.47244;
- 0 held-out cells had an unseen operator in the corresponding training fold.

Interpretation: the large V5 nuisance-only result is **not** a trivial mathematical consequence of the common-core split or of disjoint views. It may reflect the exact V5 projection, the BASE sampling composition, or genuine FULL104 batch/composition geometry. It therefore deserves direct verification rather than dismissal or automatic generalization.

This 50K diagnostic is not current-V5 authority because the projection differs from production V5.

## 6. Historical evidence is directionally compatible with shortcut risk

The frozen historical shortcut atlas independently records at u0:

- source balanced accuracy = 1.0;
- operator balanced accuracy = 0.7551 for rich_H;
- support-count R2 = 0.9998.

The historical balanced-vs-empirical synthetic study retained source BA=1.0 and support R2 ~0.995-0.997 even under balanced sampling.

Thus technical/context structure is a known substrate property, but those historical results do not prove Claude's current 0.4671 V5 nuisance-only number.

## 7. Recommended immediate reconciliation with Claude

1. Do not use `x4_within.py` output as evidence.
2. Recompute within-operator residual prediction with a single current-fold centering map.
3. Verify nuisance-only V5 R2 using direct cross-fitted operator means, not only standardized one-hot ridge.
4. Report source-only and operator-only separately.
5. Repeat headline decomposition under the explicit sample/target weighting views relevant to training design.
6. Keep source/operator results labeled `COARSE_CONTEXT_SHORTCUT_RISK`, not `PURE_TECHNICAL_EFFECT`.
7. Continue the frozen thinning matched-state/realized-state tests; the negative matched-state result remains useful but non-exculpatory.

No architecture change is justified from the local lane alone.

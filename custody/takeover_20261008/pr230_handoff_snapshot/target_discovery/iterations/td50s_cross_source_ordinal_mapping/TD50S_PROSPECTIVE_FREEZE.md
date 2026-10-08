# TD50S — Cross-Source Universal Ordinal-Mapping screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Motivation

TD48 HVS donor-heldout query-ordinal predictability survives its broken-context null.
TD49 NPH52 source-internal refit fails, potentially reflecting limited 17-donor estimation or a non-universal mapping.

TD50S asks the cleaner foundation question:
Can a predictor learned without any NPH52 target outcomes from the larger HVS+SEA_AD donor pool generalize to NPH52 query-ordinal targets?

## Target/context

Reuse TD48 exactly:
- same 64 query genes;
- same 512 visible reference genes;
- same tie-aware tau target;
- same 17,122 non-query common-scalar context genes;
- same fixed 256-dimensional TD48 rank CountSketch.

No biological labels.

## Train/test

TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD donors/cells.
TEST = all A_NATURAL_MIXTURE NPH52 donors/cells.

No NPH52 target tau is used for fitting, model selection, standardization, or target centering.

Primary biological unit remains donor. TRAIN cells are equal-donor weighted across the pooled 87 donors; NPH52 TEST is equal-donor weighted across 17 donors.

## Measurement shortcut

For cross-source generalization, shortcut uses only source-portable measurement descriptors:
- intercept
- log1p(source_library)
- log1p(full-row detected_genes)

Do not use source ID, dataset ID, matrix ID, donor ID, or operator categorical identity.

Molecular model = shortcut + 256 fixed broad-context rank-sketch coordinates.

## Model selection

Joint 64-output weighted ridge as TD48.

Inner donor folds are defined over pooled TRAIN:
SHA256("TD50S|inner|source|<source>|donor|<d>") byte-0 LSB.

Use the same lambda multiplier grid and numerical conventions.

## Primary test

Standardize predictors and 64 target coordinates using pooled TRAIN only.
Apply frozen models to NPH52.

Delta_cross =
(MSE_shortcut - MSE_molecular)/MSE_shortcut
using equal-donor NPH52 TEST MSE.

Require >=48 measurable target coordinates.

## Broken-context null

If Delta_cross>0, run 16 complete TRAIN null refits.

Within each TRAIN source separately and each donor×operator depth/detection block, cyclically permute the 256-dimensional context row:
TD50S|null|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>.

Repeat inner lambda selection and molecular refit in every null.

## Positive control

If primary fails, add the true 64 query tau coordinates as predictor coordinates in TRAIN and TEST.
Positive control must yield Delta_cross>0 or:
TD50S_NOT_MEASURABLE__CROSS_SOURCE_SCREEN_SENSITIVITY_FAILURE.

## Terminal

PASS only if:
- >=48 target coordinates measurable;
- observed Delta_cross>0;
- observed Delta_cross > max of 16 broken-context nulls.

PASS:
TD50S_CROSS_SOURCE_QUERY_ORDINAL_MAPPING_SURVIVES__FREEZE_MEASUREMENT_GATE_NEXT

If primary fails and positive control validates:
NO_UNIVERSAL_QUERY_ORDINAL_MAPPING__TD50S_FAIL

No target authority or training authorization.

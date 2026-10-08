# TD48S technical addendum v1.1

Status: PROSPECTIVE_TECHNICAL_BINDING__NO_OUTCOME_INSPECTED
Parent: TD48S_PROSPECTIVE_FREEZE.md

## Inner donor folds
For each outer TRAIN donor d:
digest = SHA256 UTF-8 of "TD48S|inner|donor|<d>".
inner fold = least-significant bit of digest byte 0.

## Context sketch
For context gene g:
digest = SHA256 UTF-8 of "TD48S|ctxgene|<g>".
bucket = first 8 digest bytes interpreted unsigned big-endian mod 256.
sign = +1 if digest byte 8 least-significant bit is 0, else -1.
Each bucket is divided by sqrt(number of context genes assigned to it).

Average-tie rank normalization is (rank-1)/(N_context-1), then subtract 0.5 before sketch accumulation.

## Ridge / weights
Use the TD45S v1.1 equal-donor weights, predictor standardization, target standardization, ridge scaling, unpenalized intercept, and inner-lambda tie rule exactly.

## Positive control
The leakage-positive control adds the 64 true TRAIN/EVAL tau query coordinates themselves as predictor coordinates. It is a pipeline-sensitivity control only and can never rescue a failed primary screen.

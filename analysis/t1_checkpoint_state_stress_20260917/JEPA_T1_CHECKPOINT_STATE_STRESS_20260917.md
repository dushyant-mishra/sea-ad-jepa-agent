# T1 checkpoint state-level masking stress — 2026-09-17

**Status:** exploratory historical stress fixture only. Not teacher authority. Not training evidence. Training remains OFF.

## Scientific target invariant
The JEPA task is to infer biological/cellular state, including query-local state associated with a particular address, from remaining RNA evidence. It is **not** hidden-gene scalar expression prediction. Expression-prediction models in the masking lane are adversarial shortcut probes only.

## Why T1 is used here
Historical T1 checkpoints contain the original online encoder, EMA target encoder, predictor, optimizer and trajectory state. Their post-u0 lineage is known to inherit a historical training-mechanics defect, so they are used only as adversarial/stress fixtures. They must not be promoted to healthy-teacher evidence or copied into V5 authority.

## State-level challenge
For held cells/query addresses:
- teacher: historical EMA target model on the unmasked/full fixed panel;
- student: historical online encoder + predictor on an equal-burden masked panel;
- masking arms: UNIFORM, RIDGE8, TOP8, PREFIX3 when applicable;
- primary diagnostic: query-local latent cosine error, not hidden-gene expression error.

### u200 result
Across 8 targets x 4 folds x 3 held cells/source per arm (96 rows per method):

| method | mean query cosine error | delta vs uniform | mean global-cell cosine error | mean targeted n |
|---|---:|---:|---:|---:|
| UNIFORM | 0.605672 | 0 | 0.092586 | 0 |
| RIDGE8 | 0.605669 | -0.000002 | 0.092598 | 8 |
| TOP8 | 0.605664 | -0.000008 | 0.092583 | 8 |
| PREFIX3 | 0.605669 | -0.000002 | 0.092585 | 1.4375 |

At this historical checkpoint, changing which equal-burden evidence is masked has essentially no effect on query-local state prediction.

### u0 matched sanity slice
For the same first target/12 held cells:
- UNIFORM mean query cosine error: 1.075453
- RIDGE8 mean query cosine error: 1.075476
- difference: +0.000023

The historical trajectory therefore improved query-state alignment strongly by u200, but the endpoint remains nearly insensitive to these local proxy removals.

## Interpretation
This is **not evidence that RIDGE8 fails**. The T1 lineage is defective and cannot define healthy biology. The result instead motivates a V5 regression requirement: a production state predictor must demonstrate that appropriate remaining RNA evidence contributes materially to query-local state inference, above query identity and generic/global-cell shortcuts.

## Historical-spillover rule
Do not copy T1 model semantics, weights, optimizer state, target construction, old CELL-only controls, or post-u0 training conclusions into V5. Reuse only the adversarial idea and the checkpoint as a quarantined regression fixture. Current V5 authority must be independently bound to current target semantics, current representation authority and current masking/evidence contracts.

Protected/pathology/D_shared outcomes were not inspected.

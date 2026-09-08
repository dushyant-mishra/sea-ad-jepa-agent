# TD49S — Independent-Source Query-Ordinal Replication gate

Status: FALSIFICATION_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Frozen object

Reuse TD48 exactly:
- same 64 query genes;
- same 512 visible reference genes;
- same tie-aware tau query target;
- same broad context = 17,122 common-scalar non-query genes;
- same 256-dimensional TD48 context rank CountSketch;
- same shortcut features;
- same nested weighted ridge and lambda grid.

No biological labels.

## Sequential source rule

Test NPH52 first. Only if NPH52 passes, test SEA_AD.
This ordering is frozen for computational efficiency and cannot change the scientific gate.

## Source donor splits

For source s:
rank donors by SHA256("TD49S|split|0|source|<s>|donor|<d>").
Alternating donors -> TRAIN/EVAL.

Inner folds:
SHA256("TD49S|inner|source|<s>|donor|<d>") byte-0 LSB.

## Primary source statistic

Compute donor-heldout Delta_tau exactly as TD48.

Run 16 complete source-specific broken-context TRAIN null refits within donor×operator depth/detection blocks:
TD49S|null|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>.

PASS_SOURCE iff:
- >=48/64 target coordinates measurable;
- observed Delta_tau > 0;
- observed Delta_tau > max of all 16 null Deltas.

## Sequential terminal

If NPH52 fails:
NO_INDEPENDENT_SOURCE_REPLICATION_OF_QUERY_ORDINAL_TARGET__TD49S_FAIL
and SEA_AD is not run.

If NPH52 passes, run SEA_AD.
If SEA_AD fails:
PARTIAL_SOURCE_REPLICATION_ONLY__QUERY_ORDINAL_TARGET_UNQUALIFIED

If both pass:
TD49S_THREE_SOURCE_QUERY_ORDINAL_TRAINABILITY_SURVIVES__FREEZE_MEASUREMENT_DEPTH_GATE_NEXT

No target authority, production sketch width, query/reference set, threshold, or training authorization.

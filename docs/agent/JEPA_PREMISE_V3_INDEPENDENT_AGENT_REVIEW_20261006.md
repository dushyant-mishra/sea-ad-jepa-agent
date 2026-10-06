# JEPA premise V3 independent-agent review — 2026-10-06

Role: `INDEPENDENT_AGENT_REVIEW__NOT_EXTERNAL_HUMAN_REVIEW__NOT_EXECUTION_AUTHORITY`
Reviewed branch: `design/premise-qualification-contract-v3-20261006`
Live main rechecked at: `102aa26730e4c2eda8b52a7532adee5332971e8b`
Behavioral/governance head verified GREEN: `6b21de80fd1b073292989e0627df41d6f5b31f3f`
GitHub Actions run: `37506442262`
Result: `45 passed`

## Review scope

Whole-branch scientific/governance review focused on representation neutrality, hidden post-outcome flexibility, observation-channel shortcuts, machine/prose agreement, stability semantics, uncertainty/OOD separation, external-evidence overclaim, and scope containment.

## Findings discovered during this review

### IR-1 — hard-state machine contract was incomplete

The governing prose kept `MULTIMODAL_TRAINING=OFF`, `500K=NOT_AUTHORIZED`, and `STAGE4=NOT_AUTHORIZED`, but those states were not directly represented or validated in the machine JSON.

Repair: add explicit false authorization fields and validator checks.

### IR-2 — observation shortcut machine contract was weaker than prose

The prose forbade pathology/outcome labels, protected-outcome-derived labels, and study identity used as memorization input, while the machine state only froze donor/dataset/matrix identity restrictions.

Repair: bind the full forbidden shortcut roster and validate it exactly.

### IR-3 — stale stability verdict vocabulary remained in binding prose

Two binding documents still used older labels such as `AXES_STABLE` and `SUBSPACE_STABLE_AXES_ROTATE` while the machine/standalone stability contract used the canonical V3 vocabulary.

Repair: unify on `STABLE_COORDINATES`, `STABLE_SUBSPACE_ONLY`, `UNSTABLE_REPRESENTATION`, and `INDETERMINATE__INSUFFICIENT_BIOLOGICAL_UNITS`.

### IR-4 — claim-ladder wording mixed evidence states with claim levels

The design document presented `OBSERVED_RNA` and `RECOVERABLE_RNA_STRUCTURE` in the same ladder as the four biological claim levels, while the standalone claim contract and machine state define four claim levels beginning at `RNA_REPRESENTATION`.

Repair: explicitly classify the first two as pre-claim evidence states and retain the four-level biological claim ladder.

## RED→GREEN evidence

New independent-review tests at `46343f62dbdae49338a011744318fe8b3d52633d` produced exactly:

`5 failed, 40 passed`

The failures corresponded to the incomplete hard-state fields, stale stability vocabulary, and missing observation shortcut bindings.

After bounded repairs, run `37506442262` at `6b21de80fd1b073292989e0627df41d6f5b31f3f` produced:

`45 passed`

## Scientific review conclusion

No remaining blocker was identified in this review for merging the package as governance/prefreeze documentation, provided owner direction explicitly chooses to merge it.

This conclusion does **not** authorize Stage A, JEPA training, TEST opening, Morabito use, 500K, Stage 4, target selection, representation selection, estimand selection, or numeric-threshold selection.

The next authority step after any governance merge would still be a separate, narrow, prospectively frozen Stage-A execution authority.

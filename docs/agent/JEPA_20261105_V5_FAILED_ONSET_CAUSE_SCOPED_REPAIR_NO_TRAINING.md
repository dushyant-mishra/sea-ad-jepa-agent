# V5 #560 first failed-onset cause — scoped non-training repair

**Source:** exact Macha #560 test-only head `0c1fd7a82f2b6c06e44e4c0f9cb5b51960cbf745`, stacked on #558 `33793a07a7c19eeb6a35273182d1ba9151bcf600`. Reviewer tests #557 (`bfa5345775570205def66eb19a98efc207d28d90`) and #560 (`3ab6c208206251728116debda1edb226cb5b647a`) are inherited and must remain byte-identical. No old RED rewritten.

## What this repairs

The #558 validator previously accepted `success=False` and all normal mechanical signals, losing the *why* of a collapse. An uncaused failure now refuses. Old, unchanged #557 mechanical failure reports still work: the validator infers a **reported mechanical cause** only where an existing signal is positive (48 dead gradients, AMP skip, etc.). Each returned receipt has a `failure_cause` and an explicit provenance label: legacy inferred or explicitly reported.

New explicit representation causes:
- `CELL_CONSTANT` — same fixed-panel CELL centered energy exactly zero.
- `IDENTITY_ONLY_GENE_TOKENS` — same-gene token cross-cell variance exactly zero.
- `EXPRESSION_RESPONSE_ZERO` — same-cell expression shuffle delta exactly zero.

Each requires an explicitly matching metric, exactly zero observed measurement, positive u0 reference, SHA-format frozen panel identifier, and an operator-homogeneous eval-mode panel with identical gene sets. Near-zero but positive measurements are **not** STOPed. All evidence remains caller-provided/self-reported, and cannot prove actual neural collapse.

## Not solved; nonpromotion

This is **not** the final schema or durable journal. A true prospective contract must require an explicitly recorded cause (the legacy mechanical compatibility path here intentionally survives unchanged #557); bind a planned horizon to a write-once run lock; integrate the checked cause payload into #559 (which currently persists arbitrary opaque bytes); and close Macha #561 E1/E2 with an external head anchor, per-attempt fsynced journal and forensic prefix read. Physical gradients, Adam/EMA, fixed TRAIN-panel probes, complete state serialization, crash/restart parity, and biologically justified thresholds remain unimplemented. No synthetic or real optimizer step, GPU, controller access or data generation was performed.

**Approval:** Author-side green CI will not substitute for independent Macha head-specific review. Do not merge, promote or train from this patch.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

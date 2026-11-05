# V5 nontraining integration: reported collapse cause + atomic onset disk bytes

This draft bridge combines **#562 cause validation** with the **#564 disk-journal / #563 forensic-prefix** lineage. It does not merge any source PR or authorize real training. Original Macha #557, #560 and #561 test blobs are inherited verbatim. Tested fixtures contain fake opaque bytes, not models.

## What actually integrates

`scripts/v5/jepa_synth2048_checkpoint_capture_prefreeze_v1.py` is the **byte-identical Git blob** from #562 (`d83e5075a98376f43f3e4263be55a2fe7cf12da7`); this adds inferred/measured-*reported* causes and exact-collapse probe requirements to the #564 checkout. New versioned adapter `scripts/v5/jepa_synth2048_typed_onset_disk_integration_v2.py` validates the failure using #562, serializes the typed receipt into canonical JSON, requires the next attempted update to follow the last physically recorded checkpoint, writes through #559/#564's fsynced intent/evidence/receipt chain, then reads the actual bytes back through SHA validation and revalidates the typed cause.

The adapter's inventory reports a run that ends before its locally declared horizon **without** a recorded failure as `INCOMPLETE_RUN_WITHOUT_RECORDED_STOP__NOT_PLANNED_SUCCESS`. It does not fabricate a cause or silently call the stop planned. An incomplete tail after interruption is accessible via a **forensic-only** prefix reader, which never treats uncommitted evidence as an actual completed update or authorizes resume.

## Smoke and hostile tests

Dedicated synthetic-only suite tests:
- u0–u12 stored as fake bytes, failed attempt u13 with `CELL_CONSTANT` exact-zero fixed-panel reported probe, last committed u12 SHA byte-read still intact, failed u13 cannot become completed checkpoint.
- Uncaused or contradictory STOP, falsely small-but-positive collapse value, malformed/misindexed receipt: refuse before writing evidence.
- Legacy mechanical dead-gradient report distinctly labeled *inferred, self-reported*.
- Mutated physical evidence must fail SHA.
- Abrupt failure between evidence and receipt: strict journal refuses; forensic reader recovers last healthy opaque checkpoint.
- A fresh Python process reads the same cause, index and SHA-verified last checkpoint bytes.
- Attacker deleting *every* same-directory intent and onset file can still create a locally consistent unfinished run; an independently retained external head would detect it, but no external custody is connected.
- All original immutable Macha #557/#560/#561 tests and old author regression suites are included in the new CI workflow; do not edit the originals.

## Limits and deliberately unintegrated work

**This is a typed evidence bridge, not a full new training-run contract.** Old low-level `save_failed_attempt_evidence` still accepts arbitrary bytes for backward compatibility and is NOT a verified typed API. All typed cause/metric fields are still caller-supplied, **not derived from physical encoder/teacher/Adam tensors**. Existing low-level successful checkpoint bytes are opaque; the bridge does not prove actual optimizer/EMA update success or track every attempted update between sparsely scheduled checkpoints. A failed attempt is accepted only as the immediate successor of the *last saved* checkpoint. It does not solve #553 F2–F4 physical evidence requirements.

Storage-intent is before disk write, not before a genuine optimizer update. Neither a connected external append-only custodian nor signed expected head is implemented. A forged whole-directory tail remains possible. The bridge does NOT prove true collapse, full healthy model state, biological validity, authenticated donor/rights, restart *model update* bit equality or Stage4 readiness.

**Next exact engineering stages (NOT authorized training):** independent Macha head-specific review; versioned every-attempt write-ahead telemetry contract with actual 48 unscaled protected gradient/Adam norms, EMA arithmetic and fixed TRAIN-panel CELL/gene-token/expressions-shuffle/source controls; serialize complete encoder/teacher/predictor/Adam/RNG/gene-address/source/rights state and design bitwise fresh-process next-update checks. Owner approval needed before any real optimizer execution. Do not repeat frozen historical experiments or change scientific hold decisions.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

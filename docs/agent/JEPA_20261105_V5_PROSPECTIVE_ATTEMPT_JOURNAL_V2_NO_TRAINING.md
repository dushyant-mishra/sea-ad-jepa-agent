# Prospective V2 attempt journal — fake bytes only, NO TRAINING

This draft is stacked on #565, with byte-identical scoped fixes sourced from #569 (honest post-step state collapse, #566 immutable RED) and #568 (corrupt-tail forensic byte-prefix, #567 immutable RED). Original Macha #557, #560, #561, #566, #567 RED files are unchanged.

## Concrete mechanisms, deliberately not yet an executable trainer

A new versioned `scripts/v5/jepa_synth2048_attempt_journal_v2.py` provides write-once POSIX fsynced RUN_OPEN (planned horizon, fixed panel/config/rights SHAs and every-success schedule), ATTEMPT_BEGIN before each prospective update, one of UPDATE_COMMITTED, STATE_COLLAPSED, ATTEMPT_FAILED or ATTEMPT_ABORTED, and RUN_CLOSED. Commit requires a caller-supplied `NOT_COLLAPSED_ONLY` state-probe receipt bound to the stored payload SHA and panel SHA, **not** physical inference. A collapsed state's full opaque payload has the same 512 MiB limit as a successful state, **not** the old 8 MiB failure evidence cap, and is never resumable. `last_neurally_healthy_checkpoint_proved` remains false. Runs lacking RUN_CLOSED are **unexpectedly incomplete**, never successful.

Each journal row has seq, previous SHA, run-lock SHA and linked payload/telemetry hashes; local row is mirrored to a **separate owner-provided directory outside the run directory**, unsigned. Loss of whole local tail is detectable while the external copy remains. The copy is not a cryptographic custodian, not proof of resistance to malicious same-writer forgery, and not on a separate physical device unless the owner arranges it. If a crash occurs after local record and before external mirror, a dedicated same-prefix ahead-by-one reconciliation copies the verified record. A crashed attempt can become explicit ATTEMPT_ABORTED, with suspicious on-disk bytes quarantined (never quietly deleted), and the run can then be closed as aborted. The low-level strict scan refuses incomplete/corrupt or unmatched custody; forensic-only scan returns the maximal verified prefix to first anomaly, not model resume authority. All these observations concern **opaque fake bytes**.

Original code paths from #562/#563/#564/#565 remain available only for backward-compatible tests; the new API is separate. No real optimizer step was executed. Smoke tests exercise the state machine, storage integrity, last committed SHA bytes, 23+ MiB synthetic onset payload, deleting record tails, corrupted later payloads, crash and custody catch-up, quarantine, runtime abort and false-planned-success refusal.

## Scientific and engineering blockers

No physical step-begin hook or true optimizer/EMA state measurement; the new call is simply a prospective software boundary. No actual encoder/teacher/predictor/Adam/RNG/source/rights full-state serialization, all-trainable gradients, fixed frozen-panel CELL/token/identity/shuffle/teacher target witnesses, or full fresh-process next-update RT1–RT8 parity. No proof that any checkpoint contains a healthy representation. A caller-supplied STOP report or reported passing probe may be fabricated. A second copy in an adjacent folder can be lost with the same disk; owner must pick independent storage and decide unsigned signing risk. Macha independent review required, including interrupted writes, orphan quarantine, and whether a record can be falsely promoted.

This branch is for review and synthetic smoke only, with no merge, neural training, GPU or Stage4 authorization.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

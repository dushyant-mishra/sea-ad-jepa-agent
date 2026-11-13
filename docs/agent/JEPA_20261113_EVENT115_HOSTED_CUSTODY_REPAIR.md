# Event115 — Repair hosted custody regressions from Event114

Event114 hosted results: #322 25/27; chronology rejected the unrecognized Event114 change type (run 43519033567), and the existing V80 original-archive check failed (43519033563). #460 2/4; both first-read checks rejected the new header (43519036581, 43519036580). Source inspection confirmed the header also lacked the exact canonical head required by the parser.

Fix: preserve all Event114 ledger/index values. The chronology validator accepts the published change type only for the exact Event114 event ID; future entries must still use a recognized type. Event115 uses `repair`. The #460 first-read names Event90 and pins the exact Event115 #322 commit. No checker disabled. Hosted revalidation is separate; this note records the old failures and submitted fixes, not a green result.

For future handoffs: check chronology enums and first-read format before publishing, and verify the hosted outcomes at both exact new heads. Next engineering items: repair the scoped #596 CI entrypoint, bind trusted environment and checkpoint readback on a separate #597 successor, then verify upstream noninterference and evaluation controls with inert fixtures. No training, restricted data, merge or pilot authorization.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

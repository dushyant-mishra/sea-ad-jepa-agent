# F1 HC3 Command 15A3 — external-review handoff

Terminal: `STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH`.

All hashes and the old rank-18/df-86 HC3 failure reproduce. However, the mandatory base is rank 7 in both prior authoritative packages and in two current implementations. Command 15A3 requires reproducing rank 8, so its own Section-1 mismatch gate stops execution before augmented-rank analysis.

The discrepancy is semantic/provenance, not an engineering failure: rank 7 is intercept + two independent source contrasts + four continuous nuisances. The earlier 8->8 trace is the design after adding NPH52 component 1, then testing component 2.

No frontier, candidate authority, rank triple, integration change, expression, model, checkpoint, outcome, training, or EMA work was performed. A corrected prospective command must explicitly require mandatory-base rank 7 before this diagnostic can resume.

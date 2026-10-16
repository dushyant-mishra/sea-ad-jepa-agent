# JEPA S149-aware primary reopen — TD41–TD43

Date: 2026-10-06
Status: `PRIMARY_REOPENED__CORE_SIGNAL_NOT_INVALIDATED_BY_S149__PANEL_GENEALOGY_STILL_OPEN__NO_TARGET_AUTHORITY`

This record is part of `JEPA_S149_AWARE_TARGET_LINEAGE_READJUDICATION_20261006_V1.md`.

## Primary artifacts reopened

- prospective TD41S freeze: `a1bfebf3ecbc55d9594058f182202e5a90a882ff`
- TD41–TD43 forensic audit protocol: `54f67f5cd5138c47311e95441b4895076ffb7bfc`
- terminal forensic audit result: `fa33944589b84d4dbf7d28dd19c743bf83843569`
- reconstructed 24-case TD43 table: `77d546710d2c5c58dac3f5aea5555591763616fe`

## Question

Does S149 — the finding that pooled real detection topology is strongly driven by study/cohort measurement composition — invalidate the historical TD41–TD43 pair-order result?

## Answer

**Not the core surviving TD41–TD43 result.**

The decisive historical evidence was not a pooled-cell correlation envelope of the type implicated by S149.

### 1. Pair identity was frozen without source/outcome selection

TD41S defined, for each fixed Molecular Ledger pair `(g,h)` in a cell, the tie-aware sign of `x_g - x_h`.

For each pre-existing 512-gene panel it enumerated all unordered pairs, ranked them by a deterministic SHA-256 address hash, and retained the first 4,096 pairs. The prospective freeze explicitly prohibited selection by expression, state label, recurrence or outcome.

Therefore the 4,096 pair subset itself was not chosen because it reproduced a pooled HVS/SEA-AD topology statistic.

### 2. Structural measurement support was common across all operators

The forensic audit proved:

- 17,186 all-42-operator common-scalar addresses;
- every TD41 panel gene was inside that set;
- every endpoint of every retained pair was inside that set;
- zero structural-support violations.

Thus the TD41 cross-source result cannot be explained by one source simply not measuring one side of the pair.

### 3. The cell-specific excess was evaluated inside each source

The audit did not pool all cells and then measure a single correlation topology.

For pair-dominance stratification it first computed donor-balanced pair-direction means separately in HVS, NPH52 and SEA_AD, then averaged the three source scores equally. The quartile definition was therefore source-balanced rather than raw-cell-pooled.

More importantly, the measurement-reliability result itself was reported separately for HVS, NPH52 and SEA_AD.

For the least globally predetermined quartile (Q1), panel 0 showed approximately:

- HVS absolute same-cell-over-wrong-cell excess: 0.127;
- NPH52: 0.134;
- SEA_AD: 0.134;
- headroom-normalized excess roughly 0.90–0.95.

Independent panels 1 and 2 reproduced positive Q1 excess in every source and both half-depth views.

The full TD43 reconstruction then passed all 24 source × panel × half cases, with weakest observed-minus-null-p95 margin 0.085626 and weakest headroom-normalized excess 0.89365.

This is a materially different evidentiary object from the S149 pooled detection topology.

## What S149 still changes

S149 does not promote TD41–TD43 to target authority. It sharpens the remaining qualification requirements.

### Open issue A — upstream 512-gene panel genealogy

TD41 reused four deterministic 512-gene TD34 panels. The TD41 freeze itself did not select pair identities by expression/source/outcome, but this reopen has **not yet reconstructed how the TD34 panel genes were originally selected**.

Until that genealogy is reopened, we cannot exclude that panel membership was influenced by a pooled source-composition statistic upstream.

This is now the highest-priority TD41 provenance question.

### Open issue B — biological meaning versus measurement reliability

The historical terminal status was correctly:

`TD43S_PAIR_DIRECTION_MEASUREMENT_RELIABILITY_SURVIVES__NO_TARGET_AUTHORITY`

Pair-order is rank/order information already implicit in RNA counts. Reliable cell-specific information does not prove that predicting it is the right JEPA biological objective.

A future target test must show material biological usefulness beyond:

- gene/address identity;
- population pair-order prior;
- global cell state;
- source/operator/depth/support;
- matched wrong-cell/null structure.

### Open issue C — cross-process biological transport

The historical result establishes source-specific reliability and cross-source state-geometry survival, but the current V3 standard requires a sharper separation of biological versus measurement OOD and explicit held-donor alignment rules.

Any future TD41-derived representation should therefore be tested as:

1. within-source existence;
2. donor-balanced stability;
3. source-held-out / operator-held-out transport;
4. measurement sensitivity versus biological-evidence sensitivity.

## Current re-adjudication

TD41–TD43 remains:

`LIVE__S149_RETEST_ELIGIBLE`

and is provisionally the strongest historical candidate family for S149-aware salvage because:

- the signal was pre-frozen;
- pair sampling was label/source/outcome independent at TD41;
- structural support was common across all 42 operators;
- the key cell-specific excess was computed within each source;
- donor-balanced source scores were used;
- matched wrong-cell nulls explicitly measured shortcut performance;
- measurement reliability was independently reproduced 24/24;
- no target authority was ever falsely claimed.

This status is **not** a target selection.

## Next action

Reconstruct the four TD34 512-gene panels back to their original selection rule and data split. Classify that upstream selection as one of:

- `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE`;
- `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES`;
- `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`.

Do not execute a new TD41 outcome analysis before this genealogy is closed.

## Authority unchanged

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`TARGET_WINNER=NONE_QUALIFIED`

`REPRESENTATION_WINNER=NONE_QUALIFIED`

No optimizer or EMA update is authorized by this record.

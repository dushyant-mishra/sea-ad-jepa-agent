# TD59 corrected replay provenance addendum

Date: 2026-10-10

Status: `PROSPECTIVE_PROVENANCE_ADDENDUM__NO_EXECUTION_AUTHORITY__NO_TARGET_AUTHORITY__NO_TRAINING_AUTHORITY`

This addendum narrows only the executable-provenance rule for TD59 inside the corrected biological replay prefreeze. It does not change TD59 science, thresholds, panels, locality, nulls, or historical outcome.

## Historical provenance fact

The original TD59 local executor was bound before outcome to SHA-256:

`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`

The project later established that the exact original executor bytes and six original result JSON bytes were not recovered. The historical working archive ends at TD58.

Therefore future corrected replay must **not** claim recovery of the original TD59 executor bytes and must not require an impossible byte-for-byte rerun of a file that is no longer in custody.

## Existing scientific-statistic closure

The project already closed this replay gap prospectively enough for reproducible statistics using:

`target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py`

Frozen successor SHA-256:

`870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`

Controlling closure record:

`target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/TD59_REPLAY_CLOSURE_20260908.md`

Closure terminal:

`PASS_TD59_REPLAY_CLOSURE_BY_INDEPENDENT_RECONSTRUCTION__ORIGINAL_EXECUTOR_BYTES_NOT_RECOVERED`

That closure independently reconstructed the frozen TD59 statistic from the prospective contract and immutable historical inputs and reported exact equality for all 24 committed case rows on the three decision-bearing statistics:
- observed median donor local-triplet agreement;
- matched-null p95;
- matched-null maximum.

It also reproduced all 24 PASS booleans, six frozen pair-address hashes, and the structural/measurable donor counts.

## Corrected replay rule

For TD59 only:

1. preserve the original executor SHA as historical provenance;
2. preserve `original_executor_bytes_recovered=false`;
3. use the exact replay-closure successor SHA above as the executable historical-statistic reference for adapter qualification;
4. require an adapter-fed historical fixture to reproduce the replay-closure successor's decision-bearing outputs and TD59 terminal before any corrected values may be consumed;
5. never describe the successor as the original executor;
6. never use this provenance repair to alter the historical TD59 terminal or locality fraction;
7. no additional 50K locality-fraction tuning is permitted.

This addendum supersedes any ambiguous instruction that could be read as requiring recovery of the missing original TD59 executor bytes.

## Authority boundary

Nothing here authorizes:
- G6/G7 execution;
- corrected TD59 replay;
- target selection;
- TD60;
- training.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

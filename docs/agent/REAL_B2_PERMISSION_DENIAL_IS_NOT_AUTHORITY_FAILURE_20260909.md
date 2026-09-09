# Real B2 permission denial is not an authority failure — 2026-09-09

Claude's attempted real production B2 execution was blocked by the Claude Code auto-mode classifier.

That means:

- the production authority was not materialized;
- no 20,804-row population artifact exists from that attempt;
- there is no replay package to accept or reject;
- this is not evidence that the dataset failed;
- this is not evidence that the authority mechanism failed.

It is an execution-permission blocker.

## Correct handling

Do not route around the classifier by disguising a production run as a test command.

Instead:

1. Commit the production runner and replay verifier.
2. Ask for or use an allowed execution path.
3. Run the committed production command openly.
4. Preserve the produced artifacts and hashes.
5. Replay from disk.

## Review status implication

Until the run completes and replays:

`STOP_T0_R5_REAL_POPULATION_AUTHORITY_NOT_MATERIALIZED`

remains the correct status.

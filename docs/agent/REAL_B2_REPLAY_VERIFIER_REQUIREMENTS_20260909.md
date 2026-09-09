# Real B2 replay verifier requirements — 2026-09-09

The replay verifier must be independent of the production run's in-memory state.

## Inputs

- path to emitted raw-source population authority artifact;
- path to logical row authority artifact;
- expected source SHA;
- expected source byte count;
- expected logical row authority root;
- expected population raw-source root;
- expected row count `20804`.

## Required behavior

1. Read emitted artifacts from disk.
2. Recompute SHA-256 for every emitted file.
3. Recompute package root from emitted bytes.
4. Recompute population raw-source root from proof rows.
5. Recompute logical root from logical authority rows.
6. Compare stored, recomputed and externally expected roots.
7. Verify row count and proof identity match logical rows.
8. Verify no emitted field or header names pathology columns.
9. Verify `real_execution_ready` is false.

## Forbidden behavior

- Do not import or reuse the object returned by the production run.
- Do not trust console logs.
- Do not skip artifact hashing.
- Do not allow expected roots to be inferred from the artifact under test.

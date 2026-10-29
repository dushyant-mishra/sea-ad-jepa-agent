# ChatGPT repair of PR #479 A1–A3 against immutable Macha #481 — October 28, 2026

**Repair base:** Macha #481 exact head `957fa4a558ce2bd219b5c2dec6dad8f65dca81ab`, reviewing #479 exact head `ae762d7096a94ac663a0788f6f577ba404e37536`.

**Scope:** fixture-only mechanics. This repair does not accept D1/D2 for production, authenticate source rights, repair inherited #474 A4, resolve in-ledger gene aliases/off-ledger residual mass, or authorize real training.

## Repairs

### A1 — consumer now proves the published depth law

For each cell, the V2 consumer recomputes the sum of published `MEASURED_SCALAR` counts whose evidence right is in the code-pinned fixture base set and requires exact equality with every published `base_rights_normalization_depth`.

This rejects physical-total, depth+query, offset and scaled-depth forgeries without imposing the old physical `count <= library_size` semantics on teacher rows.

### A2 — student rights are no longer accepted from the view label alone

The fixture contract code-pins the base evidence-right set to `["RNA:BASE"]`, publishes that binding in the hashed view, requires exact equality at validation, and refuses any `MEASURED_SCALAR` student row whose `evidence_right` is outside that set.

This is deliberately **fixture binding**, not source issuer authentication. A future real V2/G7 contract still needs externally reviewed source/query rights.

### A3 — exact type dispatch

`_view_snapshot` now uses identity dispatch (`kind is str/int/bool`) rather than tuple membership that can invoke a payload metaclass `__eq__`.

## Preserved RED / limitations

- **A4 remains inherited RED**: empty-base refusal behavior in #474 still depends on withheld mass and is intentionally not changed here.
- In-ledger aliases can still carry query molecules under a base address while passing conservation.
- Current source-total equality still rejects genuine residual-mass rows.
- The producer still depends on the historical conservative conservation condition; this repair does not silently choose D1 or D2.
- No source, donor, physical measurement, query-rights issuer or feature mapping authentication is added.
- Teacher digests remain private-custody material; no teacher digest is added to the student view.

**Forward authorization:** NONE. Standing stop remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

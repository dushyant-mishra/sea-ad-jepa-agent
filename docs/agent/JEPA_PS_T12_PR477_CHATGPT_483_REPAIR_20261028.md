# ChatGPT repair of PR #477 against immutable Macha #483 — October 28, 2026

**Repair base:** Macha #483 exact head `48ec018735a095571a0bfaa25b33f9b9deb40b39`, reviewing #477 exact head `c83088de090bc4f2fc6bbee353c46070bcca7be5`.

**Scope:** production-synthetic canonicalization mechanics only.

## Repairs

1. `semantic_sha256` now uses exact type identity for bytes/bytearray/memoryview rejection rather than `isinstance`, so a payload-controlled `__class__` is not executed.
2. `_iter_rows` no longer uses `isinstance(rows, (list, tuple))`. Exact list/tuple are handled directly; list/tuple subclasses are identified from the concrete type MRO without reading the payload object's `__class__`, and rejected before their overridden iterator can run.
3. A `TypeError` raised while obtaining an iterator is translated to `CanonicalError` with `from None`, so the payload exception is not retained as a formatting-visible cause.

## Preserved limitation and blocker

- Ordinary live generators/iterables remain lawful and can execute producer code while rows are consumed. This is explicitly retained rather than silently changing the canonical API trust model.
- T2-D external scan issuer remains RED and is checked as expected RED in CI.
- No real source, biology, target, Stage4 or training authority is added.

Platform qualification is required on Ubuntu/Windows with NumPy 1.26 and NumPy 2.x.

**Forward authorization:** NONE.

Standing stop: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

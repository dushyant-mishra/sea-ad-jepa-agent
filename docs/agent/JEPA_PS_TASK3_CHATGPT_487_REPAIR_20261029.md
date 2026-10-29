# ChatGPT repair of PS Task3 PR #486 R3/R4 against independent #487 — October 29, 2026

**Repair base:** independent review PR #487 exact head `e8d0bd1523bb377bc8b832bf28df45047f33a817`.  
**Source under repair:** Macha PR #486 exact head `f17080516f77e79fb6f6cb44903cbabdb2a85dd7`.  
**Authority:** synthetic fixture mechanics only.

## R3 repaired — registry identity is part of the contract

`RealismContract` now carries:

- `observation_parameter_registry_version`;
- `observation_parameter_registry_sha256`.

Both are included in `PRODUCTION_SYNTHETIC_REALISM_CONTRACT_V2` semantic hashing. The executable contract requires exact equality to the current code-pinned registry identity. An old issued contract therefore cannot be silently reinterpreted under a later registry revision.

The public `frozen(...)` API does not accept caller-selected registry identity. It injects the current code-pinned version/SHA.

## R4 repaired — validate before canonicalization

`RealismContract.frozen()` now exact-type validates every caller field before the canonical serializer sees it. Container subclasses and payload objects are rejected without invoking payload iteration or payload `__class__` behavior.

Only after exact validation does the code construct the canonical V2 payload and hash it.

## Preserved boundaries

- Original #480 large-integer and registry-name repairs remain unchanged.
- `OBSERVATION_PARAMETER_SEMANTICS_BOUND is False`.
- `_AUTHENTICATED_CALIBRATION_REGISTRY` remains empty.
- Realism scope remains `SYNTH_DEBUG_ONLY`.
- No durable external calibration registry exists.
- No Task4 observation operator exists, so the seven parameter names are still quantity-family labels rather than reviewed generator semantics.
- No real calibration, target, Stage4 or training authority is created.

**Forward authorization:** Task3 fixture contract mechanics may proceed to independent review only.

Standing stop:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

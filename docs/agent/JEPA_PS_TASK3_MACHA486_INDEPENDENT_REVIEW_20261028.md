# Independent ChatGPT review of Macha PR #486 — October 28, 2026

**Source under review:** PR #486 exact head `f17080516f77e79fb6f6cb44903cbabdb2a85dd7`  
**Historical immutable reviewer floor:** PR #480 exact head `f39e605abc616cf59051a8bda9b0270cef5d6f09`  
**Authority class:** synthetic / fixture mechanics only. No real calibration, human biological, target-selection, FINAL, or training authority.

## Verdict

`REPAIR_REQUIRED__R3_REGISTRY_IDENTITY_UNBOUND__R4_FROZEN_PREVALIDATION_PAYLOAD_CODE`

The original #480 R1/R2 defects appear repaired in the #486 code: universe-statistic equality no longer round-trips through binary64, and adjustable realism parameters are restricted to a closed seven-name registry rather than an arbitrary `OBS_` prefix.

Independent review adds two new RED requirements.

### R3 — observation-parameter registry identity is not bound into each realism contract

#486 publishes:

- `OBSERVATION_PARAMETER_REGISTRY_VERSION`;
- `OBSERVATION_PARAMETER_REGISTRY_SHA256`;
- registry rows naming parameter, quantity family, and source clause.

But `RealismContract` and `_contract_parts()` do not carry either the registry version or registry SHA. Therefore the contract semantic identity binds only the selected parameter names. A later registry revision could preserve a name such as `OBS_DEPTH_SCALE` while changing its quantity-family/spec mapping without changing the old contract identity.

Required repair: bind the exact registry version and semantic SHA into the prospective contract and its digest, and verify them at every use. Do not silently reinterpret an already-issued contract under a later registry.

### R4 — `RealismContract.frozen()` canonicalizes caller payloads before exact-type validation

The classmethod constructs an unvalidated object, immediately calls `_contract_digest()`, and only afterward invokes the dataclass constructor that enforces exact types. The canonical serializer uses `isinstance`, so a caller object with payload-controlled `__class__` can execute code and raise a payload-selected exception before the firewall returns `CalibrationError`.

Required repair: validate exact container/scalar types and closed names before any canonical serialization or operation that can dispatch into caller code. The repair should preserve the existing exact numeric behavior and immutable #480 tests.

## Preserved positives / limitations

Independent probes preserve these positives:

- distinct large integer witnesses remain distinct;
- mathematically equal int/float values remain comparable without lossy pre-casting;
- NaN, infinities, and bools are rejected from numeric universe witnesses;
- malicious `str`-subclass mapping keys are rejected before validator hashing/comparison;
- registry rows are closed, version-labelled, and self-hashed;
- `OBSERVATION_PARAMETER_SEMANTICS_BOUND is False`;
- `_AUTHENTICATED_CALIBRATION_REGISTRY` remains empty;
- executable realism authority remains `SYNTH_DEBUG_ONLY`.

The seven registry names are therefore **not yet tied to actual Task4 observation-operator semantics**. The source clause authorizes observation-side quantity families in principle, but there is no reviewed generator/operator binding because PS Task4 is absent.

## Forward authorization

**NONE.** This review does not authorize real calibration, Task4, real human target qualification, or JEPA training. The project stop remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

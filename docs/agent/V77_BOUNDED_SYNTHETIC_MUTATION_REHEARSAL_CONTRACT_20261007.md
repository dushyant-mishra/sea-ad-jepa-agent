# V77 bounded synthetic mutation rehearsal contract — 2026-10-07

Status: **PROSPECTIVE / NOT EXECUTED / NON-PRODUCTION**

This contract defines the only bounded synthetic mutation rehearsal currently allowed to be implemented next. It does not authorize real-data training, production training, target selection, representation selection, or any scientific claim.

## 1. Purpose

Prove that the already-qualified joined path can execute exactly one intended optimizer update, then advance the EMA teacher only after that optimizer step is physically proven complete, persist the typed continuation, and reload deterministically.

This is a mechanical wiring rehearsal. It is not a biological qualification experiment.

## 2. Frozen lineage

- canonical runtime: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- shared qualification interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- joined ZERO_UPDATE base: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- provenance-V2 successor: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- pre-rehearsal freeze record: `0ec385889630b3a7f02caa489d95d988304ad9dd`
- 2K operator-smoke CI head: `c919d957de79a3866fdaeab3ae2ae5a0891d4859`, run `37695987219`, 128 passed
- corrected S174 replay: `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`, run `37693603160`, 146 tests / zero skipped
- corrected S174 current receipt head: `750cb83c8c0535cc67a70d58b62db5607bd7d01e`

## 3. Exact rehearsal data

Reuse the existing joined ZERO_UPDATE synthetic fixture exactly:

- 2 synthetic observations
- 4 synthetic gene addresses
- observation IDs: 101, 102
- donor IDs: D0, D1
- one synthetic source/operator identity
- same model-visible expression, measurement mask and hidden-target mask already used by `tests/integration/test_v77_canonical_zero_update.py`
- same `QualificationBatchV1` construction and exact V2 physical-binding proof rules
- same bound executed q-safety proof requirements

No corrected S174 real statistic, donor-bootstrap interval, cell-class label, pathology variable or protected outcome may enter the rehearsal inputs, loss, update rule, stopping rule or verdict.

## 4. Frozen runtime configuration

Use the same canonical reference-module configuration already used by the joined ZERO_UPDATE path:

- `width=16`
- `heads=4`
- `blocks=1`
- `ffn_width=32`
- `dropout=0.10`
- AdamW learning rate `1e-3`
- betas `(0.9, 0.999)`
- eps `1e-8`
- weight decay `0.01`
- init seed `8113002`
- update index: `0 -> 1`

EMA rehearsal configuration:

- presentation unit: `SUCCESSFUL_BASE_CELL_PRESENTATIONS`
- half-life: exactly `1000` presentations
- this half-life is **test-only mechanical configuration**, inherited from the existing EMA proof tests; it is not production authority and must not be reused as a production recommendation.

## 5. Mutation budget

Exactly one optimizer update attempt is permitted.

If successful:

- exactly 2 base-cell presentations are added to teacher age;
- online encoder parameters must change;
- predictor parameters must change through the same canonical optimizer ownership as the runtime;
- optimizer state must reflect the completed step;
- teacher parameters may change only after optimizer completion is proven;
- teacher age must become exactly 2 presentations;
- one child typed EMA-bound checkpoint/continuation may be created.

No second optimizer step is permitted in the same rehearsal.

## 6. Fail-closed behavior

If gradients are invalid, GradScaler skips the step, the guard rejects the step, checkpoint completion cannot be proven, provenance fails, q-safety fails, or any precondition fails:

- the run verdict is failure;
- teacher EMA must not execute;
- teacher age must remain 0;
- no completed child continuation may be minted;
- the failure receipt must be preserved.

A retry must use a new run identity and preserve the failed attempt; no silent overwrite or same-ID retry is allowed.

## 7. Required pre/post evidence

Record before and after:

- batch scientific-identity digest;
- adapter source digest;
- runtime source digest;
- q-safety proof digest;
- physical-bindings digest;
- online-parameter digest;
- predictor-parameter digest;
- teacher-parameter digest;
- optimizer-state digest;
- checkpoint digest;
- optimizer step count;
- teacher presentations seen;
- completed guard receipt digest;
- EMA configuration identity;
- presentation-EMA completion-proof digest;
- typed persisted-continuation digest.

## 8. Mandatory adversarial tests

Before the successful rehearsal test may be GREEN, tests must prove:

1. no physical-binding proof -> no mutation;
2. wrong consumed-values proof -> no mutation;
3. wrong adapter source digest -> no mutation;
4. wrong runtime source digest -> no mutation;
5. q-safety proof replayed from another batch -> no mutation;
6. rejected/nonfinite optimizer step -> no EMA and teacher age stays 0;
7. calling EMA before proven optimizer completion is rejected;
8. a second optimizer step in the same rehearsal is rejected;
9. V1 runtime mutation proof cannot promote this rehearsal;
10. restart with changed EMA half-life/configuration is rejected;
11. child checkpoint reload reproduces the persisted state deterministically;
12. receipt flags remain `training_authorized=False` and `production_promotable=False`.

## 9. Verdict

The only success verdict allowed is:

`PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION`

A PASS means only that one tiny synthetic update is physically connected through the existing canonical runtime and fail-closed proof chain.

It does **not** mean:

- the biological target is correct;
- the representation is useful;
- the corrected synthetic model is realistic;
- the EMA half-life is scientifically selected;
- real-data training is allowed;
- more than one update is allowed.

## 10. Standing scientific constraint after rehearsal

The corrected replay showed that no current arm reproduces the real cell-class contribution to pooled correlation (corrected T5 about 0.74; replayed arms about 1.02-1.21).

That constraint belongs to the **next synthetic biological design**. It must not be used to tune this mechanical rehearsal.

## 11. Authorization boundary

This contract authorizes implementation and testing of the single-step **synthetic-only mechanical rehearsal described above**. It does not itself assert that the rehearsal has executed or passed.

All real-data and protected-data boundaries remain unchanged.

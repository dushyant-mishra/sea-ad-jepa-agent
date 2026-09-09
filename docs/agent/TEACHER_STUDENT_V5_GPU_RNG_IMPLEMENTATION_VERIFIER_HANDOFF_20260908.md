# V5 GPU keyed-RNG candidate — independent implementation-verifier handoff

Status: `IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION`.

This packet is intentionally **not** an implementation-verifier PASS. Under
`MANDATORY_IMPLEMENTATION_VERIFIER_V1`, an independent verifier has veto power
and must reconstruct expectations from the frozen contract rather than accept
implementer test outputs.

## Controlling contract

- base main: `b26ddcd587c7b63c8a2f327d74a86620eef66868`;
- frozen V5 prototype root: `9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad`;
- exact RNG contract: `src/sea_ad_jepa/v5/keyed_rng_contract_v2.py`;
- contract SHA-256: `7e8dcf488c80b4fd9b31f2dce23c6395eeebff244016d78066f4da81e91b06f1`.

The implementation must preserve the V2 Philox4x32-10 address allocation:
run seed + update in the Philox key; stable uint64 cell key, canonical token,
feature, domain, view, layer and site in the counter. Tensor position,
microbatch ordinal, device ordinal and packing shape are forbidden inputs.

## Changed implementation surface

- `src/sea_ad_jepa/v5/keyed_rng_device_v1.py`
- `src/sea_ad_jepa/v5/keyed_dropout_device_candidate_v1.py`
- `src/sea_ad_jepa/v5/inactive_update_device_candidate_v1.py`
- bounded tests and CUDA qualification harness named in the candidate manifest.

The device encoder is required to have exactly the frozen reference/V4-compatible
parameter registry. The inactive update builder deliberately reuses the frozen
update/checkpoint chronology rather than introducing a second optimizer/EMA
implementation.

## Independent adversarial mutations that must be detected

At minimum, the verifier should independently construct attacks for:

1. swapped cell-key high/low words;
2. truncation of uint64 cell identity to signed-63 or low32;
3. token `-1` / gene `0` aliasing;
4. token `65,534` and feature `65,535` upper boundaries;
5. feature/token bit-field swap or overlap;
6. any insertion of tensor row/column, packing shape, device or microbatch ID;
7. Philox multiplier/key-schedule mutation in any of ten rounds;
8. signed-int64 multiply overflow in the uint32 high-word calculation;
9. float32/float64 GPU threshold comparison replacing the exact integer keep threshold;
10. probabilities at exact open-unit boundaries and immediate binary64 neighbors;
11. `p=0` / eval no-op behavior diverging from frozen reference validation order;
12. dense/packed row or token reordering changing masks;
13. candidate parameter registry divergence from frozen reference encoder;
14. teacher gradients, optimizer multi-step, EMA-before-step, or checkpoint cursor drift;
15. any document/code path claiming CUDA qualification, training authority, successor-u0 or TD60 before separate authorities exist.

The verifier must not use candidate PASS reports as expected values. Known-answer
Philox vectors and independently reconstructed V2 address words should anchor
expected outputs.

## Implementer evidence only

Local CPU/handoff-overlay replay at packaging time:

- frozen V5 governance audit PASS;
- frozen V4+V5 combined suite 164/164 PASS;
- candidate/RNG/inactive-update surface 35 PASS, 2 CUDA-only SKIP;
- CPU candidate update is bitwise equal to the scalar-reference update through
  optimizer step + EMA and through two-update checkpoint resume;
- CUDA qualification correctly fails closed because this environment has no
  CUDA device.

These observations are not an independent terminal.

# TD53/TD54 hash-bit forensic audit

Status: `TD54_PRIOR_CLOSURE_SUPERSEDED_AS_NOT_ESTIMABLE__TD53_NEGATIVE_TERMINAL_STANDS`

## Trigger

The prospective TD53 and TD54 documents define deterministic Rademacher signs using the phrase **"the first bit of SHA256(...)"** but do not specify bit ordering within digest byte 0.

The producing scripts used the least-significant bit of digest byte 0.

A standard alternative interpretation of "first bit" is the most-significant bit of digest byte 0.

Because this choice changes the generated random feature/target matrices, the terminal must be checked for robustness rather than silently assuming one convention.

## TD53 robustness

Producing LSB convention:
- observed Delta: 0.0784598063
- aggregate alignment passes narrowly
- donor recurrence: 12/16 PASS
- LOO robustness: 7/16 PASS
- terminal: FAIL

Independent MSB convention:
- observed Delta: **0.0776984555**
- matched-eval null max: **0.0783155490**
- aggregate alignment itself FAILS
- donor recurrence: **8/16**
- LOO robustness: **0/16**
- terminal: FAIL

Thus TD53's exact numerical route depends on bit convention, but the scientific negative terminal does not.

Binding TD53 interpretation remains:
`NO_DONOR_RECURRENT_QUADRATIC_REFERENCE_CONTEXT__TD53S_FAIL`.

## TD54 material ambiguity

Producing LSB convention:
- observed Delta: 0.0727701359
- matched-eval null max: 0.0727480751
- aggregate alignment narrowly PASS
- donor recurrence: **11/16**
- LOO robustness: **5/16**
- terminal: FAIL

Independent MSB convention:
- observed Delta: **0.0986780399**
- matched-eval null max: **0.0981476684**
- aggregate alignment PASS
- donor recurrence: **13/16**
- LOO robustness: **16/16**
- terminal: PASS

Therefore the TD54 scientific terminal is **materially determined by an under-specified hash-bit convention**.

The historical closure file is preserved unchanged for chronology, but its failure classification is superseded by:

`TD54S_NOT_ESTIMABLE__HASH_BIT_CONVENTION_MATERIAL_TO_TERMINAL`

No PASS or FAIL may be claimed from TD54 without a fresh prospective successor that explicitly fixes the hash-bit convention before outcome generation.

## Effect on TD55

TD55 remains scientifically admissible despite TD54 becoming NOT_ESTIMABLE because its materially different query-specific proxy hypothesis is already motivated by the independently valid TD52 and TD53 results:
- exact query-agnostic reference context in TD52 fails donor sign recurrence;
- fixed quadratic query-agnostic context in TD53 fails robustly under both reasonable bit conventions.

TD55 must not cite TD54 as negative evidence in future promotion claims.

No target authority or training authorization.

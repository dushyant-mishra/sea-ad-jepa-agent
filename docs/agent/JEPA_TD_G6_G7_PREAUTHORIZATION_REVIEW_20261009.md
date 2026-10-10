# JEPA Target Discovery — G6/G7 preauthorization review, self-audit corrected

Date: 2026-10-09

Status: `PREAUTHORIZATION_REVIEW_CORRECTED__G6_G7_STILL_UNAUTHORIZED__NO_VALUE_READ`

This review was performed while canonical G4/G5 remains pending on PR #248. It does **not** authorize any expression-value read, corrected-value materialization, corrected TD56/TD57B/TD57C/TD59 biological replay, target selection, TD60, Stage 4, or training.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Why this review exists

If the hardened G4/G5 value-blind preflight passes, the next possible operation would be the first corrected expression-value read. The dormant G6/G7 code was therefore audited before any owner authorization so authorization, if later granted, is not used to discover avoidable engineering defects.

## G6 purpose

G6 is an integrity check, not the biological replay. For the exact 25,000 historical Sample-A cells:

- HVS/SEA-AD values would be re-read by corrected physical-ID mapping;
- NPH52 remains the authenticated unaffected historical pass-through path;
- only the exact frozen 9,216 TD56–TD59 addresses are retained;
- HVS/SEA normalization remains `log1p(raw_count * 10000 / verified_whole_cell_library_total)`;
- historical detected-gene counts are diagnostic only.

G6 PASS remains:
`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Any whole-cell library mismatch remains terminal:
`STOP_TD_G6_SOURCE_LIBRARY_MISMATCH`

## G6 defect found before execution

Historical V1 decoded physical values with `int(round(float(v)))`. Because G4/G5 deliberately does not open expression arrays, this could silently turn a fractional/transformed value into an apparent integer raw count.

No G6 value read has ever been executed, so no scientific result was affected.

Hardened candidate:
`scripts/v5/materialize_td_relational_corrected_sampleA_v2.py`

V2 requires every HVS/SEA physical value to be finite, nonnegative, and exactly integer-valued before normalization. Fractional, NaN, infinite, or negative values fail closed.

Historical V1 remains lineage only:
`scripts/v5/materialize_td_relational_corrected_sampleA.py`

## Authorization defect found by self-audit and corrected

The first version of this hardening said that future authorization was “V2 only,” but reused the historical V1 runtime schema/token. That was not a sufficient mechanical boundary because the historical V1 loader could also consume that token.

The corrected design now gives the hardened path its own runtime authority surface:

- schema: `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`
- token: `AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY`
- exact G6 entrypoint binding: `scripts/v5/materialize_td_relational_corrected_sampleA_v2.py`
- exact G7 entrypoint binding: `scripts/v5/audit_td_relational_g7_s174_overlap.py`
- `training_authorized=false`
- `biological_replay_authorized=false`

The V2 wrapper monkey-patches both the historical V1 authorization loader and row decoder before invoking the preserved mechanics. Therefore an old V1 authorization is rejected by V2, and a future V2 authorization is not valid for the historical V1 loader.

The authorization template is still **template only**. No runtime authorization exists.

## G7 purpose

G7 is independent cross-lane corroboration against the authenticated S174 rebuilt cache. It uses every natural HVS/SEA Sample-A cell overlap and the exact 9,216 replay addresses, comparing raw integer counts with zero tolerance.

No extra cell or address may be selected based on values.

Possible terminals:

- `PASS_TD_G7_S174_EXACT_OVERLAP`
- `STOP_TD_G7_S174_CROSSCHECK_MISMATCH`
- `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`

## G7 defects found before execution

The historical implementation had two avoidable hazards:

1. zero natural overlap was labeled `NOT_ESTIMABLE` but returned process exit code 0;
2. S174 reference values were cast with `int(...)` without an explicit finite/exact-integer check.

The hardened G7 path now:

- loads the hardened V2 materializer/authorization surface;
- requires finite, nonnegative, exactly integer S174 reference counts;
- returns process success only for `PASS_TD_G7_S174_EXACT_OVERLAP`;
- returns non-success for both mismatch and `NOT_ESTIMABLE`;
- writes an immutable receipt.

`NOT_ESTIMABLE` is not a PASS.

## G7 address-universe self-audit

A self-audit questioned whether comparing all 9,216 replay addresses exceeded the S174 “checked set.” The underlying S174 rebuild implementation resolves this: rebuilt HVS/SEA cache matrices are stored in the full canonical `N_ADDR = 41,238` address space. The later 14,417-address V77 analysis universe is not the cache storage geometry.

Therefore all 9,216 frozen TD replay addresses can lawfully be cross-checked against S174 **after** G4/G5 has established that those exact addresses resolve one-to-one under the corrected mapping. G7 additionally checks that the S174 cache has 41,238 columns before comparison.

## Revised authorization template

Canonical template path:
`docs/agent/JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_20261007.json`

Current template schema:
`JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_V3`

It remains non-authorizing. A runtime authorization may be created only after:

1. canonical self-audit-hardened G4/G5 PASS;
2. review of the G4/G5 receipts;
3. a new explicit owner decision;
4. qualification of the #251 focused regression tests on the canonical/repository environment.

## What G6/G7 PASS would mean

G6+G7 PASS would support the integrity of the corrected value-reading path. It would **not** establish that the historical relational biology survived.

It would not:
- select a target;
- relabel TD57C;
- authorize corrected TD56/TD57B/TD57C/TD59 biological replay;
- authorize TD60;
- authorize training.

A separate owner decision remains mandatory after G6/G7 receipt review before biological replay.

## Ordered frontier

1. Macha runs canonical self-audit-hardened G4/G5 from PR #248.
2. Any failure is preserved and stops.
3. If G4/G5 PASS, return receipts; do not create a value authorization.
4. Review and qualify #251 regression tests against the then-current #248 base.
5. Only after a new owner decision may a V2 runtime authorization be created.
6. If authorized, run only hardened V2 G6 + hardened G7.
7. G6 mismatch, G7 mismatch, or G7 `NOT_ESTIMABLE` stops for review.
8. Even G6+G7 PASS stops before corrected biological replay for another owner decision.

## Verification qualification

No G6/G7 values have been read. No CI or canonical-machine test PASS is claimed for #251 at this time. The branch contains tests for V2-only authorization, strict raw integer values, immutable output, S174 shard hashes, overlap mismatch, and `NOT_ESTIMABLE` process failure. Those tests must execute before any future value-read authorization is acted on.

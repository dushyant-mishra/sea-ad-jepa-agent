# F1 review closeout status — 2026-09-11

Status: `IN_PROGRESS__DO_NOT_PROMOTE__REAL_F1_REMAINS_UNAUTHORIZED`

Branch: `fix/f1-review-closeout-20260911`

This file records the evidence state for the September 2026 F1 closeout. It is
not an execution authorization and it does not change any frozen scientific
authority.

## Reproduced review baseline

The independent-review closeout regression suite was run from a clean GitHub
Actions checkout at commit `3958f1ae384388423eef49fda87946743534b39d`.
All 13 closeout guards failed in the RED phase. This is reviewer-reproduced
evidence that the review findings were present in that candidate; it is not
proof that every guard was perfectly specified.

One guard was itself corrected before implementation: `_construct` is a class
method in `F1ProductionAdapter`, not a top-level function. The original test
helper searched only top-level functions, so it could not inspect the actual
method. The helper now walks the AST and requires exactly one matching
function/method. The underlying device/no-grad defect was independently
confirmed in the method body.

## First repair batch

Materialized by GitHub Actions at commit
`9dbc79a55e77f3f8aa18a5c8725bb3b2a6526fa5` after an asserted one-shot patcher
verified every expected source fragment before writing.

This batch addresses only repairs whose authority is unambiguous:

- prefreeze package construction reads immutable `HEAD:<path>` bytes, refuses
  dirty/staged/untracked inputs, and never stages caller files;
- producer frozen-source binding now includes the preflight executor and
  production-mechanics validator;
- external execution authorization requires an independently supplied trusted
  issuer -> authorization-root anchor; self-consistency is no longer treated as
  issuer authenticity;
- matched-null raw counts require an independently supplied expected counts
  digest before normalization; a caller-supplied identity can no longer make
  arbitrary raw counts authentic;
- runtime adapter tensors are created on the encoder device and the authoritative
  contextual-state constructor runs under `torch.no_grad()`;
- the successful production wrapper now invokes final sweep-completeness
  verification against the frozen assignment plan before returning success.

These changes remain subject to post-repair regression/adversarial testing. A
successful patch-materialization workflow is not itself GREEN evidence.

## QID authority gap — do not silently repair

This is an older F1 lineage issue and must not be conflated with the matched-null
causal control.

The independent review at
`b0db8ea07ae0a61b5a5d37c51e419d6b2a1044b4` required the numerical F1 effect to
be produced and replayed, but it did not identify a QID paired-wrong semantic
mismatch.

The successor repair commit
`dd078625c3537f5ff2c3f8c0b382ba2803b24ee2` made the production effect row
executable. In `scripts/v4/f1_real_producer_v1.py::_effect_row_from_states`, it
computed:

```python
own = cosine(correct["contextual"], teacher["contextual"])
wrong = cosine(null["contextual"], teacher["contextual"])
...
paired_wrong_similarity=wrong
```

At the same lineage point,
`scripts/v4/contextual_target_f1_preflight_executor_v1.py::qid_v2` defined only
`qid_margin = own_similarity - paired_wrong_similarity`; it did not define a
paired-wrong query selection rule.

Separately, `F1_EA35_REPAIR_RESPONSE_20260907.md` records that `S_null` is the
frozen donor-distinct matched-null substitution retaining recipient physical
state, evidence, query identity and operator/source. That is a causal null arm,
not automatically a wrong-query pairing.

Therefore the historical implementation aliases:

`paired_wrong_similarity := cos(S_null, T_true)`

without a recovered frozen authority establishing that a matched-null student is
the intended paired-wrong query for QID.

Current terminal for this item:

`NOT_MEASURABLE_QID_PAIRED_WRONG_AUTHORITY_NOT_RECOVERED`

Required next action is lineage recovery: locate a pre-existing frozen QID
paired-wrong query authority, or prove that the current V5/student-teacher lane
superseded or no longer consumes this QID definition. Do not invent a mapping,
do not reinterpret the matched-null map as a wrong-query map, and do not promote
a QID claim while this authority is absent.

## Remaining implementation review items

Still open after the first batch:

- resume must validate shard integrity, not merely sidecar existence;
- duplicate `(cell,q)` assignments must share expensive forwards while retaining
  assignment-level effect-row fanout;
- replay must require each expected persisted shard and verify it;
- replay must recompute forward identities from persisted content rather than
  trusting recorded identities;
- replay must recompute numerical effect values independently from persisted
  states;
- provenance must allow reviewed descendants only when all bound blobs remain
  byte-identical;
- QID paired-wrong semantics remain authority-blocked as described above.

No old review thread should be marked resolved until its repair has behavioral or
adversarial test evidence and surrounding-suite evidence. No real F1 execution
is authorized by this closeout work.

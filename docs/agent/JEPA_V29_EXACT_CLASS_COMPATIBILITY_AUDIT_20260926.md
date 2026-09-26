# V29 independent exact-class compatibility audit (PR149 successor)

**Status: SOURCE-AUDITED, NO CLOSURE, NO NEW SCIENTIFIC AUTHORIZATION.**
Immutable reviewed PR149 head: `938fe5d3a7288826fef86b2650fb3a9a21fd3794`.
Canonical main governance remains V25 at `c49b13bd75c2d23716c777336db8fbfc78c09cd0`. Read PR150's V28 takeover before this independent successor and consult the separately committed S9 retraction `e00ba4ad...`.

## What was checked
The six V27 candidates passed their *own* defining-class validators under PR149's exact-role audit. This audit adds a missing **consumer-class compatibility** check by parsing the exact `CANDIDATES` bindings and the actual `validate_current_v5_authority_closure_v2` imports, annotations and strict `typed` table, not guessing from filenames. All 33 ledger slots (32 upstream, 1 preexecution) must retain their order and no root may be prematurely marked closed.

**Confirmed class-version conflicts on the reviewed head:**
- `masking_rng_replay_authority_sha256`: V27 verified `MaskingRngReplayAuthorityV3`, while closure V2 **requires** `MaskingRngReplayAuthorityV1` through an `isinstance` guard.
- `masking_qualification_parameters_authority_sha256`: V27 verified `MaskingQualificationParametersAuthorityV3`, while closure V2 **requires** `MaskingQualificationParametersAuthorityV1` by the same hard type check.

A self-valid V3 document is **not an instance of V1**. Converting its digest or supplying a well-formed V1-shaped placeholder does not make it current training evidence. In addition, current branches contain masking design V2, run-contract V4, execution V4, budget V2, target-panel V3 and RNG V3, while the reviewed closure has other V1/V2 type dependencies. These are *potential further integration review seams*; no unissued version is silently selected.

**Status of the remaining four own-schema candidates:** no known class-version contradiction under these six checked call sites, but their parent-source bytes/cross-bindings and entire current closure remain unqualified. Do NOT upgrade these to four closed roots.

**Two raw-string slots:** the full104-substrate and observation-gradient-firewall arguments are `str` in the current closure; there is no authority to invent missing dataclasses. To qualify these, authenticate their exact role-specific source bytes, assert the expected cross-bindings and attach an appropriate receipt. The ZIP metadata root is **not** the raw expression block-manifest digest `66f589...`. No heavy source was rehashed by this audit.

**Remediation review gate:** choose one coherent, versioned successor closure reflecting the *actually prospective* production scientific decisions, validate the corresponding exact-current artifacts and inputs under each class's own validator and cross-binding, require executed qualification where the class does, then independently red-team role substitutions, stale V1 instances and all 33 root positions. Do not edit current closure merely to make a V3 object accepted; evaluate whether V3 scientific semantics (panel-free seed, FULL104 parameters) actually match the final experiment. PR149 historical receipts are immutable.

No rerun of PR146 or PR149's genuine byte-identical original calibration metadata replay is requested. Sept20 canonical dense-solver runtime is already qualified with `Library/bin` on PATH: S9 fully retracted; no historical scientific re-execution due to S9. No GPU current104 expression is present here, no reader_fit B1 contract or B2 closure, no protected N1 or G5 opening. Existing inline gradient firewall is real but missing-report/Adam/checkpoint tests belong to a separate engineering lane.

## Reproduction
```bash
PYTHONPATH=src:. python scripts/v5/v27_six_candidate_authority_audit_v1.py .
PYTHONPATH=src:. python scripts/v5/v29_class_compatibility_audit.py .
PYTHONPATH=src:. python -m pytest -q tests/test_v29_class_compatibility.py
# EXPECTED STOP, never run this as an ordinary green acceptance:
PYTHONPATH=src:. python scripts/v5/v29_class_compatibility_audit.py . --require-closure
```
A successful ordinary audit **reports two blockers**, not that it closed them. The separately invoked strict closure gate must refuse. The actual original PR149 six validators and test corpus should be run separately, not inferred from this new static consumer check.

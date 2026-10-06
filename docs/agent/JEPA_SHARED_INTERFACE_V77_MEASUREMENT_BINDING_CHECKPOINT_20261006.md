# Shared-interface / V77 measurement-binding checkpoint — 2026-10-06

## Why this checkpoint exists

Claude/Macha's iterative V77 audit exposed defects that the original shared qualification-interface design did not yet machine-enforce:

- S135: the observer recorded only a support count, not per-element measurability;
- S146: a positional `source_index` was interpreted under a differently ordered source roster, swapping SEA-AD and HVS support;
- S147: registry-relative operator attrition was applied a second time inside source coverage, double-counting missingness;
- S149: pooled real detection topology is strongly study/measurement-process dependent, so source/study structure must remain available for evaluation while being firewalled from unrestricted model input.

This checkpoint records the corresponding shared-interface repairs. It does not choose a replacement real-data calibration target.

## PR #223 exact implementation sequence

Branch: `shared-qualification-interface-v1-20261006` (draft PR #223)

1. `232eb79155c226dde533c60e24499c3409fbd5f2`
   - repaired `QualificationBatchV1` to be data-kind neutral;
   - real RNA no longer requires synthetic challenge provenance;
   - synthetic provenance is required only for synthetic batches;
   - adapter/environment digests fail closed;
   - provenance uses the actual batch data kind.
   - workflow `37541247623`: SUCCESS.

2. `92f45a160d06bd4005574f5982444290f0a3c234`
   - RED tests for source-order permutation, wrong operator-to-source mapping, support-count substitution, and reconstructed/ORed support.
   - workflow `37541394455`: expected RED because the proof types did not yet exist.

3. `de9692f84e5ef23ead36ddaef82b955855c098ea`
   - added `ObservationOperatorIdentityReceiptV1` and `MeasurementSupportReceiptV1`;
   - source index must resolve to its declared source name under the exact source roster;
   - operator IDs must map to each observation's declared source;
   - support receipt is constructed from actual producer and batch per-element support rows, which must match exactly;
   - support-count scalar or non-boolean support rows cannot substitute;
   - support rule and producer manifest are bound.
   - workflow `37541522880`: SUCCESS.

4. `d40e95198575267f18132cbfe4e96bf0a4c00363`
   - RED tests requiring operator/support receipt digests to be part of immutable scientific batch identity;
   - tests also require wrong measurement-mask digest and unbound operator context to fail.
   - workflow `37541657312`: expected RED, 3 failed / 117 passed, solely because the scientific identity did not yet carry those receipt digests.

5. `5f7cbc08f8ca081efdb311f0177fc9b17e554dd7`
   - added mandatory `operator_identity_receipt_digest` and `measurement_support_receipt_digest` to `QualificationBatchIdentityV1`.

6. `d584247414fe0dfbe52da79e5b756c6ce87999cc`
   - added mandatory `operator_identity_digest` and `measurement_support_digest` to end-to-end `QualificationProvenanceReceiptV1`.

7. `04ab3b4d7a2dfbd689eb32a52689e57d4086b638`
   - `QualificationBatchV1` now requires actual operator and support receipt objects;
   - validates operator/support/feature receipt digests against immutable scientific identity;
   - validates support observation ordering;
   - validates operator observation count;
   - validates support width against authenticated feature axis;
   - validates support-rule agreement;
   - validates measurement-mask digest against producer-proven support;
   - validates operator-context digest against operator identity;
   - provenance carries both proof digests.

8. Existing tests were migrated to the stronger contract rather than retaining the pre-S146/S147 API as historical spillover. Latest fully verified head before the final edge-case self-audit: `10961995f1794c40aebbc578c62f7c75ec3dbe4a`; workflow `37542142301`: SUCCESS.

9. `1bb227f7e8f5f0cf480299299a1d404ef0c4c98c`
   - final edge-case self-audit tests added for support observation-order mismatch, support feature-width mismatch, and operator/support rule disagreement.
   - CI state was pending when this checkpoint was written; update this record with the exact result before calling the milestone closed.

## V77 repository state independently observed

Remote branch `claude/v77-synthetic-premise-custody-20261005` remained at independently observed head:

`8497916e5a9d9b232597ac1891b6c630d3b17931`

That pushed head contains the S146/S147 downstream component detect/reject driver. The user-supplied Claude/Macha transcript contains additional later local work (within-cohort envelope work, strata validation, further defect-register updates, exploratory tournament work), but those later states were not yet visible on the remote at the time of this checkpoint and therefore remain transcript/local evidence until pushed and independently audited.

## S149 decision boundary

The shared interface now supports the identity/provenance structure needed to represent source/study/operator-aware qualification without leaking arbitrary study identity into model input.

However, this lane does **not** decide whether the replacement calibration target is:

- within-cohort envelopes,
- a production-mixture-weighted envelope,
- a hierarchical donor/study estimand,
- or another scientifically justified construction.

That choice belongs to the real-data scientific/reviewer lane and must be prospectively frozen. Previously viewed V77 generator arms become exploratory relative to a newly defined target; they cannot be retroactively counted as confirmatory evidence.

## Authority remains unchanged

- TRAINING = OFF
- STAGE_A_EXECUTION = OFF
- no optimizer/EMA mutation authorized by PR #223
- no representation winner selected
- no target winner selected
- no estimand selected
- no deciding real-data threshold selected
- TEST remains sealed
- Morabito remains protected

## Next actions

1. verify `1bb227f7...` exact-head CI;
2. if GREEN, record the measurement-binding milestone complete in the native-execution ledger;
3. re-check the Claude/Macha remote for later pushed S149/within-cohort receipts and independently audit them;
4. hand S149's scientific target question to the real-data qualification/reviewer lane;
5. finish whole-branch PR #223 audit before starting #221/#222 runtime convergence;
6. only after shared interface + runtime successor are qualified, implement the V77 adapter against this common contract.

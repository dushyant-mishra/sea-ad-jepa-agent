# Unified Task 11 finalizer / generated receipts / CI contract V1 — 2026-10-14

## Status

`ANALYSIS_ONLY__PREIMPLEMENTATION_CONTRACT__TASK11_NOT_STARTED`

This document refines accepted Task 11 with Task 0 F6–F9 and old Task 2 custody obligations. It creates no execution authority.

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

---

## 1. Finalizer is an authenticator, not an authority shortcut

The finalizer recomputes and indexes evidence that already exists. It cannot:

- invent a missing prerequisite;
- convert a blocked unit to ready;
- issue independent qualification to a unit that self-certified;
- change a challenge result;
- rescue a failed world;
- infer a target from prose;
- promote downstream certification to training eligibility.

If dependencies are incomplete, the finalizer emits the incomplete state and preserves the blockers.

---

## 2. Receipt index contents

The final receipt index must bind exact identities for at least:

```text
architecture_design_head
architecture_spec_digests
accepted_implementation_plan_identity
execution_manifest
population_access_policy
qualification_registry
active/revoked/superseded unit identities
sealed challenge genesis identity
sealed challenge current anchored head
sealed commitment/reveal receipts
CaseBundle/TruthBundle schema identities
mode-path equivalence receipts
known-truth qualification/rehearsal receipts
Target Qualification Bundle
downstream certification receipt
unsatisfied prerequisite set
runtime eligibility receipt or explicit absence
current global project authority
```

A historical receipt remains visible after revocation/supersession; active usability is represented separately.

---

## 3. Recursive authentication

Before publication, the finalizer must recursively recompute:

1. every canonical payload digest;
2. every parent receipt/artifact identity;
3. exact manifest/registry identities;
4. producer/executor/policy identities;
5. access receipt identities;
6. current active-lineage status;
7. sealed-custody head chain to externally anchored genesis;
8. TQB and downstream exact-consumption bindings.

A single moved/unverifiable mandatory parent invalidates the affected active receipt even if all final numbers are unchanged.

---

## 4. Sealed-custody completion requirements

Task 11 must implement the old Task 2 external obligations that belong at finalization:

### 4.1 Genesis / anchored head

- bind one externally anchored genesis identity per testbed/qualification lineage;
- require exact last published head on load/append/finalization;
- reject a re-chained/truncated history that does not match the external head.

### 4.2 Multiplicity

Final qualification receipts report:

- qualification draws/exposures for the exact method identity;
- total qualification draws/exposures across the whole lineage.

Method relabelling does not reset the second quantity.

### 4.3 Reveal regeneration

Before a sealed qualification receipt can be final:

- verify reveal preimage;
- regenerate every authorized realization;
- recompute content digests;
- require equality with the pre-exposure attestation.

### 4.4 Secret scan scope

Finalizer verifies secret-scan receipts cover the promised exact committed-tree set. A scan over only the current checkout is insufficient.

---

## 5. Unsatisfied-prerequisite preservation

The receipt index must include the complete active unresolved prerequisite set.

At minimum, if still unresolved, retain current classes such as:

```text
G8 statistical estimand/reference producer
G6 substantive margin/scale/qualification producer
geometry producer/eigengap/adverse null
R1 human identity-null producer
G2 static baseline/strata/reference producer
candidate support overlays
G7 content-enforcing evidence-right producer
R4/C6/C4 endpoint/support/reference producers
G12 candidate human support
real reference artifacts
controller/TargetPortfolio exact bindings
readiness matrix regeneration
historical Macha evidence registration
```

Finalization cannot hide blockers because a higher-level stage is blocked.

---

## 6. F6–F9 lifecycle preservation

Final receipt index must make these constraints queryable:

- representation scope `SUBSPACE_ONLY` where still current;
- technology invariance qualification state;
- matrix identifiability/unavailable matrix scope;
- multimodal same-vs-separate-nucleus provenance;
- independent-measurement versus RNA-derived-hypothesis boundary;
- FULL104 normalization/evidence-burden/estimability/metric-blindness obligations;
- withdrawn FULL104-G finding remains withdrawn;
- runtime safety prerequisites remain downstream of scientific certification.

No finalizer may collapse these into free-text limitations only.

---

## 7. Runtime eligibility boundary

If there is no valid active `RUNTIME_ELIGIBILITY_RECEIPT_V1`, then:

```text
TRAINING_ELIGIBLE = false
```

regardless of a valid `DOWNSTREAM_CERTIFIED` receipt.

If such a receipt later exists, the finalizer authenticates it but still does not create `TRAINING_AUTHORIZED`; project-scope training authorization remains a separate explicit owner transition.

---

## 8. CI requirements

Unified CI must run:

1. all `tests/v5/td_unified/` tests;
2. canonical compatibility vectors against the old Task 1 shared JSON-native byte law;
3. custody compatibility/invariant tests adapted from old Task 2;
4. exact registered-unit adapter/regression tests required by current manifest;
5. finalizer recursive verification;
6. static guards proving protected human candidate outcomes/reader_validation/reader_oracle values are not opened by the workflow.

CI success is evidence only. It does not change `qualification_stage` or global project authority.

---

## 9. Required hostile RED tests beyond accepted Task 11

```python
def test_finalizer_rejects_rehashed_truncated_ledger_against_external_head(): ...
def test_finalizer_reports_method_and_lineage_qualification_draw_counts(): ...
def test_finalizer_regenerates_revealed_realizations_before_qualification_receipt(): ...
def test_finalizer_rejects_secret_scan_receipt_for_wrong_or_incomplete_tree_set(): ...
def test_finalizer_preserves_all_unsatisfied_prerequisites(): ...
def test_downstream_certified_without_runtime_receipt_remains_not_training_eligible(): ...
def test_runtime_receipt_cannot_expand_scientific_target_or_representation_scope(): ...
def test_full104_withdrawn_finding_remains_withdrawn_in_final_index(): ...
```

---

## 10. Terminal state

`TASK11_FINALIZER_CONTRACT_FROZEN__RECURSIVE_AUTHENTICATION_AND_EXTERNAL_CUSTODY_ANCHORS_REQUIRED__TASK11_NOT_STARTED__GLOBAL_AUTHORITY_OFF`

# Unified Task 4 sealed challenge custody contract V1 — 2026-10-14

## Status

`ANALYSIS_ONLY__PREIMPLEMENTATION_CONTRACT__TASK4_NOT_STARTED`

This contract maps the controller-verified old PR #356 Task 2 custody/RNG substrate at exact head `ff597faf2182522a320ec5322f8db9b67c9c6094` into unified Task 4 requirements without inheriting historical synthetic authority or namespace.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Prerequisites before implementation:
- Task 0 independently accepted;
- unified Tasks 1–3 each frozen at independently reviewed exact heads.

---

## 1. Separation of development and final qualification

Two challenge classes are mandatory and orthogonal to qualification stage:

```text
DEVELOPMENT_CHALLENGE
SEALED_FINAL_QUALIFICATION
```

Development challenges are inspectable and may support debugging/fixture compatibility. They can never, regardless of pass rate, issue `KNOWN_TRUTH_QUALIFIED`.

Final qualification challenge identity must be frozen before exposure and must remain hidden where the challenge law requires hidden content.

No failed/exposed final world may be deleted, replaced, rerolled, relabelled as development, or excluded from multiplicity accounting.

---

## 2. `SealedQualificationCommitment` required bindings

Required semantic fields or equivalents:

```text
schema_version
qualification_identity
manifest_digest
registry_digest
unit_identity_or_pipeline_scope
challenge_family_commitment
realization_set_commitment
realization_budget
rng_contract_digest
expected_truth_class_commitment
adjudication_policy_digest
qualification_controller_identity
adjudicator_identity
producer_executor_identity_set_digest
casebundle_schema_digest
truthbundle_schema_digest
commitment_algorithm_identity
exposure_ledger_genesis_identity
parent_receipt_digests
authority_scope
```

Hidden specifications/nonces/preimages remain controller-side. Public commitment objects must not contain reversible or dictionary-attack-friendly unsalted encodings of a small hidden specification.

---

## 3. Reuse from old Task 2

Adapt/wrap these mechanics rather than reimplementing them casually:

- nonce floor >=256 bits;
- commit/reveal mismatch fail-closed;
- identity-keyed RNG;
- exact realization-set attestation;
- append-only custody ledger;
- exposure→fit/output-freeze→reveal ordering;
- linear successor lineage;
- post-exposure defect repair receives new identity and no inherited qualification;
- secret absence scan;
- no unique public withheld-only code path;
- method-local and lineage-wide qualification draw accounting.

Historical `JEPA-PRODUCTION-SYNTHETIC-*` digest domains are compatibility evidence only. Unified custody objects must bind unified Task 1 canonical/authority receipts.

---

## 4. One-genesis law

Every sealed testbed/qualification lineage has exactly one externally anchored genesis identity.

Creating a new ledger/root cannot erase:

- prior exposures;
- failed worlds;
- prior methods;
- prior qualification draws;
- a revealed family;
- supersession or defect history.

A new scientific testbed is possible only through an explicit new-testbed authority action whose parent history records why it is scientifically distinct. It is never a reset button for an exposed failed qualification.

---

## 5. Externally anchored head law

The custody ledger's internal hash chain is insufficient because a consistently re-chained prefix can hide a tail.

Therefore every decision-bearing ledger append must produce a head receipt whose identity is anchored outside the mutable ledger object.

Every subsequent append/load must bind/verify the last published expected head.

Required hostile cases:

```python
def test_truncated_but_rehashed_ledger_fails_against_published_head(): ...
def test_fresh_ledger_cannot_reset_exposure_history(): ...
def test_stale_controller_head_cannot_append(): ...
```

---

## 6. Exposure and output-freeze law

An exposure record must bind:

```text
exact qualification identity
exact challenge realization-set identity
exact method/producer/executor identity
manifest/registry identities
exposure class
ledger head before exposure
ledger head after exposure
```

A reveal is lawful only after every decision-bearing output required by that challenge class is irreversibly frozen and content-addressed.

For pipeline qualification this includes the normal TD/controller/TQB output before TruthBundle adjudication.

Truth cannot be consulted to decide whether an output is “complete enough” to freeze.

---

## 7. Reveal regeneration law

Commitment verification alone is insufficient.

At reveal/finalization, the system must:

1. verify the commitment/preimage;
2. regenerate every authorized realization using the revealed root/specification and frozen generator/observation identities;
3. recompute each realization content digest;
4. compare against the pre-exposure realization-set attestation;
5. fail the qualification if any realization cannot be regenerated exactly or has moved.

No regeneration mismatch may be repaired in place under the same qualification identity.

---

## 8. Multiplicity law

Every qualification receipt must report both:

- draws/exposures for the exact method identity;
- all qualification draws/exposures across the whole lineage regardless of method relabelling.

A method code/configuration digest change does not reset lineage-wide multiplicity.

A trivial or cosmetic generator change does not create a clean qualification history.

---

## 9. Secret-scan law

For each sealed secret/preimage required to remain absent from public history:

- scan an exact export of every published committed tree in scope;
- do not rely on a dirty checkout, sparse checkout, untracked-file view or only the latest tree;
- bind tree identity, scan algorithm identity and public commitment to which secret was scanned;
- public receipt contains absence boolean/tree identity/counts only, never secret or matching path.

A scan of an empty/incomplete tree fails closed.

Old Task 2 scanner residual limitations remain explicit; scanner success is an evidence layer, not a mathematical proof that no arbitrarily encoded secret exists.

---

## 10. Generator-defect repair law

A post-exposure repair requires:

```text
new generator/challenge identity
explicit defect record
exact parent exposed identity
affected components/dimensions
review evidence
no inherited qualification stage
new sealed final challenge set
new multiplicity lineage entry
```

A defect record is a declaration until independently reviewed. Software accepting the shape of a defect record cannot self-establish the scientific truth of the claimed defect.

---

## 11. Required RED tests beyond accepted Task 4 plan

```python
def test_new_genesis_cannot_reset_exposed_lineage(): ...
def test_external_head_anchor_detects_tail_truncation(): ...
def test_method_relabel_does_not_reset_lineage_draw_count(): ...
def test_reveal_requires_regenerated_realization_content_match(): ...
def test_secret_scan_receipt_binds_exact_committed_tree_not_worktree(): ...
def test_defect_record_form_does_not_self_qualify_defect_truth(): ...
def test_final_qualification_receipt_reports_method_and_lineage_multiplicity(): ...
def test_truthbundle_is_not_readable_before_normal_output_freeze(): ...
```

---

## 12. Terminal state

`TASK4_SEALED_CUSTODY_CONTRACT_FROZEN__OLD_TASK2_MECHANICS_MAPPED_WITHOUT_AUTHORITY_INHERITANCE__TASK4_NOT_STARTED__NO_SEALED_EXPOSURE`

# Unified Tasks 1–4 / old PR #356 consolidation adapter contract V1 — 2026-10-14

## Status

This is a controller-side preimplementation contract. It does **not** authorize unified Task 1, old synthetic Task 3/4, sealed qualification, human execution, or training.

Global authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Observed old PR #356 implementation source:

- branch: `implementation/production-synthetic-v3-1-1-20261014`
- exact head: `ff597faf2182522a320ec5322f8db9b67c9c6094`
- controller review PR: #382
- focused review run: `38644641042`, job `116128364543`, `332 passed in 8.94s`
- inherited integration run: `38644640881`, success

Task 0 remains independently unaccepted; this document freezes only the future migration law.

---

## 1. Core consolidation decision

Old PR #356 Tasks 1–2 are **shared implementation substrate**, not completed unified Tasks 1–2.

The unified lane must preserve one scientific canonical encoding and one authority model. Therefore:

1. the old Task 1 canonical **byte serialization law** is migrated as the compatibility baseline;
2. unified receipt digests use unified domain separation and unified schemas, not historical `JEPA-PRODUCTION-SYNTHETIC-*` authority labels;
3. old Task 2 custody/RNG mechanics migrate primarily into unified Task 4 sealed challenge custody and later finalizer/whole-pipeline obligations;
4. unified Task 2 remains a new `TD_EXECUTION_MANIFEST_V1` + population/access-law implementation;
5. no old synthetic winner/gate/controller authority survives the merger.

---

## 2. Old Task 1 → unified Task 1 mapping

### 2.1 Reuse exactly as behavioral specification

The following old functions define tested behavior that the unified implementation must preserve where applicable:

- `canonical_json_bytes(obj)`
- `raw_sha256(data)`
- `load_canonical_json(data)`
- `semantic_text_sha256(raw)`
- `semantic_json_file_sha256(raw)`
- `ordered_registry_digest(rows, identity_keys)`
- `semantic_row_set_sha256(rows, identity_keys)`

The migration target is **behavioral equivalence**, not import-path authority.

### 2.2 Unified wrappers/new authority functions

Unified Task 1 still implements:

- `canonical_bytes(payload)` — uses the migrated canonical byte law;
- `canonical_sha256(payload)` — unified domain-separated scientific-object digest;
- `verify_scientific_receipt(receipt, object_resolver)` — recursive payload/parent verification;
- `QualificationStage`;
- `ActiveLineageStatus`;
- `AuthorityRecord`;
- required `authority_scope` validation.

Old `semantic_sha256` is not, by itself, the unified scientific-receipt authority because its domain is historical synthetic-specific.

### 2.3 Mandatory compatibility tests

Before unified Task 1 can be GREEN, add known-answer and cross-implementation tests proving:

- identical supported objects produce byte-for-byte identical canonical JSON bytes under old and unified encoders;
- CRLF/CR normalization, missing-value, bool/int, int/float, negative-zero and non-finite behavior match;
- duplicate normalized keys fail in both implementations;
- nonzero float-underflow-to-zero fails in both strict loaders;
- the 41,238-row ordered registry behavior stays order-sensitive;
- scientific row-set identity remains storage/shard-order invariant;
- old semantic digest domains and new unified receipt digest domains are **different by design** even when they consume identical canonical bytes.

A compatibility mismatch is a Task 1 blocker; do not silently choose one implementation.

### 2.4 Forbidden shortcut

Do not implement unified Task 1 as:

`from scripts.production_synthetic.canonical_v1 import semantic_sha256 as canonical_sha256`

That would collapse a historical synthetic namespace into unified authority and omit A1/A9 receipt/parent/state/scope requirements.

---

## 3. Old Task 2 → unified Task 4 / finalizer mapping

### 3.1 High-value reusable mechanics

Candidate mechanics to adapt and wrap:

- nonce floor and shape checks;
- `commit_secret` / `verify_reveal`;
- nonce/root commitments;
- scientific-identity-keyed RNG derivation;
- realization-set attestation;
- append-only custody ledger semantics;
- exposure → fit-output-freeze → reveal ordering;
- linear successor lineage;
- post-exposure defect-repair disposition with no qualification inheritance;
- secret-absence scanning;
- no-unique-withheld-public-code-path attestation;
- per-method and lineage-wide qualification-draw accounting.

### 3.2 Unified integration requirements

These mechanics cannot enter the unified lane unchanged as authority. They must be wrapped so that every custody object binds:

- unified canonical payload identity;
- exact unified manifest digest where applicable;
- unified qualification registry identity/stage/status/scope;
- challenge identity and exposure class;
- adjudicator/controller identity;
- immutable parent receipt lineage.

### 3.3 Deferred obligations that become mandatory unified tests

The old module explicitly records obligations it cannot prove internally. They become mandatory later-task requirements:

1. **single genesis per testbed** — no new ledger root may bypass prior exposure;
2. **externally anchored head** — publish/verify ledger head after every entry;
3. **multiplicity accounting** — report both method-local and lineage-wide qualification draws;
4. **reveal regeneration** — regenerate every realization from revealed root and verify content digest;
5. **full-tree secret audit** — scan exact committed trees for every published commit, not sparse/dirty working copies;
6. **defect independent review** — defect records are declarations until independently adjudicated.

Loss of any one of these obligations during migration is a blocking regression.

---

## 4. Unified Task 2 remains new work

Old synthetic Task 2 does **not** satisfy unified Task 2.

Unified Task 2 must newly implement:

- `TD_EXECUTION_MANIFEST_V1`;
- `PopulationAccessPolicy`;
- `ProducerAccessReceipt`;
- deterministic cross-fitting within `reader_fit`;
- protected `reader_validation` / `reader_oracle` denial under current authority;
- actual partition/access-class enumeration by producers;
- fail-closed invalidation when forbidden data were read even if the numerical output is correct;
- exact binding of code/policy/schema/registry/population/controller/gate/reference identities.

No custody/RNG GREEN result can promote these manifest/access requirements.

---

## 5. Task 3/4 old-branch control

Current controller instruction supersedes the historical broader sequence operationally:

- old Task 3: **DO NOT START**;
- old Task 4: **DO NOT START**;
- old Tasks 5–12: **NO INDEPENDENT CONTINUATION**.

The requirements from old Task 3 calibration/provenance and old Task 4 biology may still be migrated as design/test obligations into the unified architecture after Task 0 acceptance. No implementation head is required from the old branch to preserve those requirements.

---

## 6. Exact adoption sequence after independent Task 0 acceptance

1. Freeze exact source head `ff597faf2182522a320ec5322f8db9b67c9c6094` as historical reusable substrate evidence.
2. Start unified Task 1 RED-first on the accepted unified implementation branch.
3. Add old↔unified canonical compatibility tests before copying/adapting encoder logic.
4. Implement unified canonical bytes + receipt recursion + authority model.
5. Independently review/freeze unified Task 1 exact head.
6. Implement unified Task 2 manifest/access law from scratch using Task 1 primitives.
7. Independently review/freeze unified Task 2 exact head.
8. Implement unified Task 3 registry.
9. Only after Tasks 1–3 are frozen, adapt old Task 2 custody mechanics into unified Task 4 challenge custody with unified identities.
10. Preserve the six deferred custody obligations into Task 4/9/11/12 tests and receipts.

---

## 7. Stop conditions

Stop immediately if any implementation attempts to:

- treat old Task 1/2 PASS strings or CI as unified authority promotion;
- reuse a synthetic-specific digest namespace as the unified receipt namespace without an explicit compatibility/domain decision;
- import old synthetic gate/controller winner authority;
- make `reader_validation` or `reader_oracle` available through a generic held-out flag;
- start old Task 3/4 in parallel;
- drop the old custody module's explicitly deferred external obligations;
- claim Task 0 accepted without the required independent review.

Terminal controller state for this contract:

`PR356_TASK1_2_REUSE_LAW_FROZEN__UNIFIED_TASK1_NOT_STARTED__TASK0_INDEPENDENT_ACCEPTANCE_STILL_REQUIRED__NO_OLD_TASK3_4_START__NO_AUTHORITY_CHANGE`

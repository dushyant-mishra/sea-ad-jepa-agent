# Unified Task 3 B3 Actor-Registry Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Macha T3-B3 by replacing self-declared free-string actor independence with a closed, digest-bound actor registry and registered role identities.

**Architecture:** Add `actor_registry_sha` to the Task 3 registry state and canonical payload. The referenced `ACTOR_REGISTRY` is an exact canonical object containing a closed set of logical actor IDs and role-specific identity digests. Privileged actors are accepted only when their exact role object is present in that registry. Independence is compared by registry logical actor ID, not by free strings or object digests. Actor IDs use a strict ASCII grammar. External prerequisite evidence must name a registered evidence issuer; content-validation receipts must name a registered content validator. B5 will subsequently make the registry binding replay/anchor-immutable; B3 itself must ensure that arbitrary new controller/reviewer/validator objects are not authorized merely because they hash correctly.

**Tech Stack:** Python 3.11, pytest 9.1.1, canonical SHA-256 objects, existing Task 3 registry/schema/test fixtures.

**Spec:** Independent Macha review head `869ca777a498181c519ccfc04b8bf5db0f2888c7`, blocker T3-B3.

## Global Constraints

- Task 3 remains rejected until independent exact-head Macha recheck accepts it.
- Task 4 remains blocked.
- B1/B2/B4 repairs must remain green.
- B5 remains intentionally RED during this batch.
- Do not solve aliases with `.strip()`, case-folding, Unicode normalization, or other free-string heuristics alone.
- A syntactically valid but newly minted actor (for example `minted-by-producer-1`) must still be refused because it is absent from the closed registry.
- The actor registry is custody metadata only; it grants no scientific/training authority.

## Actor registry contract

Canonical object:

```text
{
  "object_role": "ACTOR_REGISTRY",
  "registry_schema": "TD_ACTOR_REGISTRY_V1",
  "actors": [
    {
      "actor_id": <strict ASCII canonical logical ID>,
      "role_identities": {
        <role>: <exact sha256 of role-specific actor object>
      }
    }
  ]
}
```

Rules:

- Exact top-level and entry fields; actor list non-empty and sorted canonically by `actor_id`.
- `actor_id` is ASCII only, no whitespace, strict grammar `^[A-Za-z0-9][A-Za-z0-9:_.-]*$`.
- Actor IDs are unique.
- Role identity digests are exact 64-hex and roles come from a closed role set.
- A role-specific actor object must canonical-hash to the bound role identity and its `actor_id` must equal the registry entry.
- Controller/reviewer/validator/evidence-issuer identities not in the registry fail closed.
- Controller, reviewer, validator and evidence issuer must be logically distinct from the unit producer/executor where required.

Closed privileged roles for this Task 3 repair:

- `SCIENTIFIC_PRODUCER`
- `SCIENTIFIC_EXECUTOR`
- `QUALIFICATION_CONTROLLER`
- `INDEPENDENT_REVIEWER`
- `CONTENT_VALIDATOR`
- `PREREQUISITE_EVIDENCE_ISSUER`

---

### Task 1: Extend RED evidence before production repair

**Files:**
- Modify: `tests/v5/td_unified/test_registry_v1_macha_rejection.py`
- Create: `tests/v5/td_unified/test_registry_v1_macha_b3_registry.py`
- Modify: `tests/v5/td_unified/registry_v1_dependency_fixtures.py` only for reusable test construction helpers, not to make attacks pass.

- [ ] **Step 1: Preserve the five existing alias/self-mint attacks against a registry that trusts only the legitimate controller/reviewer identities.**

Expected before repair: all five still succeed and therefore fail their tests.

- [ ] **Step 2: Add unregistered evidence-issuer attack.**

A well-shaped `PREREQUISITE_EVIDENCE` object from an unregistered issuer must not satisfy an external prerequisite.

- [ ] **Step 3: Add unregistered content-validator attack and registered positive control.**

A well-bound content-validation receipt from an unregistered validator must fail; the same receipt from the exact registered validator must pass when all other readiness conditions are valid.

- [ ] **Step 4: Add malformed actor-ID registry attacks.**

At minimum: leading/trailing whitespace, non-ASCII punctuation, duplicate actor IDs, and unknown role names are rejected when resolving the actor registry.

### Task 2: Implement closed actor-registry validation

**Files:**
- Modify: `scripts/v5/td_unified/registry_v1.py`
- Modify: `schemas/target_discovery/unified_v1/td_qualification_registry_v1.json`

- [ ] **Step 1: Add `actor_registry_sha` to registry state and canonical payload.**

Promotions/revocations and external evidence validation require a non-null, exact 64-hex actor-registry binding.

- [ ] **Step 2: Implement exact actor-registry parser/validator.**

Resolve by digest, verify canonical hash and role, exact fields, strict actor grammar, unique IDs, closed role set and exact role digests.

- [ ] **Step 3: Resolve privileged actors through registry membership.**

Producer/executor/controller/reviewer/revocation-controller identity checks use registered logical actor IDs. Unknown role objects fail even if their self-declared shape/hash is internally valid.

- [ ] **Step 4: Bind prerequisite evidence and content validators to registered issuers.**

External prerequisite evidence contains `issuer_identity_sha`; resolve it as registered `PREREQUISITE_EVIDENCE_ISSUER`. Content receipts resolve `validator_identity_sha` as registered `CONTENT_VALIDATOR`. Enforce required independence from the unit producer/executor.

### Task 3: Migrate legitimate synthetic fixtures without weakening attacks

**Files:**
- Modify: `tests/v5/td_unified/registry_v1_dependency_fixtures.py`
- Modify only affected Task 3 tests that represent legitimate actor/evidence issuance.

- [ ] **Step 1: Add helpers that create a closed actor registry from explicit trusted actor objects.**

Never auto-register arbitrary objects merely because they appear in the resolver used by a hostile test.

- [ ] **Step 2: Bind legitimate C1/R1 (or the local test's intended legitimate actors), producer/executor identities, evidence issuer and content validator explicitly.**

- [ ] **Step 3: Keep hostile alias/minted actors in the resolver but outside the bound registry.**

This distinction is the core B3 security property.

### Task 4: Verify partial GREEN and preserve B5 RED

- [ ] **Step 1: Run B3-focused tests.**

Expected: five alias/self-mint attacks plus evidence/validator attacks pass by refusal; registered positive controls pass.

- [ ] **Step 2: Run `python -m pytest -q tests/v5/td_unified/test_registry_v1*.py`.**

Expected after B3: only B5/H5 and B5/H6 remain RED.

- [ ] **Step 3: Run dedicated frozen Task 2 suite and broader unified regression folder.**

Dedicated Task 2 remains green. Broader folder may remain red only on B5.

- [ ] **Step 4: Record exact commit/run evidence in successor ledger.**

Do not freeze Task 3 or advance Task 4.

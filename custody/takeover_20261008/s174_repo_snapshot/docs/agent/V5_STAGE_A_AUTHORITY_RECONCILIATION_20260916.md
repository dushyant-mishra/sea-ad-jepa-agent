# V5 Stage-A authority reconciliation — 2026-09-16

Supersedes the blocking sections of `V5_STAGE_A_REGISTRY_BINDING_FAIL_CLOSED_CONTRACT_20260916.json`
for REG-1, REG-2, REG-4, REG-5. Companion to `V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json`
(authority digest `28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676`).

No provider implemented. No training. No `D_shared`. FULL104 read-only.

---

## REG-3 — semantic ruling (decided from source, not from the field name)

| item | evidence |
|---|---|
| exact field | `identity_is_audit_metadata_not_model_input: True` |
| parent object | the `contract` dict in the Phase-2 expression materializer |
| producing artifact | `docs/history/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902/source_snapshot/materialize_full104_phase2_expression.py:112` |
| surrounding fields | `cells`, `sample_level`, `donors`, `operators`, `addresses`, `block_rows`, `normalization_deferred`, then run-governance flags `original_mixed_nph_denied`, `no_validation_oracle_dev_sealed_pathology`, `no_optimizer_ema_lambda_query_schedule_gpu_mechanics_or_training` |

**What "identity" demonstrably refers to.** The producer uses the word four times, and every
other use is cell/row identity:

- L217 `raise RuntimeError(f"H5 row identity mismatch: {matrix_id}")` — guarding a comparison of
  `canonical_cell_id` and `donor_id`
- L251 "validates every block's exact **selection-row and canonical-cell identity**"
- L293 `raise RuntimeError(f"NPH block identity mismatch: {key}")`

And the per-block meta file the script writes carries exactly:
`selection_row, canonical_cell_id, donor_id, expression_row, primary_row_weight, source_library`
— per-cell identity and provenance. No address-level identity is written at all. Addresses appear
in the same contract dict separately, as the geometry fact `"addresses": ADDRESS_N`.

**Ruling.** The flag scopes **per-cell identity metadata** — `canonical_cell_id`, `selection_row`,
`donor_id`, `expression_row` — declaring those audit-only rather than model input. This is option
**E** of the offered list, not A–D as worded.

**What it does NOT establish.** It says nothing whatever about the molecular address index. It
does not authorize gene annotation, source identity, or a per-address biological memory. The
apparent conflict flagged in the prior audit dissolves: the contract was never prohibiting the
address index.

**Provider implication.** The address index is usable as a query key. The three per-cell identity
columns are now explicitly listed in `PROHIBITED_FIELDS` and enforced by test.

### `REG-3_RESOLVED__ADDRESS_INDEX_LAWFUL`

No new rule was invented to reach this; the ruling follows from the producer's own usage.

---

## REG-2 — forensic reconciliation, and a correction to my own prior audit

My previous audit called this "three inconsistent role names" and treated all three as a defect.
**That was too harsh and partly wrong.** Evidence:

- `base_training_estimand_recovery_v1.py:21` freezes
  `EXPECTED_SUPPORT_ELIGIBILITY_SHA256 = "7d61ed7b…"` **in code**.
- `current_authority_closure_v1.py:29` *enforces*
  `support_estimability.measurement_support_authority_sha256 == representation.support_authority_sha256`.

So three of the four bindings are one coherent semantic role — the **measurement-support root** —
asserted in three authorities with equality deliberately enforced by the closure. That is correct
engineering, not drift.

| field | artifact | verdict |
|---|---|---|
| `support_authority_sha256` (primary representation) | registry csv | **LEGITIMATE** — measurement-support root, closure-enforced |
| `measurement_support_authority_sha256` (support estimability) | registry csv | **LEGITIMATE** — same root, closure-enforced |
| `support_eligibility_authority_sha256` (base-training estimand) | registry csv | **LEGITIMATE** — same root, frozen in code |
| `registry_observation_state_binding_sha256` (feature parents) | registry csv | **MISLEADING AND INCOMPLETE** |

Answering the six questions posed:

1. Yes — `7d61ed7b…` is the molecular-address registry (re-hashed from the file: MATCH).
2. Yes — it is also legitimately the support-eligibility root; the registry carries
   `measurement_support_provenance` and `contributing_source_*`. One artifact, two lawful roles.
3. The field name implies a registry↔observation-state binding.
4. **It is misnamed and incomplete**, recording only the registry side.
5. It is *not* the wrong hash — the registry hash is correct for the registry side.
6. It is best read as a **composite relationship recorded with one of its two hashes**.

The decisive gap: the observation-state artifact `852cb3ec…` is bound **nowhere** by hash, even
though the 17,186 common core derives from it.

**Handled by supersession, not rewriting.** No Sept-15 artifact was edited. The new authority
binds `ADDRESS_REGISTRY` and `OPERATOR_ADDRESS_OBSERVATION_STATE` as separate artifacts and
records original artifact, original SHA, original role, defect, corrected role, corrected
binding, remaining valid scope, and forbidden-for-new-provider-binding.

---

## REG-1 / REG-4 — canonical authority and custody

`CanonicalAddressRegistryAuthorityV1` binds the registry by **content and invariants**, never by
path. Re-verified live against the real file: sha `7d61ed7b…` MATCH, 41,238 rows MATCH, index
contiguous/strictly increasing True, ids unique True (41,238 distinct); `verify_artifact` returns
True on the real artifact and False on a tampered hash.

Fail-closed on: hash mismatch, row-count mismatch, ordering mismatch, duplicate ids. The 24.9 MB
registry is **not** committed to git. `informative_path` is excluded from `canonical_digest()`, so
a drive letter cannot change authority identity — asserted by test.

Role-splicing defence is enforced: registry, observation-state and block-manifest hashes must be
mutually distinct, and the provider authority refuses a raw artifact digest where an authority
digest is required.

---

## REG-5 — enumerated policy vocabulary

`TargetAddressQueryAuthorityV1` accepts any nonempty string. Proven by test: `"anything"`,
`"TD60"`, `"historical_provider"`, `"trust_me_shared"`, `"TD57"`, `"TD59"` all passed.

`CurrentTargetAddressProviderAuthorityV1` accepts only:

| field | approved value |
|---|---|
| `query_provider_id` | `V5_SHARED_ADDRESS_QUERY_PROVIDER_V1` |
| `parameter_sharing_policy_id` | `SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1` |
| `gradient_policy_id` | `CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1` |
| `replay_policy_id` | `FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1` |

Enumerated, plus an independent guard rejecting any value containing `TD57`/`TD59`/`TD60`. No
per-address independent table is approved — that would be an imported biological memory and needs
its own authority. **Not frozen here:** width, depth, geometry, mask fraction, optimizer, EMA
timescale, seed, proposal law.

The frozen `target_address_query_authority_v1.py` is untouched; this is a successor.

---

## Authority hierarchy

```
FULL104 substrate (block manifest 66f589e5…)
  └─ canonical address-registry authority (28b20a45…)
       └─ current target-address provider authority (enumerated policy)
            └─ provider runtime/query artifact          [NOT IMPLEMENTED]
                 └─ teacher/EMA + replay + gradient qualification   [UNPROVEN]

canonical address registry  +  operator-address observation state (852cb3ec…)
  └─ support / estimability logic

FULL104 molecular features
  └─ VALUE_ONLY_256 primary representation
```

Four distinct roles. They are not interchangeable, and the new authority refuses to let one
stand in for another.

---

## Updated Stage-A 11-check matrix

| # | criterion | before | now | evidence |
|---|---|---|---|---|
| 1 | shared trainable mechanism; no per-target memorization | UNPROVEN | **UNPROVEN** | vocabulary approved; no provider exists |
| 2 | context/evidence gradient path | UNPROVEN | **UNPROVEN** | policy expressible; unimplemented |
| 3 | teacher/EMA reachability | UNPROVEN | **UNPROVEN** | nothing to enrol |
| 4 | checkpoint/restart deterministic replay | UNPROVEN | **UNPROVEN** | replay policy named; no state |
| 5 | eligibility independent of hidden target value | UNPROVEN | **UNPROVEN** | registry value-independent; eligibility path unbuilt |
| 6 | no post-hoc/value-derived QC eligibility | UNPROVEN | **UNPROVEN** | no query to perturb |
| 7 | no unauthorized lookup/coordinate/ontology/graph leakage | UNPROVEN | **UNPROVEN** | field classes now enforced, but no provider consumes them |
| 8 | **provider source/provenance bound** | **FAIL** | **PASS** | canonical authority `28b20a45…` binds registry by content+invariants; role-splicing and custody fail-closed, tested |
| 9 | no unauthorized historical carryover | PASS | **PASS** | firewall holds; wildcard hole now closed |
| 10 | no visibility/QC re-entry to primary molecular path | UNPROVEN | **UNPROVEN** | no runtime path |
| 11 | no authority-by-name from historical experiments | PASS | **PASS** | enumerated vocabulary + explicit TD57/59/60 rejection, tested |

**3 PASS · 0 FAIL · 8 UNPROVEN** (was 2 / 1 / 8). Check 8 moved FAIL → PASS. No
provider-dependent check was promoted.

---

## Remaining blockers

The eight UNPROVEN checks are all provider-dependent and cannot advance without a structural
provider. Nothing else blocks that implementation: the registry is bound, custody is portable,
policy vocabulary is enforced, REG-3 is ruled, and role-splicing fails closed.

Residual, non-blocking: the observation-state artifact is now bound by this authority but the
Sept-15 feature-parents record still carries the misleading field name — corrected by
supersession rather than edit, by design.

---

## Disposition

`AUTHORITY_RECONCILIATION_COMPLETE__PROVIDER_IMPLEMENTATION_MAY_BEGIN`

Permission to begin **structural** provider implementation only. Training remains unauthorized.

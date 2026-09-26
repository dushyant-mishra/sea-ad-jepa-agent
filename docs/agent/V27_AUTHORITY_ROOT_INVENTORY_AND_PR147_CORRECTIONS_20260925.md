# V27 first response — 32-root authority inventory, PR #147 corrections, unapproved choices, and the test plan

Append-only correction document on an owned review branch. **PR #147's receipts
and the historical 40-update artifact are not modified.** No real expression was
opened. No gate was touched.

---

## 1. The audit's two corrections are confirmed, and one was worse than reported

### 1a. Geometry — the contract was stale in **two** rows, not one

The audit flagged `24 cells/update`. Checking systematically rather than
spot-fixing found a second stale row: `width / heads / ffn` read **64 / 8 / 128**
and should read **32 / 4 / 64**.

Authoritative values, transcribed from `declared_geometry` in the published
receipt and verified field-by-field against the executed driver:

| field | value |
|---|---|
| vocabulary_size | 96 |
| width / heads / ffn_width | **32 / 4 / 64** |
| blocks | 2 |
| cells_per_update | **12** |
| dropout | 0.10 |
| target_block_count / mask_fraction | 4 / 0.40 |
| views_per_update | 2 |
| max_teacher_tokens_per_microbatch | 48 |
| ema_momentum | 0.99 |
| AdamW lr / betas / eps / weight_decay | 3e-4 / (0.9, 0.999) / 1e-8 / 0.01 |

Cause: a first geometry (vocab 256 / width 64 / 24 cells) was measured at
**169.6 s per update** and reduced for tractability. I updated the producer and
its budget note and left the contract table stale. **Documentation defect only** —
receipt, producer and executed run were mutually consistent throughout, and no
reported measurement changes. The contract table is now transcribed from the
receipt so it cannot drift again.

**The 0.40 mask fraction is a synthetic fixture value and is NOT an authorized
real-data mask fraction.** None of these numbers may transfer to V5.

### 1b. B1+B2 are necessary, not sufficient — confirmed, and the count is 32

```
CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2   = 32 roots
CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2    = 33  (adds preexecution_authority_sha256)
```

My earlier framing — "freeze the target package and issue the contract, then one
adapter" — was **incomplete**. Those two steps are entry conditions.
`issue_training_authority_v1` additionally requires a valid closure V2, a
preexecution authority V2 bound to it, a teacher-target receipt V2 validated
against the frozen package root, and digest parity for the critical-test and
runtime-source authorities. All 33 roots must close.

---

## 2. The 33-root inventory

**Method, stated so the result can be challenged.** For each root I identified the
V5 module that defines it, extracted the schema literal that module declares for
its own payload, and searched all **627 committed JSON files at this head** for an
artifact carrying that exact schema. Nothing is inferred from a filename.

**Two automated mappings were tried and discarded**, because both produced
role-confused matches — `critical_test_authority` matching a *superseded test
record*, `runtime_source_authority` matching a target-estimability file,
`masking_authority` matching a masking *parameters* artifact. Publishing either
would have been exactly the forbidden "receipt copied from another role". They
are reported here as rejected method, not as findings.

### Result

| | count |
|---|---|
| roots with an identifiable defining module | **31 / 33** |
| roots with a committed artifact of that module's own schema | **6 / 33** |
| roots with **no** committed artifact | **25 / 33** |
| roots with no single identifiable module | **2 / 33** |

**The 6 with a candidate artifact** — candidates only, see the caveat below:

| root | schema found |
|---|---|
| `representation_authority_sha256` | `V5_PRIMARY_REPRESENTATION_AUTHORITY_V1` |
| `support_estimability_authority_sha256` | `V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1` |
| `canonical_address_registry_authority_sha256` | `V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1` |
| `base_training_estimand_sha256` | `V5_BASE_TRAINING_ESTIMAND_AUTHORITY_V1` |
| `masking_rng_replay_authority_sha256` | `V5_MASKING_RNG_REPLAY_AUTHORITY_V3` |
| `masking_qualification_parameters_authority_sha256` | `V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3` |

**The 25 with no committed artifact** — including every root that a training run
most depends on:

`target_address_provider`, `target_evidence_budget`, `precision`, `outer_split`,
`target_panel`, `address_universe_ladder`, `masking_qualification_design`,
`masking_qualification_run_contract`, `masking_qualification_execution`,
**`masking_authority`**, **`target_construction`**, `remaining_rna_necessity`,
`remaining_rna_execution`, **`teacher_target_semantics`**, `schedule`, **`ema`**,
`measurement_robustness`, `target_identity_gate`, `anti_cheat`,
**`model_geometry`**, `geometry_memorization_qualification`,
`protected_registry`, `critical_test`, **`runtime_source`**,
**`preexecution`**.

**The 2 unresolved:** `full104_substrate_sha256` and
`observation_gradient_firewall_authority_sha256` — no single defining module was
identified. These are recorded as `UNRESOLVED_NO_MODULE_IDENTIFIED`, **not** as
absent, because I could not establish what would satisfy them.

**Three modules declare no schema literal at all** — `schedule_authority_v2.py`,
`production_protected_registry_authority_v1.py`,
`critical_test_execution_authority_v1.py` — so for those roots it is not
currently determinable from the code what artifact would satisfy them. That is a
finding in its own right.

### The caveat that limits all of the above

**"A committed artifact with the right schema exists" is necessary, not
sufficient.** It does not establish that the artifact is the *current* instance,
that it validates against its own validator, that its digest matches what the
closure expects, or that it was produced for this role rather than another. The
6 are **candidates requiring independent validation**, and I have not validated
them. Treating them as closed roots would repeat the error this inventory exists
to prevent.

**No digest was invented, and none is quoted.** Where a root has no artifact, the
entry is empty. An empty verifier outcome is a failure to verify, never
"0 defects".

---

## 2b. A third correction, found while implementing the audit's item 4 — and it reverses one of my own claims

The audit asked me to move the gradient predicate inline, on the finding that
PR #147 applied it retrospectively. Investigating where to put it produced two
results, one reassuring and one not.

**The gate is already enforced inline.** `_gradient_report` raises *before*
`modules.optimizer.step()`:

```python
if missing or nonfinite or exact_zero or teacher_grads:
    raise RuntimeError(f'V5 reference gradient gate failed: ...')
return {'missing':0,'nonfinite':0,'exact_zero':0,'teacher_gradients':0,
        'max_abs_gradient':maximum}
```

So no new inline runner is needed, and my post-hoc wrapper was redundant rather
than the only line of defence. `inactive_update_reference.py` is **not** in the
V4 freeze (that manifest covers 21 V4-era files), but no modification to it was
required.

**My published "protected gradient gate 40/40 affirmative" is vacuous, and I am
withdrawing it.** On the healthy path those four counters are returned as
hard-coded literal zeros; the function raises otherwise. Asserting they are zero
asserts that a function which can only return zeros returned zeros. My "strict"
predicate in §4 of the contract — `missing==0 and nonfinite==0 and
exact_zero==0 and teacher_gradients==0` — is therefore a **tautology by
construction**, the exact failure mode I claimed to have fixed when I replaced
`is not None`. I replaced one check that could not fail with another.

**What is actually evidence, and stands:**

1. the harness **raises** on each damaged condition before the optimizer steps —
   now proved by negative controls rather than assumed;
2. 40 consecutive updates completed **without raising**, which is a real
   observation about the run;
3. `max_abs_gradient` ranged **0.065887–0.189149** — a measurement, not a
   literal.

**New negative controls**, `tests/test_v5_inline_gradient_gate_negative_controls.py`,
**6 passed, 0 skipped**:

| test | proves |
|---|---|
| positive control | a healthy update is accepted — without it every refusal below could be firing for an unrelated reason |
| counters-are-literals | the vacuity claim above is checkable, not merely asserted |
| planted **zero** gradient | refuses, **and** optimizer step count unchanged **and** teacher EMA did not advance |
| planted **non-finite** gradient | same |
| planted **teacher** gradient | firewall breach refused, nothing advanced |
| refusal is clean | the optimizer still works on the next healthy update |

The historical 40-update receipt is unmodified and is **not** relabelled.

## 3. Scientifically unapproved choices — the decision surface

None of these is mine to settle. Listed so approval can be sought explicitly.

**Load-bearing and unresolved:**

1. **The teacher target itself.** The stated goal is to predict the *latent
   cellular state* at a query-local hidden gene from remaining RNA — **not** the
   hidden gene's scalar value, cell identity, QC, or source support. No frozen
   target package exists and `teacher_target_semantics` has no artifact.
2. **The masking configuration.** `masking_authority` has no artifact. The
   September-16 frozen K/R nine-cell grid produced **no qualified winner**; a
   failed arm must not be relabelled qualified, and thresholds must not be
   relaxed after looking.
3. **Measurement-state channels** must remain separate negative-control outputs,
   never a privileged shortcut into the primary molecular state.
4. **Model geometry** — `model_geometry_authority_v2.py` explicitly encodes no
   historical width/depth. Real geometry must be derived from dataset geometry,
   not from my synthetic 32/4/64.
5. **EMA timescale and schedule** — no artifacts; 0.99 was a synthetic
   diagnostic constant with no external justification.
6. **The training-donor set and weighting.** `p_i = 1/(|TRAIN_DONORS|*n_d)` over
   the *prospectively frozen* set. If a development-heldout fold is introduced,
   the denominator and counts must be recomputed from that fold alone. D1's
   donor x operator weight `1/(D*|O_d|*n_do)` is a **different law** and must not
   be substituted.
7. **A model trained on all 104 has no unseen reader_fit donor.** All-104 scoring
   must not be called LODO retroactively.
8. **Common core**: 17,186 is "measured in all 42 operators"; 17,346 is
   "measured in at least one per source". Different conditions; not
   interchangeable.

---

## 4. Code and test plan (isolated, no real data)

1. **Existing inline gradient gate — already proven; DO NOT rewrite it.**
   Section 2b supersedes the original request to move the gate inline: the
   harness already refuses invalid gradients before optimizer.step and EMA.
   Six published negative controls exercise actual refusal, its unchanged
   optimizer step and unchanged teacher, and a healthy positive control.
   Remaining separate red-team: absent/malformed report fields, skipped
   optimizer step, empty Adam moments, interrupted checkpoint and presentation
   cursor atomicity. Each newly introduced failure must stop at the planted
   update with independently checked state; preserve the original 40-update
   historical receipt and never resurrect the withdrawn vacuous 40/40 count.
2. **Test hygiene.** Mark the superseded V1–V3 freeze audits explicitly (xfail or
   retirement marker) while keeping them visible, and add a **V4 mutation
   negative control** proving a V4 source mutation actually fails. Re-run the
   selected active suite with a strict zero-skip/xfail/deselect census.
3. **Environment quarantine.** Subprocess 3x3 NumPy matmul in both `sea-ad-jepa`
   and `sea-ad-jepa-v3`, logging exit code, version, BLAS config and OS error;
   then inventory historical receipts **by their recorded environment** to
   identify which NumPy-linear-algebra results could actually be contaminated.
   Re-execute only those, with frozen original data/code/estimand. Do not assume
   every prior result is bad.
4. **Reuse PR #146's authenticated metadata** rather than re-running that ETL.

---

## 5. Status

```
PHYSICAL_EXECUTED        : 33-root enumeration; 627-file committed-artifact scan;
                           geometry reconciliation against receipt and driver
SYNTHETIC_TESTED         : the historical 40-update mechanical receipt (unchanged)
INDEPENDENT_REPRODUCED   : none claimed here
BLOCKED_BY_AUTHORIZATION : real-data reader_fit diagnostic (B1, B2, and 25 open roots)
NOT_EXECUTED             : extended report/checkpoint adversaries, V4 mutation control, environment
                           contamination inventory, teacher-target decision package
NOT_ESTIMABLE            : which artifact satisfies full104_substrate and
                           observation_gradient_firewall roots
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```

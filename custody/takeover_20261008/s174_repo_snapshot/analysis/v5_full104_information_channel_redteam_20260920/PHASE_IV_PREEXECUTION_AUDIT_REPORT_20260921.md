# Phase IV — pre-execution audit

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`**

# Final status: `STOP__PREEXECUTION_DEFECT_REMAINS`

**Good news first.** Nothing found here reverses a measured number. The Phase-I,
Phase-II and Phase-III results all stand. One blocker that was assigned to this
lane is now discharged, three defects were found and fixed with adversarial
tests, and the single most important remaining item is a scientific decision that
belongs to the owner, not a broken mechanism.

N1 is still forbidden, and that is the system working as designed.

```
audited as instructed  bb1c9ff2a92f59854711b18d2ddcf68e619296e5
re-verified against    1d2b11a35f0847a13cf4e73ae5e92c1dc8456bb9
                       (integrate/v5-full104-gpt-claude-20260921)
review branch          claude/v5-phase4-preexecution-audit-20260921
```

**The base moved 27 commits during this review.** The GPT lane independently
built much of what this audit was going to recommend — an execution-contract
builder, a no-compute preflight CLI, and semantic binding of the RNG authority.
Every finding below has been re-verified against the current head rather than
reported from the SHA I started at, and three items I had drafted as blockers are
recorded as **closed by the integration** instead.

**No N1 burden result, no terminal masking result, no P1/P2/P3/P4 selection, no
D_shared, no pathology-adaptive decision, no DEV/SEALED expression, no G5 margin,
no terminal target-panel selection, no training.**

---

## 1. Phase I re-checked with the stronger qualifier — **PASS** *(discharges B1)*

This is blocker `B1_HEAVY_QUALIFICATION_V2_REAL_RUN` in
`AUDIT_B_PREEXECUTION_STATUS_V1.json`, owner `CLAUDE_GPU_LANE`, condition *"run
V2 qualifier on the content-addressed 242 MB real artifact and obtain PASS"*.
Done, and it passes.

```
artifact  D:/jepa_full104_redteam_20260920_external/core_sufficient_statistics_v1.npz
bytes     242,087,519
sha256    f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae   MATCHES BOUND
```

| check | result |
|---|---|
| **source-library totals for all 104 donors** | **`all_104_donor_library_totals_agree: true`** |
| **complete per-cell source vector** | **`per_cell_source_vector_agrees: true`** |
| rows traversed | 4,553,407 |
| `selection_row` range | [0, 4,553,406] — closed, no gaps |
| donors / core addresses | 104 / 17,186 |
| per-source cells | HVS 198,718 · NPH52 236,476 · SEA_AD 4,118,213 |
| three-route total source library | **122,517,308,792** (metadata = artifact = Audit A) |
| failures | `[]` |

`verdict: HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE`, 26.6 s across 14 workers.
**The heavy artifact was not rebuilt** — nothing failed, so there was no reason to.

The substantive upgrade over V1 is the per-cell source vector. V1 loaded
`src_of_cell` without verifying it; V2 reconstructs it from the authenticated
donor→source map composed with pass1's `selection_row`-keyed `cell_donor` and
compares all 4,553,407 entries. That vector is the join donor-held-out evaluation
depends on, so leaving it unverified was the right thing to close.

```
receipt  analysis/.../evidence/phase_i/HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2.json
```

---

## 2. Phase-III edge cases — **all three confirmed, all three fixed**

A distinction that matters before the detail: **there are two V2 contracts.**

| | file | state |
|---|---|---|
| integrated | `src/sea_ad_jepa/v5/evidence_estimability_contract_v2.py` | **already correct on all three** |
| reference (mine) | `analysis/.../scripts/score_term_evidence_contract_v2.py` | had all three |

I probed the integrated contract first and all three passed. The defects are in
my reference implementation, which is the one the review describes. Both are now
verified to agree across the whole matrix, and a parity test keeps them from
diverging later.

### A. Missing required group — **confirmed, and worse than described**

Every supplied term estimable, group 2 declared required and absent:

```
BEFORE  policy=None -> ESTIMABLE  0.268125  full_estimand=True
        P1         -> ESTIMABLE  0.268125  full_estimand=True
        P2         -> ESTIMABLE  0.268125  full_estimand=True
        P3         -> ESTIMABLE  0.268125  full_estimand=True
        P4         -> ESTIMABLE  0.268125  full_estimand=True
```

You described this as returning an estimable number before noticing the missing
group. It is worse: **P4 failed too**, and P4 already contained a correct
coverage guard. One early return caused all five:

```python
if not terms.has_non_estimable():      # fires first, short-circuits every policy
    return Aggregate(..., status="ESTIMABLE", full_estimand_point_estimated=True, ...)
```

`has_non_estimable()` is `False` here because **no term ever carried group 2's
label**. A required source that contributed nothing was indistinguishable from
one that was never required, and the guard written to catch exactly that was
unreachable.

```
AFTER   policy=None -> NonEstimableError: one or more required groups have no estimable term
        P1         -> EXCLUDED       None   full_estimand=False
        P2         -> ESTIMABLE  0.268125   full_estimand=False,  group 2 coverage 0.0
        P3         -> ESTIMABLE  0.268125   full_estimand=False,  group 2 coverage 0.0
        P4         -> NOT_ESTIMABLE   None  full_estimand=False
```

P2/P3 still report a number — that is their definition — but the absent group is
recorded with zero coverage and the full estimand is not claimed, so it is
disclosed rather than dropped. Matches the integrated contract exactly.

### B. Empty evidence — **confirmed**

```
BEFORE  ScoreTerms(values=[], states=[], group=[])  -> constructed successfully
        aggregate(empty)                             -> ESTIMABLE  nan  full_estimand=True
```

An estimable NaN, as described. `_validate` tested `ndim != 1`, and an empty 1-D
array has `ndim == 1`, so it passed; `aggregate` then averaged an empty list.

```
AFTER   ScoreTerms(empty)             -> ContractViolation
        from_scorer_components(empty) -> ContractViolation
        from_json(empty arrays)       -> ContractViolation   (second door, also closed)
```

Zero evidence is not weak evidence. The all-`MISSING` case — non-empty but zero
*usable* evidence — was already correct and is now regression-tested.

### C. Negative sums of squares — **confirmed**

`t_bad = present & (rss <= eps)` caught every negative value, so arithmetic
failure became a legitimate scientific state.

```
BEFORE  rss_y=-1.0  -> TARGET_NON_VARIABLE        AFTER (EPS=1e-12)
        rss_y=-1e-6 -> TARGET_NON_VARIABLE          -1e-15   -> TARGET_NON_VARIABLE   (noise)
        both -1.0   -> TARGET_AND_PREDICTION_...    -1e-13   -> TARGET_NON_VARIABLE   (within tol)
                                                    -1.1e-12 -> INVALID_NUMERIC       (first past tol)
                                                    -1e-6    -> INVALID_NUMERIC
                                                    -1.0     -> INVALID_NUMERIC
```

Routing is per-term, so a bad term among good neighbours is still caught, and the
`INVALID_NUMERIC` term carries NaN, preserving the bidirectional invariant.

```
reference contract  9ef22b80545fd1b222ac8186e031ddb8d832ce887831a99eb1c8fe99b92801ea
                ->  496e5837fd86a0a83f0cb9340df338d268509187410ee7708ee587b347bce8cb
```

**No measured Phase-III number changes.** These were routes by which an undefined
quantity could have become a number in a *later* run, not corrections to the
existing result. The P4 measurement — 0.78 % of target-folds eliminating all 531
vacuous guardrails — is unaffected, because that computation supplied terms for
every required group.

---

## 3. Phase-IV freeze digest — **gap confirmed, closed by the successor contract**

The gap is real and reproduces. Each of these edits leaves `freeze_digest`
`c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac` **unchanged**:

| mutation | digest moves? |
|---|---|
| escalation threshold `0.05 → 0.50` | **no** |
| primary burden statistic redefined | **no** |
| terminal outcome → `PROCEED_ANYWAY` | **no** |
| `depends_only_on_precision → False` | **no** |
| execution requirements emptied | **no** |
| `training_authorized → True` | **no** |
| sample membership / bound hashes / ladder | yes (covered) |

**The original frozen sample was not modified and its targets were not
rerolled.** `AUDIT_B_FROZEN_TARGET_SAMPLE.json` is untouched and all seven bound
inputs still match — including `audit_b_mask_plan_generator_20260920.py` at
`fdc0cec140132b71fd0c01af5ec97c323bac091055191754dfcf81111ee6441e`,
byte-identical across the attempted optimization and its revert.

`src/sea_ad_jepa/v5/audit_b_execution_contract_v1.py` (`60a79d13…`) binds the
original sample freeze digest **plus** the execution semantics, and
`canonical_digest()` covers all of them. Verified by a 16-element mutation test:
every decision element either moves the digest or is refused outright by
`validate()`, refusal being the stronger guarantee.

It is the right mechanism, so **I am withdrawing my own parallel addendum**
(`freeze_audit_b_execution_rule_addendum_20260921.py`, built on the previous
review branch) rather than shipping two competing freezes of the same rule. The
one thing it had which the contract lacks is carried forward as R1 below.

It shipped without tests at `d41cdc15`; the GPT lane has since added its own, and
this branch adds **42 red-team tests** covering digest coverage, fail-closed
refusal, pinned-root swapping, malformed digests, role distinctness, the RNG
semantic binding, and the training and terminal-outcome boundaries.

---

## 4. RNG V3 — **design sound, and now genuinely in force**

The module is byte-identical at both heads (`6a0b854d…`). Every requirement in
item 4 passes:

| requirement | result |
|---|---|
| **target-panel authority is not an RNG input** | **PASS** — absent from the `global_seed` payload |
| target identity and fold still key masks | PASS — `derive_seed(target_id, outer_fold, cell_key)` |
| common-random masks remain method-independent | PASS — `METHOD_EXCLUSION_POLICY_ID`; method absent from payload |
| terminal outcomes cannot influence seed construction | PASS — `terminal_outcomes_inspected_before_freeze` must be `False` |
| bound to stable pre-panel roots | PASS — substrate `66f589e5…`, registry `7d61ed7b…`, split, masking parameters, burden ladder, all equality-enforced |

### What changed during the review

At `bb1c9ff2` I was going to report this as **not in force**: `MaskingRngReplayAuthorityV3`
appeared only in its own builder and test, and the frozen-bound planner
`full104_masking_streaming_executor_v1.py` (`143645be…`) takes `global_seed` as a
caller-supplied parameter. That is no longer true. At the current head:

* `audit_b_execution_preflight_v1.py` imports the authority, **rebuilds it from
  the runtime payload, re-validates it, and requires its recomputed
  `canonical_digest()` to equal the contract's `rng_authority_sha256`** and its
  `global_seed` to match;
* the contract pins `rng_authority_schema_id = "V5_MASKING_RNG_REPLAY_AUTHORITY_V3"`
  and `rng_target_panel_dependency_id = "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"`.

Verified directly: supplying the superseded V2 schema is refused with *"RNG
authority schema drifted"*, and declaring any other panel dependency is refused
with *"RNG target-panel dependency drifted"*.

**I had drafted a recommendation to pin `rng_authority_sha256` to a literal
value. That recommendation is withdrawn — the integration's approach is better.**
A literal file hash would break on any cosmetic edit and would bind the bytes
rather than the meaning; binding the schema identity and the declared
panel-dependency, then reconstructing the authority at preflight, binds what
actually matters.

*One correction to an earlier suspicion of mine:* `universe.size` in the planner's
base-mask seed is the **masking universe** (17,186 strict core), not the target
panel, so that term is panel-independent and was never the defect. The panel
dependency lived in `global_seed` under V2 — exactly what V3 removes.

### Remaining compatibility item

The authority object itself has not yet been built from the current pre-panel
roots — GPT's `B3_RNG_V3_REAL_RECEIPT`. Until it is, the preflight has nothing to
verify against. And if the eventual **terminal V4 run-contract** continues to
derive its global seed from the target-panel authority (V2 semantics), it cannot
consume RNG V3 without a successor contract; the two derive incompatible seeds,
and silently accepting V4's seed would revert panel-independence while leaving
the V3 authority in place as misleading evidence of a fix.

```
MIGRATION_REQUIRED__TERMINAL_RUN_CONTRACT_V4_MUST_CONSUME_RNG_V3_OR_DECLARE_A_SUCCESSOR
```

No workaround was implemented.

---

## 5. Precision scope — **`PRECISION_SCOPE_UNRESOLVED`**

**The 18-cell conjunction is NOT implied by the original frozen wording.**

The frozen text reads *"escalate from Nk to Nk+1 iff relative standard error of
**the primary burden statistic** > 0.05"* — singular — while the frozen
*definition* of that statistic is indexed by **policy and rung**. The wording
does not determine whether the criterion is one aggregate RSE, a conjunction over
cells, or something else. Three reasons the 18-cell reading is a new scientific
choice rather than a conservative restatement:

1. A conjunction over **3 policies × 6 rungs = 18 cells** is materially stricter
   than one aggregate RSE, so it changes *when escalation fires*.
2. The zero-mean rule (`UNDEFINED_ZERO_MEAN__FAIL_CLOSED`) appears **nowhere** in
   the frozen text. It is wholly additional.
3. **Structural risk.** The numerator is `(ADDED − DROPPED)`; the denominator is
   the *full* uniform mask. If for some policy × rung those burdens are close,
   the target-level mean approaches zero, RSE becomes undefined or very large,
   and escalation is forced by a **near-zero denominator artifact** rather than by
   genuine imprecision — potentially driving the ladder to N3 and maximum compute
   for a non-precision reason.

Whether any cell actually has a near-zero mean is an **outcome** and was
deliberately not estimated. The earlier 512-address ratios are
`REDUCED_POOL_DIAGNOSTIC` and must not be used to predict it.

The integration lane reached the same determination independently —
`PRECISION_SCOPE_UNRESOLVED = "UNRESOLVED__EXECUTION_FORBIDDEN"` is the contract's
default and `require_execution_ready()` raises `STOP_PRECISION_SCOPE_UNRESOLVED`.
Two reviewers converging on this without coordinating is the strongest available
evidence that the wording is genuinely ambiguous.

### Recommended prospective interpretation to freeze before N1

**`ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1`**, specified as:

> The primary burden statistic is the target-level mean of
> `[B2(ADDED) − B2(DROPPED)] / B2(uniform full mask)` at **one predeclared
> policy × rung cell**, named in the execution contract before N1. Escalate from
> Nk to Nk+1 iff its RSE exceeds 0.05 at Nk. The remaining 17 cells are reported
> at every rung but do not gate escalation. If the predeclared cell's target-level
> mean is within `ZERO_MEAN_TOL` of zero, the RSE is undefined and the outcome is
> `UNDEFINED_ZERO_MEAN__FAIL_CLOSED` — never a pass, and never an escalation
> trigger either, because a near-zero denominator is not evidence of imprecision.

Why this rather than the conjunction: it matches the singular wording, it is the
reading under which the frozen 0.05 was chosen, and it makes the zero-mean case an
explicit named outcome instead of letting a denominator artifact drive the ladder
to N3. The cost is that it gates on one cell, which is why the other 17 must still
be reported at every rung.

**This is the owner's call, not mine.** Either constant is lawful under the
contract; I have not set one.

### A second unresolved choice, found by the integration lane — not by me

`B2_SCIENTIFIC_EXECUTION_SCOPE` has a part (b) I did not flag: **the
source/donor/fold weighting** used to form the target-level statistic. The
current `SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1` is
recorded as a *prospective candidate* bound by the new contract, explicitly not
claimed to have been decided by the `c2c5e1b5` sample freeze. That is the correct
label and it needs the same prospective resolution as the RSE scope. I am
recording it here rather than restating it as my own finding.

---

## 6. Exact tests run

```
PYTHONPATH=src python -m pytest -q -p no:randomly \
  tests/test_v5_score_term_evidence_contract_v2_edge_cases.py
  -> 33 passed, 0 skipped, 0 failed                                       [NEW]

PYTHONPATH=src python -m pytest -q -p no:randomly \
  tests/test_v5_audit_b_execution_contract_redteam_v1.py
  -> 42 passed, 0 skipped, 0 failed                                       [NEW]

PYTHONPATH=src python -m pytest -q -p no:randomly \
  tests/test_v5_score_term_evidence_contract_v2.py
  -> 30 passed, 0 skipped, 0 failed                          [pre-existing, no regression]

PYTHONPATH=src python -m pytest -q -p no:randomly --strict-markers -rs tests/ -k v5 \
  --ignore=tests/test_contextual_target_f1_preflight_core_v1.py \
  --ignore=tests/v4/test_stage81a2r_authoritative_mapping.py \
  --ignore=tests/v4/test_stage81a3_fbsdq_outputs.py \
  --ignore=tests/v4/test_stage81a3_prrc_outputs.py
  -> 1382 passed, 0 skipped, 0 failed, 1738 deselected        (167 s, at 1d2b11a3)
```

### Mutation verification of the new tests

An adversarial test that passes against the broken code proves nothing, so the
edge-case suite was run against the pre-fix reference contract restored from
`bb1c9ff2`:

```
-> 21 failed, 12 passed        (all three edge cases represented among the failures)
```

### The four ignored files

```
tests/test_contextual_target_f1_preflight_core_v1.py
tests/v4/test_stage81a2r_authoritative_mapping.py
tests/v4/test_stage81a3_fbsdq_outputs.py
tests/v4/test_stage81a3_prrc_outputs.py
```

These fail at **collection** with `FileNotFoundError` on missing V4 result
artifacts (e.g. `results/v4/stage81a3_prrc_report.json`). Confirmed pre-existing
rather than assumed: the identical four errors occur on a pristine worktree with
all changes stashed. None of them import any file this review touched.

### Totals

```
passed   1382   (includes the 75 new tests on this branch)
skipped     0
failed      0
errors      4   pre-existing V4 collection errors, reproduced on the pristine head
```

---

## Blockers remaining before N1

| id | owner | state |
|---|---|---|
| `B1_HEAVY_QUALIFICATION_V2_REAL_RUN` | Claude GPU lane | **DISCHARGED** — item 1 above |
| `B2_SCIENTIFIC_EXECUTION_SCOPE` (a) RSE scope | scientific review | **OPEN** — recommendation in item 5 |
| `B2_SCIENTIFIC_EXECUTION_SCOPE` (b) weighting | scientific review | **OPEN** |
| `B3_RNG_V3_REAL_RECEIPT` | integration | **OPEN** |
| `B4_EXECUTION_CONTRACT_FREEZE` | integration | **OPEN** — gated on B1–B3 |
| `R1` resolution provenance | integration | **OPEN** — new, below |

### R1 — the precision-scope resolution has no provenance *(new)*

`precision_scope_id` can be moved from `UNRESOLVED` to a resolved value by typing
a different constant. Nothing records **who** resolved it, **when**, or — the one
that matters — that it was resolved **without having seen a burden outcome**. The
contract's `terminal_masking_outcomes_inspected_before_freeze` flag is
self-asserted and covers the freeze, not the resolution. Verified at the current
head: the module contains no resolver, timestamp or rationale field.

This is the same class of defect as the original freeze-digest gap — the
mechanism is sound and the thing it most needs to attest is the thing it does not
record.

Recommended: a `precision_scope_resolution` record carrying the resolver, a UTC
timestamp, the stated rationale, and the contract digest as of resolution,
required to be non-null whenever `precision_scope_id != UNRESOLVED`. I have not
made this change because it alters `canonical_digest()`'s field set, which is a
coordination decision with the integration lane rather than mine to take
unilaterally. I can implement it on instruction.

### Hardening item (not a blocker)

`measure_plan_burden` accepts `heldout_donors` but never verifies they are the
held-out set for `fold_index` under the authenticated split. A caller error would
silently measure burden on *training* donors — the exact thing the design
forbids. A fold-consistency guard should exist before execution.

---

## What must happen before N1

1. **Resolve both parts of the scientific execution scope** — the RSE scope and
   the weighting. Owner's call; my recommendation for the first is in item 5.
2. **Build and verify the content-addressed RNG V3 authority receipt** from the
   current pre-panel roots, so the preflight has something to verify against.
3. **Add resolution provenance** (R1).
4. **Build the resolved execution contract** and confirm `execution_authorized`
   is true.
5. Add the `measure_plan_burden` fold-consistency guard, and constrain `cell_key`
   so panel-dependent content cannot re-enter the per-mask seed through a free
   string.

Items 2–5 are mechanical and I can implement them prospectively on instruction —
without executing N1.

```
N1_BURDEN_RESULTS             = NOT COMPUTED
TERMINAL_MASKING_RESULTS      = UNOPENED
P1_P2_P3_P4_SELECTED          = NONE
D_SHARED / PATHOLOGY / SEALED = SEALED
G5_MARGIN_SELECTED            = NONE
TERMINAL_TARGET_PANEL         = NOT SELECTED
TRAINING_OFF
```

# Phase IV — Audit-B pre-execution red-team

Date: 2026-09-21
Scope class: **`CURRENT_FULL104_RECONNAISSANCE`**

# Conclusion: `STOP__PREEXECUTION_DEFECT_FOUND`

Three blockers must close before N1. One of them is a defect I introduced in the
Phase-IV freeze itself.

```
integration head reviewed : c985ad85d231cadd92db7d886ba8c7217f3d482f
review branch             : claude/v5-phase4-preexecution-redteam-20260921
```

**No Audit-B burden outcome was computed or inspected.** No terminal masking
outcome, no P1/P2/P3/P4 selection, no P4 adoption, no D_shared, no pathology, no
DEV/SEALED inspection, no G5 margin, no terminal panel selection, no training.

---

## Blockers

### B1 — the frozen execution rule was never cryptographically frozen *(mine)*

`AUDIT_B_FROZEN_TARGET_SAMPLE.json` binds **what is sampled**. It does **not**
bind **how the result will be decided**. Verified by mutation — each of these
leaves `freeze_digest` **unchanged**:

| mutation | digest moves? |
|---|---|
| escalation threshold `0.05 → 0.50` | **no** |
| primary burden statistic redefined | **no** |
| terminal outcome → `PROCEED_ANYWAY` | **no** |
| `depends_only_on_precision → False` | **no** |
| execution requirements emptied | **no** |
| `training_authorized → True` | **no** |
| sample membership / bound hashes / ladder | yes (covered) |

That is the wrong half. A decision rule editable without moving a digest is not
frozen in any sense that matters, and it is exactly the rule that must not be
adjustable after seeing N1. My own test was named
`test_freeze_digest_covers_the_samples_and_the_bindings` — accurate, and blind to
the gap.

**Addressed prospectively, not executed.** `AUDIT_B_EXECUTION_RULE_ADDENDUM.json`
binds the rule **without modifying the original freeze**:

```
sample_freeze_digest        c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac  (unchanged)
rule_digest                 e6335d27f8e19637f85f1b89564fb4d6842271b9a827521bf700956b5a37e0c8
execution_contract_digest   342acc235a317e46edcb86f0a9de914114dd9765764fffff2c5ca94a535f12c7
ratified                    false
```

19 tests, including a mutation test over **nine** decision elements — the test the
original freeze lacked.

### B2 — the 18-cell RSE reading is a new scientific choice

**Answer to item 4: it is NOT merely a conservative reading of the frozen text.**
It requires an explicit prospective addendum, and I have not self-ratified it.

The frozen text says *"relative standard error of **the** primary burden
statistic"* — singular — while the frozen **definition** of that statistic is
indexed by *policy* **and** *rung*. The text therefore does not determine whether
the criterion is one aggregate RSE, a conjunction over cells, or something else.

Three reasons the implementation's reading is a new choice:

1. A conjunction over **3 policies × 6 rungs = 18 cells** is materially stricter
   than one aggregate RSE, so it changes *when escalation fires*.
2. The zero-mean rule (`UNDEFINED_ZERO_MEAN__FAIL_CLOSED`) appears **nowhere** in
   the frozen text. It is wholly additional.
3. **Structural risk.** The numerator is `(ADDED − DROPPED)`; the denominator is
   the *full* uniform mask. If for some policy × rung those burdens are close,
   the target-level mean approaches zero, RSE becomes undefined or very large,
   and escalation is forced by a **near-zero denominator artifact** rather than by
   genuine imprecision on the cells that matter — potentially driving the ladder
   to N3 and maximum compute for a non-precision reason.

Whether any cell actually has a near-zero mean is an **outcome** and is
deliberately not estimated. The earlier 512-address ratios are
`REDUCED_POOL_DIAGNOSTIC` and must not be used to predict it.

Recorded as `interpretation_dispute.status = REQUIRES_EXPLICIT_RATIFICATION_BEFORE_N1`.
An execution run must refuse while `ratified` is false.

### B3 — RNG V3's panel-independence is **not in force**

The V3 design is sound. Every check in the assignment passes *for the module*:

| check | result |
|---|---|
| target-panel authority is not an RNG input | **PASS** — absent from the `global_seed` payload |
| physical FULL104 substrate bound | PASS (`66f589e5…`, equality-enforced) |
| canonical registry bound | PASS (`7d61ed7b…`, equality-enforced) |
| donor split bound | PASS |
| masking-parameter authority bound | PASS |
| burden-ladder authority bound | PASS |
| target identity + outer fold key mask generation | PASS (`derive_seed`) |
| method name cannot alter the base mask | PASS (`METHOD_EXCLUSION_POLICY_ID`; absent from payload) |
| terminal outcomes cannot affect the seed | PASS (`terminal_outcomes_inspected_before_freeze` must be `False`) |

**But nothing consumes it.** `MaskingRngReplayAuthorityV3` appears only in its own
module, its builder, and its test. The frozen-bound planner
`full104_masking_streaming_executor_v1.py` — SHA `143645be…`, unchanged and
therefore still the version the Phase-IV sample binds — takes `global_seed` as a
**parameter** and derives base masks as:

```python
_seed("V5_COMMON_RANDOM_BASE_MASK", global_seed, fold_index, target_id, universe.size)
```

So panel-independence holds only if the caller supplies a V3-derived seed, and no
such wiring exists. This is the standing rule that a contract is not in force
until the executor enforces it.

*A correction to an earlier suspicion of mine:* `universe.size` here is the
**masking universe** (17,186 strict core), **not** the target panel, so that term
is panel-independent and is not itself the defect. The panel dependency lived in
`global_seed` under V2, which is precisely what V3 removes.

**Secondary hardening:** `derive_seed(..., cell_key: str)` is an unconstrained
free string. Nothing prevents a future caller passing panel-dependent content
through it, reintroducing the defect via the parameter rather than the design.

---

## Required future migration — reported, not worked around

The eventual **terminal V4 run-contract** consumes a global seed. If V4 continues
to derive it from the target-panel authority (V2 semantics), it **cannot consume
RNG V3 without a successor contract**: the two derive incompatible seeds, and
silently accepting V4's seed would revert panel-independence while leaving the V3
authority object in place as misleading evidence that it had been fixed.

```
MIGRATION_REQUIRED__TERMINAL_RUN_CONTRACT_V4_MUST_CONSUME_RNG_V3_OR_DECLARE_A_SUCCESSOR
```

No workaround was implemented.

---

## Items that PASS

### Item 1 — evidence contract semantics preserved

`src/sea_ad_jepa/v5/evidence_estimability_contract_v2.py`
SHA `e9302a8bcdf2682b1d639b164d95ca8f8a6f69e63cce16c638b558ac6f5ae799`

Probed adversarially rather than read:

| property | result |
|---|---|
| finite value **iff** ESTIMABLE (both directions) | **PASS** at *both* entry points |
| `TARGET_NONVARIABLE` | PASS |
| `PREDICTION_NONVARIABLE` | PASS |
| `TARGET_AND_PREDICTION_NONVARIABLE` | PASS (joint state preserved) |
| `MISSING` | PASS |
| `INVALID_NUMERIC` | PASS (`|r| > 1` refused at both entry points) |
| P3 / full-estimand wording | PASS — `full_estimand_point_estimated` is `False` for P1–P4 whenever any term is non-estimable, `True` only when all are |
| no implicit undefined → zero | PASS — undefined serializes as `null`; a hand-edited payload attaching `0.0` is refused on deserialize |
| no hidden P1/P2/P3/P4 selection | PASS — `aggregate` has no default policy and refuses; `compare_policies` reports `policy_selected: None` |

Worth noting: the integration carries **two** container classes
(`ScoreTermsV2`, `ScoreObservationMatrixV2`). Both were probed; **both enforce the
same invariants**, so there is no bypass via the second entry point.

### Item 3 — Audit-B estimator guards

`src/sea_ad_jepa/v5/audit_b_production_burden_v1.py`
SHA `157f07928a43fc8ede13168d9f64db7500de82da0cdd3255da4f2160dd844152`

| check | result |
|---|---|
| target contained in the uniform denominator | **PASS** — `"uniform base mask must contain the target"` |
| target never in ADDED/DROPPED | **PASS** — `"target cannot enter added/dropped swap sets"` |
| added/dropped cardinalities equal | **PASS** — `"added/dropped address counts must match exactly"` |
| burden from held-out donors only | PASS — `heldout_donors` required; burden indexed over it |
| donors equal-weighted within source | PASS |
| sources equal-weighted within target | PASS — required source with no held-out donor **raises**, never silently dropped |
| targets equal-weighted | PASS |
| B3 cannot control escalation | **PASS** — `precision_summary` takes no metric argument and uses B2 only |
| measured zero remains evidence | PASS — a masked measured zero contributes 0 to B2 while remaining inside the uniform denominator; it is not treated as missingness |

**Hardening item (not a blocker):** `measure_plan_burden` accepts
`heldout_donors` but never verifies they are the held-out set for `fold_index`
under the authenticated split. A caller error would silently measure burden on
*training* donors — the exact thing the design forbids. A fold-consistency guard
should exist before execution.

### Item 5 — frozen sample integrity: **PASS**

`freeze_digest` = `c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac`,
identical to the Phase-IV freeze. All seven bound inputs unchanged under
**full-SHA** comparison:

| bound input | SHA-256 | match |
|---|---|---|
| target_universe | `3723ec4a3fe0e2d0…` | YES |
| split_receipt | `56f045d7dc80fde7…` | YES |
| planner_source | `143645becff6f614…` | YES |
| qualification_runner | `a98e81cd1c6ba2a9…` | YES |
| masking_parameters_authority | `e53b454673010a9e…` | YES |
| evidence_budget_authority | `b10c3ee0354d37d5…` | YES |
| **mask_plan_generator** | **`fdc0cec140132b71fd0c01af5ec97c323bac091055191754dfcf81111ee6441e`** | **YES** |

The attempted optimization (`f3dc8e68`) and its revert (`a5091e9c`) left
`audit_b_mask_plan_generator_20260920.py` **byte-identical** to the version the
freeze binds. The revert worked.

### Item 6 — heavy artifact readiness: **PASS**

Content-addressed check only; Phase-I analysis **not** repeated.

```
path   D:/jepa_full104_redteam_20260920_external/core_sufficient_statistics_v1.npz
bytes  242,087,519
sha256 f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae   MATCH
```

Qualified geometry accessible: `core` (17,186), `duniq` (104), `donor_nnz`
(104 × 17,186), `donor_umi` (104 × 17,186), `donor_cells` (Σ = 4,553,407),
`donor_src`, `libraries` (4,553,407), `pool` (512). No invariant failed, so no
re-analysis was performed.

---

## Test commands and results

```
pytest -q -p no:randomly --strict-markers -rs tests/test_v5_audit_b_execution_rule_addendum_v1.py
  19 passed, 0 skipped
```

Adversarial probes of the integrated contract (both entry points) and of the
frozen-sample/heavy-artifact integrity were run directly and are reproduced in
the sections above.

---

## What must happen before N1

1. **Ratify or revise the RSE scope** (B2). If the 18-cell conjunction is
   intended, ratify it explicitly and state how a near-zero-mean cell is handled
   so escalation cannot be driven by a denominator artifact. Re-emit the addendum
   with `--ratified`.
2. **Wire RNG V3, or declare the migration** (B3). Either the Audit-B execution
   path consumes a V3-derived `global_seed`, or the report records that it does
   not and that panel-independence is not yet in force.
3. **Constrain `cell_key`** so panel-dependent content cannot enter the per-mask
   seed through a free string.
4. **Add the fold-consistency guard** to `measure_plan_burden`.

Item 1 is the owner's; items 2–4 are mechanical and I can implement them
prospectively on instruction — without executing N1.

```
AUDIT_B_BURDEN_OUTCOME        = NOT COMPUTED
TERMINAL_MASKING_OUTCOMES     = UNOPENED
P1_P2_P3_P4_SELECTED          = NONE
P4_ADOPTED                    = NO
D_SHARED / PATHOLOGY / SEALED = SEALED
G5_MARGIN_SELECTED            = NONE
TERMINAL_TARGET_PANEL         = NOT SELECTED
TRAINING_OFF
```

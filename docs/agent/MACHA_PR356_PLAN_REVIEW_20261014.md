# Macha review — PR #356 production synthetic V3.1.1 implementation plan

Date: 2026-10-14.

**Scope.** The plan is reviewed against:
- the closure-check plan requirements (`e4576c9d`: fresh-head classification, §22, §16, E4, N1, N2, fail-closed blockers);
- V3.1 §13/§20/§22;
- current live heads.

It is not a re-audit of the design.

**Read-only throughout.** No outcomes, DEV/SEALED data or pathology were opened.

**Verdict:** `PLAN_ACCEPTED_WITH_REQUIRED_PLAN_AMENDMENTS_P1_P6__TASKS_1_3_MAY_START__AMEND_BEFORE_TASK_4`

## Custody

| object | identity |
|---|---|
| plan head | `1c764c7fd3857a54bde4faebeece715d85ed3501`. Single commit on `847fe734`; one new file, nothing else touched. |
| V3.1 blob | `48e71346…` matches `847fe734:` path; SHA-256 `234af6df…c65b`. |
| V3.1.1 blob | `977faa75…` matches `847fe734:` path; SHA-256 `ab1ae1bb…363f`. |
| #351 live head | `2abcb9fe` ≠ plan `b9774be4`. The delta is 3 lines in `tests/v5/test_jepa_post_td_harness_contract_v1.py` only. This is `BRANCH_MOVED`, not `SCIENTIFIC_EXECUTABLE_CHANGED`. |
| #350, #352–#355 | live heads equal the plan table. |

## What the plan gets right

- **N1 and N2 are encoded.** N1: executor finite-sample estimability (Global §24, T7.3, T11.3). N2: controlling specs cited by blob, and `docs/agent/**` is non-controlling.
- **External blockers stay closed.** G6, G8, R1, TargetPortfolio, the G7 decision layer and the V79↔V80 conflict all remain closed. Green CI cannot upgrade a component (T10.2–T10.4). #355 is upgraded only through a separate reviewed binding artifact (T10.5).
- **§22 items 1–7, 10 and 11 map to owning tests.** Identity-keyed streams (T2 `derive_stream(root, *identity_parts)`) bind randomness to scientific identity, not to row order.

## Required plan amendments

**P1 (MODERATE) — the pre-exposure ordering is unstated.**
- **Defect.** T10.5 runs the real #355 implementation "through the production synthetic fit-side reader". T8 sets baseline ceilings with sensitivity. Pre-exposure realism runs only in T11.1.
- **Why it matters.** If T10 or T8 runs on a realization of the production generator version, that is a downstream exposure before the realism freeze. E4 forbids realism iteration afterwards, and E1 then forbids easing.
- **Repair.**
  - State that T8 and T10 use only fixture worlds from a non-production test generator version.
  - The first invocation on a production version happens after `run_pre_exposure_realism` has frozen it.
  - That invocation must go through `record_exposure`.
  - Baseline-ceiling evaluation counts as a frozen realism metric, not a downstream method.

**P2 (MODERATE) — the withheld family's storage location and author are unstated (E2).**
- **Defect.** The plan keeps the nonce and withheld spec out of the fit-side and public manifests. It does not forbid committing the withheld mechanism as readable code, for example in `biology_v1.py`.
- **Why it matters.** This repo is pushed incrementally to GitHub, so committed code would defeat E2.
- **Repair.**
  - Generic family code may be public. The withheld parameterization/spec is controller-authored data stored off-repo.
  - Only `H(withheld_spec ‖ nonce ‖ generator_semantic_hash ‖ class_tag)` is committed.
  - No implementer subagent authors or sees it.
  - Add a test asserting that no committed file decodes to the committed preimage.

**P3 (MODERATE) — no execution stop gates.**
- **Defect.** The execution gate says approval creates no authority, but T11 and T12 generate sealed realizations and invoke the finalizer.
- **Repair.** Insert explicit STOP-for-fresh-authorization points:
  - (a) before the first production-version realization in T11;
  - (b) before the sealed qualification run;
  - (c) before the T12.7 finalizer.
- An implementation authorization covers code and tests on fixtures (T1–T10 and the T11/T12 code) only.

**P4 (MODERATE) — these §22/§20/§13 requirements are missing:**
- §22.9 + §20 + E4: freeze minimum instance counts per required support state and source/operator stratum, derived from executor resolution mathematics and the applicability law. Poison tests are needed separately for `STRUCTURALLY_UNMEASURED` and for `MEASURED_COLLISION_UNRESOLVED`, plus separate swap/poison tests for `WITHHELD_BY_EVIDENCE_RIGHTS`. T6.4 "poison masked values" does not cover these.
- §13: synthetic thinning acts only on `MEASURED_SCALAR` entries. Collision and structural states pass through, and thinned-to-zero stays `MEASURED_SCALAR`. Randomness is keyed by cell identity.
- §22.14: depth stress by repeated realization is labelled `SYNTHETIC_ONLY`.
- §22.13: any V73–V75 detected-feature envelope must prove it does not depend on the address universe before it is used in T3.
- §22.8: R5 prose PASS = `DESIGN_TEXT_PRESENT__NOT_TESTED`.
- §22.12: normalize Stage70/71 labels to the #325 classification.
- §22.7: add an explicit test that gate verdicts are derived by the controller, never carried as generator labels.

**P5 (MINOR) — classification freshness.**
- **#351.** Record `2abcb9fe` as `BRANCH_MOVED`. At that head all three checks pass (runs `38511967480`, `38511963353`, `38511967467`), so the plan's "failing broader harness" reason is stale. The classification is still `NOT_REHEARSED_BLOCKED_EXTERNAL`, now resting only on the V3.1 §15 TargetPortfolio residual gaps.
- **#343 G8.** Keep the blocker, but record the current real-lane status: `CONFORMAL_BOUND_MECHANICS_QUALIFIED__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN__HUMAN_G8_NOT_EXECUTABLE`. The controller ruling is #343's `alpha_eff=0.01/6 → 599`. The open items are now the realization unit, the reference unit, the displacement interface and the support-fraction denominator, not 299 vs 599. The V3.1 §13 label stays as spec text; no amendment is needed, because the outcome (blocked) is unchanged.
- **Dependency mobility.** Every dependency is an open, moving PR. T10.1's head-binding fixture must fail closed on any move. A test-only move is reclassified explicitly, not silently accepted.

**P6 (MINOR) — identity form.** Cite both controlling specs by SHA-256 as well as by git blob SHA-1 (values above), as N2 asked.

## Real-data input for T3/T5 (non-blocking)

The concurrent outcome-blind real audit (branch `audit/td-real-data-qualification-macha-20261014`) shows real support holes. If the plan's empirical stress geometry claims realism, it should reproduce them as `AUTHENTICATED_EMPIRICAL_CALIBRATION` inputs. Calibration from reader_fit only, per T3.1.
- NPH52 has 0 reader_validation and 2 reader_oracle donors.
- 4,894 NPH52-only addresses are never measured in reader_validation.
- 730 addresses are measured only in HVS and 4,710 only in SEA_AD.
- Held-out SEA_AD subclass strata have 4–5 donors each.

These are exactly the "source-asymmetric support" and "held-out/source-shift" regimes T5.1 names.

## Execution mode

**Recommend subagent-driven execution, with constraints:**
1. Run tasks sequentially on one stacked branch, because T2→T3→T4→T5 consume each other's types.
2. Each task gets one implementer, plus a separate fresh-context spec and hostile reviewer, before the next task starts.
3. The controller (not a subagent) authors the withheld family (P2).
4. The P3 stop gates are honored.
5. No subagent touches the real-lane PRs.

Native execution would carry a long mixed context into layers whose whole point is isolation.

Authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

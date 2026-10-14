# Macha focused acceptance review — PR #344 V3.1 consolidated corrective amendment

Date: 2026-10-14.

**Scope.** This is a design-text review of V3.1 against Macha audit B1–B35 (`7497486f`), plus a search for defects introduced by V3.1 itself. It is not a full re-archaeology.

**Read-only throughout.** No outcomes, DEV/SEALED data or pathology were opened.

**Verdict:** `V3_1_ACCEPTED__ERRATUM_V3_1_1_REQUIRED_BEFORE_WRITE_IMPLEMENTATION_PLAN_ONLY`

## 1. Custody

| object | identity |
|---|---|
| PR #344 head reviewed | `6bc6fa4de357af1392052ccc10105c9943e4ee72` (delta from `4fee29f4`: 3 new files only) |
| V3.1 amendment | `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c` (454 lines) |
| V3.1 focused re-audit | `ff2624567323a902e535a5e6236340baace325094507f78a8e71c98b03cc820d` |
| V3.1 current state | `6518926e776a7be7a494cfe529efaa9a5523ebb536ed8bd4d8bb16c2719bcb5d` |
| V80 non-regression binding (verified to support §21.3) | `results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json`: `"passed_gates": 291`, `"require_prior_v79_hard_passes_to_remain_pass": true`; V80 design §7 "every V79 hard gate that passed under V79 must pass under the successor" |
| new successors (correctly not inherited) | #353 R1 stress `1df20029`; #354 G7 convergence `d9004730`; #355 G9/S1/S2 geometry `6e5182e2` |

## 2. Disposition of B1–B35 — accepted

**CRITICAL B1–B4: closed at design-text level.**
- **B1:** freeze-before-use; nonce commit/reveal; hash-separated streams; integer offsets prohibited; single-realization attestation; sealed-only withheld family (§1). Residual: E1, E2.
- **B2:** expected-state estimand truth with **one common coordinate set per triplet**; frozen metric and tie tolerance; separate latent-fidelity truth; depth-asymmetry counterfactual (§7). Residual: E6.
- **B3:** fourth state `WITHHELD_BY_EVIDENCE_RIGHTS`; value-independent masks; content-hashed rights tokens; no hidden totals; visible bytes invariant across levels; denominator recomputation prohibited; modality-reveal ambiguity → `NOT_REHEARSED` (§6). Residual: E3.
- **B4:** candidate-shaped families and structural mirrors prohibited; biology-first vocabulary; post-realization mapping; out-of-basis, wrong-basis and capacity-only controls are verdict-bearing; mixture frozen with a candidate-independent rationale (§4).

**MAJOR B5–B20: closed, or correctly fail-closed as external blockers** (§2–§17). The blocker classes are explicit:
- G6 (`…NONDEGENERATE_MARGIN_AND_HUMAN_DECISION_CONTRACT`), including the synthetic→human flag prohibition;
- G8 (`…299_VS_599`); V3.1 rightly refuses to choose;
- R1 (`…EXECUTOR_AND_SOURCE_PARAMETERIZATION`);
- TargetPortfolio;
- G7 decision;
- G11/G12 scope limited.

The §16 three-way code-path declaration closes the "where interfaces permit" vagueness. Residual: E4.

**MODERATE/MINOR B21–B35:** carried as mandatory plan requirements (§22). Accepted.

**V79/V80 ruling (§21): accepted.**
- 207 confirmatory rows are binding; 85 post-terminal rows are forensic/non-blind only.
- The V80 "all 291" protection is real (verified above). Recording `BLOCKED_EXTERNAL_V79_TERMINAL_LOCK_VS_V80_291_NONREGRESSION_SELECTION` rather than rewriting V80 is the correct custody move.
- It blocks successor-estimator runs only, not production-synthetic planning.

**Re-audit labelling: accepted.** `DESIGN_TEXT_CLOSED__NOT_EXECUTABLE_TESTED` is honest, and the re-audit makes no executable-qualification claim.

## 3. Residual design-text defects (erratum V3.1.1 required)

By V3.1's own §0, a plan may not resolve these, so they must be fixed in design text.

**E1 (MODERATE) — the intent clause survives in the anti-weakening rule.**
- **Defect.** §1.1: "A changed version may not reduce difficulty or remove an adverse/control regime **merely because a method failed**." This is the same intent-based loophole as V3's "merely to obtain a PASS". §5 lets realism checks "reject a generator version", which gives a ready non-performance justification for an easier post-exposure version.
- **Repair.**
  1. After any downstream exposure, a new version may not reduce any frozen difficulty or regime measure, whatever the stated reason. The only exception is a separately documented generator **defect** (a bug against the frozen spec), recorded with evidence before any downstream run on the new version.
  2. The qualification report discloses the full version lineage and every downstream exposure.
  3. A version created after exposure is labelled `POST_EXPOSURE_VERSION` and must pass the §1.3 withheld-family check to qualify.

**E2 (MODERATE) — the "withheld" family is not concealed.**
- **Defect.** §1.3 withholds the sealed-only mechanism from development *realizations*. Its specification is bound into the frozen generator identity (§1.1), which in practice is readable source. Method developers can therefore know it, which defeats its anti-overfit purpose.
- **Repair.** Specify the withheld variant as a hash-committed sealed parameter or spec, in the same commit/reveal custody as the nonce. Only its existence and category are public before fit freeze; it is revealed after fit freeze.

**E3 (MODERATE) — the G7 anti-thinning enforcement point is unstated.**
- **Defect.** §6.5 says #346 is compatible "only after content-hash and anti-thinning enforcement above", and requires hostile rejection of a mislabeled thinning ladder. The real #346 validator is label-only (`td_real_evidence_ladder_contract_v1.py:49-59`). If enforcement lives only in the synthetic producer, a same-code-path rehearsal cannot show that the real path rejects a mislabeled ladder.
- **Repair.**
  - State that the rights-content binding and anti-thinning check must run in the real downstream validator for G7 static `SAME_CODE_PATH`. Until #346 or a successor enforces it, classify that property `SEMANTICS_COMPATIBLE_FIXTURE_ONLY`.
  - Raise the request to the real lane.

**E4 (MODERATE) — new frozen quantities have no derivation rules.**
- **Defect.** V3.1 introduces several quantities without saying how they are set: trivial-baseline ceilings (§5); the decoder-ceiling "authenticated envelope" (§8.2); minimum support-state counts (§20); the R1 tie tolerance τ (§7.1); and precision-budget targets (§9). Nor is there a stopping rule for the realism-check iteration (§5).
- **Repair.**
  - For each quantity, state the non-outcome derivation source: an authenticated real observation statistic, oracle/noise-floor arithmetic, or an explicitly labelled convention.
  - Require each to be frozen inside the §1.1 generator identity.
  - Add a stopping rule for realism iterations: a bounded number of pre-exposure revisions, after which the version is accepted or the axis is declared `BLOCKED_DESIGN`.

**E5 (MINOR) — the estimability mapping is implicit.** State that V3 §2.2 "ESTIMABLE" means `ESTIMABLE_WITH_TARGET_PRECISION`, where false abstention stays a hard error. Also state that for `IDENTIFIABLE_BUT_UNDERPOWERED` a calibrated COMPLETE with coverage-scored intervals is lawful as well as NOT_ESTIMABLE.

**E6 (MINOR) — the R1 metric source is unpinned.** The frozen ruler, metric, transform and τ for the estimand truth must equal the pinned real R1 executor's definitions once that blocker resolves. Until then they are synthetic-only, not a competing definition.

**E7 (MINOR) — the precedence list omits non-controlling documents.** Add that the `docs/agent` state, ledger and self-audit files (including R5 and the recovery/readiness ledgers) are non-controlling navigation, and cannot override §0 surfaces.

## 4. Next lawful action

`WRITE_V3_1_1_ERRATUM_ONLY` (E1–E7, design text).

Macha then performs a closure check of E1–E7 only; no further full audit is needed. On a pass, the next lawful action becomes **`WRITE_IMPLEMENTATION_PLAN_ONLY`**. The plan must:
- encode §22 and the §16 classifications;
- re-read the exact heads of #350–#355 and classify each.

No implementation, realization, fitting, scoring, target or representation selection, TD60, Stage4 or training is authorized.

Authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
